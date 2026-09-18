"""Presence is interval union intersected with active session segments, never frame count."""
from django.utils import timezone
from django.db import transaction
from classroom.models import Attendance, ClassSession, Event

def union(intervals):
    merged=[]
    for a,b in sorted(intervals):
        if b <= a: continue
        if merged and a <= merged[-1][1]: merged[-1]=(merged[-1][0], max(b,merged[-1][1]))
        else: merged.append((a,b))
    return merged

def active_intervals(session, now=None):
    now=now or timezone.now()
    return union([(s.start,s.end or min(now,session.heartbeat or now)) for s in session.segments.all()])

def duration(session):
    return sum((b-a).total_seconds() for a,b in active_intervals(session))

def measured(session, identity_id):
    active=active_intervals(session)
    observed=[(p.start,p.end) for p in session.presences.filter(identity_id=identity_id)]
    clips=[(max(a,c),min(b,d)) for a,b in observed for c,d in active if min(b,d)>max(a,c)]
    return union(clips)

def metrics(session, identity_id):
    spans=measured(session,identity_id)
    seconds=sum((b-a).total_seconds() for a,b in spans)
    total=duration(session)
    pct=min(100,100*seconds/total) if total else 0
    result='present' if pct>=session.present_threshold else 'partial' if pct>=session.partial_threshold else 'absent'
    if total<=0 or session.review: result='review'
    return dict(seconds=seconds,percentage=pct,result=result)

@transaction.atomic
def calculate(session):
    for p in session.participants.select_related('student__identity'):
        Attendance.objects.update_or_create(session=session,student=p.student,defaults=metrics(session,p.student.identity_id))

def recover():
    """Explicit startup recovery: never count unobserved time after a process crash."""
    for s in ClassSession.objects.filter(status__in=['live','paused']):
        end=s.heartbeat or s.started or timezone.now()
        s.segments.filter(end__isnull=True).update(end=end)
        s.status='interrupted';s.review=True;s.ended=end;s.save()
        calculate(s)
        Event.objects.create(session=s,kind='recovered',detail='Proceso interrumpido; revisar resultados.')
