"""The module permission list - ONE definition, two consumers.

WHY THIS FILE EXISTS. The same list was written twice: `all_permissions` in
`views/users.py`, which drives the User Administration screen and creates the
Permission rows, and `permissions_data` in `views_setup.py`, which seeds a
fresh environment. They had drifted. views_setup was missing
`can_access_administration`, `can_access_passports`, `can_access_recipes`,
`can_access_celebrations` and `can_access_crs`, and it carried **no
`can_edit_*` codenames at all** - so a rebuilt environment came up with about
half the permissions the system actually checks, and the missing half only
showed up as a 403 on a screen somebody could reach yesterday.

Both now read this. A new module is added HERE, once, and both the admin
screen and the seeder gain it together.

`edit_codename` is None for a module that has no edit tier - Dashboard and
Administration are look-at-it screens.
"""

MODULE_PERMISSIONS = [
    {'codename': 'can_access_properties',     'edit_codename': 'can_edit_properties',     'label': 'Properties',            'icon': 'fa-building'},
    {'codename': 'can_access_tenants',        'edit_codename': 'can_edit_tenants',        'label': 'Tenants',               'icon': 'fa-users'},
    {'codename': 'can_access_suppliers',      'edit_codename': 'can_edit_suppliers',      'label': 'Suppliers',             'icon': 'fa-truck'},
    {'codename': 'can_access_expenses',       'edit_codename': 'can_edit_expenses',       'label': 'Expenses',              'icon': 'fa-receipt'},
    {'codename': 'can_access_petty_cash',     'edit_codename': 'can_edit_petty_cash',     'label': 'Petty Cash',            'icon': 'fa-coins'},
    {'codename': 'can_access_financials',     'edit_codename': 'can_edit_financials',     'label': 'Financials',            'icon': 'fa-chart-line'},
    {'codename': 'can_access_invoices',       'edit_codename': 'can_edit_invoices',       'label': 'Invoices',              'icon': 'fa-file-invoice'},
    # Receipts is its OWN module, not a corner of Invoices: issuing a receipt
    # for cash received is a different duty from raising and chasing an
    # invoice, and the two should be grantable apart.
    {'codename': 'can_access_receipts',       'edit_codename': 'can_edit_receipts',       'label': 'Receipts',              'icon': 'fa-receipt'},
    {'codename': 'can_access_projects',       'edit_codename': 'can_edit_projects',       'label': 'Projects',              'icon': 'fa-project-diagram'},
    {'codename': 'can_access_issues',         'edit_codename': 'can_edit_issues',         'label': 'Issues',                'icon': 'fa-exclamation-circle'},
    {'codename': 'can_access_dashboard',      'edit_codename': None,                      'label': 'Dashboard',             'icon': 'fa-tachometer-alt'},
    {'codename': 'can_access_administration', 'edit_codename': None,                      'label': 'Administration',        'icon': 'fa-cogs'},
    {'codename': 'can_access_passports',      'edit_codename': 'can_edit_passports',      'label': 'Passports / Documents', 'icon': 'fa-passport'},
    {'codename': 'can_access_recipes',        'edit_codename': 'can_edit_recipes',        'label': 'Recipes',               'icon': 'fa-utensils'},
    {'codename': 'can_access_celebrations',   'edit_codename': 'can_edit_celebrations',   'label': 'Celebrations',          'icon': 'fa-birthday-cake'},
    {'codename': 'can_access_crs',            'edit_codename': 'can_edit_crs',            'label': 'CRS Reporting',         'icon': 'fa-landmark'},
    # WL-1, 30 Oct 2026 - Wellness. NO EDIT TIER: everything in it is the
    # person's own, so seeing it and changing it are the same right. And
    # access is never access to anyone else's - every query is filtered
    # by the login, superusers included.
    {'codename': 'can_access_wellness',       'edit_codename': None,                      'label': 'Wellness',              'icon': 'fa-spa'},
]

# `can_access_fsr` is checked in the Issues module and granted to the Property
# Managers group, but it is not a row on the User Administration screen. It is
# listed here so the seeder still creates it, and named separately so nobody
# adds it to the screen by accident.
EXTRA_PERMISSIONS = [
    ('can_access_fsr', 'Can access FSR module'),
]


def all_codenames():
    """Every codename the system expects to exist, access and edit tiers both."""
    out = []
    for m in MODULE_PERMISSIONS:
        out.append((m['codename'], "Can access %s" % m['label']))
        if m['edit_codename']:
            out.append((m['edit_codename'], "Can edit %s" % m['label']))
    out.extend(EXTRA_PERMISSIONS)
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
