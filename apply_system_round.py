# -*- coding: utf-8 -*-
"""apply_system_round.py - round SY-1, 26 Oct 2026.

RELEASE 21 - TWO SMALL SYSTEM FIXES.

    - Every module permission exists after every migrate: post_migrate
      calls pages.permissions.ensure_permissions(), so a fresh or rebuilt
      database no longer refuses every Edit screen until a superuser opens
      User Administration. The setup page, the old command and the old
      middleware helper look rows up by codename, not by name.
    - The push sweeps at two workers unless told otherwise (-Workers 0
      still lets the runner choose).

Stands on TI-1. Idempotent. Edits backed up to .bak_sysround; ships this
patcher and its suite. No migration.
"""
import os
import re
import sys

SUFFIX = '.bak_sysround'
MARK = 'SY-1, 26 Oct 2026'
CHECK = False
CREATES = (
    'test_system_round.py',
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'permissions.py'), [
        (r'''    out.extend(EXTRA_PERMISSIONS)
    return out
''',
         r'''    out.extend(EXTRA_PERMISSIONS)
    return out


# SY-1, 26 Oct 2026 - EVERY PERMISSION EXISTS AFTER EVERY MIGRATE.
#
# Until this round the rows were made only when a superuser opened User
# Administration (views/users.py) or the setup page (views_setup.py). A
# fresh or rebuilt database therefore came up with none of them, and the
# first sign was a 403 on an Edit screen somebody could reach yesterday.
# pages/apps.py now calls this from post_migrate, so `python manage.py
# migrate` - which every deploy runs - leaves every codename in place.
#
# LOOKED UP BY CODENAME, THE NAME ONLY A DEFAULT. A row whose name has
# drifted ("Can access Tenants module" from the old seeder) is the same
# permission; a lookup that included the name would try to create a
# second row with the same codename and hit the unique constraint.
# Existing rows are never renamed or removed.
def ensure_permissions(using='default'):
    """Create any missing permission row. Returns the codenames created."""
    from django.contrib.auth.models import Permission, User
    from django.contrib.contenttypes.models import ContentType
    ct = ContentType.objects.db_manager(using).get_for_model(User)
    made = []
    for codename, name in all_codenames():
        _p, created = Permission.objects.using(using).get_or_create(
            codename=codename, content_type=ct, defaults={'name': name})
        if created:
            made.append(codename)
    return made
'''),
    ]),
    (os.path.join('pages', 'apps.py'), [
        (r'''    def ready(self):
        """Import signals when app is ready"""
        import pages.signals''',
         r'''    def ready(self):
        """Import signals when app is ready"""
        import pages.signals
        # SY-1, 26 Oct 2026 - every module permission exists after every
        # migrate (pages/permissions.py, ensure_permissions). sender=self:
        # once per migrate, after this app's migrations; the dispatch_uid
        # keeps a second ready() from connecting it twice.
        from django.db.models.signals import post_migrate
        post_migrate.connect(_ensure_permissions, sender=self,
                             dispatch_uid='pages.ensure_permissions')


def _ensure_permissions(sender, using='default', verbosity=1, **kwargs):
    from pages.permissions import ensure_permissions
    made = ensure_permissions(using)
    if made and verbosity:
        print('  Created %d permission(s): %s' % (len(made), ', '.join(made)))'''),
    ]),
    (os.path.join('pages', 'views_setup.py'), [
        (r'''        permissions_data = all_codenames()
        
        for codename, name in permissions_data:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=content_type,
            )
            if created:
''',
         r'''        permissions_data = all_codenames()
        
        # SY-1, 26 Oct 2026 - by codename, the name only a default: a row
        # whose name had drifted made the old lookup try a duplicate
        # codename and stop the whole page on the unique constraint.
        for codename, name in permissions_data:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name},
            )
            if created:
'''),
    ]),
    (os.path.join('pages', 'management', 'commands', 'create_module_permissions.py'), [
        (r'''        content_type = ContentType.objects.get_for_model(User)
        
        # Define permissions
        permissions_data = [
            ('can_access_properties', 'Can access Properties module'),
            ('can_access_tenants', 'Can access Tenants module'),
            ('can_access_suppliers', 'Can access Suppliers module'),
            ('can_access_expenses', 'Can access Expenses module'),
            ('can_access_petty_cash', 'Can access Petty Cash module'),
            ('can_access_financials', 'Can access Financials module'),
            ('can_access_invoices', 'Can access Invoices module'),
            ('can_access_projects', 'Can access Projects module'),
            ('can_access_issues', 'Can access Issues module'),
            ('can_access_dashboard', 'Can access Dashboard module'),
        ]
        
        created_permissions = []
''',
         r'''        content_type = ContentType.objects.get_for_model(User)
        
        # SY-1, 26 Oct 2026 - THE ONE LIST (pages/permissions.py), not a
        # ten-row copy of it that had no can_edit_* and none of the five
        # modules added since. migrate now does this anyway; the command
        # stays for --create-groups.
        from pages.permissions import all_codenames
        permissions_data = all_codenames()
        
        created_permissions = []
'''),
        (r'''            permission, created = Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=content_type,
            )
            
''',
         r'''            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name},
            )
            
'''),
    ]),
    (os.path.join('pages', 'middleware.py'), [
        (r'''

# Add this function to help create permissions programmatically
def create_module_permissions():
    """
    Helper function to create module permissions.
    Run this in Django shell or create a management command.
    """
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import User
    
    # Get content type (you can use any model, or create a custom one)
    content_type = ContentType.objects.get_for_model(User)
    
    permissions = [
        ('can_access_properties', 'Can access Properties module'),
        ('can_access_tenants', 'Can access Tenants module'),
        ('can_access_suppliers', 'Can access Suppliers module'),
        ('can_access_expenses', 'Can access Expenses module'),
        ('can_access_petty_cash', 'Can access Petty Cash module'),
        ('can_access_financials', 'Can access Financials module'),
        ('can_access_invoices', 'Can access Invoices module'),
        ('can_access_projects', 'Can access Projects module'),
        ('can_access_issues', 'Can access Issues module'),
        ('can_access_dashboard', 'Can access Dashboard module'),
    ]
    
    created_permissions = []
    for codename, name in permissions:
        permission, created = Permission.objects.get_or_create(
            codename=codename,
            name=name,
            content_type=content_type,
        )
        if created:
            created_permissions.append(permission)
            print(f"Created permission: {permission.name}")
        else:
            print(f"Permission already exists: {permission.name}")
    
    return created_permissions''',
         r'''

# SY-1, 26 Oct 2026 - THE OLD HELPER, KEPT FOR ANYONE WHO CALLS IT FROM
# A SHELL, now the shared one: its own ten-row list had no can_edit_* and
# looked rows up by name, which fails on a row whose name has drifted.
def create_module_permissions():
    """Create any missing module permission; returns the codenames made."""
    from pages.permissions import ensure_permissions
    return ensure_permissions()
'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    # asked for, so a push that does not mention workers behaves
    # exactly as every push before this round did.
    [int]$Workers = 0,
    # DP-1, 22 Oct 2026 - WAIT FOR THE DEPLOY, DO NOT ANNOUNCE IT.
    # Push 4 and push 5 both ended by saying Railway would build and
''',
         r'''    # asked for, so a push that does not mention workers behaves
    # exactly as every push before this round did.
    #
    # SY-1, 26 Oct 2026 - TWO BY DEFAULT, his decision. Pushes have been
    # typed with -Workers 2 or 3, because 6 (alv_run.py's
    # own default) crashes this laptop with 0xC0000374. -Workers 0 still
    # means say nothing and let the runner choose.
    [int]$Workers = 2,
    # DP-1, 22 Oct 2026 - WAIT FOR THE DEPLOY, DO NOT ANNOUNCE IT.
    # Push 4 and push 5 both ended by saying Railway would build and
'''),
    ]),
    (os.path.join('test_push_workers.py'), [
        (r'''    par = param_block(g)
    return {
        'the push script takes a -Workers parameter':
            '[int]$Workers = 0,' in par,
        '  defaulting to zero, so a push that says nothing is unchanged':
            bool(re.search(r'\[int\]\$Workers\s*=\s*0\s*,', par)),
        'and it reaches the runner':
            '--workers' in blk,
''',
         r'''    par = param_block(g)
    return {
        # SY-1, 26 Oct 2026 - DEFAULT 2, his decision: every push was
        # being typed with -Workers 2 or 3. -Workers 0 still says nothing.
        'the push script takes a -Workers parameter':
            '[int]$Workers = 2,' in par,
        '  defaulting to two since SY-1, so a bare push sweeps at 2':
            bool(re.search(r'\[int\]\$Workers\s*=\s*2\s*,', par)),
        'and it reaches the runner':
            '--workers' in blk,
'''),
        (r'''
    # THE ONE THAT MATTERS: zero adds nothing at all.
    ok('--workers' not in simulate(False, True, 0),
       'A PUSH THAT DOES NOT MENTION WORKERS IS BYTE-FOR-BYTE THE PUSH '
       'IT WAS BEFORE THIS ROUND - which is what makes the parameter '
       'safe to add to a script that runs every delivery')

    # AND THE SIMULATOR CAN FAIL. A comparison that cannot fail is
''',
         r'''
    # THE ONE THAT MATTERS: zero adds nothing at all.
    # SY-1, 26 Oct 2026 - a push that does not mention workers now
    # passes 2; -Workers 0 is how to leave the choice to the runner.
    ok('--workers' not in simulate(False, True, 0),
       '-Workers 0 adds nothing at all, so the runner own default is '
       'still one word away')

    # AND THE SIMULATOR CAN FAIL. A comparison that cannot fail is
'''),
    ]),
    (os.path.join('test_sentinels.py'), [
        (r'''# it is written.
PINNED = {
    # THE TWENTY-FIFTH - ES-7b, 25 Oct 2026 - REVEALED, NOT BROKEN. ES-6
    # CREATED pages/views/lease_signing_approve.py WITH _attach letting go
''',
         r'''# it is written.
PINNED = {
    # THE TWENTY-SIXTH - SY-1, 26 Oct 2026 - REVEALED, NOT BROKEN. The
    # round that made Receipts its own module wrote pages/permissions.py, and no
    # version has lacked it since; SY-1 (ensure_permissions) is the
    # first round to back that file up, so the row is proven blind the
    # day it ships - pinned in the same round.
    "can_access_receipts":
        'Receipts is its own grantable module - the file was written '
        'WITH it, and SY-1 is the first round since '
        'to back that file up',
    # THE TWENTY-FIFTH - ES-7b, 25 Oct 2026 - REVEALED, NOT BROKEN. ES-6
    # CREATED pages/views/lease_signing_approve.py WITH _attach letting go
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
    raise SystemExit('SY-1 REFUSED: %s' % msg)


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
    if "'test_system_round.py'" in read(pq):
        print('SY-1 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_tenant_identity.py'" not in read(pq):
        refuse('TI-1 is not applied - this round registers after it.')
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
    q = swap(q, """    'test_tenant_identity.py'
)""", """    'test_tenant_identity.py',
    # SY-1, 26 Oct 2026 - permissions on migrate; two workers.
    'test_system_round.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        """    @{ File = 'pages/apps.py'; Text = 'post_migrate.connect(_ensure_permissions'; What = 'SY-1: every module permission is created on every migrate - without it a fresh database refuses every Edit screen until a superuser opens User Administration' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_tenant_identity.py',
]""", """    'test_tenant_identity.py',
    # SY-1, 26 Oct 2026 - permissions on migrate; two workers.
    'test_system_round.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_tenantid',
]""", """    '.bak_tenantid',
    # SY-1, 26 Oct 2026 - permissions on migrate; two workers.
    '.bak_sysround',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # SY-1, 26 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    pm = out[os.path.join(root, 'pages', 'permissions.py')]
    if 'def ensure_permissions(' not in pm:
        refuse('pages/permissions.py did not gain ensure_permissions().')
    ap = out[os.path.join(root, 'pages', 'apps.py')]
    if 'post_migrate.connect(_ensure_permissions, sender=self' not in ap:
        refuse('pages/apps.py does not connect the receiver.')
    if '[int]$Workers = 2,' not in out[pq]:
        refuse('the push default is not two workers.')

    if CHECK:
        print('SY-1 --check: %d file(s) would change, none written; %d '
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
    print('SY-1 applied - permissions created on every migrate; the push '
          'sweeps at two workers by default.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
