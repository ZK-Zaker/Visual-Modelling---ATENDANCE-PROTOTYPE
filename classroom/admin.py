from django.contrib import admin
from .models import Course, Student, Enrollment, SystemSettings, Audit
for model in [Course, Student, Enrollment, SystemSettings, Audit]: admin.site.register(model)
