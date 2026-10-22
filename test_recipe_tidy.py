# -*- coding: utf-8 -*-
"""test_recipe_tidy.py - round VR-1, 21 Oct 2026.

THE ROUND WAS PLANNED AS ONE THING AND THE TREE SAID IT WAS ANOTHER.

WHAT WAS WRITTEN DOWN, two days ago: "view_recipe's remaining 2 tables
onto .alv-table; decide out loud whether recipe_pdf stays bespoke."

WHAT IS ACTUALLY THERE. Three tables. The nutrition breakdown already
wears `table alv-table breakdown-table`. The other two are the COOKING
SCHEDULE readout inside its dialog and the hidden copy that dialog
prints, and NEITHER IS A DATA TABLE: a label on the left, a time on the
right, six rows, no header, no sort, no column meaning beyond what and
when.

.alv-table IS FOR LISTS YOU READ DOWN, with a header row. Dressing a
key-and-value readout as one would leave the next reader working out
why the schedule has headings it never uses. So they stay, and the
round says so where they live rather than leaving the question open for
a third time. Section 1 holds both of them to being readouts.

WHAT WAS GENUINELY OFF-STANDARD, and it was three colour literals, all
in the dialog's half - the printed copy was already tokenised. Section
3 measures each substitution in CIE Lab rather than asserting it:

    a 7 per cent black hairline -> var(--alv-line)       dE  1.75
    a slate heading             -> var(--alv-ink)        dE  8.31
    a hot pink icon             -> var(--alv-spice-ink)  dE 45.73

The first is below 2.0, the just-detectable threshold, so it is
invisible and should always have been the token. The last is the big
one and the plainest: the two OTHER icons on this page already wear
var(--alv-warn-ink) and var(--alv-spice-ink), and this was a pink that
belonged to nothing.

recipe_pdf STAYS BESPOKE. It has no base.html, no stylesheet and no
tokens - a var() there has nothing to resolve against. Asked and
answered, in writing.

THE EMOJI STAY. Both readouts label their rows with a flame, a steak, a
knife and a tick while the rest of the application uses Font Awesome.
That is a real inconsistency and it is not this round's: changing five
labels on a screen in daily use is a visible change nobody asked for.
Written down rather than done, and section 4 holds the round to having
left them alone.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. Three tables, one on .alv-table, two readouts that
      say why they are not - and no colour literal left in either.

  2   THE CONTROL. Re-asked of .bak_recipetidy, where the dialog's
      half carried three.

  3   THE NUMBERS. Every substitution measured against the whole
      palette, so the next round proposing one inherits a
      measurement rather than a sentence.

  4   WHAT WAS DELIBERATELY NOT DONE, held to.

  5   Scope, registration and the gate.

RUN IT AGAINST THE REVERTED TREE AND IT MUST FAIL, NOT CRASH.
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

import math
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_recipetidy'
ME = 'test_recipe_tidy.py'
PATCHER = 'apply_recipe_tidy.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'VR-1, 21 Oct 2026'
VISIBLE = 2.0

TPL = os.path.join(ROOT, 'pages', 'templates', 'view_recipe.html')
PDF = os.path.join(ROOT, 'pages', 'templates', 'recipe_pdf.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
GATE = os.path.join(ROOT, PS1)
FILES = (TPL,)

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
    with open(p, encoding='utf-8', errors='replace') as f:
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

NOW = read(TPL)
BASETXT = read(BASE)
TOKENS = dict(re.findall(r'(--alv-[a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{3,6})\s*;',
                         BASETXT))


def _rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lab(h):
    r, g, b = [v / 255.0 for v in (_rgb(h) if isinstance(h, str) else h)]

    def f(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = f(r), f(g), f(b)
    X = r * 0.4124 + g * 0.3576 + b * 0.1805
    Y = r * 0.2126 + g * 0.7152 + b * 0.0722
    Z = r * 0.0193 + g * 0.1192 + b * 0.9505

    def g2(t):
        return t ** (1 / 3.0) if t > 0.008856 else 7.787 * t + 16 / 116.0
    fx, fy, fz = g2(X / 0.95047), g2(Y / 1.0), g2(Z / 1.08883)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def dE(a, b):
    """CIE76. Crude next to dE2000 and ample for 'can I see this move'."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(_lab(a), _lab(b))))


def readout(text, which):
    """One of the two key-and-value tables, markup only.

    .find(), not .index(): against the reverted tree both anchors
    exist, but a round that moved one would otherwise crash this suite
    instead of failing it.
    """
    code = T.code_only(text)
    i = code.find(which)
    if i < 0:
        return ''
    j = code.find('</table>', i)
    return code[i:j + 8] if j > i else code[i:]


