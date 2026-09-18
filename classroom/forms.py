from django import forms
from .models import SystemSettings
class SettingsForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for field,label in [('away_notice','Fuera de vista (segundos)'),('away_brief','Pausa breve (segundos)'),('away_long','Ausencia prolongada (segundos)')]:
            self.fields[field].label=label
            self.fields[field].help_text='Aviso visual durante captura continua; no modifica la asistencia.'
    class Meta:
        model=SystemSettings
        exclude=['id']
        labels={'present':'Presencia para Presente (%)','partial':'Presencia para Parcial (%)','required':'Asistencia histórica mínima (%)','similarity':'Umbral de similitud facial','reference_count':'Referencias por persona','lost_seconds':'Continuidad máxima entre detecciones (s)','width':'Ancho de cámara','height':'Alto de cámara'}
