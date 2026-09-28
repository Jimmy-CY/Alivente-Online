# -*- coding: utf-8 -*-
"""test_table_personal.py - Section H round H4, 27 Sep 2026.

Six Personal tables onto base's .alv-table, and 87 rules that were writing
that component out by hand deleted with them.

THE LABELS ARE NOT THIS SUITE'S OPINION. Four of the six showed their
headings on a phone through
    .units-table tbody td:nth-child(2)::before { content: 'Abbreviation'; }
so section 2 reads them back out of the BACKUP and checks the data-labels
against that source. A column quietly renamed in the migration fails here.

SECTION 4 IS THE ONE THAT EARNED ITS PLACE. base hides
.desktop-action-cell below 768px, because a page carrying one is expected
to have a .mobile-action-bar twin - and only one of these six does. The
first cut of this round put the pair on all six, which would have taken
the row controls off the phone card on five pages without a word. The
check is rendered, and it carries the spoiled page as its control.

ONE BRANCH, NOT TWO: five of these tables gate a control on a permission
with {% if %}/{% else %}, and a fixture that strips template tags renders
both halves - so the row comes out with more cells than it has.
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
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
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
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_tablepersonal'
ME = 'test_table_personal.py'
PATCHER = 'apply_table_personal.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

# The six, and the label each column must carry. THE LABELS ARE NOT THIS
# SUITE'S OPINION: for four of the pages they were read out of the
# `td:nth-child(n)::before { content: '...' }` rules the round deletes, and
# section 2 goes back to the BACKUP and checks them against that source, so
# a column silently renamed during the migration is caught.
SIX = {
    'categories_management.html': ('categories-table',
                                   ['Category Name', 'Ingredients']),
    'household_member_management.html': ('hm-table', None),
    'ingredient_base_units_management.html': (
        'ingredients-table', ['Ingredient Name', 'Category',
                              'Shopping Unit', 'Conversion', 'Nutrition']),
    'measurement_units_management.html': (
        'units-table', ['Unit Name', 'Abbreviation', 'Type', 'Usage']),
    'passport_management.html': ('passport-table', None),
    'unit_conversions_management.html': ('conversions-table',
                                         ['Conversion', 'Applies To']),
}

# The only one of the six with a phone-only action bar, and therefore the
# only one whose actions cell may wear .desktop-action-cell.
HAS_MOBILE_BAR = 'passport_management.html'

# CELLS A PAGE HIDES ON A PHONE ON PURPOSE, and the rule that does it.
# Not a loophole: section 4 fails if a cell OUTSIDE this list disappears,
# and fails just as hard if one INSIDE it stops being hidden - so the list
# is a claim about the page, not an exemption from the check.
HIDDEN_ON_PHONE = {
    'household_member_management.html':
        ('hide-sm', 'Linked account, hidden on a phone before this round '
                    'and still hidden by the page\'s own .hide-sm rule'),
    'passport_management.html':
        ('desktop-action-cell', 'the desktop actions cell, which base '
                                'swaps for the .mobile-action-bar beside '
                                'it'),
}

# NOT DATA TABLES. Named here with the reason, because an exception nobody
# wrote down is a gap rather than a scope. Section 6 checks each is still
# untouched AND still matches the reason given.
LEAVE = {
    'celebration_calendar.html':
        'a CALENDAR GRID - its seven headings are Sunday..Saturday. The '
        'phone rules turn a table into one card per row, which would deal '
        'a calendar out into seven strips.',
    'view_recipe.html':
        'three tables, none of them this round\'s: the nutrition breakdown '
        'builds its rows in JS and keeps a SECOND, separately built mobile '
        'card list; the Cooking Schedule panel and the print area have no '
        '<th> at all - two columns, label and value.',
    'preview_imported_recipe.html':
        'both tables build their rows in JavaScript, so data-label has to '
        'be written into the row-building code too. Own round.',
}

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


def now(p):
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def css_of(t):
    """Style bodies with CSS COMMENTS STRIPPED. Both of this round's own
    self-checks first counted a brace and a class name that appeared only
    inside the note explaining them - a comment is not code, in this
    direction too (lesson 21)."""
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t,
                 flags=re.S)
    return re.sub(r'/\*.*?\*/', '', '\n'.join(STYLE.findall(raw)), flags=re.S)


def markup_no_comments(t):
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')


def css_of(t):
    """Style bodies with CSS COMMENTS STRIPPED - and NOT through a markup
    blanker, which wipes the very bodies wanted here (lesson from
    test_celebrations, six false failures)."""
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t,
                 flags=re.S)
    return re.sub(r'/\*.*?\*/', '', '\n'.join(STYLE.findall(raw)),
                  flags=re.S)


def markup(t):
    """Everything that is not a style or a script body, comments blanked
    on the RAW text FIRST (lesson 61: accept="image/*" opens a CSS
    comment)."""
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    t = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    out = list(t)
    for rx in (STYLE, SCRIPT):
        for m in rx.finditer(t):
            for i in range(m.start(1), m.end(1)):
                out[i] = ' '
    return ''.join(out)


def table_of(t, cls):
    mk = markup(t)
    m = re.search(r'<table[^>]*class="[^"]*(?<![\w-])' + re.escape(cls)
                  + r'(?![\w-])[^"]*"[^>]*>', mk)
    if not m:
        return None
    j = mk.find('</table>', m.end())
    return (m.start(), j + 8) if j > 0 else None


def first_row(t, span):
    mk = markup(t)[span[0]:span[1]]
    tb = mk.find('<tbody')
    m = re.search(r'<tr\b', mk[tb:]) if tb >= 0 else None
    if not m:
        return None
    s = tb + m.start()
    e = mk.find('</tr>', s)
    return (span[0] + s, span[0] + e)


def cells(t, span, tag='td'):
    mk = markup(t)
    return [m.group(0) for m in
            re.finditer(r'<%s\b[^>]*>' % tag, mk[span[0]:span[1]])]


def labels_from_backup(t, cls, n):
    """The labels the page itself was showing on a phone before the round,
    read out of the nth-child rules being deleted."""
    css = css_of(t)
    out = {}
    for m in re.finditer(
            re.escape('.' + cls) + r'\s+tbody\s+td:nth-child\((\d+)\)'
            r'::before\s*\{([^}]*)\}', css):
        c = re.search(r"content\s*:\s*['\"]([^'\"]*)['\"]", m.group(2))
        if c:
            out[int(m.group(1))] = c.group(1)
    return [out.get(i) for i in range(1, n + 1)]


# ==========================================================================
head('1. THE SIX WEAR THE HOUSE TABLE')
# ==========================================================================
for rel in sorted(SIX):
    cls = SIX[rel][0]
    t = now(os.path.join(T, rel))
    sp = table_of(t, cls)
    if not ok(sp is not None, '%-38s has its table' % rel[:38]):
        continue
    tag = t[sp[0]:t.index('>', sp[0]) + 1]
    m = re.search(r'class="([^"]*)"', tag)
    names = m.group(1).split()
    ok(names[:2] == ['table', 'alv-table'],
       '  %-36s class reads `table alv-table %s`' % ('', cls),
       ' '.join(names))
    ok(cls in names, '  %-36s and keeps its own page class' % '')
    before = markup(t)[max(0, sp[0] - 240):sp[0]]
    ok('table-container' in before,
       '  %-36s sits in a .table-container' % '',
       before[-90:].strip())

ok(all(re.search(r'\balv-table\b', now(os.path.join(T, r))) for r in SIX),
   'all six carry it', len(SIX))
ok(not any(re.search(r'\balv-table\b', markup(was(os.path.join(T, r))))
           for r in SIX),
   '  CONTROL: NONE of them did before this round - the component is in '
   'base and had 0 wearers on this side')

# ==========================================================================
head('2. EVERY CELL KEEPS THE HEADING IT ALREADY SHOWED')
# ==========================================================================
for rel in sorted(SIX):
    cls, expect = SIX[rel]
    p = os.path.join(T, rel)
    t = now(p)
    sp = table_of(t, cls)
    row = first_row(t, sp)
    tds = cells(t, row)
    got = []
    for c in tds:
        m = re.search(r'data-label="([^"]*)"', c)
        got.append(m.group(1) if m else None)
    data = [g for g, c in zip(got, tds)
            if 'action' not in c and 'mobile-action-bar' not in c]
    ok(all(g for g in data),
       '%-38s every data cell has a data-label' % rel[:38],
       '%d of %d' % (sum(1 for g in data if g), len(data)))

    if expect is None:
        ok(True, '  %-36s (labels were already attr(data-label) here)' % '')
        continue
    src = labels_from_backup(was(p), cls, len(tds))
    named = [s for s in src if s]
    ok(named[:len(expect)] == expect,
       '  %-36s the backup\'s own ::before rules said exactly these' % '',
       'backup: %s\nround : %s' % (named, expect))
    ok(data[:len(expect)] == expect,
       '  %-36s and that is what the cells now carry' % '',
       'cells: %s' % data)

# ==========================================================================
head('3. THE ACTIONS CELL, AND THE TRAP UNDER IT')
# ==========================================================================
bc = css_of(read(BASE))
# BY THE WHOLE SELECTOR, not by the first place the name appears. base
# mentions .desktop-action-cell three times and the first is
# `.alv-table .desktop-action-cell, ... { text-align: center }` - reading
# that one reported "base does not hide it", which is the opposite of the
# fact this whole section rests on.
hide = [m for m in RULE.finditer(bc)
        if ' '.join(m.group(1).split()) == '.desktop-action-cell']
ok(len(hide) == 1 and 'display: none' in hide[0].group(2),
   'base hides .desktop-action-cell outright',
   [' '.join(h.group(2).split()) for h in hide] or 'no such rule')
ok(bool(re.search(r'\.alv-table \.cell-actions', bc)),
   '  and it styles .cell-actions separately')

for rel in sorted(SIX):
    cls = SIX[rel][0]
    t = now(os.path.join(T, rel))
    sp = table_of(t, cls)
    row = first_row(t, sp)
    acts = [c for c in cells(t, row) if 'cell-actions' in c]
    ok(len(acts) == 1, '%-38s exactly one .cell-actions cell' % rel[:38],
       len(acts))
    if not acts:
        continue
    desk = 'desktop-action-cell' in acts[0]
    want = rel == HAS_MOBILE_BAR
    ok(desk == want,
       '  %-36s .desktop-action-cell: %s' % ('', 'yes' if want else 'no'),
       'it has one and should not' if desk else
       'it needs one and has none')
    if want:
        ok(any('mobile-action-bar' in c for c in cells(t, row)),
           '  %-36s because it HAS a phone bar to show instead' % '')

ok(sum(1 for r in SIX
       if 'desktop-action-cell' in ' '.join(
           cells(now(os.path.join(T, r)),
                 first_row(now(os.path.join(T, r)),
                           table_of(now(os.path.join(T, r)),
                                    SIX[r][0]))))) == 1,
   'exactly one of the six carries .desktop-action-cell')

# ==========================================================================
head('4. RENDERED AT 390px - NOTHING WENT MISSING FROM THE CARD')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception as _e:
    sync_playwright = None
    skip('sections 4 and 5', 'playwright unavailable: %s' % str(_e)[:40])

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('sections 4 and 5', 'playwright or the bootstrap fixture is gone')
else:
    IF_ELSE = None

    TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)

    def one_branch(x):
        """Keep the FIRST branch of every {% if %}, tags and all.

        Django renders one branch. The plain fixture strips the tags and
        leaves every branch standing, so a permission-gated control and
        its no-permission twin both appear and the row has twice the
        cells it really has."""
        while True:
            depth, start, first_end, cut_at = 0, None, None, None
            for m in TAG.finditer(x):
                k = m.group(1)
                if k == 'if':
                    depth += 1
                    if depth == 1:
                        start, first_end, cut_at = m.start(), m.end(), None
                elif k == 'endif':
                    depth -= 1
                    if depth == 0 and cut_at is not None:
                        x = x[:start] + x[first_end:cut_at] + x[m.end():]
                        break
                elif depth == 1 and k in ('elif', 'else') and cut_at is None:
                    cut_at = m.start()
            else:
                return x

    def styles_for(x):
        return [re.sub(r'\{%.*?%\}', '', mm.group(1), flags=re.S)
                for mm in re.finditer(r'<style[^>]*>(.*?)</style>', x,
                                      re.S | re.I)]

    def body_of(x):
        x = one_branch(x)
        mm = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock',
                       x, re.S)
        y = mm.group(1) if mm else x
        y = re.sub(r'<(script|style)\b.*?</\1>', '', y, flags=re.S | re.I)
        for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
            y = re.sub(rx, '', y, flags=re.S)
        return re.sub(r'\{\{.*?\}\}', 'x', y, flags=re.S)

    boot = read(BOOT)
    bcss = '\n'.join(styles_for(read(BASE)))

    def fixture(x):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style>%s</head>'
                '<body class="has-sidebar"><div class="main-content '
                'with-sidebar">%s</div></body></html>'
                % (boot, bcss,
                   ''.join('<style>%s</style>' % c for c in styles_for(x)),
                   body_of(x)))

    CARD = """() => {
        const t = document.querySelector('table.alv-table')
              || document.querySelector('table');
        if (!t) return null;
        const r = t.querySelector('tbody tr');
        if (!r) return null;
        const out = [];
        for (const c of r.children) {
            const b = c.getBoundingClientRect();
            const st = getComputedStyle(c, '::before');
            out.push({
                label: c.getAttribute('data-label'),
                cls: (c.className || '').slice(0, 40),
                shown: b.width > 0 && b.height > 0,
                prefix: (st.content || '').replace(/^"|"$/g, '')
            });
        }
        return out;
    }"""

    def shoot(pg, text, w):
        p = os.path.join(SCRATCH, 'fx.html')
        with open(p, 'w', encoding='utf-8') as fh:
            fh.write(fixture(text))
        pg.set_viewport_size({'width': w, 'height': 900})
        _goto(pg, p)
        return pg.evaluate(CARD)

    with sync_playwright() as pw:
        try:
            br = pw.chromium.launch(**({'executable_path': EXE}
                                       if os.path.exists(EXE) else {}))
        except Exception as _e:
            br = None
            skip('sections 4 and 5', 'no browser: %s' % str(_e)[:40])
        if br is not None:
            pg = br.new_page()
            pg.route(re.compile(r'^https?://'), lambda r: r.abort())

            for rel in sorted(SIX):
                p = os.path.join(T, rel)
                after = shoot(pg, now(p), 390)
                if not ok(after, '%-38s renders a row' % rel[:38]):
                    continue
                gone = [c for c in after if not c['shown']]
                allow = HIDDEN_ON_PHONE.get(rel)
                ok(len(gone) == (1 if allow else 0),
                   '  %-36s every cell of the card is there%s'
                   % ('', ', bar the one named' if allow else ''),
                   'hidden: %s' % [c['cls'] or c['label'] for c in gone])
                if allow:
                    ok(gone and allow[0] in gone[0]['cls'],
                       '  %-36s and the one hidden is %s' % ('', allow[1]),
                       [c['cls'] for c in gone])
                act = [c for c in after if 'cell-actions' in c['cls']]
                ok(act and (act[0]['shown'] or rel == HAS_MOBILE_BAR),
                   '  %-36s including the row controls' % '',
                   act)
                pref = [c for c in after
                        if c['label'] and 'action' not in c['cls']][1:]
                ok(all(c['prefix'] == c['label'] for c in pref),
                   '  %-36s and each cell is prefixed with its heading' % '',
                   [(c['label'], c['prefix']) for c in pref
                    if c['prefix'] != c['label']][:3])

            # -------- THE CONTROL THAT MATTERS ------------------------
            # The first cut of this round put .desktop-action-cell on all
            # six. base hides that class below 768px because a page with
            # one is expected to have a .mobile-action-bar twin, and five
            # of the six have none. Proven, not reasoned: the same page,
            # one class added.
            probe = os.path.join(T, 'measurement_units_management.html')
            good = now(probe)
            bad = good.replace('class="cell-actions"',
                               'class="desktop-action-cell cell-actions"')
            ok(bad != good, 'CONTROL: the probe page could be spoiled')
            a390 = shoot(pg, bad, 390)
            a1280 = shoot(pg, bad, 1280)
            hid390 = [c for c in (a390 or []) if not c['shown']]
            hid1280 = [c for c in (a1280 or []) if not c['shown']]
            ok(len(hid390) == 1 and not hid1280,
               '  and with .desktop-action-cell added its row controls '
               'VANISH on a phone while staying on the desktop - which is '
               'what this round avoided by reading the table, not a flag',
               '390px hidden %d, 1280px hidden %d'
               % (len(hid390), len(hid1280)))

            # ==================================================
            head('5. RENDERED AT 1280px - IT LOOKS LIKE THE HOUSE')
            # ==================================================
            HEADS = """() => {
                const t = document.querySelector('table.alv-table')
                      || document.querySelector('table');
                if (!t) return null;
                const th = [...t.querySelectorAll('thead th')];
                const td = [...t.querySelectorAll('tbody tr:first-child td')];
                const s = e => getComputedStyle(e);
                return {
                  upper: th.every(e => s(e).textTransform === 'uppercase'),
                  fill: s(th[0]).backgroundColor,
                  verticals: th.concat(td).filter(
                      e => parseFloat(s(e).borderLeftWidth) > 0
                        || parseFloat(s(e).borderRightWidth) > 0).length,
                  align: td.map(e => s(e).textAlign)
                };
            }"""

            def look(text):
                p2 = os.path.join(SCRATCH, 'fx.html')
                with open(p2, 'w', encoding='utf-8') as fh:
                    fh.write(fixture(text))
                pg.set_viewport_size({'width': 1280, 'height': 900})
                _goto(pg, p2)
                return pg.evaluate(HEADS)

            for rel in sorted(SIX):
                g = look(now(os.path.join(T, rel)))
                ok(g['upper'], '%-38s headings are uppercase' % rel[:38])
                ok(g['verticals'] == 0,
                   '  %-36s no vertical grid lines' % '', g['verticals'])

            # passport is the one that centred all eight columns
            pp = os.path.join(T, 'passport_management.html')
            b4 = look(was(pp))
            af = look(now(pp))
            ok(b4['align'].count('center') >= 7,
               'CONTROL: passport centred %d of its columns before'
               % b4['align'].count('center'), b4['align'])
            data_align = af['align'][:7]
            ok(all(a in ('start', 'left') for a in data_align),
               '  and its data columns now read left, like every other '
               'house table', af['align'])
            ok(af['align'][7] == 'center',
               '  while the actions column stays centred', af['align'])
            br.close()

# ==========================================================================
head('6. WHAT THIS ROUND DELIBERATELY DID NOT TOUCH')
# ==========================================================================
for rel, why in sorted(LEAVE.items()):
    p = os.path.join(T, rel)
    ok(not os.path.isfile(p + SUFFIX),
       '%-30s untouched - %s' % (rel[:30], why.split(' - ')[0][:34]))
    ok(not re.search(r'<table[^>]*\balv-table\b', markup(now(p))),
       '  %-28s and has no .alv-table' % '')
    print('        %s' % why[:100])
    if len(why) > 100:
        print('        %s' % why[100:200])

# the row BUTTONS are a second standard and the next round
still = {}
for rel in sorted(SIX):
    t = now(os.path.join(T, rel))
    sp = table_of(t, SIX[rel][0])
    body = markup(t)[sp[0]:sp[1]]
    n = len(re.findall(r'class="[^"]*\bbtn-(?:sm|success|warning|danger|'
                       r'outline-\w+|light|icon)\b', body))
    if n:
        still[rel] = n
print('        the row BUTTONS are untouched on purpose, and there are '
      '%d of them:' % sum(still.values()))
for rel, n in still.items():
    print('          %-40s %d' % (rel[:40], n))
ok(bool(still),
   'the row controls still wear their own classes - a second standard, '
   'and the next round', still)

# ==========================================================================
head('7. THE RULES THAT WERE DUPLICATING base ARE GONE')
# ==========================================================================
# COUNTED THE WAY THIS SUITE COUNTS, which is not the way the patcher
# counts. The patcher reports rules DELETED; this counts rules whose
# selector NAMES THE TABLE'S CLASS. For five pages the two agree. For
# unit_conversions they differ by two, because #noResultsRow's phone rules
# were duplicating base as well and carry no table class - so they are
# checked by name, just below, instead of being folded into a total that
# would then have had to be explained.
GONE = {'categories_management.html': 14,
        'household_member_management.html': 10,
        'ingredient_base_units_management.html': 17,
        'measurement_units_management.html': 16,
        'passport_management.html': 9,
        'unit_conversions_management.html': 19}
total_b = total_a = 0
for rel in sorted(SIX):
    cls = SIX[rel][0]
    p = os.path.join(T, rel)

    def count(text, c=cls):
        n = 0
        for m in RULE.finditer(css_of(text)):
            sel = ' '.join(m.group(1).split())
            if re.search(r'\b%s\b' % re.escape(c), sel):
                n += 1
        return n
    b, a = count(was(p)), count(now(p))
    total_b += b
    total_a += a
    ok(b - a == GONE[rel],
       '%-38s %d -> %d rules' % (rel[:38], b, a),
       'expected %d gone, got %d' % (GONE[rel], b - a))
ok(total_b - total_a == sum(GONE.values()),
   '%d rules deleted in all, and base declares every one of them'
   % (total_b - total_a))
ok(total_a > 0,
   '  and %d page rules are KEPT - the inline-edit state and the '
   'page\'s own cells are not table furniture' % total_a)

# the two that carry no table class, by name
conv = os.path.join(T, 'unit_conversions_management.html')
cnow, cwas = css_of(now(conv)), css_of(was(conv))


def sel_here(css, want):
    return any(' '.join(m.group(1).split()) == want
               for m in RULE.finditer(css))


for dead in ('#noResultsRow td', '#noResultsRow td::before'):
    ok(sel_here(cwas, dead) and not sel_here(cnow, dead),
       '  and `%s` went too - base makes a cell block on a phone and '
       'prints no prefix for one with no data-label' % dead,
       'before %s, after %s' % (sel_here(cwas, dead), sel_here(cnow, dead)))
ok(sel_here(cnow, '#noResultsRow[style*="table-row"]'),
   '  while the row\'s own show/hide rule is KEPT - that is page logic')

# no page still writes out the phone card by hand
hand = []
for rel in sorted(SIX):
    c = css_of(now(os.path.join(T, rel)))
    for m in RULE.finditer(c):
        sel = ' '.join(m.group(1).split())
        if re.search(r'nth-child\(\d+\)::before', sel) \
                and SIX[rel][0] in sel:
            hand.append('%s: %s' % (rel, sel))
ok(not hand,
   'not one of them still hard-codes a heading into a positional rule',
   '\n'.join(hand[:4]))

# ==========================================================================
head('8. CONTROLS, AND THE GATE')
# ==========================================================================
ok(css_of('<style>a{/* } */ color: red}</style>').count('}') == 1,
   'the CSS reader ignores a brace inside a comment (lesson 21)')
ok('alv-table' not in markup(
    '<style>.alv-table{x:1}</style><p>hello</p>'),
   '  and the markup reader does not see a class named only in the '
   'stylesheet')

base_now = read(BASE)
ok(len(re.findall(r'\.alv-table', css_of(base_now))) > 20,
   'base really does own this component', len(re.findall(
       r'\.alv-table', css_of(base_now))))
ok(was(BASE) == base_now, '  and this round did not change base at all')

# a revert must be caught
probe = os.path.join(T, 'passport_management.html')
ok('alv-table' not in markup(was(probe)),
   'reverting a page takes .alv-table off it, so section 1 would FAIL - '
   'a revert is caught')

ok(SUFFIX.lstrip('.') and SUFFIX[1:] in [r.lstrip('.') for r in ROUNDS],
   '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS:
    ok(ROUNDS.index(SUFFIX) == len(ROUNDS) - 1
       or ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_barmobile'),
       '  and after the round before it (lesson 54)',
       ROUNDS[-3:])
ps1 = read(PS1) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that the row BUTTONS inside these tables are')
print('  right. They are not - they wear btn-sm btn-warning and friends')
print('  where the house spells icon-action-btn icon-edit. Section 6')
print('  counts them and names them as the next round.')
print('=' * 74)
sys.exit(1 if failed else 0)
