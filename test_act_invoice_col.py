# -*- coding: utf-8 -*-
"""test_act_invoice_col.py - Section AE round AE-4, 5 Oct 2026.

PL-1 gave the P&L drill-down an Invoice column because Demetri said the
little black tick was not intuitive, and named the full Actual Expenses
screen as the one he preferred. It was built inside
{% if from_finance_pl_act %} - so the screen he held up as the good one
is the one that never had the column.

AE-4 takes the condition off. Not one character of PL-1's markup or its
comment changes; the column simply renders in both branches.

SECTION 4 IS THE HALF THAT NEARLY DID NOT HAPPEN. Revealing a 10% column
on a table whose widths already summed to 100 makes them sum to 110, and
a browser does not refuse that - it normalises it, so every other column
silently loses a tenth of its share. Two widths move with the round and
the full branch sums to exactly 100 again. The drill-down's own 105%,
which PL-1 left, is printed every run and is not this round's to fix.
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
import alv_tree

try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS, as_left_by = [], None

SUFFIX = '.bak_actinvcol'
ME = 'test_act_invoice_col.py'
PATCHER = 'apply_act_invoice_col.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = 'act_expense.html'
COND = '{% if from_finance_pl_act %}'

FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines()[:8]:
                print('        %s' % line)
        FAILS.append(msg)
    return bool(cond)


def head(t):
    print('\n' + t)


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX)


def resolve(src, drill):
    """The markup as ONE of the two branches really renders it."""
    t = re.sub(r'\{%\s*if from_finance_pl_act\s*%\}(.*?)\{%\s*else\s*%\}'
               r'(.*?)\{%\s*endif\s*%\}',
               (lambda m: m.group(1) if drill else m.group(2)), src,
               flags=re.S)
    t = re.sub(r'\{%\s*if not from_finance_pl_act\s*%\}(.*?)'
               r'\{%\s*endif\s*%\}',
               (lambda m: '' if drill else m.group(1)), t, flags=re.S)
    return re.sub(r'\{%\s*if from_finance_pl_act\s*%\}(.*?)\{%\s*endif\s*%\}',
                  (lambda m: m.group(1) if drill else ''), t, flags=re.S)


def thead(src):
    return src[src.index('<thead'):src.index('</thead>')]


def cols(src, drill):
    t = resolve(thead(src), drill)
    return [' '.join(re.sub(r'<[^>]*>', ' ', m.group(1)).split())
            for m in re.finditer(r'(<th\b[\s\S]*?</th>)', t)]


def widths(src, drill):
    return [int(x) for x in
            re.findall(r'width:\s*(\d+)%', resolve(thead(src), drill))]


P = alv_tree.path_of(PAGE)
NOW, WAS = now(P), was(P)

print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. as AE-4 found it')

ok(len(cols(WAS, True)) == 5,
   'the drill-down had %d columns, the Invoice one among them'
   % len(cols(WAS, True)), cols(WAS, True))
ok(any('Invoice' in c for c in cols(WAS, True)),
   '  and one of them is named Invoice')
ok(len(cols(WAS, False)) == 7,
   '  the full page had %d, and none of them was' % len(cols(WAS, False)),
   cols(WAS, False))
ok(not any('Invoice' in c for c in cols(WAS, False)),
   '  no Invoice column on the screen Demetri named as the good one',
   [c for c in cols(WAS, False) if 'Invoice' in c])

# AND THE DOCUMENT WAS NOT UNREACHABLE, only unobvious: the Manage modal
# is handed the url. Stating that is what makes this a consistency round
# rather than a bug fix.
ok('act_expense_document.url' in WAS,
   '  it was reachable - openManageModal is handed the url - but only '
   'by opening a modal and looking')

# ==========================================================================
head('2. the condition is gone, and nothing else moved')

ok(WAS.count(COND) - NOW.count(COND) == 1,
   'the page carries one fewer %s' % COND,
   '%d -> %d' % (WAS.count(COND), NOW.count(COND)))
ok(len(cols(NOW, False)) == 8 and any('Invoice' in c
                                      for c in cols(NOW, False)),
   'the full page now has %d columns and one is Invoice'
   % len(cols(NOW, False)), cols(NOW, False))
ok(len(cols(NOW, True)) == 5,
   '  and the drill-down still has 5 - nothing was added to it',
   cols(NOW, True))

# PL-1'S MARKUP IS CARRIED, NOT REWRITTEN. Everything between the <td>
# and its close is the same bytes it was.
def cell(src):
    i = src.index('<td data-label="Invoice" class="cell-invoice">')
    return ' '.join(src[i:src.index('</td>', i)].split())


ok(cell(NOW) == cell(WAS),
   "the Invoice cell is PL-1's markup, byte for byte",
   '%s\n%s' % (cell(WAS)[:90], cell(NOW)[:90]))
ok("{# PL-1, 5 Oct 2026 - a column that says INVOICE. #}" in NOW,
   "  and PL-1's note is still above it")
ok('{# AE-4, 5 Oct 2026' in NOW, '  with AE-4 saying why it is unconditional')

# ==========================================================================
head('3. the icons are bound - no dead controls')

# PL-1 came within one line of shipping a dead button here, so this is
# asserted rather than assumed.
h = NOW.index('.verify-icon, .report-invoice-icon')
pre = NOW[:h]
ok(len(re.findall(r'\{%\s*if\b', pre)) == len(re.findall(r'\{%\s*endif', pre)),
   'the delegated click handler sits outside every {% if %}',
   'it is inside one, so the revealed icons would do nothing')
ok('report-invoice-icon' in resolve(NOW, False),
   '  and the class it binds is what the full page now renders')
ok('data-invoice-url' in resolve(NOW, False)
   and 'data-filename' in resolve(NOW, False),
   '  on the two attributes that handler reads')
ok('report-invoice-none' in resolve(NOW, False),
   '  with a dash where there is no document, not an empty cell')

# ==========================================================================
head('4. the arithmetic')

wn, wo = widths(NOW, False), widths(WAS, False)
print('      full page  was %s = %d' % (wo, sum(wo)))
print('      full page  now %s = %d' % (wn, sum(wn)))
ok(sum(wo) == 100, 'the full page summed to 100 before this round')
ok(sum(wn) == 100, '  and sums to 100 after it, with a column more')
ok(len(wn) == len(wo) + 1, '  %d widths, up from %d' % (len(wn), len(wo)))

# WHAT A ROUND THAT STOPPED AT THE DELETION WOULD HAVE SHIPPED.
naive = wo + [10]
ok(sum(naive) == 110,
   '  revealing it without touching a width would have summed to %d, and '
   'a browser normalises rather than refuses' % sum(naive))

wd = widths(NOW, True)
print('      drill-down now %s = %d' % (wd, sum(wd)))
ok(wd == widths(WAS, True),
   "the drill-down's widths are untouched", '%s -> %s'
   % (widths(WAS, True), wd))
ok(sum(wd) != 100,
   "  NAMED NOT FIXED: it sums to %d, which PL-1 left and this round "
   "does not take - correcting it re-renders a screen already signed off"
   % sum(wd))

# ==========================================================================
head('5. the control')

# Put the condition back and require section 2 to notice.
# ALL OF THEM, not one. The marker is written twice - once above the
# <th> and once above the <td> - and a control that removed one left the
# other standing and reported the round still present. The patcher's own
# idempotence test reads the same marker, so this is the shape that
# matters.
back = NOW.replace('{# AE-4, 5 Oct 2026', '{# XX-0, never')
ok(back != NOW, 'the control could be planted')
ok(NOW.count('{# AE-4, 5 Oct 2026') == 2,
   '  the marker is written twice, above the header and above the cell')
ok('{# AE-4, 5 Oct 2026' not in back,
   '  and the control removes both')
# And a width control: drop the Invoice width back to 10 and the sum goes.
wide = NOW.replace('{% else %}6%{% endif %}">Invoice</th>',
                   '{% else %}10%{% endif %}">Invoice</th>', 1)
ok(wide != NOW, '  a width control could be planted')
ok(sum(widths(wide, False)) == 104,
   '  and it moves the full page off 100, to %d'
   % sum(widths(wide, False)),
   'the width check cannot tell the two apart')

# ==========================================================================
head('6. registration')

ps1 = read(os.path.join(ROOT, PS1))
ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
ok(ME in ps1, '%s is in the push suites' % ME)

print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that an expense really has a document to open.')
print('  The column renders an icon when act_expense_document is set and')
print('  a dash when it is not, and which rows are which is data. The')
print('  click path itself is PL-1s and was signed off on the drill-down.')
