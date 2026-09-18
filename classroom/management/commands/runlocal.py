from django.core.management.base import BaseCommand
from django.core.management import call_command
from classroom.services.attendance import recover
class Command(BaseCommand):
    help='Servidor local de un proceso, sin autoreload; recupera sesiones interrumpidas.'
    def handle(self,*args,**options):
        recover()
        call_command('runserver','127.0.0.1:8000',use_reloader=False)
