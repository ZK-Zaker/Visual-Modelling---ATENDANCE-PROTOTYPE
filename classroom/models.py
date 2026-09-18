from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings

class Course(models.Model):
    name = models.CharField(max_length=160)
    group = models.CharField(max_length=40, default='9A')
    is_demo = models.BooleanField(default=False)
    def __str__(self): return f'{self.name} · {self.group}'

class Identity(models.Model):
    STATES = [('pending','Pendiente'),('student','Estudiante'),('visitor','Visitante'),('intruder','Posible intruso'),('ignored','Ignorado')]
    course = models.ForeignKey(Course,on_delete=models.PROTECT)
    state = models.CharField(max_length=16,choices=STATES,default='pending')
    display_name = models.CharField(max_length=160,blank=True,default='')
    created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        try: return self.student.name
        except Student.DoesNotExist: return self.display_name or f'Unknown {self.pk:03d}'

class Student(models.Model):
    identity = models.OneToOneField(Identity,on_delete=models.PROTECT,related_name='student')
    name = models.CharField(max_length=160)
    number = models.CharField(max_length=40,unique=True)
    active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Enrollment(models.Model):
    course = models.ForeignKey(Course,on_delete=models.CASCADE)
    student = models.ForeignKey(Student,on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['course','student'],name='one_enrollment')]

class ReferenceImage(models.Model):
    identity = models.ForeignKey(Identity,on_delete=models.CASCADE,related_name='references')
    image = models.ImageField(upload_to='reference_images/%Y/%m/')
    embedding = models.JSONField(default=list)
    model = models.CharField(max_length=40,default='sface-2021dec')
    created = models.DateTimeField(auto_now_add=True)

class SystemSettings(models.Model):
    present = models.FloatField(default=70,validators=[MinValueValidator(1),MaxValueValidator(100)])
    partial = models.FloatField(default=30,validators=[MinValueValidator(0),MaxValueValidator(99)])
    required = models.FloatField(default=80,validators=[MinValueValidator(1),MaxValueValidator(100)])
    similarity = models.FloatField(default=.45,validators=[MinValueValidator(.1),MaxValueValidator(.99)])
    reference_count = models.PositiveIntegerField(default=5,validators=[MinValueValidator(1),MaxValueValidator(10)])
    lost_seconds = models.FloatField(default=2,validators=[MinValueValidator(.5),MaxValueValidator(5)])
    away_notice = models.PositiveIntegerField(default=30,validators=[MinValueValidator(5),MaxValueValidator(3600)])
    away_brief = models.PositiveIntegerField(default=120,validators=[MinValueValidator(10),MaxValueValidator(7200)])
    away_long = models.PositiveIntegerField(default=300,validators=[MinValueValidator(15),MaxValueValidator(14400)])
    width = models.PositiveIntegerField(default=640,validators=[MinValueValidator(320),MaxValueValidator(1920)])
    height = models.PositiveIntegerField(default=480,validators=[MinValueValidator(240),MaxValueValidator(1080)])
    def clean(self):
        if self.partial >= self.present: raise ValidationError('Parcial debe ser menor que Presente.')
        if not self.away_notice < self.away_brief < self.away_long:
            raise ValidationError('Los avisos deben cumplir: fuera de vista < pausa breve < ausencia prolongada.')
    @classmethod
    def get(cls): return cls.objects.get_or_create(pk=1)[0]

class ClassSession(models.Model):
    STATES=[('new','Sin iniciar'),('live','En curso'),('paused','Pausada'),('finished','Finalizada'),('interrupted','Interrumpida')]
    course=models.ForeignKey(Course,on_delete=models.PROTECT)
    title=models.CharField(max_length=160)
    status=models.CharField(max_length=16,choices=STATES,default='new')
    camera=models.PositiveIntegerField(default=0)
    started=models.DateTimeField(null=True,blank=True)
    ended=models.DateTimeField(null=True,blank=True)
    heartbeat=models.DateTimeField(null=True,blank=True)
    review=models.BooleanField(default=False)
    present_threshold=models.FloatField(default=70)
    partial_threshold=models.FloatField(default=30)
    created=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title

class Participant(models.Model):
    session=models.ForeignKey(ClassSession,on_delete=models.CASCADE,related_name='participants')
    student=models.ForeignKey(Student,on_delete=models.PROTECT)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['session','student'],name='one_participant')]

class Segment(models.Model):
    session=models.ForeignKey(ClassSession,on_delete=models.CASCADE,related_name='segments')
    start=models.DateTimeField()
    end=models.DateTimeField(null=True)

class Presence(models.Model):
    session=models.ForeignKey(ClassSession,on_delete=models.CASCADE,related_name='presences')
    identity=models.ForeignKey(Identity,on_delete=models.PROTECT)
    start=models.DateTimeField()
    end=models.DateTimeField()
    observations=models.PositiveIntegerField(default=1)

class Attendance(models.Model):
    session=models.ForeignKey(ClassSession,on_delete=models.CASCADE,related_name='records')
    student=models.ForeignKey(Student,on_delete=models.PROTECT)
    seconds=models.FloatField(default=0)
    percentage=models.FloatField(default=0)
    result=models.CharField(max_length=16,default='absent')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['session','student'],name='one_attendance')]

class Event(models.Model):
    session=models.ForeignKey(ClassSession,on_delete=models.CASCADE,related_name='events',null=True)
    identity=models.ForeignKey(Identity,on_delete=models.SET_NULL,null=True)
    at=models.DateTimeField(auto_now_add=True)
    kind=models.CharField(max_length=40)
    detail=models.CharField(max_length=250,blank=True)

class Audit(models.Model):
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True)
    at=models.DateTimeField(auto_now_add=True)
    action=models.CharField(max_length=80)
    detail=models.TextField()
