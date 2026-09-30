# -*- coding: utf-8 -*-
"""test_report_arrow.py - Section D round D2, 30 Sep 2026.

Demetri, on the Property Details Report: "Why does this Back Button not
have an arrow."

Because it was the only one of the eight without it. T1 made that
visible rather than causing it - with Back no longer stretched across the
phone, a Back that is only the word Back has nothing left saying it is a
control. On a desktop it had been a bare word since the day it was
written.

ONE LINE, ONE TEMPLATE. Section 2 proves that literally: the file before
and the file after differ by exactly one line, and that line is the old
one with the arrow inserted ahead of the word. Nothing else in the
template moved, and none of the other seven was touched.

SECTION 3 IS THE POINT OF THE ROUND. All eight report heads now carry an
arrow, and the check is written so that one of them LOSING it fails here
- which is how this one was found in the first place.
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
import difflib
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS = []
    as_left_by = None

SUFFIX = '.bak_reportarrow'
ME = 'test_report_arrow.py'
PATCHER = 'apply_report_arrow.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = 'property_report.html'
ARROW = '<i class="fas fa-arrow-left"></i> '
EIGHT = ('lease_agreement_report.html', 'lease_renewal_report.html',
         'open_invoices_report.html', 'property_report.html',
         'resolved_issues_report.html', 'supplier_report.html',
         'tenant_payment_days.html', 'tenant_report.html')

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
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def no_comments(s):
    """Lesson 21 - a gate that reads prose passes on prose."""
    s = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', s,
               flags=re.S | re.I)
    return re.sub(r'<!--.*?-->|\{#.*?#\}', '', s, flags=re.S)


def left(rel):
    """Lesson 17 - the file as THIS round left it."""
    p = alv_tree.path_of(rel)
    return (as_left_by(p, SUFFIX, read) if as_left_by else read(p))


def head_block(text):
    """The .alv-report-head element, balanced on <div>."""
    m = re.search(r'<div[^>]*\balv-report-head\b[^>]*>', text)
    if not m:
        return None
    i, d = m.start(), 0
    for x in re.finditer(r'<div\b|</div>', text[i:]):
        d += 1 if x.group(0) != '</div>' else -1
        if d == 0:
            return text[i:i + x.end()]
    return None


def back_in_head(text):
    """The Back anchor's insides, from inside the report head only.
    comments_report and friday_status_report carry a Back in an ACTION
    BAR, which is not this round's subject - T1 learnt that by asking
    the whole page first and finding ten where there are eight."""
    blk = head_block(no_comments(text))
    if blk is None:
        return None
    m = re.search(r'<a[^>]*\b(?:back-button|action-back)\b[^>]*>(.*?)</a>',
                  blk, re.S)
    return m.group(1) if m else None


print('=' * 74)
print('%s - D2, THE ONE REPORT BACK WITHOUT AN ARROW' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE PAGE HE POINTED AT')
# ==========================================================================
inner = back_in_head(left(PAGE))
ok(inner is not None, '%s has a Back inside its report head' % PAGE)
if inner is not None:
    ok('fa-arrow-left' in inner, '  and it carries the arrow now',
       ' '.join(inner.split()))
    ok(inner.count('fa-arrow-left') == 1, '  exactly one arrow, not two',
       inner.count('fa-arrow-left'))
    ok(re.search(r'\bBack\b', inner) is not None,
       '  and the word Back survived - an icon alone is not a label')
    # THE ARROW COMES FIRST. After the word it reads as a forward
    # action, which is the opposite of what it is.
    ok(inner.find('fa-arrow-left') < inner.find('Back'),
       '  the arrow sits AHEAD of the word, as the other seven write it')

# ==========================================================================
head('2. ONE LINE, AND NOTHING ELSE')
# ==========================================================================
bak = alv_tree.path_of(PAGE) + SUFFIX
if not os.path.isfile(bak):
    skip('the before and after', 'no %s backup' % SUFFIX)
else:
    was, now = read(bak).split('\n'), left(PAGE).split('\n')
    ops = [o for o in difflib.SequenceMatcher(None, was, now,
                                              autojunk=False).get_opcodes()
           if o[0] != 'equal']
    ok(len(ops) == 1, 'the template differs by exactly one region',
       ['%s %d:%d -> %d:%d' % o for o in ops])
    if len(ops) == 1:
        op, i1, i2, j1, j2 = ops[0]
        ok(op == 'replace' and (i2 - i1, j2 - j1) == (1, 1),
           '  and it is one line replaced by one line',
           '%s, %d -> %d line(s)' % (op, i2 - i1, j2 - j1))
        if (i2 - i1, j2 - j1) == (1, 1):
            ok(was[i1].replace('Back', ARROW + 'Back', 1) == now[j1],
               '  which is the old line with the arrow inserted, and no '
               'other edit', 'was %r\nnow %r' % (was[i1], now[j1]))
    # CONTROL: it really was missing before.
    ok('fa-arrow-left' not in (back_in_head(read(bak)) or ''),
       'CONTROL: before this round that Back had no arrow')

# ==========================================================================
head('3. EIGHT REPORT HEADS, EIGHT ARROWS')
# ==========================================================================
# Written so that a page LOSING its arrow fails here. That is the whole
# value of the check - the defect this round fixes was one page quietly
# not doing what the other seven did.
for rel in EIGHT:
    inner = back_in_head(left(rel))
    if inner is None:
        ok(False, '%-30s has a Back in its report head'
           % rel.replace('.html', ''))
        continue
    ok('fa-arrow-left' in inner and re.search(r'\bBack\b', inner) is not None,
       '%-30s arrow, then the word' % rel.replace('.html', ''),
       ' '.join(inner.split())[:70])

edited = [alv_tree.rel(q) for q in alv_tree.templates()
          if os.path.isfile(q + SUFFIX)]
ok(edited == [alv_tree.rel(alv_tree.path_of(PAGE))],
   'and %s is the only file this round wrote' % PAGE, edited)

# ==========================================================================
head('4. THE GATE')
# ==========================================================================
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skip('the gate', '%s not on disk' % PS1)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
