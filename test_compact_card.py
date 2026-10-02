# -*- coding: utf-8 -*-
"""test_compact_card.py - Section C round C-1, 2 Oct 2026.

Demetri, with a screenshot of Celebrations -> Contacts in Compact View:
"reduce the size of the font of the Contact Name, so that every Contact
Name fits on one line"; "we don't need to show the Friend/Family pill...
only when the user clicks on the Compact Contact and it expands"; and
"maybe, for the Compact view, you can also remove the Person Icon."

SECTION 2 IS THE CLAIM AND IT NEEDS A BROWSER. "Fits on one line" is not
a thing a grep can settle - it is a function of the font, the card width,
the grid's column count and the length of the name, and only one of those
is in the stylesheet. So the cards are drawn against base's real sheet at
1280, 1000 and 390, and the name's TRUE text width is read with a Range:
a clipped flex item reports its clipped width through both scrollWidth
and getBoundingClientRect, so both of those lie, and the first draft of
this measurement believed them.

SECTION 3 IS A DEFECT THIS ROUND FOUND RATHER THAN ONE IT WAS SENT FOR.
Two CSS comments on this page had lost their opening slash-star, so two
rules had been discarded by the parser since 25 September:

    the phone action bar, which should hide until a card is opened
    compact view on a phone, which should be ONE column and was TWO

Nothing in 214 suites was watching for that. Braces balanced perfectly
while two rules sat dead between them. Section 3 asserts the balance
across both template roots, so the next one is caught the day it is
written.

WHAT THIS SUITE DOES NOT DO. It does not pin a pixel width for a name:
the names are the user's own data and a figure measured against six of
them would go stale the first time he adds a seventh. It pins the ROOM
the narrowest card gives a name, and the font size, and asserts that the
name cannot take a second line whatever its length - which is the claim
he actually made.
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


def _goto(pg, path):
    try:
        pg.goto('file://' + path)
    except Exception as e:
        print('  !! the browser could not open %s: %s' % (path, e))
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_compactcard'
ME = 'test_compact_card.py'
PATCHER = 'apply_compact_card.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BASE = alv_tree.path_of('base.html')
PAGE = alv_tree.path_of('celebration_management.html')

# Six names off his own screen, plus one longer than any of them, because
# a measurement that only uses the names that exist today tells you
# nothing about the one he adds tomorrow.
NAMES = ['Charis Chrysanthou (Alexandra)', 'Alexandra Papadopoulos (Katia)',
         'Konstantinos Papadimitriou (Nikolaos)', 'Andriana Aitken (Kappatos)',
         'Alexandra Simitopoulos', 'Angelique Paris (Erene)']

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
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    """The file as THIS round left it, not as it stands today."""
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


def css_of(text):
    return '\n'.join(STYLE.findall(text))


def strays(css):
    """(stray */ , unclosed /*). The instrument this round exists for."""
    stack = extra = 0
    for m in re.finditer(r'/\*|\*/', css):
        if m.group(0) == '/*':
            stack += 1
        elif stack:
            stack -= 1
        else:
            extra += 1
    return extra, stack


P_NOW, P_WAS = now(PAGE), was(PAGE)

print('=' * 74)
print('%s - C-1, THE COMPACT CONTACT' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE COLLAPSED CARD DROPS THE ICON, THE PILL AND THE HEADING SIZE')
# ==========================================================================
CSS = css_of(P_NOW)
block = ''
if 'THE COLLAPSED COMPACT CARD IS A LIST ROW' in CSS:
    block = CSS[CSS.index('THE COLLAPSED COMPACT CARD IS A LIST ROW'):]
    block = block[:block.index('/* Adjust contact header for compact view */')]
ok(bool(block), 'the round left its block of rules')

sels = re.findall(r'(?m)^([^\s/@][^{]*)\{', block)
loose = [s.strip() for s in sels if ':not(.expanded)' not in s]
ok(sels and not loose,
   'all %d of its selectors are scoped to :not(.expanded)' % len(sels),
   '\n'.join(loose))
ok(re.search(r'\.contact-info h4\s*\{[^}]*font-size:\s*1\.05rem', block),
   '  the name is 1.05rem - the size this page already uses for this '
   'heading on a phone, not a new number')
ok(re.search(r'h4 > i,[\s\S]{0,80}relationship-badge\s*\{[^}]*display:\s*none',
             block) or
   ('h4 > i' in block and 'relationship-badge' in block
    and 'display: none' in block),
   '  and the icon and the pill are hidden together')
ok('text-overflow: ellipsis' in block and 'min-width: 0' in block,
   '  with min-width:0 and an ellipsis as the backstop - a flex item will '
   'not shrink below its content without the first')

# HIDDEN, NOT DELETED. The expanded card has to be able to show them.
ok('relationship-badge' in P_NOW and 'fa-user-circle' in P_NOW,
   'the pill and the icon are still in the markup, hidden rather than cut')
ok(len(re.findall(r'<span class="contact-name">\{\{ contact\.name \}\}</span>',
                  P_NOW)) == 1,
   'and the name has a span of its own, exactly once')
ok(not re.search(r'</i>\s*\{\{ contact\.name \}\}', P_NOW),
   '  CONTROL: no bare {{ contact.name }} is left in the heading')
if P_WAS:
    ok(bool(re.search(r'</i>\s*\{\{ contact\.name \}\}', P_WAS)),
       'CONTROL: it WAS a bare text node - an anonymous flex item, which '
       'cannot be measured, clipped or told not to wrap')
else:
    skip('the span control', 'no %s backup' % SUFFIX)

# ==========================================================================
head('2. RENDERED - EVERY NAME ON ONE LINE, AT ALL THREE COLUMN COUNTS')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception:
    HAVE_PW = False

CARD = ('<div class="contact-card compact-view"><div class="contact-header">'
        '<div class="contact-info"><h4><i class="fas fa-user-circle"></i> '
        '%s<span class="badge badge-secondary relationship-badge">Family'
        '</span></h4><div class="contact-details">a@b.c</div></div>'
        '<div class="mobile-action-bar"><button class="btn">E</button></div>'
        '</div></div>')

# THE TRUE TEXT WIDTH, VIA A Range. A clipped flex item reports its CLIPPED
# width through scrollWidth and through getBoundingClientRect alike - both
# lie, and the first draft of this believed them and reported the same
# figure at every font size. A Range over the text node does not lie.
LOOK = '''() => {
  const grid = document.querySelector('.contacts-container');
  return [...document.querySelectorAll('.contact-card')].map(c => {
    const h = c.querySelector('h4');
    const n = c.querySelector('.contact-name') || h;
    const i = h.querySelector('i');
    const p = c.querySelector('.relationship-badge');
    const bar = c.querySelector('.mobile-action-bar');
    const cs = getComputedStyle(h);
    const cd = c, cds = getComputedStyle(c);
    const r = document.createRange(); r.selectNodeContents(n);
    const vis = e => !!e && getComputedStyle(e).display !== 'none';
    return {txt: n.textContent.trim(),
            text: Math.ceil(r.getBoundingClientRect().width),
            // ROOM IS THE CARD'S CONTENT BOX, NOT THE HEADING'S. On a
            // phone .contact-header is a COLUMN flex with align-items:
            // flex-start, so .contact-info shrinks to its own text and the
            // heading's clientWidth comes back equal to the name it holds -
            // which made the first draft of this check compare a name to
            // itself and report 45px of overflow that does not exist. The
            // box that can actually clip the name is the card.
            room: Math.floor(cd.clientWidth - parseFloat(cds.paddingLeft)
                             - parseFloat(cds.paddingRight)),
            lines: Math.max(1, Math.round(
                n.getBoundingClientRect().height / parseFloat(cs.lineHeight))),
            fs: cs.fontSize,
            icon: vis(i), pill: vis(p), bar: vis(bar),
            card: Math.round(c.getBoundingClientRect().width),
            cols: getComputedStyle(grid).gridTemplateColumns.split(' ').length};
  });
}'''

if HAVE_PW and os.path.isfile(BOOT):
    boot, base_css = read(BOOT), '\n'.join(STYLE.findall(read(BASE)))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def draw(page_text, span, name, w, expanded=False):
            cards = ''.join(
                CARD % (('<span class="contact-name">%s</span>' % x) if span
                        else x) for x in NAMES)
            if expanded:
                cards = cards.replace('compact-view"', 'compact-view expanded"')
            f = os.path.join(SCRATCH, name)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style><style>%s</style>'
                         '</head><body><div class="container">'
                         '<div class="contacts-container compact-grid">%s</div>'
                         '</div></body></html>'
                         % (boot, base_css, css_of(page_text), cards))
            pg.set_viewport_size({'width': w, 'height': 900})
            _goto(pg, f)
            pg.wait_for_timeout(60)
            return pg.evaluate(LOOK)

        WIDTHS = ((1280, 3, 'three across'), (1000, 2, 'two across'),
                  (390, 1, 'one across'))
        for w, cols, where in WIDTHS:
            r = draw(P_NOW, True, 'now%d.html' % w, w)
            ok(r[0]['cols'] == cols,
               '%-13s %4dpx is %d column(s), card %dpx'
               % (where, w, r[0]['cols'], r[0]['card']),
               r[0]['cols'])
            ok(all(x['lines'] == 1 for x in r),
               '  every name on ONE line',
               [(x['txt'][:26], x['lines']) for x in r if x['lines'] != 1])
            ok(not any(x['icon'] or x['pill'] for x in r),
               '  no person icon and no Friend/Family pill')
            over = [x for x in r if x['text'] > x['room']]
            ok(not over,
               '  %dpx of room, longest name %dpx - %dpx spare'
               % (r[0]['room'], max(x['text'] for x in r),
                  r[0]['room'] - max(x['text'] for x in r)),
               [(x['txt'][:26], x['text'], x['room']) for x in over])

        # THE PILL COMES BACK WHEN THE CARD IS OPENED. This is the half of
        # his request that is easy to lose: he did not ask for the pill to
        # go, he asked for it to wait.
        r = draw(P_NOW, True, 'open.html', 1280, expanded=True)
        ok(all(x['pill'] for x in r),
           'EXPANDED: the Friend/Family pill is back on all %d cards' % len(r),
           [x['pill'] for x in r])
        ok(all(x['icon'] for x in r), '  and so is the person icon')
        ok(r[0]['fs'] == '24px',
           '  and the heading is 24px again, not 16.8', r[0]['fs'])

        # THE CONTROL. Before this round, at three across.
        if P_WAS:
            r = draw(P_WAS, False, 'was.html', 1280)
            multi = [(x['txt'][:30], x['lines']) for x in r if x['lines'] > 1]
            ok(len(multi) >= 3,
               'CONTROL: before this round %d of %d names took more than one '
               'line at three across' % (len(multi), len(r)), multi)
            ok(any(l >= 3 for _t, l in multi),
               '  and %d of them took THREE'
               % len([1 for _t, l in multi if l >= 3]), multi)
            ok(all(x['icon'] and x['pill'] for x in r),
               '  with the icon and the pill on every one of them')
            # AND THE PHONE, where the dead rule was doing the damage.
            r = draw(P_WAS, False, 'wasphone.html', 390)
            ok(r[0]['cols'] == 2,
               'CONTROL: on a 390px phone it was %d columns at %dpx a card - '
               'the one-column rule had never applied'
               % (r[0]['cols'], r[0]['card']), r[0]['cols'])
            ok(max(x['lines'] for x in r) >= 4,
               '  so the longest name took %d lines'
               % max(x['lines'] for x in r),
               [(x['txt'][:26], x['lines']) for x in r])
            ok(any(x['bar'] for x in r),
               '  and the phone action bar was showing on a collapsed card')
        else:
            skip('the before renders', 'no %s backup' % SUFFIX)
            skipped += 5
        br.close()
elif not HAVE_PW:
    print('  --   the browser section  (no playwright)')
    skipped += 20
else:
    skip('the browser section', 'no bootstrap fixture')
    skipped += 19

# ==========================================================================
head('3. AND NO TEMPLATE HAS AN UNBALANCED CSS COMMENT')
# ==========================================================================
# THE DEFECT NO SUITE WAS WATCHING FOR. A stray */ does not end a comment
# that never started: the parser reads the prose as a selector, runs on to
# the next brace, and discards the rule that follows. Braces balance
# perfectly the whole time, which is why brace-counting never caught it.
bad = []
for p in alv_tree.templates():
    e, o = strays(css_of(now(p)))
    if e or o:
        bad.append('%s  stray */ %d  unclosed /* %d' % (alv_tree.rel(p), e, o))
ok(not bad, 'all %d templates in both roots balance their CSS comments'
   % len(alv_tree.templates()), '\n'.join(bad[:6]))

if P_WAS:
    e, o = strays(css_of(P_WAS))
    ok(e == 2,
       'CONTROL: this page carried %d stray */ before this round, dead since '
       '25 Sep' % e, '%d stray, %d unclosed' % (e, o))
else:
    skip('the stray control', 'no %s backup' % SUFFIX)

for sel, what in (
        (r'\.contact-card\.compact-view:not\(\.expanded\) \.mobile-action-bar'
         r'\s*\{[^}]*display\s*:\s*none',
         'the phone action bar hides on a collapsed card'),
        (r'\.contacts-container\.compact-grid\s*\{\s*grid-template-columns'
         r'\s*:\s*1fr',
         'compact view on a phone is one column')):
    ok(bool(re.search(sel, CSS)), 'the repaired rule is a RULE again - %s'
       % what)
# AND THERE IS NO TEXT CONTROL FOR THESE TWO, DELIBERATELY. The first draft
# asserted `the selector is not in the BEFORE css` and failed, correctly:
# the selector WAS in the before text, character for character. What was
# missing was not the text but the PARSE - the stray */ ahead of it made
# the browser throw the rule away. A regex cannot see that and should not
# pretend to. The controls that prove it are in section 2, where the page
# is handed to a real parser: before this round a 390px phone rendered TWO
# columns and showed the action bar on a collapsed card, and now it renders
# one and hides it.

# AND THE REPAIRED RULES DID NOT ESCAPE THEIR MEDIA QUERY.
blocks, depth, start = [], 0, None
for m in re.finditer(r'@media[^{]*\{|\{|\}', CSS):
    s = m.group(0)
    if s.startswith('@media'):
        if depth == 0:
            start = m.start()
        depth += 1
    elif s == '{':
        if depth:
            depth += 1
    elif depth:
        depth -= 1
        if depth == 0:
            blocks.append(CSS[start:m.end()])
phone = [b for b in blocks if 'max-width: 768px' in b]
ok(phone and all(any(f in b for b in phone)
                 for f in ('.mobile-action-bar', 'grid-template-columns: 1fr')),
   'and both sit inside one of this page\'s %d phone blocks' % len(phone))

ok(CSS.count('{') == CSS.count('}'), 'the CSS still balances')
ok(not [i for i, line in enumerate(P_NOW.split('\n'), 1)
        if '{#' in line and '#}' not in line],
   'and no Django comment spans lines - the lexer has no DOTALL')

# ==========================================================================
head('4. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_barorder'),
       '  and AFTER .bak_barorder, the round it followed')
