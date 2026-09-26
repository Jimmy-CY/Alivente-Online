# -*- coding: utf-8 -*-
"""apply_palette.py - Section F round F1, 26 Sep 2026.

THE PALETTE WAS TUNED AGAINST WHITE. THE APP DOES NOT SIT ON WHITE.

A rendered probe measured every visible element carrying its own text in
every template - 4150 of them - and found 565 below their bar. The cause is
not the pages: several ink tokens pass on #ffffff and fail on a surface
base itself defines.

    ink               hex        #fff  #f8f9fa  #e9ecef  #eef1f2
    --alv-neutral     #6b7780    4.59    4.35!    3.87!    4.04!
    --alv-warn        #9a6a08    4.73    4.49!    3.99!    4.17!

WHAT THIS ROUND MOVES, AND WHY ONLY THIS MUCH. A first draft also moved
--alv-accent and --alv-good. Both were dropped, on evidence:

  --alv-accent  #0e7c8b is COPIED AS A LITERAL 411 TIMES ACROSS 75
                TEMPLATES, and named in 45 places across 22 suites. Moving
                the token would leave 411 stale copies of the old teal -
                strictly worse than leaving it alone. It waits for E6's
                literal sweep, after which it moves in one line. Measured,
                it was 1 of the 104 fixes.
  --alv-good    fixed 0 of the 104. It fails at 4.32 on the tint, which is
                real but currently unused. Not worth the suite churn.

Where the fixes actually came from, diffed before and after:

    .text-muted     79        --alv-neutral    9
    --alv-warn      15        --alv-accent     1        --alv-good  0

BOOTSTRAP'S .text-muted IS THE BIGGEST SINGLE ITEM. #6c757d, used 260
times across 68 templates, and base never had an opinion about it. It
scrapes 4.69 on white and fails on every house surface. It is pointed at
--alv-neutral so the house has ONE muted ink instead of two opinions about
the same idea, with !important because Bootstrap's own utility carries it.

AN ALIAS MOVES WITH ITS TOKEN. base declares several tokens as separate
literals that happen to share a value:

    #9a6a08  --alv-warn, --alv-age-2        #1e7d4f  --alv-good, --alv-grade-1
    #b3261e  --alv-bad, --alv-age-4, ...    #5b6b73  --alv-ink-soft, --alv-grade-3

They are equal by intent, not by accident, so moving --alv-warn without
--alv-age-2 would split a pair. --alv-age-2 moves with it.

AND A FALLBACK MOVES WITH ITS TOKEN. D5's chart helpers read a token with
a literal fallback - anTok('warn', '#9a6a08') - and test_ia_palette and
test_quadrant_tokens exist to catch the two drifting apart. Both fallbacks
that name a token this round moves are updated here. The ones naming
--alv-good and --alv-grade-1 are NOT touched, because those tokens do not
move.

SO THIS ROUND DOES TOUCH TEMPLATES - three of them, for fallbacks and one
sentence of prose that states base's warn value and would otherwise become
false. Every contrast fix still comes from base.

WHAT IT DOES NOT TOUCH. --alv-ink-faint #8a979d is the worst number in the
survey - 3.00 on white, 2.53 on the tint. It is the DISABLED ink, and
disabled controls are exempt (lesson 56). Darkening it would make
unavailable things look available. Its own decision, not this one.

Also left, and recorded rather than fixed: --alv-age-1 3.63, --alv-grade-2
4.20 and --alv-edit 4.36 all fail as ink on the same tint.
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, 'pages', 'templates')
BASE = os.path.join(ROOT, 'base.html')
SUFFIX = '.bak_palette'
CHECK = '--check' in sys.argv

# (old, new) - anchored on the whole declaration so a bare hex elsewhere in
# base can never be hit by accident.
TOKENS = [
    ('--alv-warn:       #9a6a08;', '--alv-warn:       #8e6207;'),
    ('--alv-age-2:      #9a6a08;', '--alv-age-2:      #8e6207;'),
    ('--alv-neutral:    #6b7780;', '--alv-neutral:    #616c74;'),
]

# A fallback names its token and repeats its value. If the token moves and
# the fallback does not, they drift - which is exactly what
# test_ia_palette and test_quadrant_tokens were written to catch.
FALLBACKS = [
    ('act_expense.html',
     "Q_WARN      = anTok('warn',      '#9a6a08'),",
     "Q_WARN      = anTok('warn',      '#8e6207'),"),
    ('fsr.html',
     "WARN    = iaTok('age-2',        '#9a6a08'),",
     "WARN    = iaTok('age-2',        '#8e6207'),"),
    # Prose, not code - but it states base's warn value as a fact, and a
    # comment that is wrong is worse than no comment (lesson 21).
    ('fsr_details.html',
     "#ffc107 is not even base's warn, which is #9a6a08.",
     "#ffc107 is not even base's warn, which is #8e6207."),
]

# Bootstrap ships `.text-muted{color:#6c757d!important}`, so the override
# needs !important to win. Checked against the gate's own fixture, not
# assumed.
MUTED_ANCHOR = '      .badge-info { background-color: var(--alv-accent); color: var(--alv-on-accent); }'
MUTED_RULE = """
      /* ===== ALV MUTED TEXT v1 ===== 26 Sep 2026
         Bootstrap's .text-muted is #6c757d, used 260 times across 68
         templates, and base never had an opinion about it. It measures
         4.69 on white - a pass, barely - and 3.95 on #e9ecef, which is
         what the cards and rows it sits on are actually painted. It was
         262 of the 565 elements the rendered survey found below their
         bar: forty-six per cent of the whole problem, in one colour.
         Pointed at --alv-neutral so the house has ONE muted ink rather
         than two opinions about the same idea. !important because
         Bootstrap's own utility carries it. */
      .text-muted { color: var(--alv-neutral) !important; }"""

CRLF = {}


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8')


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def patch_fallbacks():
    n = 0
    for name, old, new in FALLBACKS:
        path = os.path.join(ROOT, name)
        text = read(path)
        if new in text:
            continue
        if text.count(old) != 1:
            raise SystemExit('F1: fallback anchor matched %d times in %s '
                             '- it must match exactly once'
                             % (text.count(old), name))
        if not CHECK:
            bak = path + SUFFIX
            if not os.path.exists(bak):
                CRLF[bak] = CRLF.get(path)
                write(bak, text)
            write(path, text.replace(old, new))
        n += 1
    return n


def patch_base():
    text = read(BASE)
    before = text
    moved = 0
    for old, new in TOKENS:
        if new in text and old not in text:
            continue
        n = text.count(old)
        if n != 1:
            raise SystemExit(
                'F1: token anchor %r matched %d times in base - it must '
                'match exactly once' % (old[:34], n))
        text = text.replace(old, new)
        moved += 1

    added = 0
    if '.text-muted' not in text:
        n = text.count(MUTED_ANCHOR)
        if n != 1:
            raise SystemExit(
                'F1: the .text-muted insertion anchor matched %d times - '
                'it must match exactly once' % n)
        text = text.replace(MUTED_ANCHOR, MUTED_ANCHOR + '\n' + MUTED_RULE)
        added = 1

    if text == before:
        return 0, 0
    if not CHECK:
        bak = BASE + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(BASE)     # a backup is a copy (lesson 46)
            write(bak, before)
        write(BASE, text)
    return moved, added


LATER = [
    # THREE SUITES RECORD --alv-warn's VALUE AND ARE RIGHT TO. They are
    # not broken by this round; they are doing their job - a token's value
    # is a decision, and a suite that records a decision goes red when the
    # decision changes. Seventeen suites failed the first draft of this
    # round; fourteen of them were about --alv-accent and went green the
    # moment the accent was dropped. These three are the real cost of
    # moving warn and neutral, and it is three lines.
    # test_quadrant_tokens compared a FROZEN page against a LIVE base.
    # It reads act_expense through as_left_by(.bak_quad) - the file as the
    # quadrant round left it - but base with a plain read(). While no
    # token ever moved, the two agreed. The moment one moves they cannot,
    # and nothing has drifted: the check is simply reading its two sides
    # at different moments in time.
    #
    # The invariant that matters is a LIVE fallback matching a LIVE token,
    # so the comparison reads the page live. The rest of the suite keeps
    # its as_left_by view, because that part really is judging what the
    # quadrant round did (lesson 40 - ask which one a check needs).
    #
    # The second element of each tuple is unused by these two checks; it
    # is updated anyway so it does not sit there stating a stale value.
    # test_ageing_scale checks that the ageing scale's step 2 IS the warn
    # colour - "so the scale cannot drift from the semantics beside it" -
    # and checked it by hard-coding warn's VALUE. So it broke when warn
    # moved, even though --alv-age-2 moved with it and the two are still
    # identical. The check asks the right question and reads the wrong
    # thing: compare the two TOKENS, and it holds for any future move.
    #
    # Step 4 two lines down has the same latent fault against --alv-bad.
    # It passes today only because bad has not moved. Having just
    # diagnosed it, leaving it would be shipping the next failure on
    # purpose, so it goes the same way.
    ('test_ageing_scale.py',
     """check('step 2 IS the warn colour, so the scale cannot drift from the '
      'semantics beside it', '--alv-age-2:      #9a6a08' in BC)
