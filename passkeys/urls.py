from django.urls import path

from . import views

urlpatterns = [
    path('login/passkey/begin/', views.login_begin, name='passkey_login_begin'),
    path('login/passkey/finish/', views.login_finish,
         name='passkey_login_finish'),
    path('my-profile/passkeys/add/begin/', views.add_begin,
         name='passkey_add_begin'),
    path('my-profile/passkeys/add/finish/', views.add_finish,
         name='passkey_add_finish'),
    path('my-profile/passkeys/<int:pk>/remove/', views.remove,
         name='passkey_remove'),
]
