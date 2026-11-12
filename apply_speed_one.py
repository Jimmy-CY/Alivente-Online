# -*- coding: utf-8 -*-
"""apply_speed_one.py - round SP-1, 12 Nov 2026.

RELEASE 66 - THE SPEED ROUND.

    Demetri, 11:21: "Let's do the speed round."

    Measured live first: Cloudflare already compresses pages and caches
    static files and photos. What is left, and what this round does:
    - base.html's CSS (197 KB, about 59 KB compressed, on every page)
      becomes four cached files. The CSS stays in base.html.
    - Database connections are kept for 60 seconds, health-checked.
    - Gunicorn runs three workers instead of one (gunicorn.conf.py).
    - WhiteNoise moves to straight after SecurityMiddleware.

New files ship beside this patcher. Stands on Release 65. Idempotent.
Edits backed up to .bak_speed1. No migration.
"""
import os
import sys

SUFFIX = '.bak_speed1'
MARK = 'SP-1, 12 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'pages/css_files.py',
    'pages/templatetags/alv_assets.py',
    'gunicorn.conf.py',
    'test_speed_one.py',
)

SWAPS = [
    (os.path.join('pages', 'templates', 'base.html'), [
        (r'''<!doctype html>
{% load static %}

{% comment %}
''',
         r'''<!doctype html>
{% load static %}{% load alv_assets %}

{% comment %}
'''),
        (r'''         filled button.
         =================================================================== -->
    <style>
    /* B-7, 9 Oct 2026 - 1 Bootstrap literal(s) on this page
       became a var(). The ones in script blocks and in style
''',
         r'''         filled button.
         =================================================================== -->
    {% cached_css %}<style>
    /* B-7, 9 Oct 2026 - 1 Bootstrap literal(s) on this page
       became a var(). The ones in script blocks and in style
'''),
        (r'''      .list-group-item-warning { background-color: var(--alv-warn-soft); color: var(--alv-warn-ink); }
      a.text-warning:hover, a.text-warning:focus { color: var(--alv-warn-ink) !important; }
    </style>
    <link rel="stylesheet" href="{% static 'css/my_style.css' %}">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <title>{% block title %}{% endblock %} | Alivente Online</title>

    <style>
    /* ==================== SHARED ==================== */
    .notification-bell-container { position: relative; display: inline-block; }
''',
         r'''      .list-group-item-warning { background-color: var(--alv-warn-soft); color: var(--alv-warn-ink); }
      a.text-warning:hover, a.text-warning:focus { color: var(--alv-warn-ink) !important; }
    </style>{% endcached_css %}
    <link rel="stylesheet" href="{% static 'css/my_style.css' %}">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <title>{% block title %}{% endblock %} | Alivente Online</title>

    {% cached_css %}<style>
    /* ==================== SHARED ==================== */
    .notification-bell-container { position: relative; display: inline-block; }
'''),
        (r'''        body.has-sidebar .navbar.mobile-fallback-nav { display: none !important; }
    }
    </style>

    <!-- ===================================================================
''',
         r'''        body.has-sidebar .navbar.mobile-fallback-nav { display: none !important; }
    }
    </style>{% endcached_css %}

    <!-- ===================================================================
'''),
        (r'''         was caught.
         =================================================================== -->
    <style>
      :root {
        /* Surfaces and ink. Held separate from the accent so a colour
''',
         r'''         was caught.
         =================================================================== -->
    {% cached_css %}<style>
      :root {
        /* Surfaces and ink. Held separate from the accent so a colour
'''),
        (r'''        .action-more-item-danger i { color: var(--alv-danger); }
      }
    </style>
  <style>    /* B-2b, 6 Oct 2026 - 15 literal(s) on this page became a var().
       The tail of tier B: everything within 25 RGB units of a
       token that was not one of B-2 four neutrals. Twenty-one
''',
         r'''        .action-more-item-danger i { color: var(--alv-danger); }
      }
    </style>{% endcached_css %}
  {% cached_css %}<style>    /* B-2b, 6 Oct 2026 - 15 literal(s) on this page became a var().
       The tail of tier B: everything within 25 RGB units of a
       token that was not one of B-2 four neutrals. Twenty-one
'''),
        (r'''

</style>

  {# HK-3, 28 Oct 2026 - the one jQuery, Popper and Bootstrap for every page. #}
''',
         r'''

</style>{% endcached_css %}

  {# HK-3, 28 Oct 2026 - the one jQuery, Popper and Bootstrap for every page. #}
'''),
    ]),
    (os.path.join('mysite', 'settings.py'), [
        (r'''MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "pages.middleware.DatabaseConnectionMiddleware",  # Re-enabled with fixes
    "django.contrib.sessions.middleware.SessionMiddleware",
''',
         r'''MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # SP-1, 12 Nov 2026 - straight after Security, as WhiteNoise asks:
    # a stylesheet or an icon is answered before any session, login or
    # permission check runs. It was last in the list.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "pages.middleware.DatabaseConnectionMiddleware",  # Re-enabled with fixes
    "django.contrib.sessions.middleware.SessionMiddleware",
'''),
        (r'''    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

]

''',
         r'''    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

'''),
        (r'''            'autocommit': True,
        },
        'CONN_MAX_AGE': 0,  # Back to no connection pooling - good for middleware
        'ATOMIC_REQUESTS': False,
    }
}

# ========== EMAIL CONFIGURATION ==========
''',
         r'''            'autocommit': True,
        },
        # SP-1, 12 Nov 2026 - keep a connection for a minute instead of
        # opening a new one on every request; Django checks it is alive
        # before reusing it, so a connection MySQL dropped is replaced.
        'CONN_MAX_AGE': 60,
        'CONN_HEALTH_CHECKS': True,
        'ATOMIC_REQUESTS': False,
    }
}

# SP-1, 12 Nov 2026 - base.html's stylesheets as cached files, on Railway
# only. On a laptop - runserver and every suite - they stay in the page as
# before: many suites draw a page from its HTML alone, with no server to
# ask for a stylesheet. pages/css_files.py explains the files.
ALV_CSS_FILES = bool(os.environ.get('RAILWAY_ENVIRONMENT_NAME') == 'production'
                     or os.environ.get('RAILWAY_PROJECT_ID'))

# ========== EMAIL CONFIGURATION ==========
'''),
    ]),
    (os.path.join('pages', 'urls.py'), [
        (r'''from django.urls import path
from . import views
from .views_setup import setup_permissions

''',
         r'''from django.urls import path
from . import views
from . import css_files
from .views_setup import setup_permissions

'''),
        (r'''    path('admin_apms/', views.admin_apms, name='admin_apms'),
    path('personal/', views.personal_page, name='personal_page'),
    # HK-5, 29 Oct 2026 - admin_clear/ removed: no page linked to it.
    path('upload_title_deed/', views.upload_title_deed, name='upload_title_deed'),
''',
         r'''    path('admin_apms/', views.admin_apms, name='admin_apms'),
    path('personal/', views.personal_page, name='personal_page'),
    # SP-1, 12 Nov 2026 - base.html's stylesheets as cached files.
    path('alv-css/<str:digest>.css', css_files.stylesheet, name='alv_css'),
    # HK-5, 29 Oct 2026 - admin_clear/ removed: no page linked to it.
    path('upload_title_deed/', views.upload_title_deed, name='upload_title_deed'),
'''),
    ]),
    (os.path.join('pages', 'middleware.py'), [
        (r'''            # removed it.)
            'version/',
            # WL-1, 30 Oct 2026 - THE WELLNESS APP SHELL: the manifest,
            # the service worker, the stylesheet, the script and the
''',
         r'''            # removed it.)
            'version/',
            # SP-1, 12 Nov 2026 - base.html's stylesheets. The login page
            # needs them before anyone is signed in, and they hold nothing
            # but CSS that is already in the public login page.
            'alv-css/',
            # WL-1, 30 Oct 2026 - THE WELLNESS APP SHELL: the manifest,
            # the service worker, the stylesheet, the script and the
'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/modules.py'; Text = 'def tz_or_none('; What = 'WL-9/WL-16: the section switches and the time zone reader are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'wellness/training.py'; Text = 'def in_minutes('; What = 'WL-17: the workout rules know minutes from seconds - without them no workout can be started' },
    @{ File = 'wellness/modules.py'; Text = 'def phone_now('; What = "WL-16: Wellness runs on the phone's clock - without it no Wellness page can be drawn" },
''',
         r'''    @{ File = 'wellness/modules.py'; Text = 'def tz_or_none('; What = 'WL-9/WL-16: the section switches and the time zone reader are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'pages/css_files.py'; Text = 'def stylesheet(request, digest):'; What = 'SP-1: base.html links its stylesheets from here - without it every page loses its styling' },
    @{ File = 'wellness/training.py'; Text = 'def in_minutes('; What = 'WL-17: the workout rules know minutes from seconds - without them no workout can be started' },
    @{ File = 'wellness/modules.py'; Text = 'def phone_now('; What = "WL-16: Wellness runs on the phone's clock - without it no Wellness page can be drawn" },
'''),
        (r'''    'test_wellness_twenty.py',
    # WL-17, 12 Nov 2026 - Wellness: workouts - sports, starting numbers, your own exercises.
    'test_wellness_twentyone.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_twenty.py',
    # WL-17, 12 Nov 2026 - Wellness: workouts - sports, starting numbers, your own exercises.
    'test_wellness_twentyone.py',
    # SP-1, 12 Nov 2026 - the speed round: base's CSS as cached files, kept connections, three workers.
    'test_speed_one.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-17, 12 Nov 2026 - Wellness: workouts - sports, starting numbers, your own exercises.
    '.bak_wellness21',
]

''',
         r'''    # WL-17, 12 Nov 2026 - Wellness: workouts - sports, starting numbers, your own exercises.
    '.bak_wellness21',
    # SP-1, 12 Nov 2026 - the speed round.
    '.bak_speed1',
]

'''),
    ]),
    (os.path.join('test_wellness_six.py'), [
        (r'''                u.user_permissions.add(perm)
                WellnessProfile.objects.create(user=u, onboarded=True)
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
''',
         r'''                u.user_permissions.add(perm)
                WellnessProfile.objects.create(user=u, onboarded=True)
            # SP-1, 12 Nov 2026 - ONLY THIS SUITE'S PEOPLE. The job counts
            # everybody who opened Wellness in the last two weeks, and on a
            # laptop's own database that includes real people: the gate
            # stopped on "2 made" when the suite expected 1. Inside this
            # transaction (rolled back below) everyone else is set aside.
            User.objects.exclude(pk__in=[a.pk, b.pk]).update(is_active=False)
            ca = Client(SERVER_NAME='localhost')
            ca.force_login(a)
'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('SP-1 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pq = os.path.join(root, PS1)
    if "'test_speed_one.py'" in read(pq):
        print('SP-1 already applied.')
        return 0
    if "'test_wellness_twentyone.py'" not in read(pq):
        refuse('Release 65 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new wellness files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('SP-1 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('SP-1 applied - the speed round: base stylesheets as cached files, kept connections, three workers.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
