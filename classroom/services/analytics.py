from classroom.models import *
from .attendance import duration, metrics, measured

def session_data(s):
    rows=[]
    for p in s.participants.select_related('student__identity'):
        m=metrics(s,p.student.identity_id)
        spans=measured(s,p.student.identity_id)
        origin=s.started or s.created
        rows.append(dict(id=p.student_id,name=p.student.name,number=p.student.number,**m,
            intervals=[[(a-origin).total_seconds(),(b-origin).total_seconds()] for a,b in spans],
            first=spans[0][0].isoformat() if spans else None,last=spans[-1][1].isoformat() if spans else None,
            longest=max([(b-a).total_seconds() for a,b in spans],default=0)))
    return dict(id=s.pk,title=s.title,status=s.status,review=s.review,seconds=duration(s),
        started=s.started.isoformat() if s.started else None,ended=s.ended.isoformat() if s.ended else None,
        segments=[[(x.start-(s.started or s.created)).total_seconds(),((x.end or s.heartbeat or x.start)-(s.started or s.created)).total_seconds()] for x in s.segments.all()],
        rows=rows,unknown=s.presences.filter(identity__state='pending').values('identity_id').distinct().count())

def course_data(course, start=None, end=None):
    sessions=ClassSession.objects.filter(course=course,status__in=['finished','interrupted']).order_by('started')
    if start: sessions=sessions.filter(started__date__gte=start)
    if end: sessions=sessions.filter(started__date__lte=end)
    ss=list(sessions);setting=SystemSettings.get();students=[];trend=[]
    student_ids=set(Enrollment.objects.filter(course=course,active=True).values_list('student_id',flat=True))
    student_ids.update(Participant.objects.filter(session__in=ss).values_list('student_id',flat=True))
    for st in Student.objects.filter(pk__in=student_ids):
        records=list(Attendance.objects.filter(student=st,session__in=ss).select_related('session'))
        valid=[r for r in records if r.result!='review']
        rate=100*sum(r.result=='present' for r in valid)/len(valid) if valid else None
        total=sum(duration(r.session) for r in valid)
        retention=100*sum(r.seconds for r in valid)/total if total else None
        students.append(dict(id=st.pk,name=st.name,number=st.number,rate=rate,retention=retention,
            valid=len(valid),pending=len(records)-len(valid),present=sum(r.result=='present' for r in valid),
            partial=sum(r.result=='partial' for r in valid),absent=sum(r.result=='absent' for r in valid),
            risk=rate is not None and rate<setting.required,
            history=[dict(session=r.session_id,title=r.session.title,result=r.result,percentage=r.percentage) for r in records]))
    for s in ss:
        rr=list(s.records.all());valid=[r for r in rr if r.result!='review']
        trend.append(dict(id=s.pk,title=s.title,date=s.started.isoformat() if s.started else '',
            rate=100*sum(r.result=='present' for r in valid)/len(valid) if valid else None,review=s.review,
            retention=sum(r.percentage for r in valid)/len(valid) if valid else None))
    rates=[x['rate'] for x in students if x['rate'] is not None]
    retention=[x['retention'] for x in students if x['retention'] is not None]
    return dict(students=students,trend=trend,required=setting.required,sessions=len(ss),
        review=sum(s.review for s in ss),rate=sum(rates)/len(rates) if rates else None,
        retention=sum(retention)/len(retention) if retention else None,risk=sum(x['risk'] for x in students))
