# -*- coding: utf-8 -*-
"""test_housekeeping_three.py - round HK-3, 28 Oct 2026.

RELEASE 30 - ONE jQUERY, A FASTER GATE, AND THE HOUSE COLOURS.

    - ONE jQUERY, ONE BOOTSTRAP. base.html loaded jQuery at the foot of
      the page; 33 pages loaded their own copy inside their content,
      because their scripts ran before base's did. Nine of them also
      loaded a second Bootstrap (4.5.2 or 4.6.0) over base's 4.1.3. Two
      jQuerys means a plugin bound to one is invisible to the other; two
      Bootstraps means every data-toggle is answered twice. base now
      loads jQuery, Popper and Bootstrap once, in <head>, ahead of every
      page's scripts, and no page loads its own. Measured in Chromium
      with the exact CDN versions served locally, on the 21 of those
      pages that open without an id: the same jQuery and Bootstrap
      versions, the same console, and every help modal still opens on
      its button - before and after.
    - A FASTER GATE. test_print_queries (215s on the gate) and
      test_dr2_values (182s) opened a fresh page for every measurement.
      Each now loads a fixture once and resizes it through its widths.
      Alone, old against new on the same tree, every result line
      identical: 165s -> 40s and 65s -> 11s.
    - THE HOUSE COLOURS. His eye, 28 Oct: on the Notifications dashboard
      the two newest boxes were darker than the other six. The two were
      the standard - the house tokens - and the six carried Bootstrap's
      brights in their icons. All eight now use the tokens, and so do the
      other Bootstrap brights a browser reads as CSS: two edit-form
      highlights, the shopping-list headings and the lease timeline's
      bars. What is left is counted and named below.
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

SUFFIX = '.bak_housekeep3'
ME = 'test_housekeeping_three.py'
PATCHER = 'apply_housekeeping_three.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'HK-3, 28 Oct 2026'

J = os.path.join
TPL = J(ROOT, 'pages', 'templates')
BASE = J(TPL, 'base.html')
NOTIF = J(TPL, 'notifications.html')
PQ = J(ROOT, 'test_print_queries.py')
DR = J(ROOT, 'test_dr2_values.py')
GATE = J(ROOT, PS1)

# THE 33 PAGES THAT LOADED THEIR OWN jQUERY, and of them the nine that
# also loaded their own Bootstrap. Named, so a page that grows a copy
# back is caught by section 1 and a page this list forgot by section 2.
JQ_PAGES = (
    'act_expense.html', 'asset_detail.html', 'customer_list.html',
    'edit_asset.html', 'finance/cashflow_forecast.html',
    'finance/financial_indicators.html', 'finance/vacancy_management.html',
    'finance_expense_add.html', 'finance_expense_edit.html',
    'finance_expense_line_types_add.html',
    'finance_expense_line_types_edit.html', 'finance_pl_act.html',
    'finance_valuations.html', 'finance_valuations_edit.html', 'fsr.html',
    'invoices.html', 'notifications.html', 'physical_invoice_list.html',
    'projects/project_gantt.html', 'projects/project_subtasks_add.html',
    'projects/project_task_list.html', 'projects/project_tasks_add.html',
    'projects/project_tasks_delete.html', 'projects/project_tasks_edit.html',
    'projects/projects.html', 'projects/projects_add.html',
    'projects/projects_detail.html', 'projects/projects_edit.html',
    'properties.html', 'property_assets.html', 'property_detail.html',
    'tenant.html', 'tenant_add.html',
)
BS_PAGES = (
    'finance/cashflow_forecast.html', 'finance/financial_indicators.html',
    'finance/vacancy_management.html', 'finance_pl_act.html',
    'projects/project_tasks_edit.html', 'projects/projects_detail.html',
    'projects/projects_edit.html', 'property_detail.html', 'tenant_add.html',
)
# The brights converted outside the dashboard: (page, what it says now).
COLOURED = (
    ('projects/projects_edit.html',
     "targetField.css('border-color', 'var(--alv-warn)');"),
    ('projects/projects_edit.html',
     "targetField.css('border-color', 'var(--alv-good)');"),
    ('projects/project_tasks_edit.html',
     "targetField.css('border-color', 'var(--alv-warn)');"),
    ('projects/project_tasks_edit.html',
     "targetField.css('border-color', 'var(--alv-good)');"),
    ('view_recipe.html', "font-weight: 600; color: var(--alv-good);"),
    ('view_recipe.html', "font-style: italic; color: var(--alv-good);"),
    ('lease_timeline.html', "color = 'var(--alv-bad)';"),
    ('lease_timeline.html', "color = 'var(--alv-good)';"),
)
OTHER = ('view_recipe.html', 'lease_timeline.html')
EDITED = ((BASE,) + tuple(J(TPL, *r.split('/')) for r in JQ_PAGES + OTHER)
          + (PQ, DR, J(ROOT, 'test_pdf_viewer.py'),
             J(ROOT, 'test_customer_view.py'),
             J(ROOT, 'test_prorata_anchor.py'),
             J(ROOT, 'test_amber.py'), J(ROOT, 'test_cssrules_outside.py'),
             J(ROOT, 'test_recipe_tidy.py'), J(ROOT, 'test_neutrals.py')))

# THE BRIGHTS THAT ARE LEFT, outside base and the standalone templates,
# wherever they sit. Each is a decision rather than an oversight:
#   financial_indicators  5  each indicator's own hue (bullseye green,
#                            pie red, euro amber, purple, teal) - a palette
#                            of categories, not good/warn/bad, and so a
#                            design question for him, not a token swap
#                         7  the bar chart's colours, painted on a canvas,
#                            where var() means nothing
#   preview_imported_recipe 1  the spell-check highlighter's yellow
#   finance_expense_add/edit 1+1  the checkboxes' red - kept ON PURPOSE by
#                            test_control_accent, which pins it
N_BRIGHTS_LEFT = 15
BRIGHTS = ('#28a745', '#dc3545', '#ffc107', '#007bff', '#17a2b8',
           '#20c997', '#fd7e14', '#6f42c1', '#e83e8c', '#218838',
           '#c82333', '#e0a800', '#0056b3')

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

JQ_TAG = re.compile(r'<script[^>]*src="[^"]*code\.jquery\.com/jquery-[^"]*"')
BS_TAG = re.compile(r'<script[^>]*src="[^"]*/js/bootstrap(\.bundle)?'
                    r'(\.min)?\.js"')
POP_TAG = re.compile(r'<script[^>]*src="[^"]*popper[^"]*\.js"')


def tpl(rel):
    return J(TPL, *rel.split('/'))


def head_of(src):
    i = src.find('</head>')
    return (src[:i], src[i:]) if i >= 0 else ('', src)


def claims(src):
    out = []
    b = T.code_only(src[BASE])
    hd, rest = head_of(b)
    out.append((len(JQ_TAG.findall(b)) == 1 and len(JQ_TAG.findall(hd)) == 1,
                'base.html loads jQuery once, in <head>'))
    out.append((len(POP_TAG.findall(hd)) == 1
                and len(list(BS_TAG.finditer(hd))) == 1
                and not POP_TAG.search(rest) and not BS_TAG.search(rest),
                '  and Popper and Bootstrap with it, and not again at the '
                'foot'))
    if hd:
        out.append((hd.find('code.jquery.com') < hd.find('popper')
                    < hd.find('bootstrap@4.1.3/dist/js'),
                    '  in the order Bootstrap needs: jQuery, Popper, '
                    'Bootstrap'))
    else:
        out.append((False, '  in the order Bootstrap needs'))
    own = [r for r in JQ_PAGES if JQ_TAG.search(T.code_only(src[tpl(r)]))]
    out.append((not own, 'not one of the 33 pages loads its own jQuery '
                '(%d do)' % len(own)))
    bs = [r for r in BS_PAGES if BS_TAG.search(T.code_only(src[tpl(r)]))]
    out.append((not bs, 'nor its own Bootstrap - the nine that did '
                '(%d do)' % len(bs)))
    n = src[NOTIF]
    lit = re.findall(r"'#(?:28a745|dc3545|ffc107|0e7c8b)'", n)
    icons = re.findall(r'<i class="fas fa-[a-z-]+" style="color: \$\{[^}]*'
                       r"'var\(--alv-(?:good|bad|warn|accent)\)'", n)
    out.append((not lit and len(icons) == 8,
                'the eight Notifications icons take the house tokens'))
    miss = [r + ': ' + s for r, s in COLOURED if s not in src[tpl(r)]]
    out.append((not miss, 'the eight other Bootstrap brights a browser reads '
                'as CSS are tokens'))
    pq = T.python_code_only(src[PQ])
    out.append(('pages_ = {}' in pq and 'pg.set_viewport_size(' in pq
                and 'return _Kept(), pg' in pq,
                'test_print_queries keeps one page per media and resizes'))
    dr = T.python_code_only(src[DR])
    out.append(('def computed_all(page_css, klasses):' in dr
                and 'def computed(page_css, width, klass, props):' not in dr,
                'test_dr2_values loads each document once and resizes'))
    return out


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
dated = [p for p in (BASE, NOTIF, PQ, DR, tpl('lease_timeline.html'))
         if MARK not in NOW[p]]
ok(not dated, 'the round dates itself where it changed behaviour',
   ', '.join(os.path.relpath(p, ROOT) for p in dated))
strays = []
for p in T.templates():
    rel = T.rel(p).replace(os.sep, '/')
    if rel == 'base.html':
        continue
    c = T.code_only(read(p))
    if JQ_TAG.search(c) or BS_TAG.search(c):
        strays.append(rel)
ok(not strays, 'no template anywhere loads jQuery or Bootstrap\'s script '
   'but base.html', ', '.join(strays[:6]))
for s in ('test_print_queries.py', 'test_dr2_values.py'):
    ok("'%s'" % s in read(GATE),
       '  %s is still on the gate - faster, not dropped' % s)

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
held = [m for c, m in claims(OLD) if c]
ok(not held, 'CONTROL: not one of this round\'s claims held before it',
   '\n'.join(held))
had = [r for r in JQ_PAGES if JQ_TAG.search(T.code_only(OLD[tpl(r)]))]
ok(len(had) == 33, 'CONTROL: from the backups, all 33 pages loaded their '
   'own jQuery', len(had))
hadb = [r for r in BS_PAGES if BS_TAG.search(T.code_only(OLD[tpl(r)]))]
ok(len(hadb) == 9, '  and nine of them their own Bootstrap', len(hadb))

# ==========================================================================
head('3. THE BRIGHTS THAT ARE LEFT - counted, named, and why')
# ==========================================================================
STAND = set(T.standalone())


def brights(text):
    # Comments out first: base and act_expense NAME these colours in
    # prose about what they replaced, and a name is not a use.
    c = T.code_only_js(T.code_only(text))
    return [m.group(0).lower() for m in
            re.finditer(r'#[0-9a-fA-F]{6}\b', c)
            if m.group(0).lower() in BRIGHTS]


left, before = {}, {}
for p in T.templates():
    rel = T.rel(p).replace(os.sep, '/')
    if rel in STAND or rel == 'base.html':
        continue
    n_now = len(brights(read(p)))
    n_was = len(brights(OLD[p])) if p in OLD else n_now
    if n_now:
        left[rel] = n_now
    if n_was:
        before[rel] = n_was
print('  left: %r' % left)
ok(sum(left.values()) == N_BRIGHTS_LEFT,
   '%d Bootstrap bright(s) left outside base and the standalone pages - '
   'each one a decision, named at the top of this file'
   % sum(left.values()), left)
ok(set(left) <= {'finance/financial_indicators.html',
                 'preview_imported_recipe.html',
                 'finance_expense_add.html', 'finance_expense_edit.html'},
   '  and they are on the four pages named there and nowhere else',
   sorted(left))
ok(sum(before.values()) - sum(left.values()) == 19,
   'CONTROL: from the backups there were %d - the round took 19 (eleven '
   'on the dashboard, whose twelfth literal was the accent teal, not a '
   'bright; eight elsewhere)' % sum(before.values()),
   before)

# ==========================================================================
head('4. DRIVEN - two pages rendered by Django')
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
    skip('section 4', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])


class Rollback(Exception):
    """Nothing this suite writes survives it."""


have_db = False
if django_up:
    try:
        connection.ensure_connection()
        User.objects.exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('section 4', 'no database: %s' % str(_e).split('\n')[0][:70])

if have_db:
    try:
        with transaction.atomic():
            u = User.objects.create_superuser(
                username='hk3check', email='hk3@example.com',
                password='not-a-real-password')
            c = Client(SERVER_NAME='localhost')
            c.force_login(u)
            for path in ('/notifications/', '/tenant_add/'):
                r = c.get(path)
                body = r.content.decode('utf-8', 'replace')
                hd, rest = head_of(body)
                ok(r.status_code == 200, '%s renders' % path, r.status_code)
                ok(len(JQ_TAG.findall(body)) == 1
                   and len(JQ_TAG.findall(hd)) == 1,
                   '  with exactly one jQuery, and it is in <head>',
                   len(JQ_TAG.findall(body)))
                ok(len(BS_TAG.findall(body)) == 1
                   and BS_TAG.search(hd) is not None,
                   '  and exactly one Bootstrap script, in <head> too',
                   len(BS_TAG.findall(body)))
                if path == '/notifications/':
                    i = body.find('indicator-cards')
                    j = body.find('Expenses Waiting for Payment', i)
                    cards = body[i:j] if 0 <= i < j else ''
                    ok(cards and not re.search(r'#(28a745|dc3545|ffc107)',
                                               cards),
                       '  and not one Bootstrap bright reaches the cards')
                    ok(body.count("'var(--alv-good)'") >= 7,
                       '  every count-coloured icon is green by the house '
                       'token when it is clear')
            raise Rollback()
    except Rollback:
        pass

# ==========================================================================
head('5. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = 'code.jquery.com/jquery-3.5.1'; Absent = $true" in gate,
   '  with a sentinel that notices a page bringing its old jQuery back')
wd = read(J(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')
nob = [os.path.relpath(p, ROOT) for p in EDITED
       if not os.path.isfile(p + SUFFIX)]
ok(not nob, '  every file it edited has its backup', ', '.join(nob[:6]))

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