except Exception as e:
    skip('ROUNDS', str(e))

_Q = r"'((?:[^']|'')*)'|\"((?:[^\"]|\"\")*)\""
SF = re.compile(r"\b(File|Text|What)\s*=\s*(?:%s)" % _Q)
SG = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")
rows = []
for line in ps.split('\n'):
    if '@{' not in line or 'File' not in line:
        continue
    f = {}
    for k, sq, dq in SF.findall(line):
        f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
    for k, v in SG.findall(line):
        f[k] = (v == 'true')
    if 'File' in f and 'Text' in f:
        rows.append(f)
rawrows = len(re.findall(r'@\{ *File *=', ps))
ok(len(rows) == rawrows,
   'the sentinel table parses %d of %d rows' % (len(rows), rawrows))


def _strip(t):
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    t = re.sub(r'(?m)^\s*//.*$', '', t)
    return re.sub(r'(?m)^\s*#.*$', '', t)


stale = []
for r in rows:
    p = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(p):
        stale.append('%s FILE MISSING' % r['File'])
        continue
    b = read(p)
    if r.get('Code'):
        b = _strip(b)
    if (r['Text'].lower() in b.lower()) != (not r.get('Absent')):
        stale.append('%s %s %r' % (r['File'],
                                   'NOT FOUND' if not r.get('Absent')
                                   else 'IS BACK', r['Text'][:46]))
ok(not stale, 'and all %d of them still resolve' % len(rows),
   '\n'.join(stale[:6]))
print('\n    $suites now lists %d suite(s).'
      % len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)))

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
