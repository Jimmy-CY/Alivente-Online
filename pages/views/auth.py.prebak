"""
Login and logout views.

Extracted from pages/views/main.py as part of the modular views migration
(section ### USER ADMIN AND LOGIN AND LOGOUT ###).

Contains 2 functions:
  login_user  - GET renders login form; POST authenticates and logs in
  logout_user - logs out the current user (@login_required)

Note: the section name in main.py was misleading. Actual user management
views (create/edit/permissions/roles) are already in pages/views/users.py.
This module only contains the public login/logout entry points.

URL patterns remain registered in pages/urls.py.

Indentation note: login_user preserves the legacy mixed tabs/spaces from
the source (the body uses TAB for level-1, TAB+spaces for deeper levels,
and TAB+TAB for one branch). Python accepts this because tab-width 8 makes
the indentation levels internally consistent. A future cleanup pass can
normalize to PEP 8 four-space indentation. logout_user already uses
4-space indentation.
"""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def login_user(request):
    if request.method =="POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, ('You Have Successfully Logged In.'))
            return redirect('home')
        else:
            messages.success(request, ('Error Logging In - Please Try Again !!'))
            return redirect('login')
    else:
        return render(request, 'login.html', {})

@login_required
def logout_user(request):
    logout(request)
    messages.success(request, ('You Have Succefully Logged Out.'))
    return redirect('home')