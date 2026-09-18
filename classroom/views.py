import csv,io,time
from functools import wraps
from datetime import date
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse,StreamingHttpResponse,FileResponse,HttpResponse
from django.views.decorators.http import require_POST
from django.db import transaction,IntegrityError
from django.db.models import Count
from .models import *
from .forms import SettingsForm
from .services.engine import engine
from .services.analytics import course_data,session_data
from .services.attendance import calculate
from .services.observatory import wanted_cases, recent_signals

def teacher(fn):
    @wraps(fn)
    @login_required
    def wrapped(request,*args,**kwargs):
        if not request.user.is_staff: return HttpResponse('Acción reservada al profesor.',status=403)
        return fn(request,*args,**kwargs)
    return wrapped

def selected(request):
    courses=Course.objects.all().order_by('is_demo','pk')
    course=get_object_or_404(courses,pk=request.GET['course']) if request.GET.get('course') else courses.first()
    return courses,course

@login_required
def page(request,tab='dashboard',pk=None):
    courses,course=selected(request)
    if not course: return HttpResponse('Ejecuta python manage.py bootstrap para crear el curso inicial.',status=503)
    context=dict(tab=tab,courses=courses,course=course)
    if tab in ['dashboard','course','students','leaderboard','reports']:
        start=request.GET.get('start') or None;end=request.GET.get('end') or None
        try:
            if start: date.fromisoformat(start)
            if end: date.fromisoformat(end)
            if start and end and start>end: raise ValueError()
        except ValueError: return HttpResponse('Rango de fechas inválido.',status=400)
        context['data']=course_data(course,start,end)
    if tab in ['live','sessions']:
        context['sessions']=ClassSession.objects.filter(course=course).order_by('-created')
        context['live']=ClassSession.objects.filter(course=course,status__in=['live','paused']).first()
    if tab=='session':
        s=get_object_or_404(ClassSession,pk=pk);context.update(course=s.course,session=s,data=session_data(s))
    if tab=='student':
        st=get_object_or_404(Student,pk=pk);data=course_data(course)
        context.update(student=st,data=next((x for x in data['students'] if x['id']==st.pk),None),refs=st.identity.references.all())
    if tab=='unknown':
        cases=wanted_cases(course)
        context['identities']=[i for i in cases if i.state in ('pending','intruder')]
        context['resolved_identities']=[i for i in cases if i.state in ('visitor','ignored') or (i.state=='student' and i.portrait)]
        context['wanted_minutes']=round(sum(i.observed_seconds for i in context['identities'])/60,1)
        context['students']=Student.objects.filter(enrollment__course=course,active=True)
    if tab=='settings':context['form']=SettingsForm(instance=SystemSettings.get())
    return render(request,'app.html',context)

@teacher
@require_POST
def settings_save(request):
    form=SettingsForm(request.POST,instance=SystemSettings.get())
    if form.is_valid(): form.save();messages.success(request,'Configuración guardada. Los umbrales de sesiones anteriores se conservan.')
    else: messages.error(request,form.errors.as_text())
    return redirect('/settings/')

@teacher
@require_POST
def create_session(request):
    course=get_object_or_404(Course,pk=request.POST.get('course'))
    title=request.POST.get('title','').strip()
    try:
        camera=int(request.POST.get('camera',0))
        if not title or len(title)>160 or not 0<=camera<=10: raise ValueError()
    except ValueError: return HttpResponse('Título o índice de cámara inválido.',status=400)
    s=ClassSession.objects.create(course=course,title=title,camera=camera)
    return redirect(f'/live/?course={course.pk}')

@teacher
@require_POST
def session_action(request,pk,action):
    try: engine.transition(get_object_or_404(ClassSession,pk=pk),action)
    except ValueError as exc: return JsonResponse({'error':str(exc)},status=400)
    return JsonResponse({'ok':True})

