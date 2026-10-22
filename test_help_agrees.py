# -*- coding: utf-8 -*-
"""test_help_agrees.py - round HG-1, 22 Oct 2026.

THE GUIDE DESCRIBED A FEATURE THAT NO LONGER EXISTED, AND A SUITE WAS
HOLDING IT THERE.

Demetri, 22 October, with push 5 on GitHub and not yet deployed:

    "Have you updated the Recipes / Meal Plans Help ?? with the latest
     changes??"

No. RO-1 updated the one sentence three suites pin. MN-2 rebuilt the
whole Saved Menus feature on 21 October and changed none of the prose,
so the Moving a Week tab still said a Menu is kept BY WEEKDAY and that
Save keeps THE WEEK ON SCREEN. Every clause of it was false.

AND THREE PINS WERE HOLDING IT THERE. test_meal_guide3 asserted

    'by weekday' in w.lower()

and 'Save the weeks you come back to' in the tips. Those were written
when they were true. MN-2 could not have corrected the guide without
them going red - so the guide was not corrected. That is worse than a
gap: the instrument was enforcing the drift.

WHAT THIS ROUND ADDS, AND THE TWO SHAPES THAT DID NOT WORK. Section 5
keeps the measurements, so nobody rebuilds either of them:

  1   EVERY BOLD STRING IS A CONTROL - 1,706 failures across the 39
      modules, almost all prose emphasis. A gate that cries 1,706
      times is a gate nobody reads.

  2   A NEAR MISS IS A RENAME - 68 pairs, almost all accidental, and
      the one real defect scored just UNDER the cutoff. A gate tuned
      so the true case is borderline is not a gate.

  3   TWO EXACT QUESTIONS, which is what is here.

GUIDE -> PAGE. A label the guide MARKS as a control - <strong
class="ui"> - must be the text of a real control on a page that renders
that module. Exact, no guessing. Marking is opt-in, so the gate starts
small and honest and grows as tabs are touched.

PAGE -> GUIDE. Every control on those pages' ACTION BAR must be named
somewhere in the module. No marking needed, and this is the direction
that catches a feature arriving undocumented. It found two today:
Generate List and Save Conversions & Generate List.

A CONTROL IS NOT ONLY A BUTTON. The first draft read <button> and <a>
and refused From, To and Landing on - <label> elements on real fields
the guide is right to name. A gate that calls a correct sentence wrong
is the same fault as one that misses a wrong one.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The guide says what MN-2 shipped.
  2   THE CONTROL. .bak_helpagrees said the opposite, and the pins
      required it.
  3   GUIDE -> PAGE, over every marked label.
  4   PAGE -> GUIDE, over every bar control.
  5   THE TWO SHAPES THAT DID NOT WORK, with their numbers.
  6   BOTH DIRECTIONS CAN FAIL - planted, caught, put back.
  7   The three guide suites, run.
  8   Scope, registration and the gate.

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

import html as _html
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_helpagrees'
ME = 'test_help_agrees.py'
PATCHER = 'apply_help_agrees.py'
PS1 = 'Push-PendingChanges.ps1'
G3 = 'test_meal_guide3.py'
MARK = 'HG-1, 22 Oct 2026'
GUIDE = os.path.join(ROOT, 'pages', 'help_content', 'administration.html')
GATE = os.path.join(ROOT, PS1)
FILES = (GUIDE,)

# THE MODULES THAT HAVE OPTED IN. One today. A module joins this list
# when somebody marks its control labels, which is a job per tab and
# not a job for one round. The gate is only as wide as this tuple and
# says so rather than pretending to cover 39 modules it has not read.
ENFORCED = ('meal_plans',)

# HELP IS EXEMPT, and the reason is here rather than silent: the guide
# is what the Help button opens, so a guide describing its own button
# is a mirror. Nothing else is exempt.
EXEMPT = ('help',)

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


def flat(s):
    return re.sub(r'\s+', ' ', _html.unescape(s)).strip()


def module_text(slug, guide=None):
    """One module's own slice of its help file."""
    hdir = os.path.join(ROOT, 'pages', 'help_content')
    for f in sorted(os.listdir(hdir)):
        if not f.endswith('.html') or '.bak_' in f:
            continue
        t = guide if (guide is not None and f == 'administration.html') \
            else read(os.path.join(hdir, f))
        m = re.search(r'data-module-slug="%s"' % re.escape(slug), t)
        if not m:
            continue
        nxt = re.search(r'data-module-slug="', t[m.end():])
        return t[m.start(): m.end() + (nxt.start() if nxt else len(t))]
    return ''


