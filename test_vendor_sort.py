# -*- coding: utf-8 -*-
"""test_vendor_sort.py - round VS-1, 29 Oct 2026.

RELEASE 39 - SORTABLEJS FROM THE APP, AND NO SNAPSHOT CHURN. His plan of
29 October:

    - SortableJS 1.15.0 is served from the app (static/vendor, and
      staticfiles/, which WhiteNoise serves on Live) instead of the jsDelivr
      CDN, on the meal planner and the recipe import preview. The drag
      suites now serve that same file, so they run on any machine.
    - A budget or revenue snapshot identical to the one already in force is
      not appended (one expense had collected seven in a day, four of them
      identical). Skipping one changes no month the resolver reports.
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

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_vendorsort'
ME = 'test_vendor_sort.py'
PATCHER = 'apply_vendor_sort.py'
PS1 = 'Push-PendingChanges.ps1'
MARKS = ('VS-1, 29 Oct 2026',)

J = os.path.join
TPL = J(ROOT, 'pages', 'templates')
PLANNER = J(TPL, 'meal_planner.html')
PREVIEW = J(TPL, 'preview_imported_recipe.html')
MODELS = J(ROOT, 'pages', 'models.py')
SRC_JS = J(ROOT, 'static', 'vendor', 'sortablejs', 'Sortable.min.js')
LIVE_JS = J(ROOT, 'staticfiles', 'vendor', 'sortablejs', 'Sortable.min.js')
GATE = J(ROOT, PS1)
GITIGNORE = J(ROOT, '.gitignore')
EDITED = [PLANNER, PREVIEW, MODELS, GITIGNORE]
UNDATED = [J(ROOT, 'test_week_drag.py'), J(ROOT, 'test_day_order.py'),
           J(ROOT, 'test_prorata_history.py'), J(ROOT, 'test_delete_choice.py')]
CDN = 'cdn.jsdelivr.net/npm/sortablejs'
TAG = "<script src=\"{% static 'vendor/sortablejs/Sortable.min.js' %}\"></script>"

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
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402


def ignored(gitignore_text, path):
    """Would .gitignore keep `path` out of `git add -A`? A small reading of
    the two rules this round is about - a directory rule and a negation -
    not a git: asked of the current file and of the backup."""
    lines = [l.strip() for l in gitignore_text.splitlines()
             if l.strip() and not l.strip().startswith('#')]
    top = path.split('/')[0]
    if top + '/' in lines:                       # whole directory ignored
        return True
    out = False
    for l in lines:
        if l == top + '/*':
            out = True
        elif l.startswith('!') and path.startswith(l[1:]):
            out = False
    return out


def claims(planner, preview, models, gitignore_text):
    out = []
    out.append((not ignored(gitignore_text,
                            'staticfiles/vendor/sortablejs/Sortable.min.js'),
                '.gitignore lets staticfiles/vendor/ through, so git add '
                'commits the file Live serves'))
    for t, name in ((planner, 'the meal planner'),
                    (preview, 'the recipe import preview')):
        code = T.code_only(t)
        out.append((TAG in code and CDN not in code,
                    '%s loads SortableJS from the app, not the CDN' % name))
    m = T.python_code_only(models)
    out.append(('def _fh_unchanged(' in m
                and m.count('prev = _fh_unchanged(') == 2,
                'budget and revenue history skip a snapshot identical to the '
                'one in force'))
    return out


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(read(PLANNER), read(PREVIEW), read(MODELS),
                        read(GITIGNORE)):
    ok(cond, msg)
js = open(SRC_JS, 'rb').read() if os.path.isfile(SRC_JS) else b''
ok(js.startswith(b'/*! Sortable 1.15.0 - MIT'),
   'static/vendor holds SortableJS 1.15.0 (MIT), the version the CDN served')
ok(os.path.isfile(LIVE_JS) and open(LIVE_JS, 'rb').read() == js,
   '  and staticfiles/ - what WhiteNoise serves on Live - holds the same file')
# Every template in every root, as alv_tree walks them.
left = [T.rel(p) for p in T.templates()
        if CDN in T.code_only(read(p))]
ok(not left, 'no template loads SortableJS from the CDN any more',
   ', '.join(left))
# AND ASK GIT ITSELF, where there is one - the real rule, not a reading.
import subprocess                                           # noqa: E402
try:
    _r = subprocess.run(['git', 'check-ignore', '-q', '--no-index',
                         'staticfiles/vendor/sortablejs/Sortable.min.js'],
                        cwd=ROOT, capture_output=True, timeout=30)
    if _r.returncode in (0, 1):
        ok(_r.returncode == 1, '  and git check-ignore agrees: the file is '
                               'not ignored')
    else:
        skip('git check-ignore', 'not a git working tree here')
except (OSError, subprocess.SubprocessError):
    skip('git check-ignore', 'git is not available')
dated = [os.path.relpath(p, ROOT) for p in EDITED
         if not any(mk in read(p) for mk in MARKS)]
ok(not dated, 'the round dates itself in every file it edited',
   ', '.join(dated))

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
for cond, msg in claims(was(PLANNER), was(PREVIEW), was(MODELS),
                        was(GITIGNORE)):
    ok(not cond, 'CONTROL: before this round - %s' % msg.strip())

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    import django
    django.setup()
    from django.db import connection, transaction
    from django.test import Client
    import pages.models as M
    connection.ensure_connection()
    M.props.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3', 'no database: %s' % str(_e).split('\n')[0][:70])


class Rollback(Exception):
    pass


if have_db:
    import datetime as dt
    from decimal import Decimal
    FH = M.FinancialFigureHistory
    try:
        with transaction.atomic():
            p = M.props.objects.create(prop_name='VS1 Flat',
                                       prop_country='Cyprus',
                                       prop_available_for_rent='Yes')
            lt = M.expense_line_types.objects.create(
                expense_line_types_name='VS1 Line')
            et = M.expense_types.objects.create()
            kw = dict(prop=p, expense_amount=Decimal('1200.00'),
                      expense_line_types=lt, expense_types=et)
            for m in M._FH_MONTHS:
                kw['expense_' + m] = Decimal('100.00')
            e = M.expense.objects.create(**kw)
            n = lambda: FH.objects.filter(kind=FH.KIND_BUDGET,
                                          source_pk=e.expense_id).count()
            M.record_expense_history(e, dt.date(2026, 1, 1))
            M.record_expense_history(e, dt.date(2026, 3, 1))
            M.record_expense_history(e, dt.date(2026, 3, 1))
            ok(n() == 1, 'three saves with nothing changed leave ONE '
                         'snapshot, not three', n())
            e.expense_jul = Decimal('150.00')
            e.expense_amount = Decimal('1250.00')
            e.save()
            M.record_expense_history(e, dt.date(2026, 7, 1))
            ok(n() == 2, '  and a real change is still recorded', n())
            before = M.resolve_year_months_bulk([p.prop_id], FH.KIND_BUDGET,
                                                2026)
            # Backdated, identical to what was in force in May: skipped,
            # and the year reads the same.
            e2 = M.expense.objects.get(pk=e.pk)
            e2.expense_jul = Decimal('100.00')
            e2.expense_amount = Decimal('1200.00')
            M.record_expense_history(e2, dt.date(2026, 5, 1))
            after = M.resolve_year_months_bulk([p.prop_id], FH.KIND_BUDGET,
                                               2026)
            ok(n() == 2 and before == after,
               '  a backdated copy of the figures already in force is '
               'skipped, and no month of the year changes')
            raise Rollback()
    except Rollback:
        pass
    except Exception as exc:                                  # noqa: BLE001
        ok(False, 'section 3 ran', repr(exc)[:200])
    c = Client(SERVER_NAME='localhost')
    r = c.get('/static/vendor/sortablejs/Sortable.min.js')
    body = b''.join(r.streaming_content) if getattr(r, 'streaming', False) \
        else r.content
    ok(r.status_code == 200 and body.startswith(b'/*! Sortable 1.15.0'),
       'the app serves /static/vendor/sortablejs/Sortable.min.js',
       r.status_code)

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = 'def _fh_unchanged('" in gate,
   '  with a sentinel on the churn guard')
wd = read(J(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')
nob = [os.path.relpath(p, ROOT) for p in EDITED + UNDATED
       if not os.path.isfile(p + SUFFIX)]
ok(not nob, '  every file it edited has its backup', ', '.join(nob))

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
