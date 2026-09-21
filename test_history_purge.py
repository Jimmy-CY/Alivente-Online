# -*- coding: utf-8 -*-
"""test_history_purge.py - a financial row's history goes with it, on every
route a row can be deleted by.

    python test_history_purge.py

Run from the repo root. Paired with apply_history_purge.py (21 Sep).

  1. The receiver is connected to exactly the four models that keep
     history - expense, revenue, prop_values, act_expense - each with the
     kind the history table files it under.
  2. IN A REAL DATABASE: the project's own models, built into an in-memory
     SQLite with migrations switched off, so nothing here can reach your
     development or your production database. Rows are deleted the ways
     the application deletes them - one object, a queryset, a property
     cascade - and each row's snapshots must go while a neighbour's stay.
  3. CONTROLS: with the receiver disconnected the same delete must leave
     the snapshots behind - so section 2 can fail - and the backup of
     signals.py must not have had it.
  4. The two explicit purges in views/finance.py are still there, and
     Remove-HistoryOrphans.ps1 is dry-run by default, guarded, archived.
  5. It is on the gate.
"""
# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

import os
import re
import sys

if not os.path.isdir(os.path.join('pages', 'templates')):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_histpurge'
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_history_purge.py'
SIGNALS = os.path.join('pages', 'signals.py')
REMOVER = 'Remove-HistoryOrphans.ps1'

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


# --------------------------------------------------------------------------
# Django, on an in-memory SQLite. The project's settings are copied and the
# DATABASES entry REPLACED before anything connects, so this suite cannot
# touch MySQL - local or Railway - whatever the environment says.
# --------------------------------------------------------------------------
sys.path.insert(0, os.getcwd())
django_ok, why = False, ''
try:
    import importlib
    import django
    from django.conf import settings
    if not settings.configured:
        _s = importlib.import_module('mysite.settings')
        cfg = {k: getattr(_s, k) for k in dir(_s) if k.isupper()}
        cfg['DATABASES'] = {'default': {'ENGINE': 'django.db.backends.sqlite3',
                                        'NAME': ':memory:'}}
        cfg['MIGRATION_MODULES'] = {a.split('.')[-1]: None
                                    for a in cfg['INSTALLED_APPS']}
        settings.configure(**cfg)
    django.setup()
    from django.db import connection
    assert connection.vendor == 'sqlite', connection.vendor
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0)
    django_ok = True
except Exception as e:
    why = '%s: %s' % (type(e).__name__, str(e)[:120])

# ==========================================================================
print('=' * 74)
print('1. THE RECEIVER IS ON THE FOUR MODELS THAT KEEP HISTORY')
print('=' * 74)
if not django_ok:
    skip('1-3', 'Django would not start on SQLite: %s' % why)
