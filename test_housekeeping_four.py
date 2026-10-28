# -*- coding: utf-8 -*-
"""test_housekeeping_four.py - round HK-4, 28 Oct 2026.

RELEASE 32 - PROJECT HELP, THE FINANCIAL INDICATORS IN HOUSE SHADES, AND
THE GATE FASTER AGAIN. His decisions of 28 October.

    - HELP ON PROJECT DETAILS. His finding while testing Release 30: the
      Projects page had Help and the page it opens did not. The same
      Projects module now opens from Project Details, desktop and phone.
    - FINANCIAL INDICATORS IN THE HOUSE SHADES, render approved. Each
      indicator's figure carried a colour of its own - Bootstrap green,
      red, a yellow unreadable on white, purple - which read as a verdict
      on figures that are only categories. The figures take the house
      ink, as every stat card does; the bars on each graph (better than,
      near, worse than the portfolio average) take --alv-good, --alv-warn
      and --alv-bad, READ from base because a canvas cannot resolve var().
    - THE GATE, PART THREE. Nine suites ran another suite inside
      themselves - one the gate also runs by name - to read a verdict the
      gate already reaches and that stops the push exactly as hard. Each
      now checks the suite is on the gate and that the claims it was
      asked for are still in it. test_gate_walk times its regex control
      on fifteen names, not sixty (the claim is a ratio). test_line_soft
      keeps one page per width. Alone, old against new on the same tree,
      every result identical: 328s -> 140s across the eleven.
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

SUFFIX = '.bak_housekeep4'
ME = 'test_housekeeping_four.py'
PATCHER = 'apply_housekeeping_four.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'HK-4, 28 Oct 2026'

J = os.path.join
TPL = J(ROOT, 'pages', 'templates')
DETAIL = J(TPL, 'projects', 'projects_detail.html')
FI = J(TPL, 'finance', 'financial_indicators.html')
GATE = J(ROOT, PS1)

# THE NINE THAT RAN A SUITE INSIDE THEMSELVES, and the suite each ran.
NESTED = (
    ('test_bar_audit.py', ('test_bar_order.py',)),
    ('test_photo_floor.py', ('test_recipe_photos.py',)),
    ('test_week_fill.py', ('test_week_band.py',)),
    ('test_print_shape.py', ('test_print_plan.py',)),
    ('test_print_compact.py', ('test_print_shape.py',)),
    ('test_menu_range.py', ('test_meal_week.py',)),
    ('test_msg_base.py', ('test_msg_bar.py', 'test_message_bar.py',
                          'test_auth_flow.py')),
    ('test_help_agrees.py', ('test_meal_guide3.py', 'test_meal_guide5.py',
                             'test_meal_help.py')),
    ('test_meal_week.py', ('test_more_menu.py', 'test_last_menus.py')),
)
WALK = J(ROOT, 'test_gate_walk.py')
LINE = J(ROOT, 'test_line_soft.py')
PINS = ('test_bar_height.py', 'test_help_label.py', 'test_amber.py',
        'test_cssrules_outside.py', 'test_neutrals.py',
        'test_housekeeping_three.py')
EDITED = ((DETAIL, FI, WALK, LINE) + tuple(J(ROOT, s) for s, _x in NESTED)
          + tuple(J(ROOT, p) for p in PINS))

BRIGHTS = ('#28a745', '#dc3545', '#ffc107', '#6f42c1', '#20c997',
           '#17a2b8', '#007bff')

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
from alv_rounds import as_left_by                          # noqa: E402

NOW = dict((p, as_left_by(p, SUFFIX, read)) for p in EDITED)
OLD = dict((p, was(p)) for p in EDITED)


def nested_run(src, target):
    """Does this suite still launch `target` as a subprocess?"""
    code = T.python_code_only(src)
    names = set([target])
    for m in re.finditer(r'(?m)^\s*([A-Z_]+)\s*=\s*[\'"]%s[\'"]'
                         % re.escape(target), code):
        names.add(m.group(1))
    if re.search(r'for\s+\w+(?:\s*,\s*\w+)?\s+in\s+[^:]*%s'
                 % re.escape(target), code):
        names.add('suite')
    # A TUPLE NAMED ONCE AND LOOPED LATER - test_msg_base's CORRECTS.
    for m in re.finditer(r'(?m)^\s*([A-Z_]+)\s*=\s*\(.*%s'
                         % re.escape(target), code):
        for lm in re.finditer(r'for\s+(\w+)\s+in\s+%s\b' % m.group(1),
                              code):
            names.add(lm.group(1))
    runs = re.findall(r'subprocess\.run\(\[sys\.executable,\s*(\w+|\'[^\']+\')',
                      code)
    return any(r.strip("'") in names for r in runs)


def claims(src):
    out = []
    d = T.code_only(src[DETAIL])
    out.append(('{% load help_modal_tags %}' in d
                and d.count('data-target="#projectsHelpModal"') == 2
                and '{% render_help_modal "projects" %}' in d,
                'Project Details opens the Projects help, on the bar and in '
                'the phone\'s More menu'))
    f = src[FI]
    js = T.code_only_js(f)
    lits = [x for x in re.findall(r'#[0-9a-fA-F]{6}\b', T.code_only(f))
            if x.lower() in BRIGHTS]
    out.append(('indicator.color' not in js and not lits,
                'Financial Indicators carries no indicator colour and no '
                'Bootstrap bright'))
    out.append(("fiTok('good'" in js and "fiTok('warn'" in js
                and "fiTok('bad'" in js
                and "getPropertyValue('--alv-' + n)" in js,
                '  and its bars read --alv-good, --alv-warn and --alv-bad '
                'from base'))
    for suite, targets in NESTED:
        s = src[J(ROOT, suite)]
        out.append((not any(nested_run(s, t) for t in targets)
                    and 'GS-3, 28 Oct 2026' in s,
                    '%s no longer runs %s inside itself'
                    % (suite, ', '.join(targets))))
    out.append(('names[:15]' in T.python_code_only(src[WALK]),
                'test_gate_walk times its regex control on fifteen names'))
    out.append(('_PAGES = {}' in T.python_code_only(src[LINE])
                and 'ctx.close()' not in T.python_code_only(src[LINE]),
                'test_line_soft keeps one page per width'))
    return out


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
gate = read(GATE)
for suite, targets in NESTED:
    for t in targets:
        ok("'%s'" % t in gate,
           '  %s is on the gate, so its verdict still stops a push' % t)
undated = [os.path.relpath(p, ROOT) for p in EDITED
           if MARK not in NOW[p] and 'GS-3, 28 Oct 2026' not in NOW[p]]
ok(not undated, 'the round dates itself in every file it edited',
   ', '.join(undated))

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
held = [m for c, m in claims(OLD) if c]
ok(not held, 'CONTROL: not one of this round\'s claims held before it',
   '\n'.join(held))
ran = [s for s, ts in NESTED
       if not any(nested_run(OLD[J(ROOT, s)], t) for t in ts)]
ok(not ran, 'CONTROL: and the detector really saw all nine nested runs '
   'in the backups', ran)

# ==========================================================================
head('3. DRIVEN - Project Details rendered by Django')
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.contrib.auth.models import User
    from django.db import connection, transaction
    from django.test import Client
    django_up = True
except Exception as e:                                       # noqa: BLE001
    skip('section 3', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])


class Rollback(Exception):
    """Nothing this suite writes survives it."""


if django_up:
    try:
        import pages.models as M
        connection.ensure_connection()
        Project = M.Project
        with transaction.atomic():
            u = User.objects.create_superuser(
                username='hk4check', email='hk4@example.com',
                password='not-a-real-password')
            c = Client(SERVER_NAME='localhost')
            c.force_login(u)
            prop = M.props.objects.create(prop_name='HK4 Flat',
                                          prop_country='Cyprus')
            pr = Project.objects.create(project_name='HK4 Project',
                                        prop=prop)
            pk = pr.pk
            r = c.get('/projects/detail/%d/' % pk)
            body = r.content.decode('utf-8', 'replace')
            ok(r.status_code == 200, 'Project Details renders',
               r.status_code)
            ok(body.count('data-target="#projectsHelpModal"') == 2
               and 'id="projectsHelpModal"' in body,
               '  with its Help button and More-menu item, and the module '
               'they open on the page')
            r = c.get('/financial-indicators/')
            body = r.content.decode('utf-8', 'replace')
            ok(r.status_code == 200 and "fiTok('good'" in body
               and 'indicator.color' not in body,
               'Financial Indicators renders, reading its bar colours from '
               'the house tokens', r.status_code)
            raise Rollback()
    except Rollback:
        pass
    except Exception as e:                                   # noqa: BLE001
        skip('section 3', 'no database or no project model: %s'
             % str(e).split('\n')[0][:80])

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = 'data-target=\"#projectsHelpModal\"'" in gate,
   '  with a sentinel on the Project Details Help')
wd = read(J(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')
nob = [os.path.relpath(p, ROOT) for p in EDITED
       if not os.path.isfile(p + SUFFIX)]
ok(not nob, '  every file it edited has its backup', ', '.join(nob))

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
