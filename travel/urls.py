from django.urls import path

from . import views, views_inbox

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
    # TR-2, 15 Nov 2026 - stage 2: bookings read from forwarded emails.
    path('inbound/', views_inbox.inbound_view, name='inbound'),
    path('check/', views_inbox.check, name='check'),
    path('check/<int:item_id>/add/', views_inbox.check_add,
         name='check_add'),
    path('check/<int:item_id>/merge/', views_inbox.check_merge,
         name='check_merge'),
    path('check/<int:item_id>/dismiss/', views_inbox.check_dismiss,
         name='check_dismiss'),
    path('check/<int:item_id>/ask/', views_inbox.check_ask,
         name='check_ask'),
    path('request/<int:request_id>/', views_inbox.answer, name='answer'),
    path('forwarding/', views_inbox.forwarding, name='forwarding'),
    path('<int:trip_id>/merge/', views_inbox.trip_merge, name='trip_merge'),
]