def claims(text):
    code = T.code_only(text)
    sched = readout(text, 'id="modal_schedule"')
    return {
        'the schedule readout carries NO colour literal':
            not re.search(r'#[0-9a-fA-F]{3,6}\b|rgba\(', sched),
        '  its hairline is the house line token':
            'var(--alv-line)' in sched,
        '  its heading is the house ink':
            'var(--alv-ink)' in sched,
        '  and its icon wears the same ink its two siblings on this '
        'page wear':
            'var(--alv-spice-ink)' in sched,
        'the page says IN WRITING that these two are not data tables':
            'NOT A DATA TABLE' in text,
        '  and dates the round that said so':
            MARK in text,
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

CODE = T.code_only(NOW)
SCHED = readout(NOW, 'id="modal_schedule"')
PRINTED = readout(NOW, 'id="cookingSchedulePrintArea"')

ok(CODE.count('<table') == 3,
   'the page still has three tables', CODE.count('<table'))
ok(CODE.count('alv-table') == 1,
   '  and exactly ONE of them is on .alv-table - the nutrition '
   'breakdown, which really is a list you read down',
   CODE.count('alv-table'))

# THE TWO READOUTS ARE STILL READOUTS. A round that answered "not a
# data table" by quietly making one would be answering a different
# question than the one it asked.
for name, body in (('the dialog', SCHED), ('the printed copy', PRINTED)):
    if not ok(bool(body), '%s readout is on the page' % name):
        continue
    ok('<th' not in body,
       '  %s has no header row - which is what makes it a readout and '
       'not a table' % name)
    ok('alv-table' not in body,
       '  and it is NOT on .alv-table' % ())
    ok(body.count('<tr') >= 4,
       '  %s is a real list of rows, not a one-off' % name,
       body.count('<tr'))

# THE PRINTED COPY WAS ALREADY RIGHT, and still is.
ok(not re.search(r'#[0-9a-fA-F]{3,6}\b', PRINTED),
   'the printed copy carries no colour literal - it never did, and '
   'this round did not give it one')
ok('var(--alv-line)' in PRINTED,
   '  it was already using the house line token')

# GUARDS. True before and after, so not in claims().
ok('breakdown-table' in CODE,
   'GUARD: the nutrition breakdown keeps its own class as well as the '
   'house one')
ok('printCookingSchedule()' in NOW,
   'GUARD: the schedule can still be printed')
ok(NOW.count('{%') == NOW.count('%}'),
   'GUARD: the template tags balance - %d {%% against %d %%}'
   % (NOW.count('{%'), NOW.count('%}')))


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = was(TPL)
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: not one of this round claims held before it',
   'what held: %r' % (held,))

OLDSCHED = readout(BEFORE, 'id="modal_schedule"')
ok(bool(OLDSCHED), 'CONTROL: the readout was there before the round')
olds = set(re.findall(r'#[0-9a-fA-F]{3,6}\b', OLDSCHED))
ok(olds == {'#2c3e50', '#f5576c'},
   'CONTROL: it carried exactly two hex literals, and they are the two '
   'this round measured', sorted(olds))
ok('rgba(0,0,0,0.07)' in OLDSCHED,
   'CONTROL: and a hand-mixed hairline that no token owned')
ok(BEFORE.count('rgba(0,0,0,0.07)') == 4,
   'CONTROL: four times over, in the one table',
   BEFORE.count('rgba(0,0,0,0.07)'))
ok('NOT A DATA TABLE' not in BEFORE,
   'CONTROL: and nothing on the page said why these two are not data '
   'tables - which is why the question came round twice')
OLDPRINT = readout(BEFORE, 'id="cookingSchedulePrintArea"')
ok(not re.search(r'#[0-9a-fA-F]{3,6}\b', OLDPRINT),
   'CONTROL: the PRINTED copy was already clean - the drift was all in '
   'one half, which is worth knowing')


# ==========================================================================
head('3. THE NUMBERS - EVERY SUBSTITUTION MEASURED')
# ==========================================================================
# A ROUND THAT MOVES A COLOUR MEASURES THE MOVE. dE under about 2.0 is
# the threshold a trained eye can just detect, so a swap below it is
# invisible and a swap above it is a decision somebody has to agree to.
for need in ('--alv-line', '--alv-ink', '--alv-spice-ink',
             '--alv-surface', '--alv-warn-ink'):
    ok(need in TOKENS, 'base.html defines %s' % need)

# The hairline is 7 per cent black over the panel, so what it PAINTS is
# that composite - which is the thing --alv-line has to be compared
# with. Comparing the token with pure black would be measuring the
# wrong pair and would have said 90.
surf = _rgb(TOKENS['--alv-surface'])
hair = '#%02x%02x%02x' % tuple(int(round(c * 0.93)) for c in surf)
d_hair = dE(hair, TOKENS['--alv-line'])
d_head = dE('#2c3e50', TOKENS['--alv-ink'])
d_icon = dE('#f5576c', TOKENS['--alv-spice-ink'])

