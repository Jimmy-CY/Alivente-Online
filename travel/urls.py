from django.urls import path

from . import views

app_name = 'travel'

urlpatterns = [
    path('', views.trips, name='trips'),
    path('new/', views.trip_new, name='trip_new'),
    path('<int:trip_id>/', views.trip, name='trip'),
    path('<int:trip_id>/costs/', views.trip, name='trip_costs'),
    path('<int:trip_id>/edit/', views.trip_edit, name='trip_edit'),
    path('<int:trip_id>/delete/', views.trip_delete, name='trip_delete'),
    path('<int:trip_id>/share/', views.trip_share, name='trip_share'),
    path('<int:trip_id>/booking/new/', views.booking_form,
         name='booking_new'),
    path('booking/<int:booking_id>/', views.booking, name='booking'),
    path('booking/<int:booking_id>/edit/', views.booking_form,
         name='booking_edit'),
    path('booking/<int:booking_id>/delete/', views.booking_delete,
         name='booking_delete'),
    path('file/<int:file_id>/', views.booking_file, name='file'),
    path('file/<int:file_id>/delete/', views.booking_file_delete,
         name='file_delete'),
]
