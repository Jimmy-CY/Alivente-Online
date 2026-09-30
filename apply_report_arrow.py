# -*- coding: utf-8 -*-
"""SECTION D, ROUND D2 - THE ONE REPORT BACK WITHOUT AN ARROW

Demetri, on the Property Details Report: "Why does this Back Button not
have an arrow."

Because it is the only one of the eight that does not. Measured:

    lease_agreement_report      <i class="fas fa-arrow-left"></i> Back
    lease_renewal_report        <i class="fas fa-arrow-left"></i> Back
    open_invoices_report        <i class="fas fa-arrow-left"></i> Back
    property_report             Back                       <-- HIM
    resolved_issues_report      <i class="fas fa-arrow-left"></i> Back
    supplier_report             <i class="fas fa-arrow-left"></i> Back
    tenant_payment_days         <i class="fas fa-arrow-left"></i> Back
    tenant_report               <i class="fas fa-arrow-left"></i> Back

Seven of eight, and one that was missed. T1 made this visible rather than
causing it: with Back no longer stretched across the phone, a Back that
is only the word Back has nothing to say it is a control at all. On a
desktop it has been a bare word since the day it was written.

ONE LINE ON ONE TEMPLATE. No CSS, no base change, and the remaining
seven are not touched - they already say it.

Backups: .bak_reportarrow. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_reportarrow'
CRLF = {}

PAGE = 'property_report.html'
# The seven that already have it. Named, so one of them losing its arrow
# is a failure here rather than a silence.
SEVEN = ('lease_agreement_report.html', 'lease_renewal_report.html',
         'open_invoices_report.html', 'resolved_issues_report.html',
         'supplier_report.html', 'tenant_payment_days.html',
         'tenant_report.html')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('D2: %s is not a byte copy' % bak)


def head_block(text):
    """The .alv-report-head element, balanced on <div>."""
    m = re.search(r'<div[^>]*\balv-report-head\b[^>]*>', text)
    if not m:
        return None, None
    i, d = m.start(), 0
    for x in re.finditer(r'<div\b|</div>', text[i:]):
        d += 1 if x.group(0) != '</div>' else -1
        if d == 0:
            return i, i + x.end()
    return None, None


ARROW = '<i class="fas fa-arrow-left"></i> '

# ==========================================================================
print('=' * 74)
print('SECTION D, ROUND D2 - THE ONE REPORT BACK WITHOUT AN ARROW%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

p = alv_tree.path_of(PAGE)
t, raw = read(p)
print('  %s' % PAGE)

a, b = head_block(t)
if a is None:
    raise SystemExit('D2: %s has no .alv-report-head' % PAGE)
seg = t[a:b]
m = re.search(r'(<a[^>]*\b(?:back-button|action-back)\b[^>]*>)(.*?)(</a>)',
              seg, re.S)
if not m:
    raise SystemExit('D2: no Back in the report head of %s' % PAGE)

if 'fa-arrow-left' in m.group(2):
    print('     already carries the arrow')
else:
    inner = m.group(2)
    label = inner.strip()
    if label != 'Back':
        raise SystemExit('D2: the Back label reads %r, not Back - a round '
                         'that guessed here would rewrite copy' % label)
    # The arrow goes INSIDE the anchor, before the word, exactly as the
    # other seven write it. The surrounding whitespace is kept, so the
    # template's own indentation is untouched.
    was = m.group(0)
    now = m.group(1) + inner.replace('Back', ARROW + 'Back', 1) + m.group(3)
    if t.count(eol(p, was)) != 1:
        raise SystemExit('D2: the Back anchor is there %d time(s), not 1'
                         % t.count(eol(p, was)))
    t = t.replace(eol(p, was), eol(p, now), 1)
    print('     the arrow goes in, ahead of the word, as the other seven '
          'write it')

    # GATES.
    a2, b2 = head_block(t)
    seg2 = t[a2:b2]
    if seg2.count('fa-arrow-left') != 1:
        raise SystemExit('D2: %d arrow(s) in the head, not 1'
                         % seg2.count('fa-arrow-left'))
    if seg2.count('>Back<') + len(re.findall(r'\bBack\b', seg2)) < 1:
        raise SystemExit('D2: the word Back did not survive')
    # AND NOTHING ELSE MOVED. Compared LINE BY LINE: the first version
    # of this gate stripped the arrow out of the whole file and compared
    # the rest, which removed the FIRST arrow on the page rather than
    # the one this round added - the page has others.
    import difflib
    was_l = raw.decode('utf-8').replace('\r\n', '\n').split('\n')
    now_l = t.replace('\r\n', '\n').split('\n')
    ops = [o for o in difflib.SequenceMatcher(None, was_l, now_l,
                                              autojunk=False).get_opcodes()
           if o[0] != 'equal']
    if len(ops) != 1 or ops[0][0] != 'replace':
        raise SystemExit('D2: %d change region(s), not one replacement: %s'
                         % (len(ops), ops))
    _op, i1, i2, j1, j2 = ops[0]
    if (i2 - i1, j2 - j1) != (1, 1):
        raise SystemExit('D2: %d line(s) became %d - this round changes one'
                         % (i2 - i1, j2 - j1))
    if was_l[i1].replace('Back', ARROW + 'Back', 1) != now_l[j1]:
        raise SystemExit('D2: the one changed line is not the arrow going '
                         'in:\n  was %r\n  now %r' % (was_l[i1], now_l[j1]))
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ---- the seven that already say it --------------------------------------
print('  the seven that already had it, and none of them is touched')
missing = []
for rel in SEVEN:
    q = alv_tree.path_of(rel)
    a3, b3 = head_block(read(q)[0])
    if a3 is None:
        raise SystemExit('D2: %s has no report head' % rel)
    seg3 = read(q)[0][a3:b3]
    m3 = re.search(r'<a[^>]*\b(?:back-button|action-back)\b[^>]*>(.*?)</a>',
                   seg3, re.S)
    if not m3 or 'fa-arrow-left' not in m3.group(1):
        missing.append(rel)
    if os.path.exists(q + SUFFIX):
        raise SystemExit('D2: %s was edited and should not have been' % rel)
if missing:
    raise SystemExit('D2: %d of the seven no longer carry an arrow: %s'
                     % (len(missing), missing))
print('     all seven, unchanged')

print('-' * 74)
print('  eight report heads, eight arrows, one template edited.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