print('')
print('    what moved              from       to                     dE')
print('    ' + '-' * 60)
print('    row hairline            %-10s %-22s %5.2f'
      % (hair + '*', 'var(--alv-line)', d_hair))
print('    Cooking Schedule head   %-10s %-22s %5.2f'
      % ('#2c3e50', 'var(--alv-ink)', d_head))
print('    its calendar icon       %-10s %-22s %5.2f'
      % ('#f5576c', 'var(--alv-spice-ink)', d_icon))
print('    * the composite a 7 per cent black paints over the panel')
print('')

ok(d_hair < VISIBLE,
   'the hairline swap is INVISIBLE - dE %.2f, under the %.1f a trained '
   'eye can just detect' % (d_hair, VISIBLE), d_hair)
ok(d_head > VISIBLE,
   'the heading swap IS visible - dE %.2f - and it is a heading joining '
   'the cells below it, which already use tokens' % d_head, d_head)
ok(d_icon > 20,
   'the icon swap is the big one - dE %.2f - and the plainest: a hot '
   'pink that belonged to no token' % d_icon, d_icon)

# AND THE ICON NOW MATCHES ITS SIBLINGS. That is the argument for the
# 45.73, so it is asked rather than asserted.
icons = re.findall(r'<i class="fas fa-[a-z-]+"[^>]*style="color:\s*([^";]+)',
                   CODE)
ok(icons and all(i.strip().startswith('var(--alv-') for i in icons),
   'every icon colour on this page is a token now - %r'
   % ([i.strip() for i in icons],), icons)
ok('var(--alv-spice-ink)' in [i.strip() for i in icons]
   and 'var(--alv-warn-ink)' in [i.strip() for i in icons],
   '  and the schedule icon wears the ink a sibling on the same page '
   'already wore', [i.strip() for i in icons])

# NOTHING ELSE ON THE PAGE MOVED. This round touched one table.
oldlits = sorted(re.findall(r'#[0-9a-fA-F]{3,6}\b', T.code_only(BEFORE)))
newlits = sorted(re.findall(r'#[0-9a-fA-F]{3,6}\b', CODE))
ok(len(oldlits) - len(newlits) == 2,
   'exactly TWO hex literals left the page - %d before, %d after. This '
   'round is one table, not a sweep' % (len(oldlits), len(newlits)),
   (len(oldlits), len(newlits)))


# ==========================================================================
head('4. WHAT WAS DELIBERATELY NOT DONE')
# ==========================================================================
# A ROUND THAT DECIDES NOT TO DO SOMETHING HAS TO BE HELD TO IT, or
# "we decided not to" and "we forgot" look identical a week later.
EMOJI = re.compile('[\U0001F300-\U0001FAFF☀-➿✅]')
ok(len(EMOJI.findall(SCHED)) == len(EMOJI.findall(OLDSCHED)),
   'the emoji labels are UNTOUCHED - %d before, %d after. They are an '
   'inconsistency with Font Awesome and not this round'
   % (len(EMOJI.findall(OLDSCHED)), len(EMOJI.findall(SCHED))))
ok(len(EMOJI.findall(PRINTED)) == len(EMOJI.findall(OLDPRINT)),
   '  on the printed copy too',
   (len(EMOJI.findall(OLDPRINT)), len(EMOJI.findall(PRINTED))))
ok(not os.path.isfile(PDF + SUFFIX),
   'recipe_pdf.html is UNTOUCHED - it has no base, no stylesheet and '
   'no tokens, so a var() there resolves to nothing')
ok(os.path.isfile(PDF),
   '  and it is still on disk, which is the other half of leaving it '
   'alone')
patcher = read(os.path.join(ROOT, PATCHER))
ok('stays bespoke' in patcher,
   '  and the round says why, so the question stops coming round')
ok('Written down rather than done' in patcher,
   'the emoji decision is written down as a decision, not left to look '
   'like an oversight')


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
touched = [p for p in T.templates() if os.path.isfile(p + SUFFIX)]
ok([os.path.basename(p) for p in touched] == ['view_recipe.html'],
   'ONE template was touched', [os.path.basename(p) for p in touched])

gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
ok(os.path.isfile(TPL + SUFFIX),
   'backed up: pages/templates/view_recipe.html')
ok('NOT A DATA TABLE' in gate, 'the sentinel is on the push gate')
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_recipe_tidy as PATCH                           # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that view_recipe is clean. %d hex literals are still in'
      % len(newlits))
print('  its markup, in panels this round did not open. It took one')
print('  table because that is what was planned; the rest is a sweep')
print('  and a sweep is its own round.')
print('')
print('  Not that the emoji are right. They are a real inconsistency')
print('  with the Font Awesome the rest of the system uses, left')
print('  alone on purpose and recorded so nobody has to guess which.')
print('')
print('  Not that the schedule readout is well laid out. It is a')
print('  wall of inline style on a dialog nobody has looked at since')
print('  it was written. This round moved three colours into tokens;')
print('  it did not redesign anything.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
