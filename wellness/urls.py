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
    # WL-2, 30 Oct 2026 - Journal and Body.
    path('journal/', views.journal_list, name='journal_list'),
    path('journal/new/', views.journal_new, name='journal_new'),
    path('journal/<int:pk>/', views.journal_detail, name='journal_detail'),
    path('journal/<int:pk>/edit/', views.journal_edit, name='journal_edit'),
    path('journal/<int:pk>/delete/', views.journal_delete,
         name='journal_delete'),
    path('body/', views.body_home, name='body'),
    path('body/weigh/', views.body_weigh, name='body_weigh'),
    path('body/measure/', views.body_measure, name='body_measure'),
    path('body/goal/', views.body_goal, name='body_goal'),
    path('body/<int:pk>/delete/', views.body_delete, name='body_delete'),
    path('guide/', views.guide_page, name='guide'),
    path('tips/', views.tip_seen, name='tip_seen'),
    # The app shell - answered without a login; nothing personal in it.
    path('app/manifest.webmanifest', views.manifest, name='manifest'),
    path('app/sw.js', views.service_worker, name='service_worker'),
    path('app/<str:name>', views.asset, name='asset'),
]
