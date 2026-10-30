# -*- coding: utf-8 -*-
"""apply_wellness_one.py - round WL-1, 30 Oct 2026.

RELEASE 42 - WELLNESS, PART ONE: TODAY AND HABITS.

    - A new app, wellness/, mounted at /wellness/: Today, Habits, the
      guided habit setup, one-time tips, the ? guide, the installable-app
      shell (manifest, service worker, icons) and the quote library. It
      ships as files beside this patcher, not written by it.
    - A fourth tile on Personal behind a new permission,
      can_access_wellness (no edit tier), made by the next migrate.
    - INSTALLED_APPS, the root urls, the middleware (the permission, and
      wellness/app/ answering without a login), Home and both navigation
      menus learn about it.

Stands on Release 41. Idempotent. Edits backed up to .bak_wellness1.
MIGRATION: wellness 0001 - run `python manage.py migrate` after applying.
"""
import os
import sys

SUFFIX = '.bak_wellness1'
MARK = 'WL-1, 30 Oct 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/__init__.py',
    'wellness/apps.py',
    'wellness/assets/apple-touch-icon.png',
    'wellness/assets/icon-192.png',
    'wellness/assets/icon-512.png',
    'wellness/assets/icon-maskable-512.png',
    'wellness/assets/wellness.css',
    'wellness/assets/wellness.js',
    'wellness/guide.py',
    'wellness/habits.py',
    'wellness/migrations/0001_initial.py',
    'wellness/migrations/__init__.py',
    'wellness/models.py',
    'wellness/quotes.py',
    'wellness/session.py',
    'wellness/templates/wellness/base.html',
    'wellness/templates/wellness/guide.html',
    'wellness/templates/wellness/habit_detail.html',
    'wellness/templates/wellness/habit_form.html',
    'wellness/templates/wellness/habit_list.html',
    'wellness/templates/wellness/today.html',
    'wellness/templates/wellness/welcome.html',
    'wellness/urls.py',
    'wellness/views.py',
    'test_wellness_one.py',
)

