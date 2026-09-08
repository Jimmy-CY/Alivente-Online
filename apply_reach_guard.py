"""apply_reach_guard.py - scope guard #13: a check that pinned the TEXT of a
   rule the secondary-visibility round narrowed.

    python apply_reach_guard.py --check     dry run, writes nothing
    python apply_reach_guard.py

Run from the repo root.

WHAT STOPPED THE PUSH.

    test_button_reach.py
      FAIL    and the whole mobile collapse

on a tree where the mobile collapse is intact. The check was:

    '.page-action-buttons .action-secondary { display: none; }' in BLOCK

- the exact literal, byte for byte, of the rule the secondary-visibility
round narrowed to `.page-action-buttons:has(.action-more-btn)
.action-secondary`. The behaviour it names still happens; the string it
matched does not exist any more.

WHAT THE CLAIM IS ABOUT, WHICH IS THE WHOLE OF THE EIGHTH MOVE'S LESSON.

The check is called "and the whole mobile collapse". It is not about that
rule's spelling; it is about the phone block existing and doing its job. Its
own sibling suite asks the same thing and PASSED on this tree:

    test_action_standard.py
      check('  secondaries step aside',
            re.search(r'\\.action-secondary\\s*\\{\\s*display:\\s*none', MOBILE))

- scoped to the mobile block, matching the DECLARATION rather than the whole
selector. That is why one suite noticed a spelling change and the other
noticed nothing: one asked about text, the other about a rule.

So this is not "re-point the guard at the new string", which would leave it
just as brittle for the next round. The check now asks the mobile block
whether a secondary is hidden there AND whether the hide is conditioned on a
More menu - which is the collapse as it now works, and is a stronger claim
than the one it replaces.

THIRTEENTH MOVE, AND THE SIXTH THAT NAMED WHAT WOULD INVALIDATE IT. The
guard quoted, verbatim, the one rule a later round was always going to have
to change - the same shape as the print-leak note that said "it goes when the
banner round takes the banner", except that one was written as a prediction
and this one as an assertion.

HOUSE RULES: idempotent, .bak_reach backup never overwritten, --check writes
nothing, SELF-CHECK BEFORE WRITING.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
P = os.path.join(os.getcwd(), 'test_button_reach.py')
BASE = os.path.join(os.getcwd(), 'pages', 'templates', 'base.html')
if not os.path.exists(P):
    sys.exit('! test_button_reach.py not found - run from the repo root')


def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    return raw, ('\r\n' in raw), raw.replace('\r\n', '\n')


def sub1(t, old, new, what):
    n = t.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %r'
                 % (what, n, old[:120]))
    return t.replace(old, new, 1)


FAIL = []


def want(c, m):
    if not c:
        FAIL.append(m)


ORIG, CRLF, f = load(P)
DONE = 'THE COLLAPSE IS A RULE, NOT A STRING' in f

OLD = """check('  and the whole mobile collapse',
      '.page-action-buttons .action-secondary { display: none; }' in BLOCK)"""
NEW = '''# THE COLLAPSE IS A RULE, NOT A STRING - scope guard #13, 8 Sep.
#
# This read:
#
#     '.page-action-buttons .action-secondary { display: none; }' in BLOCK
#
# the exact literal of a rule the secondary-visibility round narrowed to
# `.page-action-buttons:has(.action-more-btn) .action-secondary`, so that a
# secondary hides only where a More menu actually carries it. The collapse
# still happens; the string does not. test_action_standard.py asks the same
# question with a regex scoped to the mobile block and passed unchanged,
# which is the difference between checking a rule and checking its spelling.
#
# So the claim is asked properly instead of re-pointed at the new text: the
# mobile block must hide a secondary, and the hide must be conditional on a
# More menu. That is a stronger check than the one it replaces.
_MOB = BLOCK[BLOCK.find('@media screen and (max-width: 768px)'):]
check('  and the whole mobile collapse',
      re.search(r'\\.action-secondary\\s*\\{\\s*display:\\s*none', _MOB)
      is not None)
check('    and a secondary hides only where a More menu carries it',
      re.search(r'\\.page-action-buttons:has\\(\\.action-more-btn\\)\\s*'
                r'\\.action-secondary', _MOB) is not None)
check('    CONTROL: the mobile block really was located',
      '.action-more-btn' in _MOB and len(_MOB) < len(BLOCK))'''

if DONE:
    print('  test_button_reach.py already patched')
else:
    f = sub1(f, OLD, NEW, 'REACH: the pinned literal')

# ===========================================================================
# SELF-CHECK
# ===========================================================================
_code = re.sub(r'(?m)^\s*#[^\n]*$', '', re.sub(r'"""(?:.|\n)*?"""', '', f))
want('THE COLLAPSE IS A RULE, NOT A STRING' in f, 'REACH: no note left')
want("'.page-action-buttons .action-secondary { display: none; }' in BLOCK"
     not in _code, 'REACH: the pinned literal survives in code')
want(':has(\\\\(' not in _code, 'REACH: the escape is malformed')
want(_code.count('_MOB') >= 3, 'REACH: the mobile block is not used')
try:
    compile(f, 'test_button_reach.py', 'exec')
except SyntaxError as e:
    want(False, 'REACH: will not compile - line %s: %s' % (e.lineno, e.msg))

# THE NEW CHECK MUST ACTUALLY PASS ON THIS TREE, and would have FAILED on the
# old one. Verified against base.html here rather than left to the suite.
if os.path.exists(BASE):
    _b = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', load(BASE)[2], re.S))
    _blk = _b[_b.find('@media screen and (max-width: 768px)'):]
    want(re.search(r'\.action-secondary\s*\{\s*display:\s*none', _blk)
         is not None, 'REACH: the new check does not pass on this base.html')
    want(re.search(r'\.page-action-buttons:has\(\.action-more-btn\)\s*'
                   r'\.action-secondary', _blk) is not None,
         'REACH: base has not been patched by apply_secondary_visible.py yet '
         '- run that first, or this guard move is premature')
    want('.page-action-buttons .action-secondary { display: none; }' not in _b,
         'REACH: the old literal is still in base - nothing needed moving')

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)

if not DONE:
    out = f.replace('\n', '\r\n') if CRLF else f
    print('  %-32s %d -> %d bytes'
          % (os.path.basename(P), len(ORIG.encode('utf-8')),
             len(out.encode('utf-8'))))
    if not CHECK:
        bak = P + '.bak_reach'
        if not os.path.exists(bak):
            with open(bak, 'w', encoding='utf-8', newline='') as fh:
                fh.write(ORIG)
            print('    backup -> %s' % os.path.basename(bak))
        with open(P, 'w', encoding='utf-8', newline='') as fh:
            fh.write(out)

print('\n  --check: nothing written.' if CHECK else '\n  done.')
