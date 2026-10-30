from django.urls import path

from . import views

app_name = 'wellness'

urlpatterns = [
    path('', views.today, name='today'),
    path('welcome/', views.welcome, name='welcome'),
    path('habits/', views.habit_list, name='habit_list'),
    path('habits/new/', views.habit_new, name='habit_new'),
    path('habits/<int:pk>/', views.habit_detail, name='habit_detail'),
    path('habits/<int:pk>/edit/', views.habit_edit, name='habit_edit'),
    path('habits/<int:pk>/check/', views.habit_check, name='habit_check'),
    path('habits/<int:pk>/<str:action>/', views.habit_action,
         name='habit_action'),
    path('guide/', views.guide_page, name='guide'),
    path('tips/', views.tip_seen, name='tip_seen'),
    # The app shell - answered without a login; nothing personal in it.
    path('app/manifest.webmanifest', views.manifest, name='manifest'),
    path('app/sw.js', views.service_worker, name='service_worker'),
    path('app/<str:name>', views.asset, name='asset'),
]