@teacher
@require_POST
def camera_action(request,action):
    try:
        if action=='start':
            index=int(request.POST.get('index',0))
            if not 0<=index<=10: raise ValueError('Usa un índice entre 0 y 10.')
            engine.start(index)
        elif action=='stop':engine.stop()
        elif action=='scan':
            if engine.thread and engine.thread.is_alive():raise ValueError('Detén la cámara antes de explorar fuentes.')
            import cv2
            found=[]
            for i in range(4):
                cap=cv2.VideoCapture(i)
                if cap.isOpened(): found.append(i)
                cap.release()
            return JsonResponse({'cameras':found})
        else:raise ValueError('Acción desconocida.')
    except (ValueError,ImportError) as exc: return JsonResponse({'error':str(exc)},status=400)
    return JsonResponse({'ok':True})

@login_required
def live_status(request):
    state=engine.status()
    _,course=selected(request)
    session=ClassSession.objects.filter(pk=state['session']).first() if state['session'] else None
    if session and session.course_id!=getattr(course,'pk',None):
        return JsonResponse(dict(connected=False,camera=None,session=None,fps=0,resolution='',error='La cámara está capturando otro curso.',people=[],count=0,pulse=[],events=[]))
    if session: state['data']=session_data(session)
    else: session=ClassSession.objects.filter(course=course,status__in=['paused','finished','interrupted']).order_by('-created').first()
    state['events']=recent_signals(session) if session else []
    state['session_status']=session.status if session else 'preview'
    state['session_title']=session.title if session else ''
    if not state['session']: state['pulse']=[]
    return JsonResponse(state)

@login_required
def stream(request):
    def frames():
        while True:
            with engine.lock: jpg=engine.frame;alive=bool(engine.thread and engine.thread.is_alive())
            if jpg: yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'+jpg+b'\r\n'
            elif not alive: break
            time.sleep(.1)
    response=StreamingHttpResponse(frames(),content_type='multipart/x-mixed-replace; boundary=frame')
    response['Cache-Control']='no-store';return response

@teacher
@require_POST
def student_add(request):
    name=request.POST.get('name','').strip();number=request.POST.get('number','').strip()
    course=get_object_or_404(Course,pk=request.POST.get('course'))
    if not name or not number or len(name)>160 or len(number)>40:return HttpResponse('Nombre y matrícula válidos requeridos.',status=400)
    try:
        with transaction.atomic():
            ident=Identity.objects.create(course=course,state='student')
            student=Student.objects.create(identity=ident,name=name,number=number)
            Enrollment.objects.create(course=course,student=student)
    except IntegrityError:messages.error(request,'La matrícula ya existe.')
    return redirect(f'/students/?course={course.pk}')

@teacher
@require_POST
def identify(request,pk):
    with engine.lock:
        ident=get_object_or_404(Identity,pk=pk)
        try:
            with transaction.atomic():
                action=request.POST.get('action')
                if action=='identify':
                    if ident.state=='student':raise ValueError('La identidad ya es un estudiante.')
                    target=request.POST.get('target')
                    if target:
                        student=get_object_or_404(Student,pk=target,enrollment__course=ident.course)
                        destination=student.identity
                        Presence.objects.filter(identity=ident).update(identity=destination)
                        ReferenceImage.objects.filter(identity=ident).update(identity=destination)
                        Event.objects.filter(identity=ident).update(identity=destination)
                        ident.state='ignored';ident.save()
                    else:
                        name=request.POST.get('name','').strip();number=request.POST.get('number','').strip()
                        if not name or not number or len(name)>160 or len(number)>40:raise ValueError('Nombre y matrícula válidos requeridos.')
                        student=Student.objects.create(identity=ident,name=name,number=number)
                        ident.state='student';ident.save();Enrollment.objects.create(student=student,course=ident.course)
                    # Retroactive enrollment only in sessions where this identity was actually observed.
                    for s in ClassSession.objects.filter(course=ident.course,presences__identity=student.identity).distinct():
                        Participant.objects.get_or_create(session=s,student=student)
                        if s.status in ['finished','interrupted']:calculate(s)
                elif action in ['visitor','intruder','ignored','pending']:
                    if ident.state=='student':raise ValueError('No se puede reclasificar un alumno por esta acción.')
                    ident.state=action;ident.save()
                else:raise ValueError('Acción desconocida.')
                Audit.objects.create(actor=request.user,action=action,detail=f'Identidad {pk}')
            # Flush in-memory spans BEFORE reset so subsequent frames see updated references.
            for span in engine.spans.values():
                span.refresh_from_db(fields=['identity']);span.save()
            engine.tracks={};engine.spans={};engine.gallery_epoch+=1
            messages.success(request,'Identidad actualizada.')
        except (ValueError,IntegrityError) as exc:messages.error(request,f'No se guardó: {exc}')
    return redirect(f'/unknown/?course={ident.course_id}')

