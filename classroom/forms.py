from django import forms
from .models import SystemSettings
class SettingsForm(forms.ModelForm):
    class Meta:
        model=SystemSettings
        exclude=['id']
        labels={'present':'Presencia para Presente (%)','partial':'Presencia para Parcial (%)','required':'Asistencia histórica mínima (%)','similarity':'Umbral de similitud facial','reference_count':'Referencias por persona','lost_seconds':'Continuidad máxima entre detecciones (s)','width':'Ancho de cámara','height':'Alto de cámara'}
