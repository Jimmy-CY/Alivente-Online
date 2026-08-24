<#
.SYNOPSIS
    Where is financial history being lost or left dangling? Read-only, LIVE.

.DESCRIPTION
    FinancialFigureHistory is keyed on `source_pk` - a plain integer holding an
    expense_id / revenue_id / prop_values_id / act_expense_id. It is NOT a
    foreign key, so nothing cascades and nothing complains when the row it
    points at disappears. Four sections:

      A. ORPHANS
         Snapshots whose source row no longer exists. Dead weight, and the
         history they hold is unreachable - the P&L only ever re-colours rows
         that are still live.

      B. PRO-RATA GROUPS
         The pro-rata edit screen used to delete every row in a (line type,
         expense type) group and recreate it, changing every expense_id and
         orphaning every snapshot keyed on it. Fixed on 24 Aug 2026 - it now
         updates in place. This lists the groups and the history they carry,
         which is what that fix protects.

      C. BASELINE COVERAGE
         A row whose earliest snapshot is dated after the start of a year
         resolves to blank for every month before it - that is how the EUR
         7,000 Company Tax vanished. This counts rows with history but no
         baseline, grouped by which write path created them.

      D. SUMMARY

    Read-only: no INSERT, no UPDATE, no DELETE, nothing left behind on Live.

.PARAMETER Detail
    List every affected row, not just the counts.

.PARAMETER Service
    Railway service name, if `railway link` points somewhere else.

.EXAMPLE
    .\Show-HistoryOrphans.ps1
    .\Show-HistoryOrphans.ps1 -Detail
#>

[CmdletBinding()]
param(
    [switch] $Detail,
    [string] $Service = ""
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "!!  Railway CLI not found. Install: npm i -g @railway/cli" -ForegroundColor Red
    exit 1
}

$python = @'
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, '.')
import django
django.setup()

from datetime import date
from pages.models import (expense, revenue, act_expense, prop_values,
                          expense_line_types, FinancialFigureHistory)

DETAIL = __DETAIL__
BAR = '=' * 104
MONTHS = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
BASELINE_CUTOFF = date(2001, 1, 1)   # anything this old is a baseline in spirit


def f(v):
    return 0.0 if v is None else float(v)


# kind string, live model, pk attribute, human label
KINDS = [
    ('budget_expense', expense,     'expense_id',      'Budgeted expense'),
    ('revenue',        revenue,     'revenue_id',      'Direct / seasonal revenue'),
    ('valuation',      prop_values, 'prop_values_id',  'Property valuation'),
    ('expense_actual', act_expense, 'act_expense_id',  'Actual expense amendment'),
]

ALL = list(FinancialFigureHistory.objects.select_related('prop').all())
print('')
print(BAR)
print('A. ORPHANED SNAPSHOTS  (source row no longer exists)')
print(BAR)
print('%d snapshot(s) in financial_figure_history in total.' % len(ALL))

orphan_total = 0
orphan_rows_by_kind = {}

for kind, model, pk_attr, label in KINDS:
    live = set(model.objects.values_list(pk_attr, flat=True))
    mine = [h for h in ALL if h.kind == kind]
    orphans = [h for h in mine if h.source_pk not in live]
    orphan_rows_by_kind[kind] = orphans
    orphan_total += len(orphans)

    by_pk = {}
    for h in orphans:
        by_pk.setdefault(h.source_pk, []).append(h)

    print('')
    print('  %-28s %4d live row(s), %4d snapshot(s), %4d ORPHAN in %d dead source(s)'
          % (label, len(live), len(mine), len(orphans), len(by_pk)))

    if not orphans:
        continue

    tags = {}
    for h in orphans:
        tags[h.source or '(none)'] = tags.get(h.source or '(none)', 0) + 1
    print('      written by: %s'
          % ', '.join('%s x%d' % (k, v) for k, v in sorted(tags.items())))

    if DETAIL:
        print('      %-8s %-24s %-26s %-6s %-12s %-12s'
              % ('DEAD PK', 'PROPERTY', 'LINE TYPE', 'SNAPS', 'FIRST EFF', 'LAST EFF'))
        print('      ' + '-' * 92)
        for pk in sorted(by_pk):
            hs = sorted(by_pk[pk], key=lambda h: h.effective_date)
            print('      %-8s %-24s %-26s %-6d %-12s %-12s'
                  % (pk, (hs[0].prop.prop_name or '')[:24],
                     (hs[0].line_type or '')[:26], len(hs),
                     hs[0].effective_date, hs[-1].effective_date))

