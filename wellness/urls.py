from django.urls import path

from . import views
from . import views_cycle as CY
from . import views_workouts as W

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
    # WL-3, 30 Oct 2026 - Workouts.
    path('workouts/', W.home, name='workouts'),
    path('workouts/kit/', W.kit, name='kit'),
    path('workouts/routines/new/', W.routine_edit, name='routine_new'),
    path('workouts/routines/<int:pk>/', W.routine_edit, name='routine_edit'),
    path('workouts/routines/<int:pk>/delete/', W.routine_delete,
         name='routine_delete'),
    path('workouts/start/', W.session_start, name='session_start'),
    path('workouts/<int:pk>/live/', W.session_live, name='session_live'),
    path('workouts/<int:pk>/', W.session_detail, name='session_detail'),
    path('workouts/<int:pk>/add/', W.set_add, name='set_add'),
    path('workouts/<int:pk>/finish/', W.session_finish,
         name='session_finish'),
    path('workouts/<int:pk>/delete/', W.session_delete,
         name='session_delete'),
    path('workouts/sets/<int:pk>/', W.set_save, name='set_save'),
    path('workouts/sets/<int:pk>/delete/', W.set_delete, name='set_delete'),
    path('workouts/exercises/new/', W.exercise_new, name='exercise_new'),
    path('workouts/exercises/<int:pk>/', W.exercise_detail,
         name='exercise_detail'),
    # CY-1, 30 Oct 2026 - the cycle tracker (opt-in). No pk anywhere:
    # every page is the signed-in person's own record.
    path('cycle/', CY.home, name='cycle'),
    path('cycle/log/', CY.log_day, name='cycle_log'),
    path('cycle/settings/', CY.settings_page, name='cycle_settings'),
    path('cycle/patterns/', CY.patterns, name='cycle_patterns'),
    path('cycle/report/', CY.report, name='cycle_report'),
    path('cycle/export/', CY.export, name='cycle_export'),
    path('cycle/delete/', CY.delete_all, name='cycle_delete'),
    path('guide/', views.guide_page, name='guide'),
    path('tips/', views.tip_seen, name='tip_seen'),
    # The app shell - answered without a login; nothing personal in it.
    path('app/manifest.webmanifest', views.manifest, name='manifest'),
    path('app/sw.js', views.service_worker, name='service_worker'),
    path('app/<str:name>', views.asset, name='asset'),
]
