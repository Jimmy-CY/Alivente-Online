# -*- coding: utf-8 -*-
"""issue_status_census.py - HM-2, 8 Oct 2026. READ-ONLY.

WHAT THIS IS FOR
================
`issues.issues_status` is a free `CharField(max_length=255)` with NO
choices. The app writes three spellings - Resolved, Unresolved, Issue -
and `pages/views/dashboard.py` treats the last two as open:

    issues_status__in=['Unresolved', 'Issue']

Nothing stops a fourth spelling existing. A panel built on an assumed
vocabulary is a panel that quietly undercounts, and a status nobody
expected would land in neither column. So HM-2 counts the real values
BEFORE it is designed, rather than after somebody notices the totals do
not add up.

WHAT IT DOES
============
Prints, for whichever database the settings it loads point at:

  * every distinct issues_status, with its count and its percentage;
  * which of them the app can write, and which it cannot;
  * how many rows have a resolution date against each status, because
    `Resolved with no date` and `open with a date` are both real and
    both break a count built on one field;
  * the span of issues_date_logged, which is what sets the period
    length the comparisons can honestly use.

IT WRITES NOTHING, and it prints no connection details, no credentials
and no issue text - only statuses, counts and dates.

WHERE TO RUN IT
===============
It uses whatever DJANGO_SETTINGS_MODULE resolves to, so WHERE you run
it decides WHAT it measures:

    python issue_status_census.py          - your local dev database
    railway run python issue_status_census.py   - the live one

HM-2 needs the live numbers. The local run is still worth having: if
the two vocabularies differ, that difference is itself the finding.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

import django                                              # noqa: E402
django.setup()                                             # noqa: E402

from django.db.models import Count, Min, Max               # noqa: E402
from pages.models import issues                            # noqa: E402

# The spellings the app itself can produce: the three in the
# fsr_details.html status select, plus the pair dashboard.py counts as
# open. Anything outside this set got there some other way.
KNOWN = ('Resolved', 'Unresolved', 'Issue')
OPEN_PER_DASHBOARD = ('Unresolved', 'Issue')

total = issues.objects.count()
print('')
print('=' * 70)
print('  ISSUE STATUS CENSUS - %d row(s)' % total)
print('=' * 70)
if not total:
    print('  No issues on this database. Run it where the data is.')
    raise SystemExit(0)

rows = list(issues.objects.values('issues_status')
            .annotate(n=Count('issues_id'))
            .order_by('-n'))

print('')
print('  %-34s %7s %7s  %s' % ('status', 'count', 'pct', 'the app can write it'))
print('  ' + '-' * 66)
unknown = []
for r in rows:
    s = r['issues_status']
    known = s in KNOWN
    if not known:
        unknown.append((s, r['n']))
    print('  %-34s %7d %6.1f%%  %s'
          % (repr(s), r['n'], 100.0 * r['n'] / total,
             'yes' if known else 'NO - unexpected'))

print('')
if unknown:
    print('  %d UNEXPECTED SPELLING(S), %d row(s) in all. HM-2 cannot treat'
          % (len(unknown), sum(n for _s, n in unknown)))
    print('  these as either open or resolved without being told which:')
    for s, n in unknown:
        print('     %-34s %d' % (repr(s), n))
else:
    print('  Every value is one the app can write. The vocabulary is the')
    print('  three the status select offers and nothing else.')

missing = [k for k in KNOWN if k not in [r['issues_status'] for r in rows]]
if missing:
    print('  (%s occur(s) nowhere in the data, though the app offers it.)'
          % ', '.join(repr(m) for m in missing))

# ---- the resolution date against the status -------------------------
print('')
print('  RESOLUTION DATE vs STATUS')
print('  ' + '-' * 66)
print('  %-34s %10s %10s' % ('status', 'has date', 'no date'))
for r in rows:
    s = r['issues_status']
    q = issues.objects.filter(issues_status=s)
    has = q.exclude(issues_resolution_date=None).count()
    print('  %-34s %10d %10d' % (repr(s), has, r['n'] - has))
print('')
print('  A row counted open BY STATUS that carries a resolution date, or')
print('  one counted resolved without one, is a row two honest methods')
print('  would count differently. HM-2 has to pick one field and say so.')

openq = issues.objects.filter(issues_status__in=OPEN_PER_DASHBOARD)
print('')
print("  Open by dashboard.py's rule (%s): %d of %d"
      % (' or '.join(OPEN_PER_DASHBOARD), openq.count(), total))
print('  Open by "no resolution date"                 : %d of %d'
      % (issues.objects.filter(issues_resolution_date=None).count(), total))

# ---- the span, which sets the period length -------------------------
span = issues.objects.aggregate(lo=Min('issues_date_logged'),
                                hi=Max('issues_date_logged'))
nodate = issues.objects.filter(issues_date_logged=None).count()
print('')
print('  LOGGED DATES')
print('  ' + '-' * 66)
print('  earliest : %s' % span['lo'])
print('  latest   : %s' % span['hi'])
print('  no date  : %d row(s)' % nodate)
if nodate:
    print('')
    print('  Those %d cannot be placed in a period at all, so they can be' % nodate)
    print('  in the status counts and not in the comparisons. HM-2 says')
    print('  which, in the panel, rather than leaving a total that does')
    print('  not add up.')
print('')