print('')
if orphan_total:
    print('  >> %d orphaned snapshot(s). Their history is unreachable: the P&L can'
          % orphan_total)
    print('     only re-colour rows that still exist live.')
else:
    print('  >> No orphans. Nothing has been lost yet.')

# ------------------------------------------------------------------ SECTION B
print('')
print(BAR)
print('B. PRO-RATA GROUPS AND THE HISTORY THEY NOW KEEP')
print(BAR)
print('Until 24 Aug 2026 finance_expense_edit_commit deleted every expense row')
print('sharing a (line type, expense type) pair and recreated it, so every')
print('expense_id changed and every snapshot below was cut adrift. That is what')
print('destroyed the Company Tax trail - the ten dead ids in section A.')
print('')
print('The edit now matches rows on the natural key and updates them in place,')
print('so this is the history being PROTECTED, not the history at risk. Section')
print('A is the regression test: edit any of these groups and the orphan count')
print('must not move.')

exp_rows = list(expense.objects.select_related('prop', 'expense_line_types',
                                               'expense_types').all())
hist_by_pk = {}
for h in ALL:
    if h.kind == 'budget_expense':
        hist_by_pk.setdefault(h.source_pk, []).append(h)

prorata_lt = {lt.expense_line_types_id: lt for lt in expense_line_types.objects.all()
              if (lt.expense_line_types_prorata or '').strip().lower() == 'yes'}

groups = {}
for e in exp_rows:
    if e.expense_line_types_id not in prorata_lt:
        continue
    key = (e.expense_line_types_id, e.expense_types_id)
    groups.setdefault(key, []).append(e)

print('')
print('  %d pro-rata line type(s), %d group(s) carrying history.'
      % (len(prorata_lt), len(groups)))

at_risk_groups, at_risk_snaps = 0, 0
if groups:
    print('')
    print('  %-26s %-16s %6s %8s %12s %-12s'
          % ('LINE TYPE', 'EXPENSE TYPE', 'ROWS', 'SNAPS', 'BUDGETED', 'OLDEST EFF'))
    print('  ' + '-' * 92)
    for key in sorted(groups, key=lambda k: str(prorata_lt[k[0]])):
        rows = groups[key]
        snaps = [h for e in rows for h in hist_by_pk.get(getattr(e, 'expense_id'), [])]
        budget = sum(f(getattr(e, 'expense_' + m)) for e in rows for m in MONTHS)
        oldest = min((h.effective_date for h in snaps), default=None)
        if snaps:
            at_risk_groups += 1
            at_risk_snaps += len(snaps)
        print('  %-26s %-16s %6d %8d %12.2f %-12s'
              % (str(prorata_lt[key[0]])[:26],
                 str(rows[0].expense_types)[:16], len(rows), len(snaps), budget,
                 oldest if oldest else '-'))

print('')
if at_risk_snaps:
    print('  >> %d snapshot(s) across %d group(s) that the old delete-and-recreate'
          % (at_risk_snaps, at_risk_groups))
    print('     would have destroyed. They survive an edit now.')
else:
    print('  >> No pro-rata group currently carries history.')

# ------------------------------------------------------------------ SECTION C
print('')
print(BAR)
print('C. BASELINE COVERAGE  (rows that would blank out a past year)')
print(BAR)
print('A row whose earliest snapshot falls after 1 Jan of a year resolves to')
print('blank for every month before it. A baseline snapshot prevents that.')

