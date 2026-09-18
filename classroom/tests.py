from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.management import call_command
from classroom.models import *
from classroom.services.attendance import metrics,calculate,recover
from classroom.services.analytics import course_data
from classroom.services.engine import Engine,engine

class AttendanceFixture(TestCase):
    def setUp(self):
        self.course=Course.objects.create(name='VM')
        self.ident=Identity.objects.create(course=self.course,state='student')
        self.student=Student.objects.create(identity=self.ident,name='Alumno',number='001')
        Enrollment.objects.create(course=self.course,student=self.student)
        self.start=timezone.now()-timedelta(hours=2)
        self.s=ClassSession.objects.create(course=self.course,title='Sesión',status='finished',started=self.start,ended=self.start+timedelta(seconds=100),heartbeat=self.start+timedelta(seconds=100))
        Segment.objects.create(session=self.s,start=self.start,end=self.s.ended)
        Participant.objects.create(session=self.s,student=self.student)
    def span(self,a,b,identity=None):
        return Presence.objects.create(session=self.s,identity=identity or self.ident,start=self.start+timedelta(seconds=a),end=self.start+timedelta(seconds=b))
class AttendanceTests(AttendanceFixture):
    def test_union_prevents_double_count(self):
        self.span(0,40);self.span(20,70)
        self.assertEqual(metrics(self.s,self.ident.pk)['percentage'],70)
        self.assertEqual(metrics(self.s,self.ident.pk)['result'],'present')
    def test_pause_excluded_and_intervals_clipped(self):
        self.s.segments.all().delete()
        Segment.objects.create(session=self.s,start=self.start,end=self.start+timedelta(seconds=30))
        Segment.objects.create(session=self.s,start=self.start+timedelta(seconds=70),end=self.s.ended)
        self.span(0,100)
        self.assertEqual(metrics(self.s,self.ident.pk)['seconds'],60)
        self.assertEqual(metrics(self.s,self.ident.pk)['percentage'],100)
    def test_exact_boundaries(self):
        p=self.span(0,30)
        self.assertEqual(metrics(self.s,self.ident.pk)['result'],'partial')
        p.end=self.start+timedelta(seconds=29.9);p.save()
        self.assertEqual(metrics(self.s,self.ident.pk)['result'],'absent')
    def test_missing_camera_is_review_not_absence(self):
        self.s.review=True;self.s.save();calculate(self.s)
        self.assertEqual(self.s.records.get().result,'review')
        self.assertIsNone(course_data(self.course)['rate'])
    def test_zero_duration_review(self):
        self.s.segments.all().delete()
        self.assertEqual(metrics(self.s,self.ident.pk)['result'],'review')
    def test_idempotent_calculation(self):
        self.span(0,85);calculate(self.s);calculate(self.s)
        self.assertEqual(self.s.records.count(),1)
    def test_setting_changes_do_not_rewrite_threshold(self):
        self.span(0,75)
        cfg=SystemSettings.get();cfg.present=90;cfg.save()
        self.assertEqual(metrics(self.s,self.ident.pk)['result'],'present')
    def test_recovery_closes_at_checkpoint(self):
        self.s.status='live';self.s.heartbeat=self.start+timedelta(seconds=50);self.s.save()
        self.s.segments.update(end=None);recover();self.s.refresh_from_db()
        self.assertEqual(self.s.status,'interrupted');self.assertTrue(self.s.review)
        self.assertEqual(self.s.segments.get().end,self.s.heartbeat)
    def test_pause_flushes_in_memory_presence(self):
        self.s.status='live';self.s.save();p=self.span(0,30);p.end=self.start+timedelta(seconds=40)
        e=Engine();e.session_id=self.s.pk;e.spans={self.ident.pk:p}
        e.transition(self.s,'pause');p.refresh_from_db()
        self.assertEqual(p.end,self.start+timedelta(seconds=40))
    def test_multiple_sessions_rejected(self):
        self.s.status='live';self.s.save()
        new=ClassSession.objects.create(course=self.course,title='Otra')
        e=Engine();e.camera=0
        with patch.object(e,'status',return_value={'connected':True}):
            with self.assertRaises(ValueError):e.transition(new,'start')