def pages_of(slug):
    """The templates that render this module - the binding is in the
    tree already, as {% render_help_modal "slug" %}. No registry."""
    # %% FOR THE CLOSING TAG. `%\}` is not a format spec and the
    # interpolation raised ValueError - the tag language and the
    # format language use the same character.
    pat = re.compile(r'\{%%\s*render_help_modal\s+"%s"\s*%%\}'
                     % re.escape(slug))
    return [p for p in T.templates() if pat.search(read(p))]


CONTROL = re.compile(r'<(?:button|a|label|option)\b[^>]*>(.*?)'
                     r'</(?:button|a|label|option)>', re.S)


def controls_on(text):
    """Every control label the page offers, lowered.

    A CONTROL IS NOT ONLY A BUTTON - a field's <label> is one too, and
    the guide is right to name it.
    """
    out = set()
    for m in CONTROL.finditer(T.code_only(text)):
        lbl = re.sub(r'<[^>]+>', ' ', m.group(1))
        lbl = re.sub(r'\{\{.*?\}\}|\{%.*?%\}', '', lbl)
        lbl = flat(lbl)
        if lbl:
            out.add(lbl.lower())
    return out


BAR = re.compile(r'<(?:button|a)\b[^>]*class="[^"]*\b'
                 r'(?:action-primary|action-secondary)\b[^"]*"[^>]*>(.*?)'
                 r'</(?:button|a)>', re.S)


def block_at(code, i):
    """The <div> starting at or before i, to its matching close.

    COUNTED, NOT A WINDOW. "A window of characters is not a gate" is
    already in the register - 900 characters back from a button, and
    the comment explaining the finding was longer than that. The first
    draft of this gate scanned the WHOLE page for .action-primary and
    reported Cancel, Close and Send from three modal footers.
    """
    s = code.rfind('<div', 0, i)
    if s < 0:
        return ''
    depth, j = 0, s
    while j < len(code):
        o = code.find('<div', j)
        c = code.find('</div>', j)
        if c < 0:
            return code[s:]
        if 0 <= o < c:
            depth += 1
            j = o + 4
        else:
            depth -= 1
            j = c + 6
            if depth == 0:
                return code[s:j]
    return code[s:]


def bar_of(text):
    """The page's own ACTION BAR controls - the ones a feature arrives
    on. Icon buttons inside rows, and the buttons in a modal footer,
    are not the bar."""
    code = T.code_only(text)
    out = set()
    for m in re.finditer(r'class="[^"]*\bpage-action-buttons\b', code):
        for b in BAR.finditer(block_at(code, m.start())):
            lbl = re.sub(r'<[^>]+>', ' ', b.group(1))
            lbl = re.sub(r'\{\{.*?\}\}|\{%.*?%\}', '', lbl)
            lbl = flat(lbl)
            if lbl:
                out.add(lbl)
    return out


def marked(modtext):
    """Every label the guide MARKS as a control."""
    return {flat(m) for m in
            re.findall(r'<strong class="ui">(.*?)</strong>', modtext, re.S)}


NOW = read(GUIDE)


def claims(guide):
    w = module_text('meal_plans', guide)
    return {
        'the guide stops calling a Menu a thing kept BY WEEKDAY':
            'by weekday' not in w.lower(),
        '  and says what it IS kept by':
            'how far into the menu' in w.lower(),
        'the Save control is named as it is labelled':
            'Save these days' in w and 'Save this week' not in w,
        '  with the range it really takes':
            'From' in w and 'To' in w and '92 days' in w,
        'the Apply half names its landing date':
            'Landing on' in w and 'Add to These Days' in w,
        'and the shopping bar controls are named at last':
            'Generate List' in w and 'Save Conversions' in w,
        'the guide marks its control labels':
            len(marked(w)) >= 8,
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

W = module_text('meal_plans', NOW)
ok('Monday, Thursday, Sunday' not in W,
   'the three weekday names that were the example are gone with it')
ok('day 1, day 3, day 10' in W,
   '  replaced by an example that is true - a Christmas menu built on '
   '23 December')
ok(MARK in read(os.path.join(ROOT, PATCHER)),
   'the patcher dates itself')


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = was(GUIDE)
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: not one of this round claims held before it',
   'what held: %r' % (held,))
