"""apply_filter_guard.py - scope guard #14: a CONTROL whose premise the
   secondary-visibility round made conditional.

    python apply_filter_guard.py --check     dry run, writes nothing
    python apply_filter_guard.py

Run from the repo root.

WHAT STOPPED THE PUSH.

    test_filter_toggle.py
      FAIL  passport_management.html  CONTROL: a secondary is hidden there 72px

on eight pages that passed and one that did not. The control asserts that at
375px a secondary measures zero:

    check('... CONTROL: a secondary is hidden there', sec <= 0, ...)

It is there for a good reason - it proves the mobile collapse is actually in
force, so that the "Filter survives the collapse" measurement beside it is
not vacuous. But its premise was "a secondary is ALWAYS hidden at 375px",
and the secondary-visibility round made that conditional: a secondary hides
only where an `.action-more-btn` carries it. Eight of these nine pages have
one. `passport_management` does not, which is exactly why its Help button
used to disappear and now does not.

WHAT THE CLAIM IS ABOUT. Not "secondaries are hidden" - that is no longer a
fact - but "the collapse is in force here, so the Filter measurement means
something". Asked properly, that is now a TWO-SIDED control, and a stronger
one than before: on a bar WITH a More menu the secondary must be hidden, and
on a bar WITHOUT one it must be visible. Either way the collapse is proved to
be running, and the new rule is exercised on nine real pages for free.

FOURTEENTH MOVE. The refinement from the eighth still holds: ask what the
claim is ABOUT. Re-pointing this at `sec <= 0 or page is passport` would have
been an exception list, and would have quietly stopped testing the very thing
that changed.

HOUSE RULES: idempotent, .bak_fguard backup never overwritten, --check writes
nothing, SELF-CHECK BEFORE WRITING.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
P = os.path.join(os.getcwd(), 'test_filter_toggle.py')
if not os.path.exists(P):
    sys.exit('! test_filter_toggle.py not found - run from the repo root')


def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    return raw, ('\r\n' in raw), raw.replace('\r\n', '\n')


def sub1(t, old, new, what):
    n = t.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %r'
                 % (what, n, old[:150]))
    return t.replace(old, new, 1)


FAIL = []


def want(c, m):
    if not c:
        FAIL.append(m)


ORIG, CRLF, f = load(P)
DONE = 'THE COLLAPSE IS PROVED EITHER WAY' in f
DONE2 = '_unlink(' in f

OLD = """            sec = await pg.evaluate("()=>{const e=document.querySelector("
                                    "'.page-action-buttons .action-secondary');"
                                    "return e?e.getBoundingClientRect().width:-1}")
            check('%-26s   CONTROL: a secondary is hidden there' % short, sec <= 0,"""

NEW = """            # THE COLLAPSE IS PROVED EITHER WAY - scope guard #14, 8 Sep.
            #
            # This asserted `sec <= 0`: a secondary always measures zero at
            # 375px. It is here to prove the collapse is in force, so the
            # Filter measurement above is not vacuous - a good control with
            # a premise that stopped being true. base now hides a secondary
            # only where an .action-more-btn carries it, and eight of these
            # nine pages have one. passport_management does not, which is
            # why its Help button used to vanish and now does not.
            #
            # So the control is two-sided instead of exception-listed: with
            # a More menu the secondary must be hidden, without one it must
            # be visible. Either outcome proves the collapse is running, and
            # the new rule gets exercised on nine real pages for free.
            sec = await pg.evaluate("()=>{const e=document.querySelector("
                                    "'.page-action-buttons .action-secondary');"
                                    "return e?e.getBoundingClientRect().width:-1}")
            more = await pg.evaluate("()=>!!document.querySelector("
                                     "'.page-action-buttons .action-more-btn')")
            check('%-26s   CONTROL: a secondary is %s there' %
                  (short, 'hidden' if more else 'visible - no More menu '
                   'carries it'),
                  (sec <= 0) if more else (sec > 20),"""

HELPER = (
    "def _unlink(path, tries=20):\n"
    '    """Remove a temp fragment, or say so - never raise.\n'
    "\n"
    "       Windows keeps the file until Chromium's renderer exits, which\n"
    "       can be a moment after page.close() has returned.\"\"\"\n"
    "    import time\n"
    "    for _ in range(tries):\n"
    "        try:\n"
    "            os.remove(path)\n"
    "            return True\n"
    "        except FileNotFoundError:\n"
    "            return True\n"
    "        except OSError:\n"
    "            time.sleep(0.05)\n"
    "    print('  NOTE  could not delete %s - still held open. Harmless; '\n"
    "          'delete it by hand.' % os.path.basename(path))\n"
    "    return False\n"
    "\n"
    "\n"
    "asyncio.run(drive())")

if DONE:
    print('  test_filter_toggle.py already patched')
else:
    f = sub1(f, OLD, NEW, 'FGUARD: the one-sided control')

# ---------------------------------------------------------------------------
# AND A CLEANUP THAT CANNOT FAIL THE SUITE.
#
#     PermissionError: [WinError 32] The process cannot access the file
#     because it is being used by another process: '_filt_suppliers.html'
#
# `await pg.close()` returns before Chromium's renderer has released its
# handle on the file:// document, so the os.remove() a line later races it.
# On Linux this never appears - unlinking an open file is legal there -
# which is exactly why a build sandbox could not see it and Windows could.
#
# A temp file that will not delete is not a defect in the code under test and
# must not take a green suite down with it. Retry briefly, then report and
# carry on. This is the same shape as the CDN timeout that stopped a push
# earlier today: a gate that cannot FINISH blocks exactly as hard as one that
# fails, and for a reason that is not about the code.
if not DONE2:
    f = sub1(f, "            await pg.close()\n            os.remove(f)",
             "            await pg.close()\n            _unlink(f)",
             'FGUARD: the racing cleanup')
    f = sub1(f, "asyncio.run(drive())", HELPER,
             'FGUARD: somewhere to put the helper')

_code = re.sub(r'(?m)^\s*#[^\n]*$', '', f)
want('THE COLLAPSE IS PROVED EITHER WAY' in f, 'FGUARD: no note left')
want('action-more-btn' in _code, 'FGUARD: the control never looks for a menu')
want('(sec <= 0) if more else (sec > 20)' in _code,
     'FGUARD: the control is not two-sided')
want(_code.count('check(\'%-26s   CONTROL: a secondary is') == 1,
     'FGUARD: the control was duplicated')
want('def _unlink(' in _code, 'FGUARD: the cleanup helper is missing')
want('os.remove(f)' not in _code,
     'FGUARD: a raw os.remove survives - it races Chromium on Windows')
want(_code.count('_unlink(f)') == 1, 'FGUARD: the cleanup call is wrong')
# The helper is a module-level def and must be DEFINED before asyncio.run
# reaches it - inserting it after the call would raise NameError at cleanup,
# which is a worse version of the bug being fixed.
want(_code.find('def _unlink(') < _code.find('asyncio.run(drive())'),
     'FGUARD: the helper is defined after the run that uses it')
try:
    compile(f, 'test_filter_toggle.py', 'exec')
except SyntaxError as e:
    want(False, 'FGUARD: will not compile - line %s: %s' % (e.lineno, e.msg))

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
        bak = P + '.bak_fguard'
        if not os.path.exists(bak):
            with open(bak, 'w', encoding='utf-8', newline='') as fh:
                fh.write(ORIG)
            print('    backup -> %s' % os.path.basename(bak))
        with open(P, 'w', encoding='utf-8', newline='') as fh:
            fh.write(out)

print('\n  --check: nothing written.' if CHECK else '\n  done.')
