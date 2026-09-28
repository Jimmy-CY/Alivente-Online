# -*- coding: utf-8 -*-
"""test_table_preview.py - Section H round H5a, 28 Sep 2026.

The two imported-recipe grids onto base's .alv-table. The first of the two
JS-built Personal tables H4 set aside, and the reason it was set aside is
section 2: each grid is built ONCE BY DJANGO AND AGAIN BY JAVASCRIPT, for
"Add Another". A round that labelled only the markup would give a phone
card its headings on the rows that came from the server and none on the
rows the person just added.

SECTION 4 IS THE ONE THAT EARNED ITS PLACE, and it is rendered. base lays
a phone cell out as label left, value right; this page pinned its remove
button to the card's top-right corner with position:absolute. On the house
card the instructions grid's step-number badge moved from x=52 to x=307
and landed underneath a button pinned at x=320. The first cut of this
round shipped that overlap. The check puts the pin back and watches the
collision return, so it is a check that can be seen to fail - and only at
390px, which is why reading the desktop would have missed it.

These are tables of FORM INPUTS, which was a real question and was
measured rather than assumed: the ingredient row goes from 494px tall to
354px and every field keeps its width.
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

SUFFIX = '.bak_tablepreview'
ME = 'test_table_preview.py'
PATCHER = 'apply_table_preview.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'
REL = 'preview_imported_recipe.html'
PAGE = os.path.join(T, REL)

# The two grids, and the label each column must carry. THE LABELS ARE NOT
# THIS SUITE'S OPINION: they were read out of the
# `td:nth-child(n)::before { content: '...' }` rules the round deletes, and
# section 3 goes back to the BACKUP and checks them against that source.
GRIDS = {
    'ingredientsTable': [None, 'Quantity', 'Measurement', 'Ingredient',
                         'Preparation', 'Group', None],
    'instructionsTable': [None, 'Step', 'Instruction', 'Group', None],
}

# The JavaScript that builds the SECOND row template, for "Add Another".
JS_MARK = {'ingredientsTable': "newRow.className = 'ingredient-row';",
           'instructionsTable': "newRow.className = 'instruction-row';"}

# The pin this round retired, and why it cannot come back. Section 4 puts
# it back on purpose and shows the collision return.
PIN = ('#ingredientsTable td.actions-col, '
       '#instructionsTable td:last-child')
PIN_BODY = ('position: absolute !important; top: 8px; right: 8px; '
            'width: auto !important; padding: 0 !important;')

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
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t,
                 flags=re.S)
    return re.sub(r'/\*.*?\*/', '', '\n'.join(STYLE.findall(raw)),
                  flags=re.S)


def markup(t):
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    t = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    out = list(t)
    for rx in (STYLE, SCRIPT):
        for m in rx.finditer(t):
            for i in range(m.start(1), m.end(1)):
                out[i] = ' '
    return ''.join(out)


def js_of(t):
    return '\n'.join(SCRIPT.findall(
        re.sub(r'<!--.*?-->', ' ', t, flags=re.S)))


def table_of(t, tid):
    mk = markup(t)
    m = re.search(r'<table[^>]*id="%s"[^>]*>' % re.escape(tid), mk)
    if not m:
        return None
    j = mk.find('</table>', m.end())
    return (m.start(), j + 8) if j > 0 else None


def markup_row(t, tid):
    """The <td> opening tags of the Django prototype row."""
    sp = table_of(t, tid)
    if sp is None:
        return []
    mk = markup(t)[sp[0]:sp[1]]
    tb = mk.find('<tbody')
    m = re.search(r'<tr\b', mk[tb:]) if tb >= 0 else None
    if not m:
        return []
    s = tb + m.start()
    e = mk.find('</tr>', s)
    return [x.group(0) for x in re.finditer(r'<td\b[^>]*>', mk[s:e])]


def js_row(t, tid):
    """The <td> opening tags of the JavaScript row template."""
    js = js_of(t)
    i = js.find(JS_MARK[tid])
    if i < 0:
        return []
    m = re.search(r'newRow\.innerHTML\s*=\s*`(.*?)`;', js[i:], re.S)
    if not m:
        return []
    return [x.group(0) for x in re.finditer(r'<td\b[^>]*>', m.group(1))]


def labels(tags):
    out = []
    for x in tags:
        m = re.search(r'data-label="([^"]*)"', x)
        out.append(m.group(1) if m else None)
    return out


def sel_here(css, want):
    w = ' '.join(want.split())
    return sum(1 for m in RULE.finditer(css)
               if ' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                                  flags=re.S).split()) == w)


# ==========================================================================
head('1. BOTH GRIDS WEAR THE HOUSE TABLE')
# ==========================================================================
t_now, t_was = now(PAGE), was(PAGE)
for tid in sorted(GRIDS):
    sp = table_of(t_now, tid)
    if not ok(sp is not None, '#%-22s has its table' % tid):
        continue
    tag = t_now[sp[0]:t_now.index('>', sp[0]) + 1]
    names = re.search(r'class="([^"]*)"', tag).group(1).split()
    ok(names[:2] == ['table', 'alv-table'],
       '  %-20s class reads `table alv-table ingredient-table`' % '',
       ' '.join(names))
    ok('ingredient-table' in names,
       '  %-20s and keeps its own page class' % '')
    ok('table-container' in markup(t_now)[max(0, sp[0] - 240):sp[0]],
       '  %-20s sits in a .table-container' % '')
ok(not re.search(r'<table[^>]*\balv-table\b', markup(t_was)),
   'CONTROL: neither did before this round')

# ==========================================================================
head('2. TWO ROW TEMPLATES, AND THEY AGREE')
# ==========================================================================
# A round that labelled only the markup would give a phone card its
# headings on the rows that came from the server and none at all on the
# rows the person just added.
for tid in sorted(GRIDS):
    want = GRIDS[tid]
    mrow, jrow = markup_row(t_now, tid), js_row(t_now, tid)
    ok(len(mrow) == len(want),
       '#%-22s Django row builds %d cell(s)' % (tid, len(mrow)), len(want))
    ok(len(jrow) == len(want),
       '  %-20s "Add Another" builds %d too' % ('', len(jrow)), len(want))
    ok(labels(mrow) == want,
       '  %-20s and the Django row carries exactly these labels' % '',
       labels(mrow))
    ok(labels(jrow) == want,
       '  %-20s and so does the JavaScript one' % '', labels(jrow))
    ok(labels(mrow) == labels(jrow),
       '  %-20s the two agree, so a card is the same shape wherever the '
       'row came from' % '')
    # the control cell takes the house class in BOTH
    ok('cell-actions' in mrow[-1] and 'cell-actions' in jrow[-1],
       '  %-20s and the control cell is .cell-actions in both' % '',
       (mrow[-1][:50], jrow[-1][:50]))
    ok(not labels(js_row(t_was, tid))[1:-1] or
       all(x is None for x in labels(js_row(t_was, tid))),
       '  %-20s CONTROL: the backup\'s JS row had no labels at all' % '',
       labels(js_row(t_was, tid)))

# ==========================================================================
head('3. THE LABELS CAME FROM THE RULES BEING DELETED')
# ==========================================================================
cw = css_of(t_was)
for tid in sorted(GRIDS):
    src = {}
    for m in re.finditer(r'#%s td:nth-child\((\d+)\)::before\s*\{([^}]*)\}'
                         % tid, cw):
        c = re.search(r"content\s*:\s*['\"]([^'\"]*)['\"]", m.group(2))
        if c:
            src[int(m.group(1))] = c.group(1)
    named = [src[k] for k in sorted(src)]
    want = [x for x in GRIDS[tid] if x]
    ok(named == want,
       '#%-22s the backup\'s own ::before rules said exactly these' % tid,
       'backup %s\nround  %s' % (named, want))
    ok(not re.search(r'#%s td:nth-child\(\d+\)::before' % tid,
                     css_of(t_now)),
       '  %-20s and not one of them is left' % '')

# ==========================================================================
head('4. RENDERED - NOTHING IN A ROW SITS ON TOP OF ANYTHING ELSE')
# ==========================================================================
# THE CHECK THAT EARNED ITS PLACE. base lays a phone cell out as label
# left, value right. This page pinned its remove button to the card's top
# right corner with position:absolute - so on the house card the
# instructions grid's step-number badge moved from x=52 to x=307 and
# landed underneath a button pinned at x=320. The first cut of this round
# shipped that, and reading the stylesheet would not have found it.
try:
    from playwright.sync_api import sync_playwright
except Exception as _e:
    sync_playwright = None
    skip('section 4', 'playwright unavailable: %s' % str(_e)[:40])

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('section 4', 'playwright or the bootstrap fixture is gone')
else:
    TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)

    def one_branch(t):
        """Keep the FIRST branch of every {% if %}. A stack, so an
        if/else nested inside an else-less if collapses too."""
        while True:
            stack, cut = [], None
            for m in TAG.finditer(t):
                k = m.group(1)
                if k == 'if':
                    stack.append([m.start(), m.end(), None])
                elif k in ('elif', 'else'):
                    if stack and stack[-1][2] is None:
                        stack[-1][2] = m.start()
                elif k == 'endif':
                    if not stack:
                        return t
                    start, first_end, cut = stack.pop()
                    if cut is not None:
                        t = t[:start] + t[first_end:cut] + t[m.end():]
                        break
            else:
                return t

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

    OVERLAP = """(tid) => {
        const t = document.getElementById(tid);
        if (!t) return null;
        const r = t.querySelector('tbody tr');
        if (!r) return null;
        const box = e => { const b = e.getBoundingClientRect();
            return {x: b.left, y: b.top, w: b.width, h: b.height}; };
        const hit = (a, b) => !(a.x + a.w <= b.x || b.x + b.w <= a.x
                             || a.y + a.h <= b.y || b.y + b.h <= a.y);
        const k = [...r.querySelectorAll(
            'input, textarea, button, .step-number-badge-table,'
            + ' .drag-handle')].map(box).filter(b => b.w > 0 && b.h > 0);
        let n = 0;
        for (let i = 0; i < k.length; i++)
            for (let j = i + 1; j < k.length; j++)
                if (hit(k[i], k[j])) n++;
        return {items: k.length, overlaps: n,
                rowH: Math.round(r.getBoundingClientRect().height)};
    }"""

    with sync_playwright() as pw:
        try:
            br = pw.chromium.launch(**({'executable_path': EXE}
                                       if os.path.exists(EXE) else {}))
        except Exception as _e:
            br = None
            skip('section 4', 'no browser: %s' % str(_e)[:40])
        if br is not None:
            pg = br.new_page()
            pg.route(re.compile(r'^https?://'), lambda r: r.abort())

            def look(text, w, tid):
                fp = os.path.join(SCRATCH, 'fx.html')
                with open(fp, 'w', encoding='utf-8') as fh:
                    fh.write(fixture(text))
                pg.set_viewport_size({'width': w, 'height': 1600})
                _goto(pg, fp)
                return pg.evaluate(OVERLAP, tid)

            tall = {}
            for w in (390, 1280):
                for tid in sorted(GRIDS):
                    g = look(t_now, w, tid)
                    ok(g and g['overlaps'] == 0,
                       '#%-22s %4dpx  %d control(s), none overlapping'
                       % (tid, w, g['items'] if g else 0), g)
                    ok(g and g['items'] >= 4,
                       '  %-20s and there really are controls to check' % '',
                       g)
                    if w == 390:
                        tall[tid] = g['rowH']

            for tid in sorted(GRIDS):
                b = look(t_was, 390, tid)
                ok(b and tall[tid] < b['rowH'],
                   '#%-22s the phone row is SHORTER than before: '
                   '%dpx -> %dpx' % (tid, b['rowH'], tall[tid]),
                   '%s -> %s' % (b, tall[tid]))

            # ---- THE CONTROL. Put the retired pin back and watch it break.
            spoiled = t_now.replace(
                '</style>',
                '@media screen and (max-width: 768px){ %s { %s } }</style>'
                % (PIN, PIN_BODY), 1)
            ok(spoiled != t_now, 'CONTROL: the page could be spoiled')
            g = look(spoiled, 390, 'instructionsTable')
            ok(g and g['overlaps'] > 0,
               '  and with the retired pin put back the step badge lands '
               'under the remove button again - so this check can be seen '
               'to FAIL, and the pin is why it was retired', g)
            g2 = look(spoiled, 1280, 'instructionsTable')
            ok(g2 and g2['overlaps'] == 0,
               '  CONTROL: and only on a phone, which is why reading the '
               'desktop would have missed it', g2)
            br.close()

# ==========================================================================
head('5. THE RULES base NOW OWNS ARE GONE, AND PAGE LOGIC IS NOT')
# ==========================================================================
cn = css_of(t_now)


def table_rules(css):
    n = 0
    for m in RULE.finditer(css):
        sel = ' '.join(m.group(1).split())
        if re.search(r'\.ingredient-table\b|#(ingredients|instructions)'
                     r'Table\b', sel):
            n += 1
    return n


ok(table_rules(cw) - table_rules(cn) == 22,
   '22 rule(s) deleted  (%d -> %d)' % (table_rules(cw), table_rules(cn)),
   'expected 22, got %d' % (table_rules(cw) - table_rules(cn)))
ok(table_rules(cn) > 0,
   '  and %d are KEPT - the column widths, the input borders and the '
   'valid/invalid colouring are the page\'s own' % table_rules(cn))

KEPT = ['.ingredient-table input',
        '.ingredient-table .drag-col',
        '#ingredientsTable td.drag-col, #instructionsTable td:first-child']
for sel in KEPT:
    ok(sel_here(cn, sel) == 1, '  %s is kept' % sel[:56])
ok(sel_here(cn, PIN) == 0 and sel_here(cw, PIN) == 1,
   '  and the actions pin is gone - section 4 shows what it did',
   '%d now, %d before' % (sel_here(cn, PIN), sel_here(cw, PIN)))

# the teal band
m = re.search(r'\.ingredient-table thead\s*\{([^}]*)\}', cw)
ok(m is not None and '#0e7c8b' in m.group(1),
   'CONTROL: the backup\'s thead was a teal band with white text, which '
   'is the biggest visible change this round makes',
   m.group(1).strip() if m else 'no such rule')

# ==========================================================================
head('6. CONTROLS, AND THE GATE')
# ==========================================================================
ok(css_of('<style>a{/* } */ color: red}</style>').count('}') == 1,
   'the CSS reader ignores a brace inside a comment (lesson 21)')
ok('<td' not in markup('<script>var a = "<td>";</script>'),
   '  and the markup reader does not see a cell built in a script')
ok(js_of('<script>x</script>').strip() == 'x',
   '  while the script reader does')

ok(not re.search(r'<table[^>]*\balv-table\b', markup(t_was)),
   'reverting takes .alv-table off both grids, so section 1 would FAIL - '
   'a revert is caught')
ok(all(x is None for x in labels(js_row(t_was, 'ingredientsTable'))),
   '  and it takes the JS labels with it, so section 2 would FAIL too')

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and '.bak_rowpersonal' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_rowpersonal'),
       '  and after the round before it (lesson 54)', ROUNDS[-3:])
ps1 = read(PS1) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that a seven-column grid of text fields is the')
print('  right way to correct an imported recipe on a phone at all. It is')
print('  now a house table and 90px shorter per row; whether the screen')
print('  should be a list of cards instead is a question for a person.')
print('=' * 74)
sys.exit(1 if failed else 0)