@login_required
def reference(request,pk):
    ref=get_object_or_404(ReferenceImage,pk=pk)
    try: response=FileResponse(ref.image.open('rb'),content_type='image/jpeg');response['Cache-Control']='private, no-store';return response
    except FileNotFoundError:return HttpResponse('Referencia no disponible.',status=404)

@teacher
@require_POST
def student_update(request,pk):
    st=get_object_or_404(Student,pk=pk)
    name=request.POST.get('name','').strip()
    if name and len(name)<=160: st.name=name
    st.active=request.POST.get('active')=='on';st.save()
    Audit.objects.create(actor=request.user,action='student_update',detail=f'Estudiante {pk}; activo={st.active}')
    return redirect(f'/students/{pk}/?course={request.POST.get("course",st.identity.course_id)}')

@login_required
def export(request,kind):
    _,course=selected(request)
    if not course:return HttpResponse(status=404)
    start=request.GET.get('start') or None;end=request.GET.get('end') or None
    try:
        if start:date.fromisoformat(start)
        if end:date.fromisoformat(end)
        if start and end and start>end:raise ValueError()
    except ValueError:return HttpResponse('Fechas inválidas',status=400)
    data=course_data(course,start,end)
    rows=[['Nombre','Matricula','Asistencia %','Permanencia %','Presentes','Parciales','Ausentes','Revision']]
    for st in data['students']:
        if request.GET.get('student') and str(st['id'])!=request.GET['student']:continue
        rows.append([st['name'],st['number'],round(st['rate'],2) if st['rate'] is not None else '',round(st['retention'],2) if st['retention'] is not None else '',st['present'],st['partial'],st['absent'],st['pending']])
    if kind=='csv':
        response=HttpResponse(content_type='text/csv; charset=utf-8');response.write('\ufeff');writer=csv.writer(response)
        for row in rows:writer.writerow([("'"+x if isinstance(x,str) and x.startswith(('=','+','-','@')) else x) for x in row])
        response['Content-Disposition']='attachment; filename="attendance.csv"';return response
    if kind!='pdf':return HttpResponse(status=404)
    from reportlab.platypus import SimpleDocTemplate,Table,TableStyle,Paragraph,Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape,A4
    from xml.sax.saxutils import escape
    buf=io.BytesIO();doc=SimpleDocTemplate(buf,pagesize=landscape(A4));styles=getSampleStyleSheet()
    safe=[[Paragraph(escape(str(v)),styles['BodyText']) for v in row] for row in rows]
    table=Table(safe,repeatRows=1,colWidths=[145,80,80,85,60,60,60,60]);table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dbe9e5')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),9),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]))
    doc.build([Paragraph('Attendance Viz · Reporte de curso',styles['Title']),Paragraph(escape(str(course)),styles['Normal']),Paragraph(f'Periodo: {start or "inicio"} / {end or "fin"}. Las sesiones en revisión se excluyen de porcentajes. Permanencia observada no mide atención.',styles['Normal']),Spacer(1,16),table])
    buf.seek(0);return FileResponse(buf,as_attachment=True,filename='attendance.pdf')

@teacher
@require_POST
def acknowledge_review(request,pk):
    s=get_object_or_404(ClassSession,pk=pk,status__in=['finished','interrupted'])
    reason=request.POST.get('reason','').strip()
    if len(reason)<10:return HttpResponse('Indica el motivo de revisión (mínimo 10 caracteres).',status=400)
    with transaction.atomic():
        s.review=False;s.save();calculate(s)
        Audit.objects.create(actor=request.user,action='review_accepted',detail=f'Sesión {pk}: {reason}. Se aceptan solo los intervalos observados.')
    messages.success(request,'Revisión registrada. Se calcularon resultados sobre la duración capturada; consulta la bitácora.')
    return redirect(f'/session/{pk}/')