for kind, model, pk_attr, label in (KINDS[0], KINDS[1]):
    live_rows = list(model.objects.select_related('prop').all())
    mine = {}
    for h in ALL:
        if h.kind == kind:
            mine.setdefault(h.source_pk, []).append(h)

    with_hist, covered, exposed = 0, 0, []
    by_first_source = {}
    for r in live_rows:
        pk = getattr(r, pk_attr)
        hs = mine.get(pk)
        if not hs:
            continue
        with_hist += 1
        hs = sorted(hs, key=lambda h: (h.effective_date, h.changed_at))
        first = hs[0]
        tag = first.source or '(none)'
        by_first_source[tag] = by_first_source.get(tag, 0) + 1
        if first.source == 'baseline' or first.effective_date < BASELINE_CUTOFF:
            covered += 1
        else:
            exposed.append((pk, r, first, len(hs)))

    print('')
    print('  %s' % label)
    print('    %d live row(s), %d with history, %d baselined, %d EXPOSED'
          % (len(live_rows), with_hist, covered, len(exposed)))
    if by_first_source:
        print('    earliest snapshot written by: %s'
              % ', '.join('%s x%d' % (k, v) for k, v in sorted(by_first_source.items())))

    if exposed:
        # Two different symptoms, and it matters which is which:
        #   - the year CONTAINING the first snapshot goes part-blank, because
        #     the months before it resolve to None and the P&L drops them
        #   - years BEFORE that resolve to nothing at all, so the caller falls
        #     back to the live cells: today's figure shown for a past year
        print('    %-8s %-24s %-26s %-6s %-12s %s'
              % ('PK', 'PROPERTY', 'LINE TYPE', 'SNAPS', 'FIRST EFF', 'EFFECT'))
        print('    ' + '-' * 92)
        for pk, r, first, n in sorted(exposed, key=lambda t: t[2].effective_date):
            y = first.effective_date.year
            bits = []
            if first.effective_date > date(y, 1, 1):
                bits.append('%d part-blank' % y)
            bits.append('%d and earlier show today\'s figure' % (y - 1))
            print('    %-8s %-24s %-26s %-6d %-12s %s'
                  % (pk, (r.prop.prop_name or '')[:24],
                     (first.line_type or '')[:26], n, first.effective_date,
                     '; '.join(bits)))

# ------------------------------------------------------------------ SECTION D
print('')
print(BAR)
print('D. SUMMARY')
print(BAR)
print('  orphaned snapshots (history already unreachable) : %d' % orphan_total)
print('  snapshots the next pro-rata edit would orphan    : %d' % at_risk_snaps)
print('')
print('  Sections A and B are about row IDENTITY - history losing the row it')
print('  described. Section C is about COVERAGE - history that exists but does')
print('  not reach back far enough. They need different fixes.')
print(BAR)
print('')
'@

$python = $python.Replace('__DETAIL__', $(if ($Detail) { 'True' } else { 'False' }))

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
$remote = "echo '$b64' | base64 -d > /tmp/horph.py && python /tmp/horph.py; rc=`$?; rm -f /tmp/horph.py; exit `$rc"

$railwayArgs = @('ssh')
if ($Service) { $railwayArgs += @('--service', $Service) }
$railwayArgs += $remote

Write-Host "==> Auditing financial history on Live (read-only)" -ForegroundColor Cyan
Write-Host ""
& railway @railwayArgs
$code = $LASTEXITCODE
Write-Host ""
if ($code -eq 0) {
    Write-Host "==> Done. Nothing on Live was changed." -ForegroundColor Cyan
} else {
    Write-Host "!!  railway ssh exited with code $code" -ForegroundColor Red
    Write-Host "    Try:  railway link    (or add -Service <name>)"
}
exit $code
