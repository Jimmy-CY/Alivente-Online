# -*- coding: utf-8 -*-
"""apply_housekeeping_two.py - round HK-2, 27 Oct 2026.

RELEASE 27 - HOUSEKEEPING, from the September backlog, re-measured first.

    - railway.json loses its dead "crons" entry (a command that does not
      exist; Railway's cron-service runs its own start command). The build
      section is unchanged.
    - The Passport and Recipe help sections ask for can_access_passports and
      can_access_recipes instead of the deleted can_access_personal, so the
      people who use those modules can read their help.
    - The duplicate projects/<id>/assignees/ route goes.

Stands on LS-1. Idempotent. Edits backed up to .bak_housekeep2; ships this
patcher and its suite. No migration.
"""
import os
import re
import sys

SUFFIX = '.bak_housekeep2'
MARK = 'HK-2, 27 Oct 2026'
CHECK = False
CREATES = (
    'test_housekeeping_two.py',
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('railway.json'), [
        (r'''    "builder": "NIXPACKS",
    "installCommand": "python -m pip install -r mysite/cron-requirements.txt"
  },
  "crons": [
    {
      "name": "Lease Renewal Check",
      "schedule": "*/5 * * * *",
      "command": "python manage.py check_lease_renewals"
    }
  ]
}''',
         r'''    "builder": "NIXPACKS",
    "installCommand": "python -m pip install -r mysite/cron-requirements.txt"
  }
}'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''
<!-- ======= PASSPORT MANAGEMENT ======= -->
<section data-module-slug="passport_management"
         data-module-group="Personal"
         data-module-permission="can_access_personal"
         data-module-name="Passport / ID Management"
         data-module-icon="fa-id-card"
''',
         r'''
<!-- ======= PASSPORT MANAGEMENT ======= -->
<!-- HK-2, 27 Oct 2026 - can_access_personal was deleted (0065); the module's own permission now decides who sees this help. -->
<section data-module-slug="passport_management"
         data-module-group="Personal"
         data-module-permission="can_access_passports"
         data-module-name="Passport / ID Management"
         data-module-icon="fa-id-card"
'''),
        (r'''</section>

<section data-module-slug="recipe_management"
         data-module-group="Personal"
         data-module-permission="can_access_personal"
         data-module-name="Recipe Management"
         data-module-icon="fa-utensils"
''',
         r'''</section>

<!-- HK-2, 27 Oct 2026 - as above: the Recipes permission, not the deleted can_access_personal. -->
<section data-module-slug="recipe_management"
         data-module-group="Personal"
         data-module-permission="can_access_recipes"
         data-module-name="Recipe Management"
         data-module-icon="fa-utensils"
'''),
    ]),
    (os.path.join('pages', 'urls.py'), [
        (r'''    path('projects/<int:project_id>/task-list/', views.project_task_list, name='project_task_list'),
    path('translate/', views.translate_text, name='translate_text'),
    path('projects/<int:project_id>/assignees/', views.get_project_assignees, name='get_project_assignees'),
    path('projects/ajax/delete-task/', views.ajax_delete_task, name='ajax_delete_task'),

''',
         r'''    path('projects/<int:project_id>/task-list/', views.project_task_list, name='project_task_list'),
    path('translate/', views.translate_text, name='translate_text'),
    # HK-2, 27 Oct 2026 - a second route for projects/<id>/assignees/ named
    # get_project_assignees stood here. Django only ever matched the first
    # (project_assignees, above) and nothing reverses either name.
    path('projects/ajax/delete-task/', views.ajax_delete_task, name='ajax_delete_task'),

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
    raise SystemExit('HK-2 REFUSED: %s' % msg)


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
    if "'test_housekeeping_two.py'" in read(pq):
        print('HK-2 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_lease_status.py'" not in read(pq):
        refuse('LS-1 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, rel)):
            refuse('%s is missing - it ships with this patcher; copy it in '
                   'first.' % rel)

    # ---- THE SWAPS
    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    # ---- REGISTRATION
    q = out.get(pq, read(pq))
    q = swap(q, """    'test_lease_status.py'
)""", """    'test_lease_status.py',
    # HK-2, 27 Oct 2026 - housekeeping from the September backlog.
    'test_housekeeping_two.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'pages/views/lease_signing_status.py'; Text = "@permission_required('auth.can_access_tenants'";""",
        """    @{ File = 'pages/help_content/administration.html'; Text = 'data-module-permission="can_access_personal"'; Absent = $true; What = 'HK-2: no help section asks for can_access_personal - migration 0065 deleted it, and a section that asks for it is hidden from everybody but a superuser' },
    @{ File = 'pages/views/lease_signing_status.py'; Text = "@permission_required('auth.can_access_tenants'";""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_lease_status.py',
]""", """    'test_lease_status.py',
    # HK-2, 27 Oct 2026 - housekeeping from the September backlog.
    'test_housekeeping_two.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_leasestatus',
]""", """    '.bak_leasestatus',
    # HK-2, 27 Oct 2026 - housekeeping from the September backlog.
    '.bak_housekeep2',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # HK-2, 27 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    import json as _json
    try:
        _rj = _json.loads(out[os.path.join(root, 'railway.json')])
    except ValueError as e:
        refuse('railway.json would not parse: %s' % e)
    if 'crons' in _rj or 'build' not in _rj:
        refuse('railway.json must keep its build section and lose crons.')

    if CHECK:
        print('HK-2 --check: %d file(s) would change, none written; %d '
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
    print('HK-2 applied - railway.json without the dead cron; Passport and '
          'Recipe help visible to their users; one assignees route.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
