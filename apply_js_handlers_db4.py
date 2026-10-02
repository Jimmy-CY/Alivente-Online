# -*- coding: utf-8 -*-
"""J-2, PART 3 - DB-4'S PLACEHOLDER, ANSWERED.

test_pl_invoice_icon.py has carried this since DB-4 shipped:

    # THE REPORT DRILL IS NAMED, NOT FIXED. It has the same defect and it
    # is a different modal with a different endpoint - said here so it is
    # not mistaken for something nobody noticed.
    ok('reportViewInvoice(' in now(AE) and ...
       'the Report drill still builds reportViewInvoice by string '
       'concatenation - SAME defect, different modal, named rather than '
       'quietly left', 'not found - has it been fixed?')

That is a check that asserts a FAULT, deliberately, with a detail line that
asks to be told when the fault goes. It is the right way to leave a known
defect behind - and it means the day the defect is fixed, the suite fails.

Today is that day. J-2 put the drill icon on DB-4's own two attributes and
widened DB-4's own listener to read them, so reportViewInvoice has no
callers and is gone.

THE CHECK IS TURNED OVER RATHER THAN DELETED. A deleted check is a claim
nobody is making any more; this one still has something to say, and what it
says now is the opposite: the drill icon carries its values as attributes,
there is no reportViewInvoice left, and ONE listener serves both icons -
which is the thing DB-4 was building towards and could not finish in its
own round.

Backups: .bak_jshandlers, the same suffix as parts 1 and 2.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_jshandlers'
ROOT = os.getcwd()
TARGET = os.path.join(ROOT, 'test_pl_invoice_icon.py')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    return raw.decode('utf-8'), raw, (b'\r\n' in raw)


def write(path, text, crlf):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n') if crlf
            else data.replace(b'\r\n', b'\n'))
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
            raise SystemExit('J2DB4: %s is not a byte copy' % bak)


def swap(text, old, new, what, crlf):
    o, n = old.replace('\r\n', '\n'), new.replace('\r\n', '\n')
    if crlf:
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('J2DB4: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('J-2 PART 3 - DB-4 PLACEHOLDER ANSWERED%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

HELPER = '''

def _live(p):
    """The file AS IT STANDS NOW, not as this round left it. Used by exactly
    one check - see the note at it."""
    return read(p)


'''
OLD = '''# THE REPORT DRILL IS NAMED, NOT FIXED. It has the same defect and it is
# a different modal with a different endpoint - said here so it is not
# mistaken for something nobody noticed.
ok('reportViewInvoice(' in now(AE) and "+ e.doc_url +" in now(AE).replace(
       "' + e.doc_url + '", "+ e.doc_url +"),
   'the Report drill still builds reportViewInvoice by string '
   'concatenation - SAME defect, different modal, named rather than '
   'quietly left', 'not found - has it been fixed?')'''

NEW = '''# THE REPORT DRILL WAS NAMED HERE, AND J-2 FIXED IT - 2 Oct 2026.
#
# This check used to assert the FAULT: that the drill still built
# reportViewInvoice by string concatenation, with a detail line reading
# "not found - has it been fixed?". That was deliberate. A known defect
# left behind without a check is a defect nobody is counting, and a check
# that asserts the fault fails on the day the fault goes, which is exactly
# when somebody should look.
#
# It has gone. J-2 put the drill icon on DB-4\'s own two attributes and
# widened DB-4\'s own listener to read them, so reportViewInvoice had no
# callers left. The check is turned over rather than deleted: it says the
# opposite now, and it is still the thing that notices if the drill grows a
# second way of doing this.                            [test_js_handlers.py]
#
# AND IT READS THE LIVE FILE, WHICH NO OTHER CHECK IN THIS SUITE DOES.
# now() is as_left_by(AE, \'.bak_plicon\') - the page AS DB-4 LEFT IT - and
# that is right for every other claim here, because a scope guard that
# reads the live file measures every round that came after. This claim is
# the exception on purpose: it is about what a LATER round did to the thing
# this round named, so the state it has to look at is today\'s. The four
# claims below are also made properly, against J-2\'s own backups, in
# test_js_handlers.py; these exist so DB-4\'s suite stops asserting a fault
# it no longer has.
_drill = _live(AE)
_drill_code = re.sub(r'(?m)^\\s*//.*$', '', _drill)
ok('reportViewInvoice' not in _drill_code,
   'the Report drill no longer hand-builds a handler - J-2 finished what '
   'this round started')
ok("closest('.verify-icon, .report-invoice-icon')" in _drill_code,
   '  and ONE delegated listener now serves both icons, which is what '
   'these two attributes were for')
ok('data-invoice-url="\\' + escapeHtml(e.doc_url)' in _drill,
   '  the drill icon carries data-invoice-url, escaped')
ok('data-filename="\\' + escapeHtml(e.doc_name' in _drill,
   '  and data-filename, the same two names the table icon uses')'''

t, raw, crlf = read(TARGET)

if 'J-2 fixed it' in t or 'J-2 FIXED IT' in t:
    print('  test_pl_invoice_icon.py  already turned over')
else:
    if OLD not in t.replace('\r\n', '\n'):
        raise SystemExit('J2DB4: the DB-4 placeholder is not where it was')
    t = swap(t, OLD, HELPER.strip('\n') + '\n\n' + NEW,
             'the DB-4 placeholder', crlf)
    if 'import re' not in t.split('\n\n')[0] and '\nimport re\n' not in t:
        raise SystemExit('J2DB4: the suite does not import re, and the new '
                         'check needs it')
    if not CHECK:
        back_up(TARGET, raw)
        write(TARGET, t, crlf)
    print('  test_pl_invoice_icon.py  the placeholder now asserts the fix')

print('-' * 74)

if CHECK:
    print('  --check: nothing written')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
t = read(TARGET)[0]

import ast
try:
    ast.parse(t)
except SyntaxError as e:
    raise SystemExit('J2DB4: test_pl_invoice_icon.py no longer parses: %s' % e)
print('  the suite still parses')

if "'reportViewInvoice(' in now(AE)" in t:
    raise SystemExit('J2DB4: the old placeholder is still there')
if "reportViewInvoice' not in _drill_code" not in t:
    raise SystemExit('J2DB4: the turned-over check is not there')
print('  the old claim is gone and the new one is in its place')

# IT MUST ACTUALLY RUN, AND PASS. A rewritten check that was never executed
# is a comment.
import subprocess
r = subprocess.run([sys.executable, 'test_pl_invoice_icon.py'],
                   capture_output=True, text=True, cwd=ROOT)
if r.returncode != 0:
    bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:6]
    raise SystemExit('J2DB4: test_pl_invoice_icon.py fails:\n   %s'
                     % '\n   '.join(bad or [r.stderr[-400:]]))
tail = [ln for ln in r.stdout.split('\n') if 'passed' in ln]
print('  and it passes -%s' % (tail[-1] if tail else ' rc 0'))

# AND THE COUNT WENT UP BY THREE: one claim became four.
was = read(TARGET + SUFFIX)[0]
a, b = t.count('\nok('), was.count('\nok(')
if a != b + 3:
    raise SystemExit('J2DB4: %d ok() calls, was %d, expected %d'
                     % (a, b, b + 3))
print('  one claim became four: %d -> %d' % (b, a))

print('-' * 74)
print('=' * 74)
