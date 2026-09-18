from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth
from classroom import views as v
urlpatterns=[path('admin/',admin.site.urls),path('login/',auth.LoginView.as_view(),name='login'),path('logout/',auth.LogoutView.as_view(),name='logout'),path('',v.page),
path('session/<int:pk>/review/',v.acknowledge_review),path('sessions/new/',v.create_session),path('sessions/<int:pk>/<str:action>/',v.session_action),
path('session/<int:pk>/',v.page,{'tab':'session'}),path('students/add/',v.student_add),
path('students/<int:pk>/',v.page,{'tab':'student'}),path('students/<int:pk>/update/',v.student_update),
path('identity/<int:pk>/',v.identify),path('reference/<int:pk>/',v.reference),
path('settings/save/',v.settings_save),path('api/camera/<str:action>/',v.camera_action),
path('api/live/',v.live_status),path('stream/',v.stream),path('export/<str:kind>/',v.export)]
for tab in ['live','students','sessions','unknown','leaderboard','course','reports','settings']:
    urlpatterns.append(path(tab+'/',v.page,{'tab':tab}))
