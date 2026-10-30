# -*- coding: utf-8 -*-
"""wellness/session.py - WL-1, 30 Oct 2026. Thirty days for Wellness on
the phone; one hour for everything else, as now.

DEMETRI, 30 OCT: "Let's keep the one hour login for the main app as it
is. For the Wellness module specifically, let's give it a 30 day period
on the phone."

ONE COOKIE CANNOT HAVE TWO LIFETIMES, so this keeps one long session and
puts the hour back where it belongs:

    - A Wellness page opened ON A PHONE stretches the session to 30 days
      (sliding: each visit restarts the 30) and marks it 'long'.
    - Logging in stamps the main app's own hour (MAIN_UNTIL). It is
      never moved by a Wellness visit.
    - On a long session, any main-app page after that hour goes to the
      login page - the session is kept, so Wellness carries on working,
      and logging in again gives the main app a fresh hour.

A session that never touched Wellness on a phone is untouched by this
file: Django's own SESSION_COOKIE_AGE governs it exactly as before.
"""
import time

from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.http import HttpResponseRedirect
from django.urls import reverse

LONG_DAYS = 30
LONG = 'wl_long'
MAIN_UNTIL = 'wl_main_until'
PHONE_MARKS = ('Mobi', 'Android', 'iPhone', 'iPad')

# Paths the main app's hour does not apply to: Wellness itself, and the
# pages a person needs in order to log in again or that are public anyway.
FREE = ('/wellness/', '/login/', '/logout/', '/static/', '/media/',
        '/version/', '/forgot-password/', '/set-password/', '/sign/',
        '/robots.txt', '/favicon.ico')


def main_hour():
    return int(getattr(settings, 'SESSION_COOKIE_AGE', 1209600))


def is_phone(request):
    ua = request.META.get('HTTP_USER_AGENT', '')
    return any(m in ua for m in PHONE_MARKS)


@receiver(user_logged_in)
def stamp_main_hour(sender, request, user, **kwargs):
    if request is not None and hasattr(request, 'session'):
        request.session[MAIN_UNTIL] = int(time.time()) + main_hour()


class WellnessSessionMiddleware:
    """After AuthenticationMiddleware, before ModuleAccessMiddleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            path = request.path
            s = request.session
            if path.startswith('/wellness/'):
                if is_phone(request):
                    if MAIN_UNTIL not in s:
                        # A session from before this release: its hour
                        # began no later than now.
                        s[MAIN_UNTIL] = int(time.time()) + main_hour()
                    s[LONG] = True
                    s.set_expiry(LONG_DAYS * 86400)
            elif s.get(LONG) and not path.startswith(FREE):
                if int(time.time()) > int(s.get(MAIN_UNTIL) or 0):
                    return HttpResponseRedirect(
                        '%s?next=%s' % (reverse('login'), path))
        return self.get_response(request)