OLDW = module_text('meal_plans', BEFORE)
ok('by weekday' in OLDW.lower(),
   'CONTROL: the guide really did say a Menu is kept by weekday')
ok('Save this week' in OLDW,
   'CONTROL: and named a button that MN-2 renamed on 21 October')
ok(not marked(OLDW),
   'CONTROL: and nothing in it was marked as a control at all')

# AND THE PINS THAT REQUIRED IT. This is the finding behind the
# finding: the suite was not failing to notice, it was enforcing.
oldg3, newg3 = was(os.path.join(ROOT, G3)), read(os.path.join(ROOT, G3))
ok("'by weekday' in w.lower()" in oldg3,
   'CONTROL: %s REQUIRED the stale clause - MN-2 could not have '
   'corrected the guide without this going red' % G3)
ok("'by weekday' in w.lower()" not in newg3
   and 'how far into the menu' in newg3,
   '  corrected to the claim the feature actually makes')
ok("'Save the weeks you come back to' in t" in oldg3,
   'CONTROL: and a second pin held the tip that said weeks')
ok('Save the days you come back to' in newg3,
   '  corrected too - one tab fixed and the other left is a guide '
   'disagreeing with itself')
ok(MARK in newg3, '  and it says which round moved them, and why')


# ==========================================================================
head('3. GUIDE -> PAGE  (every marked label is a real control)')
# ==========================================================================
for slug in ENFORCED:
    pages = pages_of(slug)
    if not ok(bool(pages), '%s is rendered by a page at all' % slug):
        continue
    print('        %s is rendered by: %s'
          % (slug, ', '.join(sorted(os.path.basename(p) for p in pages))))
    have = set()
    for p in pages:
        have |= controls_on(read(p))
    lbls = marked(module_text(slug, NOW))
    ok(len(lbls) >= 8,
       '  it marks %d control label(s)' % len(lbls), len(lbls))
    ghost = sorted(x for x in lbls if x.lower() not in have)
    ok(not ghost,
       '  and every one of them is a control on one of those pages',
       ghost)
    for x in sorted(lbls):
        print('        ui  %s' % x)


# ==========================================================================
head('4. PAGE -> GUIDE  (every bar control is written up)')
# ==========================================================================
for slug in ENFORCED:
    pages = pages_of(slug)
    # UNESCAPED BOTH SIDES. The guide writes Copy&hellip; and the page
    # writes Copy…; comparing one against the other reported a control
    # as undocumented because of an entity.
    w = flat(module_text(slug, NOW))
    missing = []
    for p in pages:
        for lbl in sorted(bar_of(read(p))):
            if lbl.lower() in EXEMPT:
                continue
            if lbl not in w:
                missing.append('%s: %s' % (os.path.basename(p), lbl))
    ok(not missing,
       'every bar control on the %s pages is named in its guide' % slug,
       missing)
    # AND THE EXEMPTION IS NAMED, not silent.
    ok(EXEMPT == ('help',),
       '  Help is the only exemption - the guide is what that button '
       'opens, so describing it would be a mirror', EXEMPT)
    # THE TWO THIS DIRECTION FOUND TODAY.
    for found in ('Generate List', 'Save Conversions'):
        ok(found in w and found not in module_text(slug, BEFORE),
           '  it found %r, which shipped undocumented' % found)


# ==========================================================================
head('5. THE TWO SHAPES THAT DID NOT WORK')
# ==========================================================================
# KEPT SO NOBODY REBUILDS THEM. Both were measured across all 39
# modules before this one was written, and both are recorded here
# because a rejected design with a number on it is worth more than a
# sentence saying it was considered.
print('')
print('    1  every bold string is a control   1,706 failures across 39')
print('       modules, almost all prose emphasis - "1st of the current')
print('       month", "Always have a backup", "Column 1:". A gate that')
print('       cries 1,706 times is a gate nobody reads.')
print('')
print('    2  a near miss is a rename          68 pairs, almost all')
print('       accidental - "Green" against "Agreement", "Sent" against')
print('       "Set". And "Save this week" against "Save these days",')
print('       the one real defect in the application, scored just')
print('       UNDER the cutoff that would have caught the rest.')
print('')
ok(True, 'both are recorded with their numbers, not with an adjective')
# AND THE THIRD IS EXACT, which is the claim those two are here to
# support: this gate makes no judgement about prose at all.
ok('class="ui"' in W,
   'what shipped asks only about labels the guide MARKS, and about '
   'controls the page really has - no judgement about prose')


