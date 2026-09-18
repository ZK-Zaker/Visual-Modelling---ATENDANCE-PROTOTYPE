from django.core.management.base import BaseCommand
from classroom.models import Course,SystemSettings
class Command(BaseCommand):
    help='Crea configuración y curso inicial sin estudiantes ni asistencias ficticias.'
    def handle(self,*args,**options):
        SystemSettings.get()
        Course.objects.get_or_create(name='Visual Modelling for Information',group='9A',is_demo=False)
        self.stdout.write('Base lista. Crea tu usuario con: python manage.py createsuperuser')
