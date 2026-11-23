# -*- coding: utf-8 -*-
"""apply_ra18_acquisitions.py - round RA18, 23 Nov 2026.

RELEASE RA18 - PROPERTY ACQUISITIONS, STEP 1: THE FOUNDATION.

    Step 1 of the Property Acquisitions module, built in Demetri's other
    chat (models, scoring engine, admin, seed and import commands, 8
    tests), brought into Alivente Online inside the house standard, the
    way CRS is. Demetri, 23 Nov: "Obviously anything built would need to
    comply with our system standards" - two releases (this, then the 11
    screens), under Property Operations, unknown-Musts limit 4.

    - acquisitions/ ships beside this patcher: its own Django app, CRLF
      like CRS, migration 0001 (12 tables). Scenario.max_unknown_musts
      defaults to 4. seed_acquisitions and import_listings_csv both take
      --dry-run (everything inside a transaction, reported, rolled back);
      the import uses the local day, and reports each listing.
    - mysite/settings.py: the app in INSTALLED_APPS.
    - pages/permissions.py: a new module row (the 20th) -
      can_access_acquisitions / can_edit_acquisitions. migrate creates both
      (ensure_permissions).
    - pages/middleware.py: acquisitions/ paths need can_access_acquisitions.
    - pages/activity.py: Acquisitions under Property Operations; scenarios,
      rules, listing decisions and viewings watched; re-scoring is not
      anybody's change (MACHINE_FIELDS).
    - Help: the Permissions screen's module list, brought up to date.
    - No screens yet - Django admin only. They come in RA19.

Stands on RA17. Idempotent. Edits backed up to .bak_ra18.
MIGRATION: run  python manage.py migrate  before pushing.
"""
import os
import sys

SUFFIX = '.bak_ra18'
MARK = 'RA18, 23 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'acquisitions/README.md',
    'acquisitions/__init__.py',
    'acquisitions/admin.py',
    'acquisitions/apps.py',
    'acquisitions/management/__init__.py',
    'acquisitions/management/commands/__init__.py',
    'acquisitions/management/commands/import_listings_csv.py',
    'acquisitions/management/commands/seed_acquisitions.py',
    'acquisitions/migrations/0001_initial.py',
    'acquisitions/migrations/__init__.py',
    'acquisitions/models.py',
    'acquisitions/scoring.py',
    'acquisitions/signals.py',
    'acquisitions/tests.py',
    'test_fixture_acq_listings.csv',
    'test_ra18_acquisitions.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_ra16_meal_send_drag.py',
    # RA17, 23 Nov 2026 - Send in the house shape; the month on screen.
    'test_ra17_send_standard_month.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_ra16_meal_send_drag.py',
    # RA17, 23 Nov 2026 - Send in the house shape; the month on screen.
    'test_ra17_send_standard_month.py',
    # RA18, 23 Nov 2026 - Property Acquisitions, step 1: the foundation.
    'test_ra18_acquisitions.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA17, 23 Nov 2026 - Send in the house shape; the month on screen.
    '.bak_ra17',
]

''',
         r'''    # RA17, 23 Nov 2026 - Send in the house shape; the month on screen.
    '.bak_ra17',
    # RA18, 23 Nov 2026 - Property Acquisitions, step 1: the foundation.
    '.bak_ra18',
]

'''),
    ]),
    (os.path.join('mysite', 'settings.py'), [
        (r'''    # TR-1, 15 Nov 2026 - Travel: its own app, like Wellness.
    "travel",
    # PK-1, 30 Oct 2026 - sign in with a fingerprint. No templates.
    "passkeys",
''',
         r'''    # TR-1, 15 Nov 2026 - Travel: its own app, like Wellness.
    "travel",
    # RA18, 23 Nov 2026 - Property Acquisitions: its own app, like CRS -
    # inside the house standard, under Property Operations.
    "acquisitions.apps.AcquisitionsConfig",
    # PK-1, 30 Oct 2026 - sign in with a fingerprint. No templates.
    "passkeys",
'''),
    ]),
    (os.path.join('pages', 'activity.py'), [
        (r'''    ('projects', 'Projects', 'ops', '',
     ['projects', 'ajax/projects', 'ajax/tasks', 'translate']),
    ('dashboard', 'Dashboard', 'ops', '',
     ['property_management_dashboard', 'property_detail']),
''',
         r'''    ('projects', 'Projects', 'ops', '',
     ['projects', 'ajax/projects', 'ajax/tasks', 'translate']),
    # RA18, 23 Nov 2026 - a business area, so its changes are logged.
    ('acquisitions', 'Acquisitions', 'ops', '', ['acquisitions']),
    ('dashboard', 'Dashboard', 'ops', '',
     ['property_management_dashboard', 'property_detail']),
'''),
        (r'''    ('pages', 'issues', 'issues', 'Issue'),
    ('pages', 'Project', 'projects', 'Project'),
    ('pages', 'ProjectTask', 'projects', 'Task'),
    ('pages', 'invoices', 'invoices', 'Invoice'),
