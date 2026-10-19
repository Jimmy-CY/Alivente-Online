# -*- coding: utf-8 -*-
"""check_db_target.py - WHICH database is this process talking to?

    python check_db_target.py

READ-ONLY. It opens a connection, asks three questions and closes it.
It writes nothing, migrates nothing and creates nothing.

IT PRINTS NO PASSWORD. The USER and PASSWORD settings are reported as
`set` or `NOT SET` and never as values. The HOST and NAME are printed
in full, because they are the answer - but they are an endpoint of
yours, so the output is split into two parts and only the SAFE TO
PASTE half is meant to leave your machine.

WHY IT EXISTS. On 19 Oct the local runserver said:

    You have 1 unapplied migration(s) ... app(s): pages
    Table 'railway.meal_entries' doesn't exist

`railway` is the default schema name on every Railway MySQL instance,
so the message does NOT say which instance. Meanwhile
alivente.online serves the planner, which means the database
PRODUCTION uses does have that table. Two databases, both called
railway, and the local .env names one of them.

Knowing which one matters before anything is run, because every
credential comes from the environment: `manage.py migrate` on the
laptop writes to whatever HOST the .env names, which may not be a
local database at all.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

import django                                                # noqa: E402

django.setup()

from django.conf import settings                             # noqa: E402
from django.db import connection                             # noqa: E402
from django.db.migrations.loader import MigrationLoader      # noqa: E402

d = settings.DATABASES['default']

print('')
print('=' * 70)
print('  FOR YOUR EYES - this names an endpoint of yours')
print('=' * 70)
print('  HOST     : %s' % (d.get('HOST') or '(empty - a local socket)'))
print('  PORT     : %s' % (d.get('PORT') or '(default)'))
print('  NAME     : %s' % d.get('NAME'))
print('  USER     : %s' % ('set' if d.get('USER') else 'NOT SET'))
print('  PASSWORD : %s' % ('set' if d.get('PASSWORD') else 'NOT SET'))
print('')
print('  Compare that HOST with the one Railway shows for the service')
print('  alivente.online runs on. If they differ, this laptop is')
print('  pointed at a DIFFERENT database from the live site.')

ok_conn, tables, applied, unapplied = False, [], [], []
try:
    with connection.cursor() as c:
        c.execute("SELECT DATABASE()")
        schema = c.fetchone()[0]
        c.execute("SHOW TABLES LIKE 'meal%'")
        tables = sorted(r[0] for r in c.fetchall())
        c.execute("SHOW TABLES LIKE 'menu%'")
        tables += sorted(r[0] for r in c.fetchall())
    ok_conn = True
except Exception as e:
    schema = None
    err = str(e).split('\n')[0][:160]

if ok_conn:
    loader = MigrationLoader(connection)
    done = loader.applied_migrations
    for node in sorted(loader.graph.nodes):
        if node[0] != 'pages':
            continue
        (applied if node in done else unapplied).append(node[1])

print('')
print('=' * 70)
print('  SAFE TO PASTE - no host, no user, no password')
print('=' * 70)
if not ok_conn:
    print('  CONNECTED            : NO')
    print('  reason               : %s' % err)
    print('')
    print('  Nothing else can be asked until a connection opens.')
    sys.exit(1)

print('  CONNECTED            : yes, schema %r' % schema)
print('  meal/menu tables     : %s' % (', '.join(tables) if tables
                                       else 'NONE'))
print('  pages migrations     : %d applied, %d unapplied'
      % (len(applied), len(unapplied)))
if unapplied:
    print('  the unapplied one(s) : %s' % ', '.join(unapplied[:5]))
print('  latest applied       : %s' % (applied[-1] if applied else 'none'))
print('')

want = ('meal_entries', 'menus', 'menu_items')
missing = [t for t in want if t not in tables]
if missing:
    print('  VERDICT: this database is MISSING %s.' % ', '.join(missing))
    print('           Migration 0100 has not run against it.')
else:
    print('  VERDICT: this database has all three of 0100 tables.')
    print('           Whatever the warning was about, it is not these.')
print('=' * 70)
print('')