SWAPS = [
    (os.path.join('mysite', 'settings.py'), [
        (r'''    "pages",
    "crs",
    "whitenoise.runserver_nostatic",
    "django.contrib.humanize",
''',
         r'''    "pages",
    "crs",
    # WL-1, 30 Oct 2026 - Wellness: its own app, outside the house standard.
    "wellness",
    "whitenoise.runserver_nostatic",
    "django.contrib.humanize",
'''),
        (r'''    "django.contrib.auth.middleware.AuthenticationMiddleware",
    'pages.workspace.WorkspaceMiddleware',    
    "pages.middleware.ModuleAccessMiddleware",  # Add this line
    "django.contrib.messages.middleware.MessageMiddleware",
''',
         r'''    "django.contrib.auth.middleware.AuthenticationMiddleware",
    'pages.workspace.WorkspaceMiddleware',    
    # WL-1, 30 Oct 2026 - 30 days for Wellness on a phone, the main app's
    # hour kept. Before ModuleAccessMiddleware, so an expired hour goes to
    # the login page before any permission is looked at.
    "wellness.session.WellnessSessionMiddleware",
    "pages.middleware.ModuleAccessMiddleware",  # Add this line
    "django.contrib.messages.middleware.MessageMiddleware",
'''),
    ]),
    (os.path.join('mysite', 'urls.py'), [
        (r'''    path('', include('pages.urls')),
    path("crs/", include("crs.urls")),
    path('robots.txt', robots_txt),
    # DP-1, 22 Oct 2026. Public on purpose - see deploy_version and the
''',
         r'''    path('', include('pages.urls')),
    path("crs/", include("crs.urls")),
    # WL-1, 30 Oct 2026 - Wellness. wellness/app/ (the installable-app
    # shell) answers without a login; everything else needs one.
    path("wellness/", include("wellness.urls")),
    path('robots.txt', robots_txt),
    # DP-1, 22 Oct 2026. Public on purpose - see deploy_version and the
'''),
    ]),
    (os.path.join('pages', 'permissions.py'), [
        (r'''    {'codename': 'can_access_celebrations',   'edit_codename': 'can_edit_celebrations',   'label': 'Celebrations',          'icon': 'fa-birthday-cake'},
    {'codename': 'can_access_crs',            'edit_codename': 'can_edit_crs',            'label': 'CRS Reporting',         'icon': 'fa-landmark'},
]

''',
         r'''    {'codename': 'can_access_celebrations',   'edit_codename': 'can_edit_celebrations',   'label': 'Celebrations',          'icon': 'fa-birthday-cake'},
    {'codename': 'can_access_crs',            'edit_codename': 'can_edit_crs',            'label': 'CRS Reporting',         'icon': 'fa-landmark'},
    # WL-1, 30 Oct 2026 - Wellness. NO EDIT TIER: everything in it is the
    # person's own, so seeing it and changing it are the same right. And
    # access is never access to anyone else's - every query is filtered
    # by the login, superusers included.
    {'codename': 'can_access_wellness',       'edit_codename': None,                      'label': 'Wellness',              'icon': 'fa-spa'},
]

'''),
    ]),
    (os.path.join('pages', 'middleware.py'), [
        (r'''            # removed it.)
            'version/',
            'media/',  # Media files
            'static/',  # Static files
''',
         r'''            # removed it.)
            'version/',
            # WL-1, 30 Oct 2026 - THE WELLNESS APP SHELL: the manifest,
            # the service worker, the stylesheet, the script and the
            # icons. A phone fetches the manifest and icons with no
            # session, so a login redirect here would make Wellness
            # uninstallable. Nothing personal is served under it - the
            # pages themselves are under wellness/ and keep their check.
            'wellness/app/',
            'media/',  # Media files
            'static/',  # Static files
'''),
        (r'''            # ---------- CRS REPORTING ----------
            ('crs/', 'auth.can_access_crs'),

            # ---------- RECIPES ----------
''',
         r'''            # ---------- CRS REPORTING ----------
            ('crs/', 'auth.can_access_crs'),

            # ---------- WELLNESS (WL-1, 30 Oct 2026) ----------
            # No trailing slash: the path is matched with its slash
            # stripped, so 'wellness/' would miss /wellness/ itself.
            ('wellness', 'auth.can_access_wellness'),

            # ---------- RECIPES ----------
'''),
    ]),
    (os.path.join('pages', 'views', 'administration.py'), [
        (r'''        'celebrations': request.user.has_perm('auth.can_access_celebrations'),
        'crs':          request.user.has_perm('auth.can_access_crs'),
    }
    return render(request, "personal.html", {
''',
         r'''        'celebrations': request.user.has_perm('auth.can_access_celebrations'),
        'crs':          request.user.has_perm('auth.can_access_crs'),
        # WL-1, 30 Oct 2026 - the fourth tile.
        'wellness':     request.user.has_perm('auth.can_access_wellness'),
    }
    return render(request, "personal.html", {
'''),
    ]),
    (os.path.join('pages', 'views', 'home.py'), [
        (r'''                'celebrations': request.user.has_perm('auth.can_access_celebrations'),
                'crs':          request.user.has_perm('auth.can_access_crs'),
                'personal': (
                    request.user.has_perm('auth.can_access_passports')
                    or request.user.has_perm('auth.can_access_recipes')
                    or request.user.has_perm('auth.can_access_celebrations')
                    or request.user.has_perm('auth.can_access_crs')
                ),
                'administration': request.user.has_perm('auth.can_access_administration'),
''',
         r'''                'celebrations': request.user.has_perm('auth.can_access_celebrations'),
                'crs':          request.user.has_perm('auth.can_access_crs'),
                'wellness':     request.user.has_perm('auth.can_access_wellness'),
                # WL-1, 30 Oct 2026 - Wellness lives on Personal, so a
                # login with only Wellness still needs the way in.
                'personal': (
                    request.user.has_perm('auth.can_access_passports')
                    or request.user.has_perm('auth.can_access_recipes')
                    or request.user.has_perm('auth.can_access_celebrations')
                    or request.user.has_perm('auth.can_access_crs')
                    or request.user.has_perm('auth.can_access_wellness')
                ),
                'administration': request.user.has_perm('auth.can_access_administration'),
'''),
    ]),
    (os.path.join('pages', 'templates', 'base.html'), [
        (r'''      {% endif %}

      {% if user.is_superuser or perms.auth.can_access_passports or perms.auth.can_access_recipes or perms.auth.can_access_celebrations or perms.auth.can_access_crs %}
      <a href="{% url 'personal_page' %}" class="sidebar-link {% if request.resolver_match.url_name == 'personal_page' %}active{% endif %}" data-tooltip="Personal">
          <i class="fas fa-user-circle"></i><span class="link-text">Personal</span>
''',
         r'''      {% endif %}

      {% if user.is_superuser or perms.auth.can_access_passports or perms.auth.can_access_recipes or perms.auth.can_access_celebrations or perms.auth.can_access_crs or perms.auth.can_access_wellness %}
      <a href="{% url 'personal_page' %}" class="sidebar-link {% if request.resolver_match.url_name == 'personal_page' %}active{% endif %}" data-tooltip="Personal">
          <i class="fas fa-user-circle"></i><span class="link-text">Personal</span>
'''),
        (r'''            {% endif %}
            {% if user.is_superuser or perms.auth.can_access_administration %}<li class="nav-item"><a class="nav-link" href="{% url 'admin_apms' %}">Administration</a></li>{% endif %}
            {% if user.is_superuser or perms.auth.can_access_passports or perms.auth.can_access_recipes or perms.auth.can_access_celebrations or perms.auth.can_access_crs %}<li class="nav-item"><a class="nav-link" href="{% url 'personal_page' %}">Personal</a></li>{% endif %}
            <li class="nav-item"><a class="nav-link" href="{% url 'help_page' %}"><i class="fas fa-question-circle"></i> Help</a></li>
          {% endif %}
''',
         r'''            {% endif %}
            {% if user.is_superuser or perms.auth.can_access_administration %}<li class="nav-item"><a class="nav-link" href="{% url 'admin_apms' %}">Administration</a></li>{% endif %}
            {% if user.is_superuser or perms.auth.can_access_passports or perms.auth.can_access_recipes or perms.auth.can_access_celebrations or perms.auth.can_access_crs or perms.auth.can_access_wellness %}<li class="nav-item"><a class="nav-link" href="{% url 'personal_page' %}">Personal</a></li>{% endif %}
            <li class="nav-item"><a class="nav-link" href="{% url 'help_page' %}"><i class="fas fa-question-circle"></i> Help</a></li>
          {% endif %}
'''),
    ]),
    (os.path.join('pages', 'templates', 'personal.html'), [
        (r'''        <i class="fas fa-birthday-cake"></i>
        <h6>Celebrations</h6>
      </a>
      {% endif %}
''',
         r'''        <i class="fas fa-birthday-cake"></i>
        <h6>Celebrations</h6>
      </a>
      {% endif %}

      {% if perms_map.wellness %}
      <!-- Wellness - WL-1, 30 Oct 2026. The fourth tile; the module
           behind it is its own app at /wellness/. -->
      <a href="{% url 'wellness:today' %}" class="admin-btn btn-personal">
        <i class="fas fa-spa"></i>
        <h6>Wellness</h6>
      </a>
      {% endif %}
'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'pages/views/lease_signing_create.py'; Text = 'from .lease_signing_sign import _invite'; What = 'ES-3b: one spelling of mint-a-link-and-send-it, imported from ES-4 rather than copied - a second copy here would be a second answer to what a resend does to the old link, and ES-1 made that a rule when it stored the token hashed' },
    @{ File = 'pages/management/commands/check_lease_renewal_and_invoices.py'; Text = 'Celebration email to %s'; What = 'CX-1: the celebrations email retries like the others - without it one mail-server hiccup loses every celebration email for the day' },
    @{ File = 'pages/models.py'; Text = 'def _fh_unchanged('; What = 'VS-1: a budget or revenue save that changes nothing appends no snapshot - without it every save adds an identical history row' },
    @{ File = 'cron-service/start.sh'; Text = 'python manage.py check_lease_renewal_and_invoices'; What = 'HK-5: the daily job runs the command that exists - without it the 06:00 UTC run fails and physical invoices, e-signing expiry and reminders never happen' },
''',
         r'''    @{ File = 'pages/views/lease_signing_create.py'; Text = 'from .lease_signing_sign import _invite'; What = 'ES-3b: one spelling of mint-a-link-and-send-it, imported from ES-4 rather than copied - a second copy here would be a second answer to what a resend does to the old link, and ES-1 made that a rule when it stored the token hashed' },
    @{ File = 'pages/management/commands/check_lease_renewal_and_invoices.py'; Text = 'Celebration email to %s'; What = 'CX-1: the celebrations email retries like the others - without it one mail-server hiccup loses every celebration email for the day' },
    @{ File = 'wellness/habits.py'; Text = 'def can_establish('; What = 'WL-1: the Wellness habit rules are on disk - without them Today cannot be drawn' },
    @{ File = 'pages/models.py'; Text = 'def _fh_unchanged('; What = 'VS-1: a budget or revenue save that changes nothing appends no snapshot - without it every save adds an identical history row' },
    @{ File = 'cron-service/start.sh'; Text = 'python manage.py check_lease_renewal_and_invoices'; What = 'HK-5: the daily job runs the command that exists - without it the 06:00 UTC run fails and physical invoices, e-signing expiry and reminders never happen' },
'''),
        (r'''    'test_celebration_help.py',
    # 30 Oct 2026 - the colour-literal census: no template gains a hex colour.
    'test_colour_census.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_celebration_help.py',
    # 30 Oct 2026 - the colour-literal census: no template gains a hex colour.
    'test_colour_census.py',
    # WL-1, 30 Oct 2026 - Wellness, part one: Today and Habits.
    'test_wellness_one.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # CX-1, 29 Oct 2026 - celebrations retry; Help on Task List and Gantt.
    '.bak_celebhelp',
]

''',
         r'''    # CX-1, 29 Oct 2026 - celebrations retry; Help on Task List and Gantt.
    '.bak_celebhelp',
    # WL-1, 30 Oct 2026 - Wellness, part one: Today and Habits.
    '.bak_wellness1',
]

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
    raise SystemExit('WL-1 REFUSED: %s' % msg)


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
    if "'test_wellness_one.py'" in read(pq):
        print('WL-1 already applied.')
        return 0
    if "'test_colour_census.py'" not in read(pq):
        refuse('Release 41 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'wellness folder and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('WL-1 --check: %d file(s) would change, none written; %d '
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
    print('WL-1 applied - Wellness, part one: Today and Habits.')
    print('      MIGRATION: run  python manage.py migrate  (wellness 0001).')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
