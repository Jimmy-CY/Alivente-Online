# -*- coding: utf-8 -*-
"""test_grey_tail.py - Section B round B-5b, 8 Oct 2026.

THE 81 WAS NOT ONE JOB, AND THAT IS THE CLAIM THIS SUITE DEFENDS.

B-5a left a tail it described as "tier C, 81 uses: #adb5bd at 56 RGB
units, #ced4da at 33". A true sentence about distance and a useless one
about the work. Read, the 81 are five different things:

    19  muted text        2.07:1 at 11-14px. Below AA, and not narrowly.
    12  .empty-state i    the SAME selector, TWO different greys.
     6  disabled          low contrast is the signal.
    19  #ced4da borders   every neutral line token is LIGHTER.
    ..  chevrons, a drag handle, hover border-colours, 8 standalone.

This round takes two of them - 22 conversions - and section 5 proves the
other 59 are still there, by name. **A round that leaves something has
to be able to say what.**

=====================================================================
SECTION 3 IS THE POINT: --alv-ink-soft IS NOT A NEW DECISION
=====================================================================

At 11-12px AA is 4.5:1 - the 3:1 allowance starts at 18.66px bold.

    #adb5bd                2.07 on paper, 1.97 on surface
    var(--alv-ink-faint)   3.00 / 2.85   better, still fails
    var(--alv-ink-soft)    5.53 / 5.25   clears it

B-2 ALREADY CHOSE THIS TOKEN FOR THIS JOB on 6 Oct: its own table calls
#6c757d "muted and small text" and moves it to --alv-ink-soft, 4.69 to
5.53. These 18 are the stragglers of that decision - the same job in a
lighter grey, 133 units away where B-2\'s ceiling was 25. Section 3
asserts the after-value clears AA on BOTH grounds, and the control
asserts the before-value cleared neither.

=====================================================================
SECTION 4: A WATERMARK IN TWO COLOURS
=====================================================================

Twelve pages carry `.empty-state i`. TEN drew it #dee2e6 and TWO
#adb5bd; two more pages draw the same idea under their own names. No
contrast ratio applies to a watermark - the only thing wrong was that it
was two colours, and section 4 asserts it is now one.

IT STAYS A LITERAL, DELIBERATELY. The house has no token for a
watermark; the nearest is --alv-line at 8.8 units, which is a LINE token
used as ink - the exact mis-mapping B-5a\'s note warns about. Inventing
--alv-ink-ghost is a base change, so WIDE, so a full sweep for one
glyph. Section 4 asserts the gap is written down instead of invented.

=====================================================================
SECTION 6: TWO THINGS THE CLASSIFIER GOT WRONG
=====================================================================

Both found by reading the rule rather than the name:

  .drag-handle is font-size: 22px under a comment reading "Drag handle -
  bigger touch target". A grip glyph, not a sentence. The decorative
  test looked for icon, chevron, thumb and placeholder and never thought
  of a handle.

  .month-chip-no is the judgement call, and it is IN. A twelve-across
  strip of month labels at 11px uppercase: the months that apply are
  8.57:1, the ones that do not were 2.07. You have to read JAN FEB MAR
  to know which are off, so it is information, not a disabled control.
  The fill and border are untouched, so only the month names change.
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
TPL = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(TPL):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)

SUFFIX = '.bak_greytail'
ME = 'test_grey_tail.py'
PATCHER = 'apply_grey_tail.py'
PS1 = 'Push-PendingChanges.ps1'

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
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_rounds as RD                                    # noqa: E402
import alv_tree as T                                       # noqa: E402
import alv_cssrules as R                                   # noqa: E402
import apply_grey_tail as P                                # noqa: E402
import apply_neutrals as N      # rgb / lum / contrast     # noqa: E402

PAPER = '#ffffff'
SURFACE = '#f8f9fa'
AA = 4.5
OLD = '#adb5bd'


def left(p):
    return RD.as_left_by(p, SUFFIX, read)


def was(p):
    b = p + SUFFIX
    return read(b) if os.path.isfile(b) else None


def bodies_of(txt, selector):
    """EVERY declaration body whose selector ends in this one.

    The first cut of this returned the FIRST match, and preview_imported
    _recipe.html declares .drag-handle three times - desktop, :hover, and
    a phone override. The check read the desktop rule, found no literal,
    and failed a claim about a rule it had never looked at. A reader that
    sees one of three is a reader that gives a wrong answer quietly.
    """
    code = T.code_only(txt)
    out = []
    for sa, sb in R.style_spans(code):
        seen = set()
        for sel, ba, bb, _ra, _rb in R.rule_spans(code, sa, sb):
            if (ba, bb) in seen:
                continue
            seen.add((ba, bb))
            if ' '.join(sel.split('&&')[-1].split()) == selector:
                out.append(code[ba:bb])
    return out


def body_of(txt, selector):
    """The ONE body carrying this round's literal or its replacement,
    else the first. Callers that care about a specific rule say so."""
    bs = bodies_of(txt, selector)
    for b in bs:
        if OLD in b or INK_SOFT in b or 'var(--alv-ink-soft)' in b \
                or P.GHOST in b:
            return b
    return bs[0] if bs else ''


TOKENS = N.base_tokens()
INK_SOFT = TOKENS.get('--alv-ink-soft', '#5b6b73').strip()


# ==========================================================================
head('1. THE 22 CONVERSIONS, EACH ONE NAMED')
# ==========================================================================
ok(len(P.CSS_TARGETS) == 21 and len(P.INLINE_PAGES) == 2,
   'the patcher names %d CSS targets and %d inline ones, 23 in all'
   % (len(P.CSS_TARGETS), len(P.INLINE_PAGES)))
muted = [t_ for t_ in P.CSS_TARGETS if t_[2] == P.INK_SOFT]
ghost = [t_ for t_ in P.CSS_TARGETS if t_[2] == P.GHOST]
ok(len(muted) == 17 and len(ghost) == 4,
   '  17 ink rules and 4 empty-state strays', (len(muted), len(ghost)))
for page, sel, new in P.CSS_TARGETS:
    txt = left(T.path_of(page))
    body = body_of(txt, sel)
    ok(new in body,
       '%-38s %-28s -> %s' % (page[:38], sel[:28], new), body[:120])
    ok(OLD not in body,
       '  and no %s left in that rule' % OLD, body[:120])
for page in P.INLINE_PAGES:
    txt = left(T.path_of(page))
    ok(P.INLINE_NEW in txt, '%-38s the inline <em> is converted' % page[:38])
    ok(P.INLINE_OLD not in txt, '  and the literal form is gone')


# ==========================================================================
head('2. THE CONTROL - EVERY ONE OF THEM WAS #adb5bd BEFORE')
# ==========================================================================
n_ctrl = 0
for page, sel, _new in P.CSS_TARGETS:
    w = was(T.path_of(page))
    if w is None:
        skip('the control on %s' % page, 'no %s backup' % SUFFIX)
        continue
    # ANY of the rules with that selector, not the one body_of picks.
    # .drag-handle has three, and in the BACKUP the desktop one already
    # carried --alv-ink-soft - so asking for "the" body got the wrong
    # rule a second time, in the control this time.
    bs = bodies_of(w, sel)
    if ok(any(OLD in b for b in bs),
          '%-38s %-28s was %s' % (page[:38], sel[:28], OLD),
          ' | '.join(b[:60] for b in bs)):
        n_ctrl += 1
ok(n_ctrl == len(P.CSS_TARGETS),
   'all %d were the literal before this round - the round is not a no-op '
   'and it did not invent a target' % len(P.CSS_TARGETS))


# ==========================================================================
head('3. AA, ON BOTH GROUNDS - AND IT IS B-2\'S DECISION, NOT A NEW ONE')
# ==========================================================================
before_p = N.contrast(OLD, PAPER)
before_s = N.contrast(OLD, SURFACE)
after_p = N.contrast(INK_SOFT, PAPER)
after_s = N.contrast(INK_SOFT, SURFACE)
faint = TOKENS.get('--alv-ink-faint', '#8a979d').strip()
print('      %-22s paper %5.2f   surface %5.2f' % (OLD + '  (before)',
                                                   before_p, before_s))
print('      %-22s paper %5.2f   surface %5.2f' % ('--alv-ink-faint',
                                                   N.contrast(faint, PAPER),
                                                   N.contrast(faint, SURFACE)))
print('      %-22s paper %5.2f   surface %5.2f' % ('--alv-ink-soft  (after)',
                                                   after_p, after_s))
ok(before_p < AA and before_s < AA,
   'the literal failed AA on both grounds - %.2f and %.2f against %.1f'
   % (before_p, before_s, AA))
ok(after_p >= AA and after_s >= AA,
   'and --alv-ink-soft clears it on both - %.2f and %.2f'
   % (after_p, after_s))
ok(N.contrast(faint, PAPER) < AA,
   '  CONTROL: --alv-ink-faint would NOT have - %.2f. At 11-12px the 3:1 '
   'allowance does not apply, so the nearer token was not the answer'
   % N.contrast(faint, PAPER))
pc = read(os.path.join(ROOT, 'test_colour_neutrals.py'))
ok('muted and small text' in pc,
   "B-2's own table calls #6c757d \"muted and small text\"")
ok('--alv-ink-soft' in pc,
   '  and moves it to --alv-ink-soft - so this round finishes a decision '
   'rather than taking one')
# .month-chip-no is measured against the ground it actually declares.
chip = body_of(left(T.path_of('finance_expense_types.html')), '.month-chip-no')
ok('var(--alv-surface)' in chip,
   '.month-chip-no declares its own ground, var(--alv-surface)', chip[:110])
ok(N.contrast(INK_SOFT, SURFACE) >= AA,
   '  and the month names clear AA on it - %.2f' % N.contrast(INK_SOFT,
                                                              SURFACE))
ok('var(--alv-good-ink)' in body_of(
    left(T.path_of('finance_expense_types.html')), '.month-chip-yes'),
   '  while the months that DO apply keep --alv-good-ink, so green against '
   'grey still carries the distinction and only the names got legible')


# ==========================================================================
head('4. THE WATERMARK IS ONE VALUE NOW')
# ==========================================================================
ES = '.empty-state i'
pages_es = {}
for p in T.templates():
    body = body_of(left(p), ES)
    for pos, _e, lit in R.colour_spans(body):
        pages_es.setdefault(T.rel(p), set()).add(lit.strip().lower())
vals = sorted({v for s in pages_es.values() for v in s})
ok(len(pages_es) >= 12,
   '%d page(s) carry %s' % (len(pages_es), ES), sorted(pages_es))
ok(vals == [P.GHOST],
   'and every one of them draws it in %s - ONE value' % P.GHOST, vals)
for page, sel, new in ghost:
    ok(new == P.GHOST, '  %-38s %s -> %s' % (page[:38], sel, new))
# the control
wvals = {}
for p in T.templates():
    w = was(p)
    if w is None:
        continue
    for pos, _e, lit in R.colour_spans(body_of(w, ES)):
        wvals.setdefault(T.rel(p), set()).add(lit.strip().lower())
if wvals:
    seen = sorted({v for s in wvals.values() for v in s})
    ok(len(seen) > 1,
       'CONTROL: before this round it was drawn in %d different greys - %s'
       % (len(seen), ', '.join(seen)), seen)
else:
    skip('the watermark control', 'no backups to read')
ok('no token for a watermark' in read(os.path.join(ROOT, PATCHER)),
   'and the missing token is WRITTEN DOWN rather than invented - '
   '--alv-line is a line token and using it as ink is the mis-mapping '
   "B-5a's own note warns about")


# ==========================================================================
head('5. WHAT THE ROUND LEFT, NAMED, AND STILL THERE')
# ==========================================================================
for page, sels in sorted(P.LEFT_ALONE.items()):
    txt = left(T.path_of(page))
    for sel in sels:
        body = body_of(txt, sel)
        ok(OLD in body or OLD in txt,
           '%-40s %-28s keeps its %s' % (page[:40], sel[:28], OLD))
ced = 0
for p in T.templates():
    if T.rel(p) in set(T.standalone()):
        continue
    for pos, _e, lit in R.colour_spans(T.code_only(left(p))):
        if lit.strip().lower() == '#ced4da':
            ced += 1
ok(ced >= 19,
   'the %d #ced4da border uses are untouched - every neutral line token is '
   'LIGHTER than the literal, so every available move makes an input '
   'border fainter' % ced)
for tok, val in (('--alv-line', '#e3e8ea'), ('--alv-line-soft', '#f1f3f5'),
                 ('--alv-surface-deep', '#e9ecef')):
    v = TOKENS.get(tok, '').strip()
    ok(v and N.contrast(v, PAPER) < N.contrast('#ced4da', PAPER),
       '  %-20s %s is fainter than #ced4da (%.2f vs %.2f)'
       % (tok, v, N.contrast(v, PAPER), N.contrast('#ced4da', PAPER)))
ok('--alv-line-strong' in read(os.path.join(ROOT, PATCHER)),
   '  so a --alv-line-strong is logged as a base decision instead of 19 '
   'forms being quietly degraded')


# ==========================================================================
head('6. THE TWO THE CLASSIFIER GOT WRONG')
# ==========================================================================
dhs = bodies_of(left(T.path_of('preview_imported_recipe.html')),
                '.drag-handle')
ok(len(dhs) >= 2,
   '.drag-handle is declared %d times on that page - desktop, and a phone '
   'override' % len(dhs))
phone = [b for b in dhs if 'font-size: 22px' in b]
ok(len(phone) == 1, '  one of them is the 22px phone override', len(phone))
ok(phone and OLD not in phone[0],
   '  and it no longer carries %s' % OLD, phone[0][:110] if phone else '')
ok(phone and 'var(--alv-ink-soft)' in phone[0],
   '  it takes the SAME value its own desktop rule already had, so the '
   'handle is one colour at both widths', phone[0][:110] if phone else '')
w = was(T.path_of('preview_imported_recipe.html'))
if w:
    wph = [b for b in bodies_of(w, '.drag-handle') if 'font-size: 22px' in b]
    ok(wph and OLD in wph[0],
       '  CONTROL: before this round the phone handle was FAINTER than the '
       'desktop one, which is backwards for a bigger touch target',
       wph[0][:110] if wph else '')
ok('a page disagreeing with itself' in read(os.path.join(ROOT, PATCHER)),
   '  and the patcher records that this one was excluded twice before the '
   'suite put it back')
ok(any(s == '.month-chip-no' for _p, s, _n in P.CSS_TARGETS),
   '.month-chip-no IS in the round - it is information, not a disabled '
   'control')
ok('judgement call' in read(os.path.join(ROOT, PATCHER)),
   '  and is recorded as the judgement call of the set')


# ==========================================================================
head('7. NOTHING ELSE MOVED')
# ==========================================================================
moved = []
for p in T.templates():
    w = was(p)
    if w is None:
        continue
    a, b = T.code_only(w), T.code_only(left(p))
    if a.count('{') != b.count('{') or a.count('}') != b.count('}'):
        moved.append('%s braces' % T.rel(p))
    for sa, sb in R.style_spans(b):
        R.rule_spans(b, sa, sb)
ok(not moved, 'no page changed its brace count - this round rewrites values',
   moved)
# THE NUMBER COMES FROM THE TARGET LIST, NOT FROM A HAND-TYPED COUNT.
# The first cut pinned 13 and the drag handle made it 14 - a literal
# that only this file knew about, which is the fault class this repo
# keeps paying for. The patcher's own targets are the source.
want_pages = {p for p, _s, _n in P.CSS_TARGETS} | set(P.INLINE_PAGES)
n_back = len([p for p in T.templates() if os.path.isfile(p + SUFFIX)])
ok(n_back == len(want_pages),
   '%d page(s) carry a %s backup - one per page the patcher names'
   % (n_back, SUFFIX), sorted(want_pages))


# ==========================================================================
head('8. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that --alv-ink-soft is the right weight for')
print('  muted text. It is the weight B-2 chose for the same job, and')
print('  this round follows it rather than re-opening it. If muted text')
print('  should sit somewhere between 3.00 and 5.53, the house has no')
print('  token there and that is a base decision, not this round.')
sys.exit(1 if failed else 0)