check('step 4 IS the bad colour', '--alv-age-4:      #b3261e' in BC)""",
     """# LATER - F1, 26 Sep. Was hard-coded to warn's and bad's VALUES, so it
# broke the moment a token moved even though the scale moved with it.
# Ask whether the two TOKENS agree - which is what the check is for. [F1]
def _tokval(t):
    m = re.search(re.escape(t) + r':\s*(#[0-9a-fA-F]{6})', BC)
    return m.group(1).lower() if m else None


check('step 2 IS the warn colour, so the scale cannot drift from the '
      'semantics beside it',
      _tokval('--alv-age-2') is not None
      and _tokval('--alv-age-2') == _tokval('--alv-warn'))
check('step 4 IS the bad colour',
      _tokval('--alv-age-4') is not None
      and _tokval('--alv-age-4') == _tokval('--alv-bad'))"""),
    ('test_quadrant_tokens.py',
     "                       ('warn', '#9a6a08'), ('warn-soft', '#fdf3dd'),",
     "                       ('warn', '#8e6207'), ('warn-soft', '#fdf3dd'),"),
    ('test_quadrant_tokens.py',
     """    _m = re.search(r"anTok\('%s',\s*'(#[0-9a-f]{6})'\)" % re.escape(name),
                   P_NOW)""",
     """    # LATER - F1, 26 Sep. Read the page LIVE here. P_NOW is the file
    # as the QUADRANT round left it, and base below is read live, so
    # comparing them asks whether a frozen page matches a moving base -
    # true only until a token moves. [F1]
    _m = re.search(r"anTok\('%s',\s*'(#[0-9a-f]{6})'\)" % re.escape(name),
                   read(PAGE))"""),
    ('test_table_invoices.py',
     "'unapprove': 'rgb(154, 106, 8)',",
     "'unapprove': 'rgb(142, 98, 7)',"),
    ('test_table_standard.py',
     "              pn['color'] == 'rgb(107, 119, 128)')",
     "              pn['color'] == 'rgb(97, 108, 116)')"),
    ('alv_rounds.py',
     "    '.bak_namedbars',\n]",
     "    '.bak_namedbars',\n    '.bak_palette',\n]"),
    ('Push-PendingChanges.ps1',
     "    'test_named_bars.py'",
     "    'test_named_bars.py'\n    'test_palette.py'"),
]


def patch_later():
    done = 0
    for name, old, new in LATER:
        path = os.path.join(HERE, name)
        text = read(path)
        if new in text:              # decided by the NEW text alone (47)
            continue
        if text.count(old) != 1:
            raise SystemExit('F1/LATER: anchor matched %d times in %s'
                             % (text.count(old), name))
        if not CHECK:
            bak = path + SUFFIX
            if not os.path.exists(bak):
                CRLF[bak] = CRLF.get(path)
                write(bak, text)
            write(path, text.replace(old, new))
        done += 1
    return done


def main():
    print('=' * 70)
    print('SECTION F, ROUND F1 - THE PALETTE LEAVES WHITE - %s'
          % ('CHECK ONLY' if CHECK else 'APPLYING'))
    print('=' * 70)
    moved, added = patch_base()
    fb = patch_fallbacks()
    later = patch_later()
    if moved or added:
        for old, new in TOKENS:
            print('  %-46s -> %s' % (old.strip()[:46], new.strip().split()[-1]))
        if added:
            print('  %-46s -> %s' % ('.text-muted (new rule in base)',
                                     'var(--alv-neutral) !important'))
    else:
        print('  base.html                                already applied')
    print('-' * 70)
    print('  %d token(s) moved, %d rule(s) added, %d fallback(s) '
          'realigned,\n  %d LATER edit(s). Every CONTRAST fix comes from '
          'base; the fallbacks\n  exist only so a token and its copy do '
          'not drift apart.' % (moved, added, fb, later))
    print()
    print('  LEFT ALONE, with the reason:')
    print('    --alv-accent   #0e7c8b  411 literal copies in 75 templates.')
    print('        Moving the token would strand every one of them. It')
    print('        waits for E6, then moves in a line. Cost: 1 of 104.')
    print('    --alv-good     #1e7d4f  fixed 0 of the 104 measured.')
    print('    --alv-ink-faint #8a979d 3.00 on white - the worst number in')
    print('        the survey, and the DISABLED ink. Exempt; darkening it')
    print('        would make unavailable things look available.')
    print('    --alv-age-1 3.63, --alv-grade-2 4.20, --alv-edit 4.36 all')
    print('        fail as ink on the same tint. Recorded, not fixed.')
    print('=' * 70)


if __name__ == '__main__':
    main()
