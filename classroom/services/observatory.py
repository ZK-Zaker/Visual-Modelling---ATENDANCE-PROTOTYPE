"""Visual summaries derived from observations, never inferred attendance or attention."""
from collections import defaultdict
from classroom.models import Identity, Presence, Event
from .attendance import union


def wanted_cases(course):
    identities = list(Identity.objects.filter(course=course).select_related('student').prefetch_related('references'))
    spans = defaultdict(lambda: defaultdict(list))
    for p in Presence.objects.filter(identity__in=identities, session__course=course):
        spans[p.identity_id][p.session_id].append((p.start, p.end))
    for ident in identities:
        sessions = spans[ident.pk]
        ident.appearances = len(sessions)
        ident.observed_seconds = sum((b-a).total_seconds() for items in sessions.values() for a,b in union(items))
        ident.observed_minutes = round(ident.observed_seconds/60, 1)
        ident.last_seen = max((b for items in sessions.values() for a,b in items), default=None)
        ident.portrait = next(iter(ident.references.all()), None)
    identities.sort(key=lambda i: (i.appearances, i.observed_seconds, i.pk), reverse=True)
    return identities


def recent_signals(session):
    labels = {'detected':'Identidad observada', 'lost':'Fuera de vista',
              'unknown_created':'Nueva identidad pendiente', 'start':'Sesión iniciada',
              'resume':'Captura reanudada', 'pause':'Sesión pausada',
              'end':'Sesión finalizada', 'camera_gap':'Captura interrumpida'}
    return [dict(at=e.at.isoformat(), label=labels.get(e.kind,e.kind),
                 person=str(e.identity) if e.identity else '', kind=e.kind)
            for e in Event.objects.filter(session=session).select_related('identity','identity__student').order_by('-at','-pk')[:12]]
