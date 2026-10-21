# -*- coding: utf-8 -*-
"""test_say_today.py - round SC-1, 21 Oct 2026.

TODAY, NOT TONIGHT - AND TWO SHORTCUTS, NOT THREE.

Demetri, testing AP-1 on Live:

    "On the Recipe Management, Add from Recipe Libraries, at the top,
     Tonight should be Today. Then let's remove This Saturday - it
     doesn't really add value."

THE LABEL AND THE VALUE DISAGREED. The button read "Tonight" and its
data-plan-when was `today`. There are no meal types in this module -
his decision, 19 October - so the planner does not know morning from
evening and a label that implies it is a label the model cannot back.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. Two shortcuts, the first says Today, and when()
      has a branch for each one that is left.

  2   THE CONTROL. Re-asked of the pre-round file, where there were
      three and the first said Tonight.

  3   DRIVEN. The popover opened in a real browser: the buttons that
      are really there, and the date each one really computes.

  4   Scope, registration and the gate.

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

import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_saytoday'
ME = 'test_say_today.py'
PATCHER = 'apply_say_today.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'SC-1, 21 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates', 'recipe_management.html')
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

NOW = dict((p, read(p)) for p in FILES)

QUICK = re.compile(r'<button[^>]*class="plan-quick"[^>]*'
                   r'data-plan-when="([a-z]+)"[^>]*>([^<]*)</button>')


def claims(bundle):
    code = T.code_only(bundle[TPL])
    found = QUICK.findall(code)
    codes = [c for c, _ in found]
    labels = [l.strip() for _, l in found]
    c = {}
    c['THE FIRST SHORTCUT SAYS TODAY - the finding'] = (
        bool(labels) and labels[0] == 'Today')
    c['  and nothing on the row says Tonight'] = (
        'Tonight' not in labels)
    c['TWO SHORTCUTS, NOT THREE'] = (len(found) == 2)
    c['  today and tomorrow, in that order'] = (
        codes == ['today', 'tomorrow'])
    c['  and the third button is gone'] = ('saturday' not in codes)
    # THE BRANCH, NOT THE WORD. The comment above when() names the
    # day it removed, deliberately, so a check for the word would
    # fail against the correct file - the patcher's own gate did
    # exactly that before it was made structural.
    c['  and when() has no branch for it either'] = (
        not re.search(r"code\s*===\s*'saturday'", code))
    # NOT HERE: "tomorrow still has a branch". True before this round
    # and after it, so asked as a delta it fails the control for being
    # right. It is section 1's, below, where an unchanging claim
    # belongs - and it still has to hold, because a round that removed
    # the wrong branch would satisfy everything above.
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

# EVERY BUTTON ON THE ROW HAS A BRANCH, AND EVERY BRANCH A BUTTON.
# This is the claim that keeps the two halves in step whatever the
# next round does to them - a shortcut with no arithmetic adds today,
# silently, and arithmetic with no button is dead.
code = T.code_only(NOW[TPL])
ok(bool(re.search(r"code\s*===\s*'tomorrow'", code)),
   'and tomorrow still has its branch - the round removed one, not two')
btns = set(QUICK.findall(code) and [c for c, _ in QUICK.findall(code)])
brs = set(re.findall(r"code\s*===\s*'([a-z]+)'", code))
# `today` needs no branch - it is the unmodified date when() starts from.
ok(brs | {'today'} == btns,
   'every shortcut has a branch and every branch a button',
   'buttons %r  branches %r' % (sorted(btns), sorted(brs)))


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = {TPL: was(TPL)}
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: before this round not one of these claims held',
   'what held: %r' % (held,))
oldcode = T.code_only(BEFORE[TPL])
old = QUICK.findall(oldcode)
ok(len(old) == 3, 'CONTROL: there really were three shortcuts', len(old))
ok(old and old[0][1].strip() == 'Tonight',
   'CONTROL: and the first really said Tonight',
   old[0][1] if old else '?')
ok(bool(re.search(r"code\s*===\s*'saturday'", oldcode)),
   'CONTROL: and when() really had a branch computing it')


# ==========================================================================
head('3. DRIVEN - THE POPOVER, OPENED')
# ==========================================================================
# WHAT THE SOURCE CANNOT SAY: which buttons a browser actually draws,
# and what date each one resolves to. The dates are arithmetic on
# `new Date()`, so they are asked of the engine rather than retyped.
import datetime as _dt                                      # noqa: E402
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if sync_playwright is None:
    skip('the popover', 'playwright is absent')
else:
    body = NOW[TPL]
    # class="plan-pop-quick", NOT plan-pop-quick. The first draft
    # searched for the bare name and found the CSS RULE 14k characters
    # earlier in the <style> block, so the slice ran from a selector to
    # a closing tag that was nowhere near it and came out empty - and
    # an empty slice skips this section, which reads like a pass.
    # A selector that names a class is not an element wearing it.
    i = body.find('class="plan-pop-quick"')
    j = body.find('</div>', i)
    row = body[body.rfind('<div', 0, i):j + 6] if i > 0 else ''
    row = re.sub(r'\{#.*?#\}', '', row, flags=re.S)
    js = ''
    # BRACE-COUNTED, not indentation-matched. The first draft keyed
    # on '\n    }' and found nothing the moment the body was reindented
    # by one space - a skipped section that reads like a passing one.
    k = body.find('function when(code)')
    if k >= 0:
        depth, end = 0, -1
        for n in range(body.index('{', k), len(body)):
            if body[n] == '{':
                depth += 1
            elif body[n] == '}':
                depth -= 1
                if depth == 0:
                    end = n + 1
                    break
        js = body[k:end] if end > 0 else ''
    if not row or not js:
        skip('the popover', 'could not isolate the row or when()')
    else:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page()
            pg.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg.set_content('<body>%s<script>%s</script>' % (row, js),
                           wait_until='domcontentloaded')
            seen = pg.evaluate(
                """() => [...document.querySelectorAll('.plan-quick')]
                     .map(b => [b.getAttribute('data-plan-when'),
                                b.textContent.trim(),
                                Math.round(b.getBoundingClientRect().height)])""")
            dates = pg.evaluate(
                """(codes) => codes.map(c => {
                       const d = when(c);
                       return d.getFullYear() + '-' +
                              String(d.getMonth()+1).padStart(2,'0') + '-' +
                              String(d.getDate()).padStart(2,'0');
                   })""", [s[0] for s in seen])
            br.close()
        print('')
        for (cd, lab, h), dte in zip(seen, dates):
            print('  %-9s %-10s %3dpx  ->  %s' % (cd, lab, h, dte))
        print('')
        ok(len(seen) == 2, 'the browser draws two shortcuts', len(seen))
        ok([s[1] for s in seen] == ['Today', 'Tomorrow'],
           'labelled Today and Tomorrow', [s[1] for s in seen])
        today = _dt.date.today()
        ok(dates and dates[0] == today.isoformat(),
           'and Today really resolves to today', (dates[:1], today))
        ok(len(dates) > 1
           and dates[1] == (today + _dt.timedelta(days=1)).isoformat(),
           '  and Tomorrow to tomorrow', dates[1:2])
        # A LABEL THAT AGREES WITH ITS VALUE, which is the finding
        # stated as a measurement rather than as a word.
        ok(dates and dates[0] == today.isoformat()
           and seen[0][1] == 'Today',
           'THE LABEL AND THE DATE AGREE - which is what "Tonight" '
           'could not claim')


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
# THE PIN AP-1 LEFT, MOVED IN THE SAME PATCHER. test_add_planner
# counts the shortcuts; there are two now.
ap = read(os.path.join(ROOT, 'test_add_planner.py'))
ok(MARK in ap,
   'test_add_planner carries this round reason for counting two')
ok("the two shortcuts are there" in ap and "'saturday'" not in ap,
   '  and it counts two, not three')
ok(os.path.isfile(os.path.join(ROOT, 'test_add_planner.py') + SUFFIX),
   '  and it is backed up')

patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_say_today as PATCH                             # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
