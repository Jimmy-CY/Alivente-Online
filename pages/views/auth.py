"""
Login and logout views.

Extracted from the legacy pages/views/main.py during the modular views
migration (it lived under the misleadingly named
"### USER ADMIN AND LOGIN AND LOGOUT ###" section). The actual user
management views - create / edit / permissions / roles - are in
pages/views/users.py; this module holds only the public login/logout
entry points. URL patterns are registered in pages/urls.py.

Functions
---------
- login_user  : GET renders the login form; POST authenticates and logs
                the user in, then redirects home.
- logout_user : Logs out the current user (@login_required).
"""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def login_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'You Have Successfully Logged In.')
            return redirect('home')
        else:
            messages.error(request, 'Error Logging In - Please Try Again !!')
            return redirect('login')
    else:
        return render(request, 'login.html', {})


@login_required
def logout_user(request):
    logout(request)
    messages.success(request, 'You Have Successfully Logged Out.')
    return redirect('home')