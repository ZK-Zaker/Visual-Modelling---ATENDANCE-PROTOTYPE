"""Session-local messages from continuous observations, independent of attendance."""
from collections import deque


class AwayMonitor:
    def __init__(self):
        self.reset()

    def reset(self):
        self.students={};self.previous=None;self.session=None
        self.returns=deque(maxlen=8);self.alerts=[];self.group_warning=False

    def update(self, session, tick, people, settings):
        # Long stalls have unknown coverage. Start fresh, never count the gap.
        if session!=self.session or (self.previous is not None and (tick-self.previous>5 or tick<self.previous)):
            self.reset();self.session=session
        delta=0 if self.previous is None else tick-self.previous
        self.previous=tick
        visible={p['identity']:p for p in people if p['state']=='student' and p['identity'] is not None}
        for identity,p in visible.items():
            old=self.students.get(identity)
            if old and not old['suppressed'] and old['seconds']>=settings.away_notice:
                self.returns.append(dict(identity=identity,name=p['name'],seconds=int(old['seconds']),level='returned',until=tick+30))
            self.students[identity]=dict(name=p['name'],seconds=0,suppressed=False)
        for identity,record in self.students.items():
            if identity not in visible:record['seconds']+=delta
        # Three or more identities lost within five seconds, at least half the
        # recently visible group: suppress those individual inferences until seen.
        recent=[r for i,r in self.students.items() if i not in visible and 0<r['seconds']<=5]
        if len(recent)>=3 and len(recent)>=len(visible):
            for record in recent:record['suppressed']=True
        self.group_warning=any(r['suppressed'] for r in self.students.values())
        alerts=[]
        for identity,r in self.students.items():
            if r['suppressed'] or r['seconds']<settings.away_notice:continue
            level='long' if r['seconds']>=settings.away_long else 'brief' if r['seconds']>=settings.away_brief else 'notice'
            alerts.append(dict(identity=identity,name=r['name'],seconds=int(r['seconds']),level=level))
        alerts.sort(key=lambda a:a['seconds'],reverse=True)
        self.returns=deque((r for r in self.returns if r['until']>tick and r['identity'] in visible),maxlen=8)
        self.alerts=alerts+[dict((k,v) for k,v in r.items() if k!='until') for r in reversed(self.returns)]