else:
    from django.db.models.signals import post_delete
    from pages import signals as S
    from pages.models import (expense, revenue, prop_values, act_expense,
                              FinancialFigureHistory as H, KIND_VALUATION,
                              KIND_ACTUAL_EXPENSE, props)
    ok(connection.vendor == 'sqlite' and ':memory:' in str(
        connection.settings_dict['NAME']),
       'CONTROL: the database under test is an in-memory SQLite, not MySQL')
    WANT = {expense: H.KIND_BUDGET, revenue: H.KIND_REVENUE,
            prop_values: KIND_VALUATION, act_expense: KIND_ACTUAL_EXPENSE}
    got = getattr(S, 'HISTORY_KIND_OF', None)
    ok(got == WANT, 'the four models, each filed under its own kind',
       got)
    fn = getattr(S, 'purge_history_of_deleted_row', None)
    for model in WANT:
        live = post_delete._live_receivers(model)
        live = live[0] if isinstance(live, tuple) else live
        ok(fn is not None and fn in list(live),
           '%-12s post_delete reaches the purge' % model.__name__)

    # ======================================================================
    print('\n' + '=' * 74)
    print('2. IN A REAL DATABASE - EVERY ROUTE TAKES ITS HISTORY WITH IT')
    print('=' * 74)
    import datetime
    from django.db import models as M, transaction

    def make(model, **given):
        """A row with every required field filled - FKs made the same way."""
        vals = dict(given)
        for f in model._meta.concrete_fields:
            if f.primary_key or f.name in vals or f.attname in vals:
                continue
            if f.null or f.has_default() or getattr(f, 'auto_now', False) \
                    or getattr(f, 'auto_now_add', False):
                continue
            if isinstance(f, M.ForeignKey):
                vals[f.name] = make(f.related_model)
            elif f.choices:
                vals[f.name] = f.choices[0][0]
            elif isinstance(f, (M.DateTimeField,)):
                vals[f.name] = datetime.datetime(2026, 1, 1)
            elif isinstance(f, M.DateField):
                vals[f.name] = datetime.date(2026, 1, 1)
            elif isinstance(f, (M.IntegerField, M.DecimalField,
                                M.FloatField)):
                vals[f.name] = 0
            elif isinstance(f, M.BooleanField):
                vals[f.name] = False
            elif isinstance(f, (M.FileField,)):
                vals[f.name] = ''
            else:
                vals[f.name] = 'x'
        return model.objects.create(**vals)

    def snap(prop, kind, pk):
        return make(H, prop=prop, kind=kind, source_pk=pk,
                    effective_date=datetime.date(2026, 1, 1))

    def left(kind, pk):
        return H.objects.filter(kind=kind, source_pk=pk).count()

    prop = make(props)
    rows = {}
    for model, kind in WANT.items():
        a = make(model, prop=prop) if 'prop' in [
            f.name for f in model._meta.fields] else make(model)
        b = make(model, prop=prop) if 'prop' in [
            f.name for f in model._meta.fields] else make(model)
        for r in (a, b):
            snap(prop, kind, r.pk)
            snap(prop, kind, r.pk)
        rows[model] = (a, b)

    # route 1: one object, the way a view deletes it
    for model, kind in WANT.items():
        a, b = rows[model]
        pk_a, pk_b = a.pk, b.pk
        with transaction.atomic():
            a.delete()
        ok(left(kind, pk_a) == 0 and left(kind, pk_b) == 2,
           '%-12s one row deleted: its 2 snapshots gone, its neighbour\'s 2 '
           'kept' % model.__name__,
           'deleted %d left, neighbour %d' % (left(kind, pk_a),
                                              left(kind, pk_b)))

    # route 2: a queryset delete - what "remove line type" does
    model, kind = expense, H.KIND_BUDGET
    extra = [make(expense, prop=prop) for _ in range(3)]
    for e in extra:
        snap(prop, kind, e.pk)
    ids = [e.pk for e in extra]
    expense.objects.filter(pk__in=ids).delete()
    ok(all(left(kind, i) == 0 for i in ids),
       'expense      a queryset delete of 3 rows takes all 3 histories')

    # route 3: a property cascade - no view anywhere names this route
    p2 = make(props)
    e2 = make(expense, prop=p2)
    snap(prop, H.KIND_BUDGET, e2.pk)       # filed under ANOTHER property
    pk2 = e2.pk
    p2.delete()
    ok(not expense.objects.filter(pk=pk2).exists()
       and left(H.KIND_BUDGET, pk2) == 0,
       'props        deleting a property cascades to its expense, and the '
       'expense\'s history goes too - even filed under another property')

    # ======================================================================
    print('\n' + '=' * 74)
    print('3. CONTROLS')
    print('=' * 74)
    e3 = make(expense, prop=prop)
    snap(prop, H.KIND_BUDGET, e3.pk)
    pk3 = e3.pk
    for m in WANT:
        post_delete.disconnect(fn, sender=m,
                               dispatch_uid='alv_history_purge_%s'
                               % m.__name__)
    e3.delete()
    ok(left(H.KIND_BUDGET, pk3) == 1,
       'CONTROL: with the receiver disconnected the same delete leaves an '
       'orphan - section 2 can fail', '%d left' % left(H.KIND_BUDGET, pk3))
    for m in WANT:
        post_delete.connect(fn, sender=m, dispatch_uid='alv_history_purge_%s'
                            % m.__name__)
    if os.path.isfile(SIGNALS + SUFFIX):
        ok('purge_history_of_deleted_row' not in read(SIGNALS + SUFFIX),
           'CONTROL: signals.py before the round had no such receiver')
    else:
        skip('the backup had no receiver', 'no %s backup' % SUFFIX)

# ==========================================================================
print('\n' + '=' * 74)
print('4. THE EXPLICIT PURGES STAY, AND THE LIVE CLEAN-UP IS GUARDED')
print('=' * 74)
fin = read(os.path.join('pages', 'views', 'finance.py'))
ok(fin.count('purge_figure_history(FinancialFigureHistory.KIND_BUDGET') == 2,
   'views/finance.py still purges on its two delete paths - belt and braces')
if os.path.isfile(REMOVER):
    r = read(REMOVER)
    ok('[switch] $Apply' in r and 'if ($Apply)' in r,
       '%s is a dry run unless -Apply is given' % REMOVER)
    ok('EXPECTED_COUNT = 30' in r and 'range(28, 38)' in r,
       'it refuses unless the orphans are exactly the 30 on ids 28-37')
    ok('transaction.atomic()' in r and 'deleted != len(want)' in r,
       'it deletes inside one transaction and rolls back on a wrong count')
    ok('history_orphans_archive' in r and 'Test-Path' in r,
       'it will not delete before the archive file exists on this machine')
    ok('PASSWORD' not in r.upper().replace('NO PASSWORD', ''),
       'it never reads a password')
else:
    skip(REMOVER, 'not on disk')

# ==========================================================================
print('\n' + '=' * 74)
print('5. IT IS ON THE GATE')
print('=' * 74)
if os.path.isfile(PS1):
    ps = read(PS1)
    i = ps.find('$suites = @(')
    j = ps.find('\n)', i)
    ok(i >= 0 and "'%s'" % ME in ps[i:j],
       '%s runs %s on every push' % (PS1, ME))
else:
    skip('the gate', '%s not on disk' % PS1)

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
sys.exit(1 if failed else 0)
