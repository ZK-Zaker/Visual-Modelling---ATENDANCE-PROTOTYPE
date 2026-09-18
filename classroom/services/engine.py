"""Single-process camera owner. Web requests share one producer; no frame DB writes."""
import threading,time,logging
from django.utils import timezone
from django.db import close_old_connections
from django.core.files.base import ContentFile
from classroom.models import *
from .attendance import calculate
log=logging.getLogger(__name__)

class Engine:
    def __init__(self):
        self.lock=threading.RLock();self.stop_event=threading.Event();self.thread=None
        self.frame=None;self.error='';self.camera=None;self.session_id=None;self.detected=[]
        self.fps=0;self.resolution='';self.tracks={};self.spans={};self.last_frame=0;self.gallery_epoch=0

    def status(self):
        with self.lock:
            return dict(connected=bool(self.thread and self.thread.is_alive() and self.frame),camera=self.camera,
                session=self.session_id,fps=round(self.fps,1),resolution=self.resolution,error=self.error,
                people=list(self.detected),count=len(self.detected))

    def start(self, index):
        with self.lock:
            if self.thread and self.thread.is_alive():
                if self.camera!=index: raise ValueError('Detén la cámara antes de cambiar la fuente.')
                return
            self.camera=index;self.error='';self.frame=None;self.stop_event.clear()
            self.thread=threading.Thread(target=self.run,name='camera-engine',daemon=True);self.thread.start()

    def stop(self):
        self.stop_event.set()
        t=self.thread
        if t: t.join(timeout=8)
        if t and t.is_alive(): raise ValueError('La cámara sigue cerrándose. Espera unos segundos.')
        with self.lock: self.frame=None;self.detected=[]

    def close_segment(self,s,at):
        for span in self.spans.values(): span.save()
        s.segments.filter(end__isnull=True).update(end=at)
        self.spans={}

    def transition(self,s,action):
        with self.lock:
            s.refresh_from_db();now=timezone.now()
            if action in ('start','resume'):
                if not self.status()['connected']: raise ValueError('Inicia la cámara y espera a ver video antes de iniciar la sesión.')
                if self.camera!=s.camera: raise ValueError('La cámara activa no coincide con la sesión.')
                if ClassSession.objects.filter(status__in=['live','paused']).exclude(pk=s.pk).exists(): raise ValueError('Hay otra sesión activa.')
                if (action=='start' and s.status!='new') or (action=='resume' and s.status!='paused'): raise ValueError('Transición de sesión inválida.')
                if action=='start':
                    cfg=SystemSettings.get();s.present_threshold=cfg.present;s.partial_threshold=cfg.partial;s.started=now
                    Participant.objects.bulk_create([Participant(session=s,student=e.student) for e in Enrollment.objects.filter(course=s.course,active=True,student__active=True)])
                s.status='live';s.heartbeat=now;s.save();Segment.objects.create(session=s,start=now)
                self.session_id=s.pk;self.tracks={};self.spans={}
            elif action=='pause':
                if s.status!='live': raise ValueError('Solo puedes pausar una sesión en curso.')
                self.close_segment(s,now);s.status='paused';s.heartbeat=now;s.save();self.session_id=None
            elif action=='end':
                if s.status not in ('live','paused'): raise ValueError('La sesión no está activa.')
                self.close_segment(s,now);s.ended=now;s.status='finished';s.heartbeat=now;s.save()
                self.session_id=None;calculate(s)
            else: raise ValueError('Acción desconocida.')
            Event.objects.create(session=s,kind=action)

    def gallery(self,course):
        from django.db.models import Q
        return list(ReferenceImage.objects.filter(Q(identity__student__enrollment__course=course,identity__student__enrollment__active=True,identity__student__active=True)|Q(identity__course=course,identity__state__in=['pending','visitor','intruder','ignored'])).select_related('identity').distinct())

    def resolve(self,feature,refs,threshold):
        import numpy as np
        scores={}
        for ref in refs:
            if ref.model!='sface-2021dec' or len(ref.embedding)!=len(feature): continue
            v=np.asarray(ref.embedding);score=float(np.dot(feature,v)/(np.linalg.norm(v)+1e-9))
            scores[ref.identity_id]=max(scores.get(ref.identity_id,-1),score)
        rank=sorted(scores.items(),key=lambda x:x[1],reverse=True)
        if not rank: return None
        if rank[0][1]<threshold or (len(rank)>1 and rank[0][1]-rank[1][1]<.06): return None
        return rank[0][0]

    def run(self):
        cap=None
        try:
            from .vision import Vision
            import cv2
            vision=Vision();cfg=SystemSettings.get()
            cap=cv2.VideoCapture(self.camera)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,cfg.width);cap.set(cv2.CAP_PROP_FRAME_HEIGHT,cfg.height)
            if not cap.isOpened(): raise RuntimeError('No se pudo abrir la cámara. Revisa el índice y los permisos del sistema.')
            last_flush=0;last_gallery=0;refs=[];last_course=None;epoch=-1
            while not self.stop_event.is_set():
                t=time.monotonic();ok,frame=cap.read()
                if not ok: raise RuntimeError('Cámara desconectada o sin imagen. La sesión requiere revisión.')
                with self.lock:
                    sid=self.session_id
                    s=ClassSession.objects.get(pk=sid) if sid else None
                    boxes=vision.detect(frame) if s else []
                    now=timezone.now();visible=[];seen=set();claimed=set()
                    if s and (t-last_gallery>3 or last_course!=s.course_id or epoch!=self.gallery_epoch):
                        refs=self.gallery(s.course);last_gallery=t;last_course=s.course_id;cfg=SystemSettings.get();epoch=self.gallery_epoch
                    for tid,box in boxes:
                        seen.add(tid);a,b,c,d=box
                        tr=self.tracks.setdefault(tid,dict(identity=None,last=t,checked=0,candidate=None,hits=0,saved=0,lastsave=0))
                        if t-tr['last']>cfg.lost_seconds:
                            tr.update(identity=None,candidate=None,hits=0)
                        tr['last']=t;face=None;face_identity=None
                        if t-tr['checked']>.7:
                            tr['checked']=t;face=vision.extract(frame[b:d,a:c])
                            if face is not None:
                                candidate=self.resolve(face[0],refs,cfg.similarity);face_identity=candidate
                                if candidate is not None:
                                    if tr['identity'] and tr['identity']!=candidate: tr['identity']=None
                                    tr['hits']=tr['hits']+1 if tr['candidate']==candidate else 1;tr['candidate']=candidate
                                    if tr['hits']>=3: tr['identity']=candidate
                                elif tr['identity'] is None:
                                    tr['hits']=tr['hits']+1 if tr['candidate']=='unknown' else 1;tr['candidate']='unknown'
                                    if tr['hits']>=3:
                                        ident=Identity.objects.create(course=s.course);tr['identity']=ident.pk;face_identity=ident.pk
                                        Event.objects.create(session=s,identity=ident,kind='unknown_created')
                        ident=Identity.objects.filter(pk=tr['identity']).first() if tr['identity'] else None
                        if ident and ident.pk in claimed:
                            ident=None # Ambiguous simultaneous tracks must not share identity.
                        if ident:
                            claimed.add(ident.pk)
                            if face is not None and face_identity==ident.pk and t-tr['lastsave']>1.5 and ident.references.count()<cfg.reference_count:
                                import numpy as np
                                previous=[np.asarray(x.embedding) for x in refs if x.identity_id==ident.pk]
                                if not previous or max(float(np.dot(face[0],v)) for v in previous)<.995:
                                    good,jpg=cv2.imencode('.jpg',face[1])
                                    if good:
                                        r=ReferenceImage(identity=ident,embedding=face[0].tolist())
                                        r.image.save(f'{ident.pk}-{time.time_ns()}.jpg',ContentFile(jpg.tobytes()),save=True)
                                        refs.append(r);tr['lastsave']=t
                            span=self.spans.get(ident.pk)
                            if span and (now-span.end).total_seconds()<=cfg.lost_seconds:
                                span.end=now;span.observations+=1
                            else:
                                if span: span.save()
                                span=Presence.objects.create(session=s,identity=ident,start=now,end=now)
                                self.spans[ident.pk]=span
                                Event.objects.create(session=s,identity=ident,kind='detected')
                            label=str(ident);state=ident.state
                        else: label=f'Track {tid}';state='unidentified'
                        visible.append(dict(track=tid,identity=ident.pk if ident else None,name=label,state=state))
                        color=(170,220,35) if state=='student' else (60,190,245)
                        cv2.rectangle(frame,(a,b),(c,d),color,2)
                        cv2.putText(frame,label.encode('ascii','replace').decode(),(a,max(20,b-8)),cv2.FONT_HERSHEY_SIMPLEX,.55,color,2)
                    for ident_id,span in list(self.spans.items()):
                        if (now-span.end).total_seconds()>cfg.lost_seconds:
                            span.save();del self.spans[ident_id]
                            Event.objects.create(session=s,identity_id=ident_id,kind='lost')
                    self.tracks={k:v for k,v in self.tracks.items() if t-v['last']<15}
                    if s and t-last_flush>=2:
                        for span in self.spans.values(): span.save()
                        s.heartbeat=now;s.save(update_fields=['heartbeat']);last_flush=t
                    self.detected=visible;self.resolution=f'{frame.shape[1]} × {frame.shape[0]}'
                    good,jpg=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,80])
                    if good: self.frame=jpg.tobytes();self.last_frame=t
                    self.fps=1/max(time.monotonic()-t,.001)
                self.stop_event.wait(.015)
        except Exception as exc:
            log.exception('Camera engine failed')
            with self.lock: self.error=f'{type(exc).__name__}: {exc}'
        finally:
            if cap is not None: cap.release()
            with self.lock:
                for span in self.spans.values(): span.save()
                if self.session_id:
                    s=ClassSession.objects.get(pk=self.session_id)
                    end=s.heartbeat or timezone.now();self.close_segment(s,end)
                    s.status='paused';s.review=True;s.save()
                    Event.objects.create(session=s,kind='camera_gap',detail=self.error or 'Cámara detenida durante sesión.')
                self.session_id=None;self.frame=None;self.detected=[];self.spans={}
            close_old_connections()

engine=Engine()
