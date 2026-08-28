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
