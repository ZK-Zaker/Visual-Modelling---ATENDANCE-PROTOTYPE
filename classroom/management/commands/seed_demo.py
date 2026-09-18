from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from classroom.models import *
from classroom.services.attendance import calculate
class Command(BaseCommand):
    help='Crea un curso claramente SINTÉTICO separado; no carga fotos ni identidades reales.'
    def handle(self,*args,**kwargs):
        course,created=Course.objects.get_or_create(name='DEMO · Attendance Lab',group='SYNTHETIC',is_demo=True)
        if not created:self.stdout.write('El curso demo ya existe.');return
        students=[]
        for i in range(12):
            ident=Identity.objects.create(course=course,state='student')
            st=Student.objects.create(identity=ident,name=f'Estudiante Demo {i+1:02}',number=f'DEMO-{i+1:03}')
            Enrollment.objects.create(course=course,student=st);students.append(st)
        base=timezone.now()-timedelta(days=20)
        for j in range(8):
            start=base+timedelta(days=2*j)
            s=ClassSession.objects.create(course=course,title=f'Sesión demo {j+1:02}',started=start,ended=start+timedelta(hours=1),heartbeat=start+timedelta(hours=1),status='finished',review=j==5)
            Segment.objects.create(session=s,start=start,end=s.ended)
            for i,st in enumerate(students):
                Participant.objects.create(session=s,student=st)
                ratio=[.98,.92,.86,.75,.61,.45,.20,0][(i+j//3)%8]
                if ratio:
                    begin=start+timedelta(seconds=40)
                    Presence.objects.create(session=s,identity=st.identity,start=begin,end=begin+timedelta(seconds=ratio*1800))
                    Presence.objects.create(session=s,identity=st.identity,start=begin+timedelta(seconds=1800),end=min(s.ended,begin+timedelta(seconds=1800+ratio*1800)))
            calculate(s)
        self.stdout.write('Curso SINTÉTICO creado. Selecciónalo en el menú de curso.')
