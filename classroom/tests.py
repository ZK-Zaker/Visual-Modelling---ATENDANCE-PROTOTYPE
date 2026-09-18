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


class ObservatoryTests(AttendanceFixture):
    def setUp(self):
        super().setUp()
        self.user=get_user_model().objects.create_user('observer-test',password='test-password',is_staff=True)
        self.client.force_login(self.user)
    def test_wanted_unions_overlaps_and_ranks_sessions_first(self):
        from classroom.services.observatory import wanted_cases
        one=Identity.objects.create(course=self.course)
        two=Identity.objects.create(course=self.course,state='intruder')
        self.span(0,60,one);self.span(20,80,one)
        self.span(0,2,two)
        other=ClassSession.objects.create(course=self.course,title='Otra')
        Presence.objects.create(session=other,identity=two,start=self.start,end=self.start+timedelta(seconds=2))
        cases=wanted_cases(self.course)
        self.assertEqual(cases[0].pk,two.pk)
        self.assertEqual(next(i for i in cases if i.pk==one.pk).observed_seconds,80)
        response=self.client.get('/unknown/')
        self.assertContains(response,'WANTED')
        self.assertEqual(len(response.context['identities']),2)

    def test_resolved_cases_leave_open_board(self):
        ident=Identity.objects.create(course=self.course)
        self.client.post(f'/identity/{ident.pk}/',{'action':'visitor'})
        response=self.client.get('/unknown/')
        self.assertEqual(len(response.context['identities']),0)
        self.assertEqual(response.context['resolved_identities'][0].pk,ident.pk)

    def test_pulse_sampling_pause_and_session_reset(self):
        e=Engine()
        people=[dict(state='student',identity=1),dict(state='pending',identity=2),dict(state='unidentified',identity=None)]
        e.sample_pulse(1,self.start,people)
        e.sample_pulse(1,self.start+timedelta(seconds=1),[])
        self.assertEqual(len(e.pulse),1)
        self.assertEqual(e.pulse[0]['students'],1)
        self.assertEqual(e.pulse[0]['pending'],1)
        self.assertEqual(e.pulse[0]['unconfirmed'],1)
        e.pulse_break=True
        e.sample_pulse(1,self.start+timedelta(seconds=3),[])
        self.assertTrue(e.pulse[-1]['gap'])
        e.sample_pulse(2,self.start+timedelta(seconds=4),[])
        self.assertEqual(len(e.pulse),1)
        self.assertEqual(e.pulse[-1]['total'],0)

    def test_live_does_not_leak_other_course(self):
        other=Course.objects.create(name='Otro curso')
        with patch.object(engine,'status',return_value=dict(session=self.s.pk)):
            response=self.client.get(f'/api/live/?course={other.pk}')
        self.assertEqual(response.json()['people'],[])
        self.assertEqual(response.json()['pulse'],[])
        self.assertIsNone(response.json()['session'])

    def test_named_intruder_is_not_enrolled_and_keeps_evidence(self):
        ident=Identity.objects.create(course=self.course,state='intruder')
        span=self.span(0,50,ident)
        before=Student.objects.count()
        response=self.client.post(f'/identity/{ident.pk}/',{'action':'name_identity','display_name':'Alex','classification':'intruder'})
        self.assertEqual(response.status_code,302)
        ident.refresh_from_db();span.refresh_from_db()
        self.assertEqual((str(ident),ident.state),('Alex','intruder'))
        self.assertEqual(span.identity_id,ident.pk)
        self.assertEqual(Student.objects.count(),before)
        self.assertFalse(Participant.objects.filter(student__identity=ident).exists())
        self.assertContains(self.client.get('/unknown/'),'Alex')

    def test_visitor_can_be_named_in_archive_then_enrolled_explicitly(self):
        ident=Identity.objects.create(course=self.course,state='visitor')
        self.span(0,80,ident)
        self.client.post(f'/identity/{ident.pk}/',{'action':'name_identity','display_name':'Visita','classification':'visitor'})
        self.assertContains(self.client.get('/unknown/'),'Visita')
        self.client.post(f'/identity/{ident.pk}/',{'action':'identify','name':'Nuevo alumno','number':'002'})
        ident.refresh_from_db()
        self.assertEqual(ident.state,'student')
        self.assertEqual(Attendance.objects.get(student=ident.student,session=self.s).percentage,80)

    def test_name_action_cannot_create_student_or_bypass_role(self):
        ident=Identity.objects.create(course=self.course,state='intruder')
        self.client.post(f'/identity/{ident.pk}/',{'action':'name_identity','display_name':'Alex','classification':'student'})
        ident.refresh_from_db();self.assertEqual(ident.display_name,'')
        self.user.is_staff=False;self.user.save()
        self.assertEqual(self.client.post(f'/identity/{ident.pk}/',{'action':'name_identity','display_name':'Alex'}).status_code,403)

    def test_away_thresholds_require_strict_order(self):
        from classroom.forms import SettingsForm
        from django.forms.models import model_to_dict
        cfg=SystemSettings.get();values=model_to_dict(cfg)
        values.update(away_notice=30,away_brief=30,away_long=300)
        self.assertFalse(SettingsForm(values,instance=cfg).is_valid())
        values['away_brief']=120
        self.assertTrue(SettingsForm(values,instance=cfg).is_valid())