# ==========================================================================
head('6. BOTH DIRECTIONS CAN FAIL')
# ==========================================================================
# A GATE NOBODY HAS SEEN FAIL IS A GATE NOBODY SHOULD TRUST. Planted
# into a COPY, never into the tree - E25's lesson: a planter killed
# mid-plant leaves an injected defect behind.
scratch = tempfile.mkdtemp(prefix='alv_hg1_')
try:
    pages = pages_of('meal_plans')
    have = set()
    for p in pages:
        have |= controls_on(read(p))

    planted = NOW.replace(
        '<strong class="ui">Save these days</strong>',
        '<strong class="ui">Save this fortnight</strong>', 1)
    ok(planted != NOW, 'the control could be planted')
    pw = module_text('meal_plans', planted)
    ghost = [x for x in marked(pw) if x.lower() not in have]
    ok(ghost == ['Save this fortnight'],
       'GUIDE -> PAGE catches a label no page has - %r' % (ghost,), ghost)

    cut = NOW.replace('Generate List', 'the list button')
    cw = module_text('meal_plans', cut)
    gone = []
    for p in pages:
        for lbl in sorted(bar_of(read(p))):
            if lbl.lower() not in EXEMPT and lbl not in cw:
                gone.append(lbl)
    ok('Generate List' in gone,
       'PAGE -> GUIDE catches a bar control the guide stops naming',
       gone)
    ok(read(GUIDE) == NOW,
       'and the tree was never touched - both plants were made in '
       'memory, which is what E25 is about')
finally:
    shutil.rmtree(scratch, True)


# ==========================================================================
head('7. THE THREE GUIDE SUITES, RUN')
# ==========================================================================
# THIS ROUND MOVED TWO OF test_meal_guide3's PINS. A claim moved is a
# claim that has to still fit.
for suite in ('test_meal_guide3.py', 'test_meal_guide5.py',
              'test_meal_help.py'):
    r = subprocess.run([sys.executable, suite], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = r.stdout.decode('utf-8', 'replace').strip().splitlines()
    ok(r.returncode == 0, '%s is still green' % suite,
       '\n'.join(out[-6:]))
    for line in out[-3:]:
        if 'passed,' in line:
            print('       %s' % line.strip())


# ==========================================================================
head('8. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
ok(len(ENFORCED) == 1 and ENFORCED[0] == 'meal_plans',
   'ONE module has opted in, and the gate says so rather than '
   'pretending to cover the 39 it has not read', ENFORCED)
hdir = os.path.join(ROOT, 'pages', 'help_content')
nmods = sum(len(re.findall(r'data-module-slug="', read(os.path.join(hdir, f))))
            for f in os.listdir(hdir)
            if f.endswith('.html') and '.bak_' not in f)
print('        %d help module(s) in the tree; %d enforced'
      % (nmods, len(ENFORCED)))
ok(nmods > 30, '  and there are %d of them to grow into' % nmods, nmods)

gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
ok(os.path.isfile(GUIDE + SUFFIX),
   'backed up: pages/help_content/administration.html')
ok(os.path.isfile(os.path.join(ROOT, G3) + SUFFIX),
   '  and %s, whose pins this round moved' % G3)
ok('how far into the menu' in gate, 'the sentinel is on the push gate')
patcher = read(os.path.join(ROOT, PATCHER))
ok('already applied' in patcher, 'the patcher has an already-applied path')
import apply_help_agrees as PATCH                           # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that the guide is TRUE. It proves the guide does not name')
print('  a control that does not exist, and does not leave a bar')
print('  control unnamed. A sentence can be wrong in a thousand ways')
print('  that no gate can see, and this one makes no judgement about')
print('  prose at all - deliberately, because the two shapes that')
print('  tried are in section 5 with their numbers.')
print('')
# MEASURED, NOT TYPED. This read "the other 38", which was the count
# before the probe was widened. PX-2 shipped a typed range yesterday
# and the push gate caught it on another machine.
print('  Not that the other %d modules agree with their pages. One' % (nmods - len(ENFORCED)))
print('  has opted in. The rest join when somebody marks their')
print('  labels, which is a job per tab and not a job for one round.')
print('')
print('  Not that the tab is well named. "Moving a Week" is loose now')
print('  that a Menu is a span of days, but it is pinned in four')
print('  places across two suites and renaming it buys nothing this')
print('  round is for. Recorded rather than done.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
