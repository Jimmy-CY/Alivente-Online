# -*- coding: utf-8 -*-
"""test_tap_target.py - Section C, round C2: 44px to tap on a phone.

    python test_tap_target.py

Run from the repo root, after apply_tap_target.py.

  1. base: the bar's phone heights are 44px, not 38; ALV TAP TARGET v1 is
     there once, inside the phone query, and is a floor (min-height) for
     the house buttons and a 44px square for .icon-action-btn.
  2. The pages' own 44px copies are gone - and ONLY those declarations:
     every other line of every one of those rules is still there. The
     filter selects' 44px is not a copy and stays; so do Personal's.
  3. The page-own buttons are raised in their pages.
  4. THE PHONE, 375px, every business template: every house button,
     status button, pop-up footer button and row icon that shows is at
     least 44px - icons 44 wide as well; the invoice toolbar and the
     quick-set pills too. Edit Asset's photo buttons stay 28px circles
     but answer a tap 8px outside their edge, and a tap between the two
     lands on neither. CONTROL: from the backups the bar is 38px.
  5. THE DESK, 1280px, every business template: every button measures
     exactly what it did before the round.
  6. Registered in alv_rounds, and on the gate.
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

# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# This suite renders a fixture in Chromium, and a fixture has to be a real
# file before file:// can reach it. Those files used to be written into
# the repo root. Three things are wrong with that, and the third one bit:
#
#   - the root is a git working tree, so a suite that dies before its own
#     cleanup leaves an untracked file where the next commit can see it;
#   - the root is inside OneDrive, so every fixture is a create, an upload
#     and a delete for the sync client to chase;
#   - THE NAME WAS NOT UNIQUE. Four suites all wrote _sup_probe.html into
#     that one directory. On the push gate test_table_tenants.py runs
#     immediately before test_table_lease_agreement.py, so the same path
#     was created, deleted and created again within a second or two, and
#     Chromium answered the second one with net::ERR_FAILED. Run
#     alphabetically by Show-GateAudit.py the order is different, nobody
#     hands another suite a path they have just deleted, and the same
#     suite passes - which is why this read as a fault in the gate.
#
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however they are ordered, and
# nothing is written into the working tree at all.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import difflib
import os
import re
import sys

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:           # a crash says less than a failure
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_tap'
ME = 'test_tap_target.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')
MARK = re.compile(r'/\* ===== ALV TAP TARGET v1 =====.*?'
                  r'/\* ===== /ALV TAP TARGET v1 ===== \*/', re.S)
PERSONAL = ('recipe', 'meal_plan', 'ingredient', 'wcim', 'celebration',
            'pantry', 'unit_conversions', 'measurement_units',
            'household_member', 'map_ingredients', 'import_recipe',
            'preview_imported', 'categories_management', 'my_profile',
            'personal_', 'workspace')
LOCAL = {
    'finance.html': ['.action-back'],
    'finance/cashflow_forecast.html': ['.action-back'],
    'finance/financial_indicators.html': [
        '.action-primary', '.modal-dialog.modal-xl .modal-footer .btn'],
    'finance/vacancy_management.html': [
        '#propertyDetailsModal .modal-footer .btn'],
    'finance_expense_add.html': ['#prorataPreviewModal .modal-footer .btn'],
    'finance_expense_edit.html': ['#prorataPreviewModal .modal-footer .btn'],
    'finance_expense_line_types.html': ['#deleteModal .modal-footer .btn'],
    'finance_expense_line_types_edit.html': [
        '#prorataChangePreviewModal .modal-footer .btn'],
    'finance_pl_act.html': ['.action-more-btn', '.action-back'],
    'finance_valuations_add.html': ['.action-back'],
    'finance_valuations_edit.html': ['.action-back'],
    'fsr.html': ['.action-more-btn', '.action-back'],
    'occupancy_trends.html': ['#yearDetailModal .modal-footer .btn'],
    'projects/project_subtasks_add.html': ['.action-back'],
    'projects/project_task_list.html': ['.action-more-btn', '.action-back'],
    'projects/project_tasks_add.html': ['.action-back'],
    'projects/project_tasks_delete.html': ['.action-back'],
    'projects/project_tasks_edit.html': ['.action-back'],
    'projects/projects.html': ['.action-more-btn', '.action-back'],
    'projects/projects_add.html': ['.action-back'],
    'projects/projects_detail.html': ['.action-more-btn', '.action-back'],
    'projects/projects_edit.html': ['.action-back'],
}
INVOICE = ['customer_invoice_form.html', 'physical_invoice_edit.html']
QUICKSET = ['finance_expense_types_add.html', 'finance_expense_types_edit.html',
            'finance_revenue_types_add.html', 'finance_revenue_types_edit.html']
PHOTO = 'edit_asset.html'
DECL44_LINE = re.compile(r'^\s*min-(?:height|width)\s*:\s*44px\s*;\s*$')
DECL44 = re.compile(r'\s*min-(?:height|width)\s*:\s*44px\s*;')

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
            for line in str(detail).split('\n')[:10]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def path(rel):
    return os.path.join(T, *rel.split('/'))


def now(p):
    """The file as THIS round left it. See alv_rounds.py."""
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    """The file before this round - its backup, or, if the round did not
       touch it, the file as this round left it."""
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def nocomment(t):
    return re.sub(r'/\*.*?\*/', '', t, flags=re.S)


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                 re.S | re.I)]


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*)', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
    b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)


def rule_bodies(css, selector):
    pat = re.compile(r'(?:^|[{};]|\*/)\s*' + re.escape(selector) + r'\s*\{'
                     r'([^{}]*)\}', re.M)
    return pat.findall(css)


def business(rel):
    return not any(p in rel for p in PERSONAL)


TEMPLATES = []
for _d, _sub, _fs in os.walk(T):
    for _f in _fs:
        if not _f.endswith('.html') or '.bak_' in _f:
            continue
        _rel = os.path.relpath(os.path.join(_d, _f), T).replace(os.sep, '/')
        if _rel == 'base.html' or 'OLD DO NOT USE' in _rel:
            continue
        if not business(_rel):
            continue
        if 'extends' not in read(os.path.join(_d, _f))[:3000]:
            continue
        TEMPLATES.append(_rel)
TEMPLATES.sort()

B_NOW, B_WAS = now(BASE), was(BASE)

# ==========================================================================
head('1. BASE: THE BAR IS 44PX ON A PHONE, AND THE FLOOR')
# ==========================================================================
blocks = MARK.findall(B_NOW)
ok(len(blocks) == 1, 'base carries ALV TAP TARGET v1 once', len(blocks))
blk = nocomment(blocks[0]) if blocks else ''
ok(blk.strip().startswith('@media screen and (max-width: 768px) {'),
   'the whole block is inside the phone query - a desk is untouched')
ok(blk.count('{') == blk.count('}') == 3,
   'one query holding two rules - nothing else hides in it',
   '%d/%d' % (blk.count('{'), blk.count('}')))
_floor = re.search(r'\{\s*([^{}]*?)\s*\{\s*min-height:\s*44px;\s*\}', blk)
_sels = set(s.strip() for s in _floor.group(1).split(',')) if _floor else set()
for s in ('.page-action-buttons .btn', '.action-more-item',
          '.btn.action-primary', '.btn.action-secondary', '.btn.action-danger',
          '.btn.action-back', '.btn.back-button', '.status-btn',
          '.modal-footer .btn'):
    ok(s in _sels, 'the floor covers %s' % s)
ok(re.search(r'\.icon-action-btn\s*\{\s*width:\s*44px;\s*height:\s*44px;\s*\}',
             blk) is not None, 'and a row icon is a 44px square')
ok(not re.search(r'(?<![-\w])height:\s*(?!\s|44px)', blk),
   'the floor pins no other height')

BC = nocomment(B_NOW)
for sel in ('.page-action-buttons .action-primary',
            '.page-action-buttons .action-secondary',
            '.page-action-buttons .action-back',
            '.page-action-buttons .action-more-btn',
            '.page-action-buttons .action-filter'):
    bodies = [b for b in rule_bodies(BC, sel)
              if re.search(r'(?<![-\w])height:', b)]
    ok(bodies and all(re.search(r'(?<![-\w])height:\s*44px', b)
                      for b in bodies),
       'on a phone %s is 44px tall' % sel.split()[-1], bodies)
ok(not re.search(r'\.page-action-buttons \.action-[a-z-]+\s*\{[^}]*'
                 r'(?<![-\w])height:\s*38px', BC),
   'no bar rule in base says 38px any more')
if os.path.isfile(BASE + SUFFIX):
    ok(re.search(r'(?<![-\w])height:\s*38px', nocomment(B_WAS)) is not None,
       'CONTROL: before the round it did')
    # Scope: base is its backup plus exactly the round.
    _exp = B_WAS
    for a, b in (('min-width: 0;\n          height: 38px;',
                  'min-width: 0;\n          height: 44px;'),
                 ('width: 44px;\n          height: 38px;',
                  'width: 44px;\n          height: 44px;'),
                 ('width: 44px; height: 38px;', 'width: 44px; height: 44px;'),
                 ('its neighbours are all 38px and it came out 35. */',
                  'its neighbours were all 38px and it came out 35.\n'
                  '           44px since 22 Sep, with the rest of the bar - '
                  'ALV TAP TARGET. */')):
        _exp = _exp.replace(a, b)
    _exp = _exp.replace(
        '  .page-action-buttons .action-filter { position: relative; }\n}\n',
        '  .page-action-buttons .action-filter { position: relative; }\n}\n\n'
        + (blocks[0] + '\n' if blocks else ''), 1)
    ok(_exp == B_NOW, 'base is its backup plus exactly this round')

# ==========================================================================
head('2. THE PAGES\' OWN 44PX COPIES ARE GONE - AND ONLY THEY')
# ==========================================================================
for rel, sels in sorted(LOCAL.items()):
    p = path(rel)
    n_, w_ = now(p), was(p)
    css = nocomment('\n'.join(styles_of(n_)))
    left = [s for s in sels if any(DECL44.search(b)
                                   for b in rule_bodies(css, s))]
    ok(not left, '%s: no copy of 44px left' % rel, left)
    if not os.path.isfile(p + SUFFIX):
        skip('  %s scope' % rel, 'no backup')
        continue
    had = [s for s in sels if any(
        DECL44.search(b) for b in rule_bodies(nocomment(
            '\n'.join(styles_of(w_))), s))]
    ok(had == sels, '  CONTROL: each was there before', had)
    a, b = w_.split('\n'), n_.split('\n')
    bad = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, a, b, autojunk=False).get_opcodes():
        if tag == 'equal':
            continue
        if tag == 'delete' and all(DECL44_LINE.match(x) for x in a[i1:i2]):
            continue
        if tag == 'replace' and i2 - i1 == j2 - j1 and all(
                ' '.join(DECL44.sub('', x).split()) == ' '.join(y.split())
                for x, y in zip(a[i1:i2], b[j1:j2])):
            continue
        bad.append('%s %r -> %r' % (tag, a[i1:i2][:2], b[j1:j2][:2]))
    ok(not bad, '  nothing else in it changed', '\n'.join(bad[:4]))

for rel in ('fsr.html', 'projects/projects.html', 'tenant.html',
            'properties.html', 'suppliers.html'):
    ok(re.search(r'\.filter-select[^{]*\{[^}]*min-height:\s*44px',
                 now(path(rel))) is not None,
       '%s keeps its filter select at 44px - a control, not a copy' % rel)
# LATER - Section E round E3b, 25 Sep. celebration_management HAS HAD ITS
# ROUND. It no longer declares a minimum of its own: its two action grids
# were local copies of .mobile-action-bar, and deleting them hands the
# buttons to base's .mobile-action-btn, which gives 56px - LARGER than the
# 44px and 50px the local rules declared. Rendered at 390px the round
# leaves no control under 44px at all (see test_named_bars.py section 2).
# So the page is no longer "untouched", and what it lost made it better.
# The tap round itself still never touched it - no .bak_tap backup. [E3b]
DONE_OWN_ROUND = {'celebration_management.html':
                  'E3b - its grids are base\'s now, and base gives 56px'}
for rel in ('celebration_management.html', 'view_recipe.html',
            'ingredient_base_units_management.html', 'wcim_extras.html'):
    if os.path.isfile(path(rel)):
        if rel in DONE_OWN_ROUND:
            ok(not os.path.isfile(path(rel) + SUFFIX),
               '%s had its own round (%s), and the tap round still never '
               'touched it' % (rel, DONE_OWN_ROUND[rel]))
            continue
        ok('min-height: 44px' in read(path(rel))
           and not os.path.isfile(path(rel) + SUFFIX),
           '%s (Personal) is untouched until its own round' % rel)

# ==========================================================================
head('3. THE PAGE-OWN BUTTONS ARE RAISED IN THEIR PAGES')
# ==========================================================================


def phone_css(t):
    out = []
    for css in styles_of(t):
        css = nocomment(css)
        for m in re.finditer(r'@media screen and \(max-width:\s*768px\)\s*\{',
                             css):
            d, i = 1, m.end()
            while d and i < len(css):
                d += {'{': 1, '}': -1}.get(css[i], 0)
                i += 1
            out.append(css[m.end():i - 1])
    return '\n'.join(out)


for rel in INVOICE:
    ok(re.search(r'\.btn-approve, \.btn-delete, \.btn-duplicate, \.btn-send,'
                 r'\s*\.btn-unapprove \{ min-height: 44px; \}\s*'
                 r'\.icon-action-btn \{ width: 44px; height: 44px; \}',
                 phone_css(now(path(rel)))) is not None,
       '%s raises its status toolbar and line icon on a phone' % rel)
for rel in QUICKSET:
    ok(re.search(r'\.quickset-btn \{ min-height: 44px; \}',
                 phone_css(now(path(rel)))) is not None,
       '%s raises its quick-set pills on a phone' % rel)
_pc = phone_css(now(path(PHOTO)))
ok('inset: -8px' in _pc and 'gap: 16px' in _pc,
   '%s grows the photo buttons\' target, not the circles' % PHOTO)

# ==========================================================================
head('4. THE PHONE, 375PX - EVERY BUSINESS TEMPLATE')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'
OPEN = ('<style>.modal{display:block!important;position:static!important;'
        'opacity:1!important}.modal.fade .modal-dialog{transform:none!important}'
        '</style>')

HOUSE = ('.page-action-buttons .btn, .action-more-item, .btn.action-primary, '
         '.btn.action-secondary, .btn.action-danger, .btn.action-back, '
         '.btn.back-button, .status-btn, .modal-footer .btn, .icon-action-btn')
SIZE_JS = r"""([house, own]) => {
  const out = [];
  const one = (el, kind) => {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) return;
    if (getComputedStyle(el).visibility === 'hidden') return;
    out.push({kind, cls: [...el.classList].join('.') || el.tagName,
              h: Math.round(r.height * 10) / 10,
              w: Math.round(r.width * 10) / 10,
              icon: el.classList.contains('icon-action-btn')});
  };
  document.querySelectorAll(house).forEach(el => one(el, 'house'));
  if (own) document.querySelectorAll(own).forEach(el => one(el, 'own'));
  return out;
}"""
DESK_JS = r"""() => [...document.querySelectorAll(
    'button, a.btn, input[type=submit], input[type=button], .status-btn, '
    + '.icon-action-btn')].map(el => { const r = el.getBoundingClientRect();
      return [[...el.classList].join('.') || el.tagName,
              Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]
                .join(' '); })"""
PHOTO_JS = r"""() => {
  // The template draws the cover star OR the set-cover star; with the
  // Django tags stripped both are here, side by side. A tile has one.
  const active = document.querySelector('.btn-photo-star-active');
  if (active && document.querySelector('.btn-photo-star:not([disabled])'))
    active.remove();
  const star = document.querySelector('.btn-photo-star');
  const del = document.querySelector('.btn-photo-delete');
  if (!star || !del) return null;
  star.scrollIntoView({block: 'center'});
  const s = star.getBoundingClientRect(), d = del.getBoundingClientRect();
  const hit = (x, y) => { const e = document.elementFromPoint(x, y);
    return e ? (e.closest('.btn-photo-delete') ? 'delete' :
                e.closest('.btn-photo-star') ? 'star' : 'none') : 'none'; };
  const sy = s.top + s.height / 2, dy = d.top + d.height / 2;
  const gap = d.left - s.right;
  return {size: [s.width, s.height, d.width, d.height],
          starOuter: hit(s.left - 7, sy),         // 7px outside the circle
          delOuter: hit(d.right + 7, dy),
          delAbove: hit(d.left + d.width / 2, d.top - 7),
          betweenNearStar: hit(s.right + gap / 2 - 2, sy),
          betweenNearDel: hit(s.right + gap / 2 + 2, sy),
          gap};
}"""


def page_html(boot, base_src, t, width_note=''):
    return ('<!doctype html><html><head><meta charset="utf-8"><meta '
            'name="viewport" content="width=device-width, initial-scale=1">'
            '<title>t</title><style>%s</style><style>%s</style>%s%s</head>'
            '<body class="has-sidebar"><div class="main-content with-sidebar">'
            '%s</div></body></html>'
            % (boot, '\n'.join(styles_of(base_src)),
               ''.join('<style>%s</style>' % c for c in styles_of(t)), OPEN,
               body_markup(t)))


def own_of(rel):
    if rel in INVOICE:
        return '.btn-approve, .btn-delete, .btn-duplicate, .btn-send, ' \
               '.btn-unapprove'
    if rel in QUICKSET:
        return '.quickset-btn'
    return ''


if sync_playwright is None or not os.path.isfile(BOOT):
    skip('4 and 5', 'playwright or %s missing' % BOOT)
else:
    boot = read(BOOT)
    k = [0]

    def render(pg, html, js, arg=None):
        k[0] += 1
        fx = os.path.join(SCRATCH, '_tap_%05d.html' % k[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        _goto(pg, fx)
        return pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        def ctx_at(w):
            c = br.new_context(viewport={'width': w, 'height': 900})
            c.route(re.compile(r'^https?://'), lambda r: r.abort())
            return c, c.new_page()

        c, pg = ctx_at(375)
        short, counted, own_n = [], 0, 0
        for rel in TEMPLATES:
            got = render(pg, page_html(boot, B_NOW, now(path(rel))), SIZE_JS,
                         [HOUSE, own_of(rel)])
            for e in got:
                counted += 1
                own_n += e['kind'] == 'own'
                if e['h'] < 44 or (e['icon'] and e['w'] < 44):
                    short.append('%s  %s  %sx%s' % (rel, e['cls'], e['w'],
                                                    e['h']))
        ok(counted > 250, 'measured %d buttons on %d templates'
           % (counted, len(TEMPLATES)))
        ok(own_n >= 20, '  among them %d of the pages\' own' % own_n)
        ok(not short, 'every one is at least 44px - row icons 44 wide too',
           '\n'.join(short[:10]) + ('\n... %d in all' % len(short)
                                    if len(short) > 10 else ''))

        # CONTROL: the same probe on the pages before the round.
        before = []
        for rel in ('fsr.html', 'finance_expense_add.html',
                    'customer_invoice_form.html', 'act_expense.html'):
            got = render(pg, page_html(boot, B_WAS, was(path(rel))), SIZE_JS,
                         [HOUSE, own_of(rel)])
            before += [e for e in got if e['h'] < 44]
        ok(len(before) >= 4, 'CONTROL: from the backups, %d of them on four '
           'pages were under 44 - so the probe sees the change' % len(before))

        # Edit Asset: the circles stay, the target grows.
        r = render(pg, page_html(boot, B_NOW, now(path(PHOTO))), PHOTO_JS)
        ok(r is not None and max(r['size']) <= 32,
           'the photo buttons are still the page\'s 32px circles, not grown',
           r and r['size'])
        ok(r is not None and r['starOuter'] == 'star'
           and r['delOuter'] == 'delete' and r['delAbove'] == 'delete',
           '  and each answers a tap 7px outside its edge', r)
        ok(r is not None and r['betweenNearStar'] == 'star'
           and r['betweenNearDel'] == 'delete',
           '  and a tap between them goes to the nearer one - never to '
           'Delete from Star\'s side', r)
        r0 = render(pg, page_html(boot, B_WAS, was(path(PHOTO))), PHOTO_JS)
        ok(r0 is not None and r0['starOuter'] == 'none',
           'CONTROL: before the round a tap 7px out missed', r0)
        c.close()

        # ==================================================================
        head('5. THE DESK, 1280PX - NOTHING MOVED')
        # ==================================================================
        c, pg = ctx_at(1280)
        moved, same = [], 0
        for rel in TEMPLATES:
            a = render(pg, page_html(boot, B_NOW, now(path(rel))), DESK_JS)
            b = render(pg, page_html(boot, B_WAS, was(path(rel))), DESK_JS)
            if a == b:
                same += 1
            else:
                d = [x for x in difflib.unified_diff(b, a, lineterm='', n=0)
                     if x[:1] in '+-' and x[:3] not in ('+++', '---')]
                moved.append('%s: %s' % (rel, '; '.join(d[:2])))
        ok(not moved, 'on a desk all %d templates measure exactly as before'
           % len(TEMPLATES), '\n'.join(moved[:8]))
        # CONTROL: the same block without its phone query DOES move a
        # desk - so "nothing moved" is the query working, not a blind probe.
        _glob = B_NOW
        if blocks:
            _g = blocks[0].replace('@media screen and (max-width: 768px) {',
                                   '@media all {', 1)
            _glob = B_NOW.replace(blocks[0], _g, 1)
        a = render(pg, page_html(boot, _glob, now(path('fsr.html'))), DESK_JS)
        b = render(pg, page_html(boot, B_NOW, now(path('fsr.html'))), DESK_JS)
        ok(a != b, 'CONTROL: the floor applied on a desk would move fsr\'s '
           'buttons - so the probe can see a change')
        c.close()
        br.close()

# ==========================================================================
head('6. REGISTERED, AND ON THE GATE')
# ==========================================================================
ok(SUFFIX in ROUNDS and '.bak_csmall' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_csmall'),
   'alv_rounds lists %s after .bak_csmall' % SUFFIX)
ps = read(PS1) if os.path.isfile(PS1) else ''
_s = ps[ps.find('$suites = @('):]
_m = re.search(r'\n\)\s*?\n', _s)
ok(_m is not None and "'%s'" % ME in _s[:_m.end()],
   '%s is on the push gate' % ME)
_sv = read('test_secondary_visible.py') if os.path.isfile(
    'test_secondary_visible.py') else ''
ok('# LATER - test_tap_target.py, 22 Sep.' in _sv and 'ROW_H' in _sv
   and not re.search(r'height:\\s\*38px|== 38\b', _sv),
   'test_secondary_visible reads the bar height from base, not 38')

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