class AwayMonitorTests(TestCase):
    def setUp(self):
        from classroom.services.away import AwayMonitor
        from types import SimpleNamespace
        self.monitor=AwayMonitor()
        self.cfg=SimpleNamespace(away_notice=30,away_brief=120,away_long=300)
        self.person=dict(identity=1,state='student',name='Alumno')

    def feed(self,start,end,people,session=1):
        for tick in range(start,end+1):self.monitor.update(session,tick,people,self.cfg)

    def test_thresholds_and_return(self):
        self.feed(0,0,[self.person]);self.feed(1,29,[])
        self.assertEqual(self.monitor.alerts,[])
        self.feed(30,30,[]);self.assertEqual(self.monitor.alerts[0]['level'],'notice')
        self.feed(31,120,[]);self.assertEqual(self.monitor.alerts[0]['level'],'brief')
        self.feed(121,300,[]);self.assertEqual(self.monitor.alerts[0]['level'],'long')
        self.feed(301,301,[self.person]);self.assertEqual(self.monitor.alerts[0]['level'],'returned')
        self.feed(302,332,[self.person]);self.assertEqual(self.monitor.alerts,[])

    def test_unknowns_and_never_seen_students_do_not_create_alerts(self):
        self.feed(0,0,[dict(identity=2,state='intruder',name='Visita')]);self.feed(1,400,[])
        self.assertEqual(self.monitor.alerts,[])

    def test_stall_reset_pause_and_other_session_do_not_count_gaps(self):
        self.feed(0,0,[self.person]);self.feed(1,40,[])
        self.monitor.update(1,100,[],self.cfg)
        self.assertEqual(self.monitor.alerts,[])
        self.feed(101,101,[self.person]);self.feed(102,150,[])
        self.monitor.reset();self.feed(151,151,[])
        self.assertEqual(self.monitor.alerts,[])
        self.feed(152,152,[self.person]);self.feed(153,200,[])
        self.feed(201,201,[],session=2);self.assertEqual(self.monitor.alerts,[])

    def test_collective_loss_is_suppressed_until_reacquired(self):
        group=[dict(identity=i,state='student',name=f'Alumno {i}') for i in range(4)]
        self.feed(0,0,group);self.feed(1,400,[])
        self.assertTrue(self.monitor.group_warning);self.assertEqual(self.monitor.alerts,[])
        self.feed(401,401,group)
        self.assertFalse(self.monitor.group_warning);self.assertEqual(self.monitor.alerts,[])
        self.feed(402,432,group[1:])
        self.assertEqual(self.monitor.alerts[0]['identity'],0)