class WebTests(AttendanceFixture):
    def setUp(self):
        super().setUp()
        self.user=get_user_model().objects.create_user('teacher',password='long-test-password',is_staff=True)
        self.client.force_login(self.user)
    def test_all_pages_and_exports(self):
        self.span(0,80);calculate(self.s)
        for path in ['/','/live/','/students/','/sessions/','/course/','/unknown/','/leaderboard/','/reports/','/settings/',f'/session/{self.s.pk}/',f'/students/{self.student.pk}/','/api/live/','/export/csv/','/export/pdf/']:
            with self.subTest(path=path):self.assertEqual(self.client.get(path).status_code,200)
    def test_anonymous_blocked(self):
        self.client.logout()
        for path in ['/','/api/live/','/stream/','/export/csv/']:
            self.assertEqual(self.client.get(path).status_code,302)
    def test_coordinator_read_only(self):
        self.user.is_staff=False;self.user.save()
        self.assertEqual(self.client.get('/course/').status_code,200)
        self.assertEqual(self.client.post('/api/camera/stop/').status_code,403)
    def test_csrf_required(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.user)
        self.assertEqual(client.post('/api/camera/stop/').status_code,403)
    def test_identify_new_preserves_history(self):
        ident=Identity.objects.create(course=self.course);self.span(0,80,ident)
        self.client.post(f'/identity/{ident.pk}/',{'action':'identify','name':'Nuevo','number':'002'})
        ident.refresh_from_db();self.assertEqual(ident.state,'student')
        self.assertEqual(Attendance.objects.get(student=ident.student,session=self.s).percentage,80)
    def test_merge_unions_history(self):
        self.span(0,60);unknown=Identity.objects.create(course=self.course);self.span(20,80,unknown)
        self.client.post(f'/identity/{unknown.pk}/',{'action':'identify','target':self.student.pk})
        self.assertEqual(Attendance.objects.get(student=self.student,session=self.s).percentage,80)
    def test_duplicate_registration_rolls_back(self):
        count=Identity.objects.count()
        self.client.post('/students/add/',{'name':'Otro','number':'001','course':self.course.pk})
        self.assertEqual(Identity.objects.count(),count)
    def test_invalid_settings_rejected(self):
        cfg=SystemSettings.get()
        self.client.post('/settings/save/',{'present':20,'partial':30,'required':80,'similarity':.45,'reference_count':5,'lost_seconds':2,'width':640,'height':480})
        cfg.refresh_from_db();self.assertEqual(cfg.present,70)
    def test_invalid_dates_return_400(self):
        self.assertEqual(self.client.get('/?start=bad').status_code,400)
        self.assertEqual(self.client.get('/export/csv/?start=2026-09-10&end=2026-08-01').status_code,400)
    def test_csv_formula_escaped(self):
        self.student.name='=DANGER';self.student.save();calculate(self.s)
        self.assertIn("'=DANGER",self.client.get('/export/csv/').content.decode())
    def test_demo_is_separate_and_idempotent(self):
        call_command('seed_demo');call_command('seed_demo')
        self.assertEqual(Course.objects.filter(is_demo=True).count(),1)
        self.assertEqual(Enrollment.objects.filter(course=self.course).count(),1)

class EngineIntegrationTests(AttendanceFixture):
    def test_known_identity_pipeline_with_simulated_camera(self):
        import numpy as np,itertools
        from unittest.mock import MagicMock
        self.s.status='live';self.s.save();self.s.segments.update(end=None)
        ReferenceImage.objects.create(identity=self.ident,embedding=[1.,0.],image='fixture-not-served.jpg')
        image=np.zeros((100,100,3),dtype=np.uint8)
        vision=MagicMock();vision.detect.return_value=[(1,(0,0,100,100))]
        vision.extract.return_value=(np.array([1.,0.]),image)
        cap=MagicMock();cap.isOpened.return_value=True
        cap.read.side_effect=[(True,image.copy()) for _ in range(8)]+[(False,None)]
        e=Engine();e.session_id=self.s.pk;e.camera=0
        with patch('classroom.services.vision.Vision',return_value=vision),patch('cv2.VideoCapture',return_value=cap),patch('classroom.services.engine.time.monotonic',side_effect=itertools.count(1)),patch('classroom.services.engine.log.exception'):
            e.run()
        self.assertTrue(Presence.objects.filter(session=self.s,identity=self.ident).exists())
        self.assertEqual(Identity.objects.count(),1)
        self.s.refresh_from_db();self.assertEqual(self.s.status,'paused');self.assertTrue(self.s.review)
        self.assertIn('Cámara desconectada',e.error)
    def test_closed_camera_reports_error(self):
        from unittest.mock import MagicMock
        cap=MagicMock();cap.isOpened.return_value=False;e=Engine()
        with patch('classroom.services.vision.Vision'),patch('cv2.VideoCapture',return_value=cap),patch('classroom.services.engine.log.exception'):
            e.run()
        self.assertIn('No se pudo abrir',e.error)
    def test_ambiguous_similarity_rejected(self):
        import numpy as np
        from types import SimpleNamespace
        refs=[SimpleNamespace(model='sface-2021dec',embedding=[1.,0.],identity_id=1),SimpleNamespace(model='sface-2021dec',embedding=[.999,.01],identity_id=2)]
        self.assertIsNone(Engine().resolve(np.array([1.,0.]),refs,.45))
