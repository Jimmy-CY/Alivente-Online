# -*- coding: utf-8 -*-
"""SECTION P, ROUND P5 - THREE STATS ON ONE LINE

Demetri, on the Task List: "Can we fit Total Tasks, Completed and
Pending in one line, in smaller boxes (for the mobile)."

They go two-up and then one, because base takes every stats strip to two
columns below 768px:

    .alv-stats { grid-template-columns: repeat(2, 1fr); gap: 10px; }

WHY NOT JUST CHANGE THAT. fsr has FIVE stats and tenant_payment_days has
four; both rely on that rule. Three across is right for a strip of
three and wrong for a strip of five, so this is an opt-in, not a new
default.

AND WHY THE TYPE TIGHTENS TOO, which is measured rather than taste.
Three across at base's existing phone sizes fits at 386px and WRAPS
below it. Measured in Chromium, the height of the "Total Tasks" label:

    width   base sizes, 3-up      tightened
    320     37px  (two lines)     16px
    360     37px  (two lines)     16px
    386     19px                  16px
    414     19px                  16px

360 is an ordinary Android width and 320 is an older iPhone, so a strip
that only holds its line on the larger phones is not finished. The
tightening takes the box from 112x73 to 113x64 at 386 - which is also
the "smaller boxes" Demetri asked for.

ONE CLASS, NOT A VARIABLE. --alv-stats-cols would set the column count
but cannot reach the padding and the type, and those have to move
together or the labels wrap. .is-3up says one thing - three across on a
phone - and carries all four rules. The is- prefix is base's own:
.alv-filter.is-open, .alv-stats-collapse.is-open, .table-container
.is-stuck, .status-btn.is-disabled.

NOT SWEPT IN. finance/financial_indicators and finance/vacancy_management
also show three stats and could take this. Demetri asked about the Task
List, and nobody has walked those two screens. They are named in the
suite rather than opted in on a guess.

Backups: .bak_stats3up. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_stats3up'
CRLF = {}
SENTINEL = 'test_stats_3up.py'
PAGE = os.path.join('projects', 'project_task_list.html')


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
            raise SystemExit('P5: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o, n = eol(path, old), eol(path, new)
    c = text.count(o)
    if c != 1:
        raise SystemExit('P5: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


# ==========================================================================
print('=' * 74)
print('SECTION P, ROUND P5 - THREE STATS ON ONE LINE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ---- base gains the opt-in, inside its own phone block -----------------
BP = alv_tree.path_of('base.html')
bt, braw = read(BP)
if SENTINEL in bt:
    print('  base already done')
else:
    ANCHOR = ('        .alv-stats { grid-template-columns: repeat(2, 1fr); '
              'gap: 10px; }\n'
              '        .alv-stat { padding: 12px 10px; }\n'
              '        .alv-stat-value { font-size: 1.4rem; }\n')
    NEW = ANCHOR + """
        /* THREE ACROSS, FOR A STRIP OF THREE - 1 Oct 2026.
           Two columns is right for four or five stats and leaves a
           strip of three as 2 + 1. Demetri asked for the Task List's
           three on one line.

           The type tightens with the column count because it has to:
           three across at the sizes above holds its label on one line
           at 386px and WRAPS at 360 and 320. Measured, "Total Tasks":
           37px tall at those widths untightened, 16px with this.
           360 is an ordinary Android width.

           overflow-wrap is for GREEK. This page has a language switch,
           and the Greek labels are long words - a 13-character
           OLOKLIROMENES does not fit an 83px box and SPILLS OUT of it
           at 320 and 360 without this. English never needs it. The
           before measured the same spill at 320 already, so this fixes
           something that was there and stops the round spreading it to
           360.

           Opt in with .is-3up. It is not the default, because fsr has
           five stats and three of those would be 77px wide.
                                                [test_stats_3up.py] */
        .alv-stats.is-3up { grid-template-columns: repeat(3, 1fr);
                            gap: 8px; }
        .alv-stats.is-3up .alv-stat { padding: 10px 4px; }
        .alv-stats.is-3up .alv-stat-value { font-size: 1.25rem; }
        .alv-stats.is-3up .alv-stat-label { font-size: 0.66rem;
                                            letter-spacing: .2px;
                                            overflow-wrap: break-word; }
"""
    bt = swap(bt, ANCHOR, NEW, 'base\'s phone stats block', BP)
    # it must land INSIDE the phone media query, not after it
    at = bt.find('.alv-stats.is-3up')
    depth = bt.count('{', 0, at) - bt.count('}', 0, at)
    if depth != 1:
        raise SystemExit('P5: the opt-in landed at depth %d, not inside the '
                         'phone block' % depth)
    if not CHECK:
        back_up(BP, braw)
        write(BP, bt)
    print('  base.html                      .alv-stats.is-3up, inside the '
          'phone block')

# ---- the Task List opts in --------------------------------------------
PATH = alv_tree.join(PAGE)
t, raw = read(PATH)
if 'alv-stats task-summary is-3up' in t:
    print('  %-30s already done' % PAGE.replace(os.sep, '/'))
else:
    t = swap(t, '<div class="alv-stats task-summary">',
             '<div class="alv-stats task-summary is-3up">',
             'the Task List stats strip', PATH)
    body = re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->|\{#.*?#\}', '', t, flags=re.S),
                  flags=re.S)
    if body.count('is-3up') != 1:
        raise SystemExit('P5: is-3up appears %d times on the page, not 1'
                         % body.count('is-3up'))
    if body.count('alv-stat ') + body.count('alv-stat alv-stat') != 3:
        n = len(re.findall(r'class="alv-stat(?:\s|")', body))
        if n != 3:
            raise SystemExit('P5: the strip has %d stats, not 3 - is-3up '
                             'would be wrong' % n)
    if not CHECK:
        back_up(PATH, raw)
        write(PATH, t)
    print('  %-30s opted in (3 stats)' % PAGE.replace(os.sep, '/'))

# ---- GATES -------------------------------------------------------------
print('-' * 74)
# NOBODY ELSE OPTED IN. A strip of four or five taking is-3up would cut
# a column off, and that is the failure this round must not cause.
wrong = {}
for q in alv_tree.templates():
    src = read(q)[0]
    if 'is-3up' not in src or os.path.basename(q) == 'base.html':
        continue
    body = re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->|\{#.*?#\}', '', src, flags=re.S),
                  flags=re.S)
    n = len(re.findall(r'class="alv-stat(?:\s|")', body))
    if n != 3:
        wrong[alv_tree.rel(q)] = n
if wrong:
    raise SystemExit('P5: a strip that is not three stats wears is-3up: %s'
                     % wrong)
print('  and every page wearing is-3up really has exactly three stats')

print('-' * 74)
print('  Total Tasks, Completed and Pending sit on one line on a phone,')
print('  down to 320px, and the labels hold their line.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
