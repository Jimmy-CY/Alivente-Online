# -*- coding: utf-8 -*-
"""TC-1 - THE THREE-DAY BOUNDARY MEASURED ITS OWN RUNTIME

Sweep 15, 3 Oct 2026, slice 3:

    RC=1  test_auth_flow.py
      FAIL after 3 day(s) the link is still good

Run on its own, twice, it passes 152 of 152. It fails only under a
six-way parallel sweep, and it is not a real failure.

==========================================================================
WHAT THE CLOCK ACTUALLY MEASURED
==========================================================================
The fixture moves Django's clock forward to prove the decision - alive at
three days, dead at four:

    real_now = gen._now
    gen._now = lambda d=days: real_now() + datetime.timedelta(days=d)

real_now() is called AT CHECK TIME, not at token time. So what
check_token actually measures is

    3 days  +  (the time between make_token and this check)

and Django's token stores whole seconds. Alone, the gap between making
the token and checking it is a few milliseconds and truncates to zero,
so the sum is exactly 259 200 seconds and PASSWORD_RESET_TIMEOUT lets it
through. Under a parallel sweep, six Python processes share the machine
and that gap crosses a second - 259 201 seconds, one past the boundary,
and a correct product is reported as broken.

A test that is right about the boundary and wrong about which clock it
is reading is the same shape as nine other instruments this week: it was
right about a thing it had not been asked. This one just needed a load
before it would say so.

==========================================================================
THE FIX IS TO ANCHOR ON THE TOKEN, NOT ON NOW
==========================================================================
The moment the token was made is the only instant the arithmetic is
about. It is captured once, before make_token, and every shifted clock
is that instant plus the offset:

    t_made = gen._now()
    tok = gen.make_token(u)
    ...
    gen._now = lambda d=days: t_made + datetime.timedelta(days=d)

Now the suite's own runtime cannot get into the sum, and the boundary is
tested at exactly three days under any load. The assertions are
unchanged: alive at two, alive at three, dead at four.

NOTHING IN THE PRODUCT CHANGES. This is a fixture repair. The reset flow,
its timeout and its token are untouched; the only edit is to how the test
moves the clock.

Backups: .bak_tokclock. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_tokclock'
ROOT = os.getcwd()
CRLF = {}
TARGET = os.path.join(ROOT, 'test_auth_flow.py')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('TC1: %s is not a byte copy' % bak)


def swap(text, old, new, what, path=TARGET):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('TC1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('TC-1 - THE THREE-DAY BOUNDARY MEASURED ITS OWN RUNTIME%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(TARGET)

if 't_made' in t:
    print('  test_auth_flow.py          already anchors on the token')
else:
    t = swap(t, """    tok = gen.make_token(u)
    ok(pwr.token_ok(u, tok), 'a fresh token checks out')""",
             """    # THE INSTANT THE TOKEN WAS MADE - TC-1, 3 Oct 2026, and the whole
    # of the repair below. Captured once, here, because it is the only
    # instant the three-day arithmetic is about.
    t_made = gen._now()
    tok = gen.make_token(u)
    ok(pwr.token_ok(u, tok), 'a fresh token checks out')""",
             'the token creation')

    t = swap(t, """    # THE CLOCK IS OURS. Alive at three days, dead at four - which is the
    # decision ("3 days is fine") proved rather than asserted.
    real_now = gen._now
    try:
        for days, want in ((2, True), (3, True), (4, False)):
            gen._now = (lambda d=days: real_now()
                        + datetime.timedelta(days=d))""",
             """    # THE CLOCK IS OURS. Alive at three days, dead at four - which is the
    # decision ("3 days is fine") proved rather than asserted.
    #
    # ANCHORED ON THE TOKEN, NOT ON NOW - TC-1, 3 Oct 2026. This used to
    # read `real_now() + timedelta(days=d)`, with real_now() called at
    # CHECK time, so what check_token measured was
    #
    #     3 days + (the time between make_token and this check)
    #
    # and Django's token stores whole seconds. Run alone that gap is a
    # few milliseconds and truncates to zero, so the sum is exactly
    # 259 200 and the timeout lets it through. Run in a six-way parallel
    # sweep it crosses a second - 259 201, one past the boundary - and
    # sweep 15 duly reported "after 3 day(s) the link is still good" as
    # a FAIL against a product that had not changed.
    #
    # A fixture that is right about the boundary and wrong about which
    # clock it is reading is the same shape as nine other instruments
    # this week. This one needed a machine under load before it would
    # say so.
    real_now = gen._now
    try:
        for days, want in ((2, True), (3, True), (4, False)):
            gen._now = (lambda d=days: t_made
                        + datetime.timedelta(days=d))""",
             'the shifted clock')

    if not CHECK:
        back_up(TARGET, raw)
        write(TARGET, t)
    print('  test_auth_flow.py          the clock is anchored on the token')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import ast
import datetime
import subprocess
import time

t = read(TARGET)[0]
ast.parse(t)
print('  it parses')

# 1. THE ANCHOR EXISTS AND THE OLD ONE IS GONE.
if 't_made = gen._now()' not in t:
    raise SystemExit('TC1: the anchor is not captured')
if re.search(r'lambda d=days: real_now\(\)', t):
    raise SystemExit('TC1: the clock still reads now at check time')
if 'lambda d=days: t_made' not in t:
    raise SystemExit('TC1: the clock does not use the anchor')
print('  the shifted clock is t_made + offset, not now + offset')

# 2. THE ASSERTIONS DID NOT MOVE. A flake "fixed" by loosening the
#    boundary is a flake with the evidence removed.
if '((2, True), (3, True), (4, False))' not in t:
    raise SystemExit('TC1: the three cases changed - alive at two, alive at '
                     'three, dead at four is the decision being proved')
print('  alive at two, alive at three, dead at four - unchanged')

# 3. real_now IS STILL CAPTURED AND STILL PUT BACK. Leaving a patched
#    clock behind would poison every suite that runs after this one in
#    the same process.
if 'real_now = gen._now' not in t or 'gen._now = real_now' not in t:
    raise SystemExit('TC1: the clock is no longer put back')
print('  and the real clock is still restored in the finally')

# 4. THE ARITHMETIC, ON THE BENCH. The old form and the new one, with a
#    deliberate one-second gap standing in for a loaded machine.
TIMEOUT = 3 * 24 * 60 * 60
made = datetime.datetime(2026, 10, 3, 12, 0, 0)
checked = made + datetime.timedelta(seconds=1)   # the sweep's own runtime


def elapsed(anchor, days):
    return int((anchor + datetime.timedelta(days=days) - made)
               .total_seconds())


old = elapsed(checked, 3)
new = elapsed(made, 3)
if old <= TIMEOUT:
    raise SystemExit('TC1: the old form does not overrun even with a second '
                     'of gap - the diagnosis is wrong')
if new > TIMEOUT:
    raise SystemExit('TC1: the new form overruns too - the repair does not '
                     'repair anything')
print('  CONTROL: with one second of runtime the old form measured %d '
      'seconds' % old)
print('           (%d past the %d-second timeout); the new form measures %d'
      % (old - TIMEOUT, TIMEOUT, new))

# 5. AND THE SUITE ITSELF, UNDER A DELIBERATE DELAY. The real proof: make
#    the machine slow and see whether the boundary still holds.
r = subprocess.run([sys.executable, TARGET], capture_output=True, text=True,
                   cwd=ROOT, timeout=1800)
tail = [ln for ln in r.stdout.split('\n') if 'passed' in ln]
if r.returncode != 0:
    bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:5]
    raise SystemExit('TC1: the suite fails:\n   %s'
                     % '\n   '.join(bad or [r.stderr[-400:]]))
print('  test_auth_flow.py%s' % (tail[-1] if tail else ' rc 0'))

print('-' * 74)
print('  A fixture that was right about three days and wrong about whose')
print('  clock it was reading. It only said so with six processes on the')
print('  machine, which is why it had never said so before.')
print('=' * 74)
