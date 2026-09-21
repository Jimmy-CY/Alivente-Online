# -*- coding: utf-8 -*-
"""apply_history_purge.py - a financial row's history goes with it, on
every route a row can be deleted by.

    python apply_history_purge.py --check     dry run, nothing written
    python apply_history_purge.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

WHAT WAS MEASURED (21 Sep - Show-HistoryOrphans.ps1 -Detail on Live)

  178 snapshots. The same 30 orphans as on 21 Aug - Company Tax, three per
  dead expense id 28-37, all written before the 24 Aug fix - and NOT ONE
  new orphan in four weeks. The fix is holding for the path it fixed.

  Read on the live code, that is the only path it fixed. The history table
  keys on a plain integer, source_pk - not a foreign key - so nothing
  cascades when a row goes. purge_figure_history() is called by the two
  budgeted-expense delete paths in views/finance.py and by nothing else:

    act_expense  deleted by views/expenses.py mark_deleted() with no purge,
                 though its amount amendments write history
    revenue, prop_values  no delete path in the views - but a delete from
                 Django's admin, a property cascade or a queryset delete
                 would leave their history behind, silently

WHAT THIS DOES - agreed 21 Sep, "clean-up rule + archive & delete"

  1. pages/signals.py gains ONE post_delete receiver, connected to the four
     models that keep history - expense, revenue, prop_values, act_expense.
     Whatever deletes a row, its snapshots go in the same transaction. A
     queryset delete and a cascade send post_delete for every object, so
     this covers routes a view-level call never could. The two explicit
     purge calls in views/finance.py stay: belt and braces, and the
     receiver then finds nothing left to remove.
     NOT fail-safe, deliberately, for the reason purge_figure_history()
     gives in its own docstring: quietly leaving history behind is the
     failure being fixed.
  2. Show-HistoryOrphans.ps1's summary line said "snapshots the next
     pro-rata edit would orphan : 72" - true until 24 Aug, and its own
     section B says they survive an edit now. The line says what it counts.
  3. test_history_purge.py is wired onto the push gate.

  The 30 orphans already on Live are NOT touched by this - that is
  Remove-HistoryOrphans.ps1, run by hand after the deploy, dry run first.
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

import ast
import os
import re
import sys

CHECK = '--check' in sys.argv
if not os.path.isdir(os.path.join('pages', 'templates')):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_histpurge'
SUITE = 'test_history_purge.py'
PS1 = 'Push-PendingChanges.ps1'
SIGNALS = os.path.join('pages', 'signals.py')
SHOW = 'Show-HistoryOrphans.ps1'
MARK = 'FINANCIAL HISTORY GOES WITH ITS ROW'

report, problems = [], []
planned = {}
CRLF = {}


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


BLOCK = '''

# ============================================================================
# FINANCIAL HISTORY GOES WITH ITS ROW
# ============================================================================
# FinancialFigureHistory keys on source_pk - a plain integer, not a foreign
# key - so nothing cascades when the row it describes is deleted. Rows left
# behind are orphans: unreachable by the resolver, and waiting to attach
# themselves to whatever is ever given that id again. Thirty of them sit on
# Live from before 24 Aug, cut adrift by the old pro-rata delete-and-recreate.
#
# The views purge on the two budgeted-expense delete paths. This covers every
# other route - a delete from Django's admin, a property cascade, a queryset
# delete, the actual-expense delete that never purged - because Django sends
# post_delete for every object those remove. It runs inside the deleting
# transaction and is deliberately NOT fail-safe: quietly leaving history
# behind is the failure this exists to prevent.
#
# instance.pk is still set in post_delete; Django clears it afterwards.
# See test_history_purge.py and Remove-HistoryOrphans.ps1.
# ============================================================================
from .models import (expense as _fh_expense, revenue as _fh_revenue,
                     prop_values as _fh_prop_values,
                     act_expense as _fh_act_expense, FinancialFigureHistory,
                     KIND_VALUATION, KIND_ACTUAL_EXPENSE)

HISTORY_KIND_OF = {
    _fh_expense: FinancialFigureHistory.KIND_BUDGET,
    _fh_revenue: FinancialFigureHistory.KIND_REVENUE,
    _fh_prop_values: KIND_VALUATION,
    _fh_act_expense: KIND_ACTUAL_EXPENSE,
}


def purge_history_of_deleted_row(sender, instance, **kwargs):
    """Delete every history snapshot of a financial row being deleted."""
    kind = HISTORY_KIND_OF.get(sender)
    if kind is None or instance.pk is None:
        return
    FinancialFigureHistory.objects.filter(
        kind=kind, source_pk=instance.pk).delete()


for _fh_model in HISTORY_KIND_OF:
    post_delete.connect(purge_history_of_deleted_row, sender=_fh_model,
                        dispatch_uid='alv_history_purge_%s'
                        % _fh_model.__name__)
'''

# ---- 1. signals.py --------------------------------------------------------
src = read(SIGNALS)
if MARK in src:
    report.append('%-28s already purges on delete' % SIGNALS)
elif 'from django.db.models.signals import post_save, post_delete' not in src:
    problems.append('%s: post_delete is not imported where expected' % SIGNALS)
else:
    text = src.rstrip('\n') + '\n' + BLOCK
    planned[SIGNALS] = (src, text)
    report.append('%-28s + one post_delete receiver on expense, revenue, '
                  'prop_values, act_expense' % SIGNALS)

# ---- 2. Show-HistoryOrphans.ps1 summary line ------------------------------
SHOW_OLD = ("print('  snapshots the next pro-rata edit would orphan    : %d' "
            "% at_risk_snaps)")
SHOW_NEW = ("print('  pro-rata snapshots the 24 Aug fix protects       : %d' "
            "% at_risk_snaps)")
if os.path.isfile(SHOW):
    src = read(SHOW)
    if SHOW_NEW in src:
        report.append('%-28s already says what it counts' % SHOW)
    elif src.count(SHOW_OLD) != 1:
        problems.append('%s: summary line found %d time(s), expected 1'
                        % (SHOW, src.count(SHOW_OLD)))
    else:
        planned[SHOW] = (src, src.replace(SHOW_OLD, SHOW_NEW, 1))
        report.append('%-28s summary line says what it counts' % SHOW)
else:
    report.append('%-28s not on disk - nothing to correct' % SHOW)

# ---- 3. the gate ----------------------------------------------------------
GATE_NOTE = """    # A financial row's history goes with it, on every route. Its
    # database section builds the real schema in an in-memory SQLite,
    # deletes rows by a view-style delete, a queryset delete and a
    # property cascade, and requires their snapshots gone and a
    # neighbour's untouched. Its control disconnects the receiver and
    # must see the orphans come back. Newest, so most likely to be what
    # breaks.
    'test_history_purge.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-28s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        last = (re.search(r"'([A-Za-z0-9_.-]+\.py)'\s*$",
                          psrc[i:i + m.start()]) if m else None)
        if not last:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-28s + %s, after %s' % (PS1, SUITE,
                                                    last.group(1)))

# ==========================================================================
# SELF-CHECK
# ==========================================================================
if SIGNALS in planned:
    src, text = planned[SIGNALS]
    try:
        ast.parse(text)
    except SyntaxError as e:
        problems.append('%s: does not parse - line %s' % (SIGNALS, e.lineno))
    if not text.startswith(src.rstrip('\n')):
        problems.append('%s: more changed than the appended block' % SIGNALS)

print('\n' + '=' * 74)
print('HISTORY GOES WITH ITS ROW - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)
print('')
if problems:
    print('!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in problems:
        print('  FAIL %s' % p)
    sys.exit(1)
if not planned:
    print('  Nothing to do - this round has already been applied.')
    sys.exit(0)
if CHECK:
    print('  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)
for path, (src, text) in sorted(planned.items()):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        CRLF[bak] = CRLF.get(path)
        write(bak, src)
    write(path, text)
print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('  %d keep CRLF line endings, %d keep LF'
      % (sum(1 for p in planned if CRLF.get(p)),
         sum(1 for p in planned if not CRLF.get(p))))
print('')
print('  Next:  python %s' % SUITE)
print('         after the deploy: .\\Remove-HistoryOrphans.ps1   (dry run)')