''',
         r'''    ('pages', 'issues', 'issues', 'Issue'),
    ('pages', 'Project', 'projects', 'Project'),
    # RA18 - Acquisitions: what a person decides. A property's FACTS and
    # its scores are written by searches and re-scoring, many at a time,
    # and are not watched; the rules, the scenarios and your decisions on
    # a listing are.
    ('acquisitions', 'Scenario', 'acquisitions', 'Search scenario'),
    ('acquisitions', 'Criterion', 'acquisitions', 'Search rule'),
    ('acquisitions', 'ScenarioMatch', 'acquisitions', 'Listing decision'),
    ('acquisitions', 'Viewing', 'acquisitions', 'Viewing'),
    ('pages', 'ProjectTask', 'projects', 'Task'),
    ('pages', 'invoices', 'invoices', 'Invoice'),
'''),
        (r'''

def _fields(obj):
    for f in obj._meta.concrete_fields:
        if f.primary_key or f.name in NOT_SHOWN or \
                getattr(f, 'auto_now', False):
            continue
''',
         r'''

# RA18, 23 Nov 2026 - FIELDS A MACHINE WRITES, per model. A search
# scenario's match is re-scored whenever a rule or a fact changes, often
# hundreds at a time; those writes are not anyone's change. What a person
# decides on a listing - its status, your comments - still is, and a save
# that changes only these fields logs nothing at all.
MACHINE_FIELDS = {
    ('acquisitions', 'scenariomatch'): {
        'score', 'raw_score', 'is_capped', 'passes_musts', 'failed_musts',
        'unknown_musts', 'breakdown', 'judgements', 'flags', 'last_checked'},
}


def _fields(obj):
    skip = MACHINE_FIELDS.get((obj._meta.app_label, obj._meta.model_name),
                              ())
    for f in obj._meta.concrete_fields:
        if f.primary_key or f.name in NOT_SHOWN or f.name in skip or \
                getattr(f, 'auto_now', False):
            continue
'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0; color:#0e7c8b;"><i class="fas fa-key"></i> <strong>Permissions</strong> <small class="text-muted">(teal)</small></h6>
        <p class="mb-1" style="font-size:13px;">Opens the Permissions screen, where you tick which of the 12 modules the user can access (Properties, Tenants, Suppliers, Expenses, Petty Cash, Financials, Invoices, Projects, Issues, Dashboard, Administration, Personal).</p>
''',
         r'''      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0; color:#0e7c8b;"><i class="fas fa-key"></i> <strong>Permissions</strong> <small class="text-muted">(teal)</small></h6>
        <p class="mb-1" style="font-size:13px;">Opens the Permissions screen, where you tick which modules the user can open and, for most of them, whether they can also change things (view only, or view and edit). <strong>Property Operations:</strong> Properties, Tenants, Suppliers, Issues, Projects, <strong>Acquisitions</strong> (the property search) and Dashboard. <strong>Financial Management:</strong> Invoices, Receipts, Expenses, Petty Cash and Financials. <strong>Administration.</strong> <strong>Personal:</strong> Passports / Documents, Recipes, Celebrations, CRS Reporting, Wellness and Travel. Dashboard, Administration, Wellness and Travel have no separate edit right.</p>
'''),
    ]),
    (os.path.join('pages', 'middleware.py'), [
        (r'''            ('travel', 'auth.can_access_travel'),

            # ---------- RECIPES ----------
            ('recipe_management', 'auth.can_access_recipes'),
''',
         r'''            ('travel', 'auth.can_access_travel'),

            # ---------- ACQUISITIONS (RA18, 23 Nov 2026) ----------
            # No trailing slash, for Wellness's reason.
            ('acquisitions', 'auth.can_access_acquisitions'),

            # ---------- RECIPES ----------
            ('recipe_management', 'auth.can_access_recipes'),
'''),
    ]),
    (os.path.join('pages', 'permissions.py'), [
        (r'''    # its owner's, and shared ones are shared to change as well as see.
    {'codename': 'can_access_travel',         'edit_codename': None,                      'label': 'Travel',                'icon': 'fa-plane'},
]

''',
         r'''    # its owner's, and shared ones are shared to change as well as see.
    {'codename': 'can_access_travel',         'edit_codename': None,                      'label': 'Travel',                'icon': 'fa-plane'},
    # RA18, 23 Nov 2026 - Property Acquisitions, under Property Operations.
    # AN EDIT TIER, like the other business modules: Demetri wants to be
    # able to give someone view-only access to the search and its results.
    {'codename': 'can_access_acquisitions',   'edit_codename': 'can_edit_acquisitions',   'label': 'Acquisitions',          'icon': 'fa-search-location'},
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
    raise SystemExit('RA18 REFUSED: %s' % msg)


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
    if "'test_ra18_acquisitions.py'" in read(pq):
        print('RA18 already applied.')
        return 0
    if "'test_ra17_send_standard_month.py'" not in read(pq):
        refuse('RA17 (apply_ra17_send_standard_month.py) is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('RA18 --check: %d file(s) would change, none written; %d '
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
    print('RA18 applied - Property Acquisitions, step 1. Now run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
