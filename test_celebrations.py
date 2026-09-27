# -*- coding: utf-8 -*-
"""test_celebrations.py - Section H round H2, 27 Sep 2026.

Judges Celebrations joining the house: the dashboard's two cards becoming
buttons, the search field moving above the bar so Back can go right, the
five modal footers, the ten row action items, and the calendar's Back.

TWO CLAIMS ARE RENDERED, NOT READ.

  * "Back goes to the right" is a claim about POSITION. base right-aligns it
    with `.page-action-buttons .action-back { margin-left: auto }`, and that
    rule cannot fire while a search box owns the right-hand slot. Section 2
    renders the page and requires Back's left edge to be further right than
    every other control in the bar - and requires the BACKUP to fail that,
    so the check can be seen failing (lesson 58).
  * The row action items are required to render as OUTLINED icons, not
    filled ones: a transparent-to-white background and a coloured border,
    which is what .icon-action-btn is.

AND ONE COUNT CAUGHT THE ROUND OUT. The first draft swapped five row
buttons. There are TEN - every one has a no-permission twin in an
{% else %} branch, a <span> wearing the same colours plus
.btn-action-disabled. The exact-count gate in the patcher refused the round
rather than doing half of it, and section 4 pins both halves.
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

SUFFIX = '.bak_celebrations'
ME = 'test_celebrations.py'
PATCHER = 'apply_celebrations.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'
BAR = 'page-action-buttons'

DASH = os.path.join(T, 'celebration_dashboard.html')
MGMT = os.path.join(T, 'celebration_management.html')
CAL = os.path.join(T, 'celebration_calendar.html')

COLOUR = re.compile(r'\bbtn-(?:secondary|success|light|info|primary|dark|'
                    r'warning|danger|sm|outline-secondary)\b')
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')

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


def _sp(m):
    return re.sub(r'[^\n]', ' ', m.group(0))


def blanked(t):
    """Comments blanked on the RAW text FIRST, then script and style - the
    house order is defeated by accept="image/*" (lesson 61)."""
    t = re.sub(r'<!--.*?-->', _sp, t, flags=re.S)
    t = re.sub(r'\{#.*?#\}', _sp, t, flags=re.S)
    for rx in (STYLE, SCRIPT):
        out, pos = [], 0
        for m in rx.finditer(t):
            out.append(t[pos:m.start(1)])
            out.append(re.sub(r'[^\n]', ' ', m.group(1)))
            pos = m.end(1)
        out.append(t[pos:])
        t = ''.join(out)
    return t


def wears(text, cls):
    """By EXACT token - a substring match counts action-back-label as
    action-back (lesson 30)."""
    return sum(1 for m in re.finditer(r'class="([^"]*)"', blanked(text))
               if cls in m.group(1).split())


def css_of(t):
    # NOT blanked(t) - THAT WIPES THE STYLE BODIES. blanked() exists to make
    # the MARKUP safe to scan, and it blanks <style> and <script> on purpose.
    # Feeding it here returned empty stylesheets, so every "base declares X"
    # check failed while base plainly declared X. Comments only.
    raw = re.sub(r'<!--.*?-->', _sp, t, flags=re.S)
    raw = re.sub(r'\{#.*?#\}', _sp, raw, flags=re.S)
    return '\n'.join(STYLE.findall(raw))


def rules_for(t, cls):
    return sum(1 for m in RULE.finditer(css_of(t))
               if re.search(r'(?<![\w-])\.' + re.escape(cls) + r'(?![\w-])',
                            ' '.join(m.group(1).split())))


def bar_at(text):
    m = re.search(r'<div[^>]*class="[^"]*(?<![\w-])' + BAR
                  + r'(?![\w-])[^"]*"[^>]*>', blanked(text))
    return m.start() if m else None


# ==========================================================================
head('1. THE DASHBOARD CARDS ARE BUTTONS, LEFT OF HELP')
# ==========================================================================
if not os.path.isfile(DASH):
    skip('section 1', 'celebration_dashboard.html is not on disk')
else:
    a, b = was(DASH), now(DASH)
    ok(wears(a, 'action-card') == 2,
       'before: two .action-card tiles', wears(a, 'action-card'))
    ok(wears(b, 'action-card') == 0 and rules_for(b, 'action-card') == 0,
       'after: .action-card is gone from markup AND stylesheet',
       'worn %d, rules %d' % (wears(b, 'action-card'),
                              rules_for(b, 'action-card')))
    ok(rules_for(b, 'dashboard-actions') == 0,
       '  and so is .dashboard-actions')
    inner = re.search(r'<div[^>]*class="[^"]*' + BAR + r'[^"]*"[^>]*>(.*?)'
                      r'\n</div>', blanked(b), re.S)
    seg = inner.group(1) if inner else blanked(b)
    order = [m.start() for m in
             (re.search(r'Manage Contacts and Events', seg),
              re.search(r'View Events', seg),
              re.search(r'Help', seg)) if m]
    ok(len(order) == 3 and order == sorted(order),
       'both controls sit in the bar, in front of Help', order)
    ok('action-primary' in b and 'Manage Contacts and Events' in b,
       '  Manage Contacts and Events is the primary')
    ok(b.count('Manage Contacts and Events') == 1
       and b.count('View Events') == 1,
       '  and neither was duplicated',
       '%d / %d' % (b.count('Manage Contacts and Events'),
                    b.count('View Events')))
    # The sentences go with the cards - the same decision G1 took.
    ok('Add, edit, and organize your contacts' in a
       and 'Add, edit, and organize your contacts' not in b,
       '  their descriptive sentences go too - a description is not a '
       'house control')

# ==========================================================================
head('2. THE SEARCH MOVED UP, SO BACK CAN GO RIGHT')
# ==========================================================================
if not os.path.isfile(MGMT):
    skip('section 2', 'celebration_management.html is not on disk')
else:
    a, b = was(MGMT), now(MGMT)
    ok(rules_for(a, 'celebration-toolbar') > 0,
       'before: the page declared its own .celebration-toolbar')
    ok(wears(b, 'celebration-toolbar') == 0
       and rules_for(b, 'celebration-toolbar') == 0,
       'after: it is gone from markup and stylesheet')
    ok(bar_at(b) is not None, '  the controls sit in .%s now' % BAR)
    srch = re.search(r'<div[^>]*class="[^"]*toolbar-search', blanked(b))
    ok(srch is not None and bar_at(b) is not None
       and srch.start() < bar_at(b),
       '  and the search field comes BEFORE it, as Properties does',
       '%s vs %s' % (srch.start() if srch else None, bar_at(b)))
    ok(rules_for(b, 'toolbar-actions') == 0,
       '  the local layout rules base owns are deleted')

# ==========================================================================
head('3. THE FIVE MODAL FOOTERS')
# ==========================================================================
FOOTERS = (('Save Contact', 'action-primary'),
           ('Save Event', 'action-primary'),
           ('Delete Contact', 'action-danger'),
           ('Delete Event', 'action-danger'),
           ('Import Contacts', 'action-primary'))
if not os.path.isfile(MGMT):
    skip('section 3', 'not on disk')
else:
    a, b = was(MGMT), now(MGMT)
    for label, want in FOOTERS:
        m = re.search(r'<button[^>]*class="([^"]*)"[^>]*>(?:(?!</button>).)*?'
                      + re.escape(label), blanked(b), re.S)
        ok(m is not None and want in m.group(1).split(),
           '%-18s wears .%s' % (label, want),
           m.group(1) if m else 'not found')
        ok(m is not None and not COLOUR.search(m.group(1)),
           '  and no Bootstrap colour class', m.group(1) if m else '')
    ok(blanked(b).count('class="btn action-secondary" data-dismiss="modal"')
       == 5, 'all five Cancels are .action-secondary',
       blanked(b).count('class="btn action-secondary" data-dismiss="modal"'))
    # The HEADERS were already right and must not have moved.
    ok(wears(a, 'alv-modal-head') == wears(b, 'alv-modal-head') == 5,
       'CONTROL: the five .alv-modal-head headers were already house, '
       'and are untouched',
       '%d -> %d' % (wears(a, 'alv-modal-head'), wears(b, 'alv-modal-head')))
    ok('alv-modal-head--danger' in b,
       '  including the two --danger ones')

# ==========================================================================
head('4. TEN ROW ACTION ITEMS, NOT FIVE')
# ==========================================================================
if not os.path.isfile(MGMT):
    skip('section 4', 'not on disk')
else:
    a, b = was(MGMT), now(MGMT)
    ok(wears(a, 'btn-sm') == 10,
       'before: TEN btn-sm row controls - five actions and five '
       'no-permission twins in {% else %} branches', wears(a, 'btn-sm'))
    ok(wears(b, 'btn-sm') == 0, 'after: not one survives', wears(b, 'btn-sm'))
    ok(wears(b, 'icon-action-btn') == 10,
       '  all ten wear .icon-action-btn', wears(b, 'icon-action-btn'))
    for cls, n in (('icon-event', 1), ('icon-edit', 2), ('icon-delete', 2),
                   ('icon-disabled', 5)):
        ok(wears(b, cls) == n, '  .%-14s worn %d time(s)' % (cls, n),
           wears(b, cls))
    ok(wears(b, 'row-actions') >= 2,
       '  and they sit inside .row-actions, as the house does',
       wears(b, 'row-actions'))
    # ONE CLASS, ONE PICTURE - test_icon_buttons §1b exists for this.
    # ONE CLASS, ONE PICTURE - but the class is .icon-edit, not the page.
    # The four fa-edit that REMAIN are on .mobile-action-btn, a different
    # base component with its own glyph set, and they are not this round's
    # business. What must be true is that no .icon-edit carries fa-edit.
    icon_edit_glyphs = set()
    for m in re.finditer(r'class="([^"]*icon-edit[^"]*)"[^>]*>\s*'
                         r'<i class="([^"]*)"', blanked(b)):
        icon_edit_glyphs |= set(x for x in m.group(2).split()
                                if x.startswith('fa-'))
    ok(icon_edit_glyphs == {'fas', 'fa-pencil-alt'} - {'fas'},
       'every .icon-edit carries fa-pencil-alt and nothing else - nine '
       'house buttons already wear that pair', sorted(icon_edit_glyphs))
    ok(blanked(b).count('<i class="fas fa-pencil-alt"></i>') == 4,
       '  all four row actions were converted',
       blanked(b).count('<i class="fas fa-pencil-alt"></i>'))
    mob = len(re.findall(r'fa-edit mobile-action-icon', blanked(b)))
    ok(mob == 4,
       '  NOTED: %d fa-edit remain on .mobile-action-btn, a different '
       'component - tree-wide that bar is 14 fa-pencil-alt to 6 fa-edit, '
       'which is a glyph round of its own' % mob, mob)

# ==========================================================================
head('5. THE CALENDAR BACK SAYS "BACK" AND HAS NO COLOUR')
# ==========================================================================
if not os.path.isfile(CAL):
    skip('section 5', 'celebration_calendar.html is not on disk')
else:
    a, b = was(CAL), now(CAL)
    ok('Back to Dashboard' in a and wears(a, 'action-back') == 0,
       'before: it said "Back to Dashboard" and wore NO .action-back - '
       'which is why G2\'s class-keyed census never saw it')
    ok(wears(b, 'action-back') == 1, 'after: it wears .action-back',
       wears(b, 'action-back'))
    m = re.search(r'<a[^>]*class="([^"]*action-back[^"]*)"', blanked(b))
    ok(m is not None and not COLOUR.search(m.group(1)),
       '  with no Bootstrap colour class', m.group(1) if m else '')
    ok('<span class="action-back-label"> Back</span>' in b,
       '  and the word is "Back", inside the span base hides on a phone')
    ok(bar_at(b) is not None and rules_for(b, 'calendar-toolbar') == 0,
       '  its toolbar is the house bar now')

# ==========================================================================
head('6. base GAINED ONE NAME, ON AN EXISTING COLOUR')
# ==========================================================================
bc = css_of(read(BASE))
ok(bc.count('.icon-event') >= 1, 'base declares .icon-event')
m = re.search(r'\.icon-event\s*\{([^}]*)\}', bc)
ok(m is not None and 'var(--alv-view)' in m.group(1),
   '  aliasing var(--alv-view), exactly as .icon-manage does',
   m.group(1).strip() if m else '')
ok(m is not None and '#' not in m.group(1),
   '  and inventing no colour of its own')
mm = re.search(r'\.icon-manage\s*\{([^}]*)\}', bc)
ok(mm is not None and m is not None
   and ' '.join(m.group(1).split()) == ' '.join(mm.group(1).split()),
   '  its declaration is byte for byte .icon-manage\'s',
   '%r vs %r' % (m.group(1).strip() if m else None,
                 mm.group(1).strip() if mm else None))

# ==========================================================================
head('7. RENDERED - BACK REALLY IS ON THE RIGHT')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception as e:
    sync_playwright = None
    skip('section 7', 'playwright unavailable: %s' % str(e)[:40])

if sync_playwright is None or not os.path.isfile(BOOT) \
        or not os.path.isfile(MGMT):
    skip('section 7', 'playwright, the bootstrap fixture or the page is '
                      'missing')
else:
    MODAL_IF = re.compile(
        r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)

    def styles_of(t):
        return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)),
                       flags=re.S)
                for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                     re.S | re.I)]

    def body_markup(t):
        m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t,
                      re.S)
        x = m.group(1) if m else t
        x = re.sub(r'<(script|style)\b.*?</\1>', '', x, flags=re.S | re.I)
        for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
            x = re.sub(rx, '', x, flags=re.S)
        return re.sub(r'\{\{.*?\}\}', 'x', x, flags=re.S)

    boot = read(BOOT)
    bcss = '\n'.join(styles_of(read(BASE)))

    def fixture(t):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style>%s</head>'
                '<body class="has-sidebar"><div class="main-content '
                'with-sidebar">%s</div></body></html>'
                % (boot, bcss,
                   ''.join('<style>%s</style>' % c for c in styles_of(t)),
                   body_markup(t)))

    GEOM = """() => {
        const bar = document.querySelector('.page-action-buttons');
        const back = document.querySelector('.action-back');
        if (!back) return null;
        const others = [...document.querySelectorAll(
            '.page-action-buttons .btn')].filter(e => e !== back);
        const r = back.getBoundingClientRect();
        return {
            backX: Math.round(r.x),
            maxOtherX: others.length
                ? Math.max(...others.map(e =>
                    Math.round(e.getBoundingClientRect().x))) : -1,
            others: others.length,
            inBar: !!(bar && bar.contains(back))
        };
    }"""
    ICON = """() => {
        const e = document.querySelector('.icon-action-btn');
        if (!e) return null;
        const s = getComputedStyle(e);
        return {bg: s.backgroundColor, border: s.borderTopColor,
                w: Math.round(e.getBoundingClientRect().width)};
    }"""

    launched = False
    with sync_playwright() as pw:
        try:
            br = pw.chromium.launch(**({'executable_path': EXE}
                                       if os.path.exists(EXE) else {}))
            launched = True
        except Exception as _e:
            skip('section 7', 'chromium would not launch: %s'
                 % str(_e).split('\n')[0][:60])

        if launched:
            n = [0]

            def probe(text, js, tag):
                n[0] += 1
                fx = os.path.join(SCRATCH, 'cl_%s_%d.html' % (tag, n[0]))
                with open(fx, 'w', encoding='utf-8') as fh:
                    fh.write(fixture(text))
                ctx = br.new_context(viewport={'width': 1280, 'height': 900})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                _goto(pg, fx)
                try:
                    return pg.evaluate(js)
                finally:
                    ctx.close()

            g = probe(now(MGMT), GEOM, 'now')
            ok(g is not None and g['inBar'],
               'Back renders inside the action bar', g)
            ok(g is not None and g['others'] >= 3,
               '  CONTROL: with %s other control(s) beside it to be right of'
               % (g['others'] if g else '?'))
            ok(g is not None and g['backX'] > g['maxOtherX'],
               '  and it is further right than every one of them: '
               '%s vs %s' % (g['backX'] if g else '?',
                             g['maxOtherX'] if g else '?'))
            gw = probe(was(MGMT), GEOM, 'was')
            ok(gw is None or not gw['inBar'] or gw['backX'] <= gw['maxOtherX'],
               '  CONTROL: from the backup it was NOT - the check can be '
               'seen failing', gw)

            ic = probe(now(MGMT), ICON, 'icon')
            ok(ic is not None, 'a row action renders', ic)
            ok(ic is not None
               and ('rgba(0, 0, 0, 0)' in ic['bg'] or '255, 255, 255'
                    in ic['bg']),
               '  OUTLINED, not filled - its background is transparent or '
               'white where the old ones were solid green, amber and red',
               ic['bg'] if ic else '')
            ok(ic is not None and ic['border'] not in ('rgba(0, 0, 0, 0)',),
               '  and it carries a coloured border', ic['border'] if ic else '')
            br.close()

# ==========================================================================
head('8. CONTROLS, AND THE GATE')
# ==========================================================================
# THE CALENDAR KEEPS ONE, AND IT IS NAMED. Its view toggle is deliberately
# desktop-only - `#viewToggleBtn { display: none !important }` below 768px,
# with a banner in its place saying the calendar grid is desktop-only - so
# it cannot wear .action-secondary, whose whole point is that a secondary
# stays reachable on a phone. Its blue belongs to the Bootstrap-family
# round, and its right home is .alv-seg, which base declares and NOTHING
# wears. Named here so it cannot grow back in silence.
KEEPS_COLOUR = {'celebration_calendar.html': ['btn-info']}
for p, rel in ((DASH, 'celebration_dashboard.html'),
               (MGMT, 'celebration_management.html'),
               (CAL, 'celebration_calendar.html')):
    if not os.path.isfile(p):
        continue
    b = blanked(now(p))
    left = sorted(set(c for m in re.finditer(r'class="([^"]*)"', b)
                      for c in m.group(1).split() if COLOUR.match(c)))
    ok(left == KEEPS_COLOUR.get(rel, []),
       '%-32s carries %s' % (rel, 'only its named exception %s'
                             % KEEPS_COLOUR[rel] if rel in KEEPS_COLOUR
                             else 'no Bootstrap colour class at all'), left)
cal_css = css_of(now(CAL)) if os.path.isfile(CAL) else ''
ok('#viewToggleBtn' in cal_css and 'display: none !important' in cal_css,
   '  and that toggle really is hidden on a phone, which is why it cannot '
   'be a .action-secondary')
ok(wears('<a class="action-back-label">x</a>', 'action-back') == 0,
   'the class match is by token - action-back-label is not action-back')
cm = MGMT
if os.path.isfile(cm + SUFFIX):
    ok(wears(was(cm), 'btn-sm') == 10,
       'reverting puts the ten btn-sm controls back, so section 4 would '
       'FAIL - a revert is caught')
else:
    skip('the revert check', 'no %s backup' % SUFFIX)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
ok(SUFFIX in ROUNDS and '.bak_personalteal' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_personalteal'),
   '  and after the round before it (lesson 54)')
ps1 = os.path.join(ROOT, PS1)
ok(os.path.isfile(ps1) and ME in read(ps1), '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
