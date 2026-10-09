# -*- coding: utf-8 -*-
"""issue_date_check.py - IS-1, 9 Oct 2026. READ-ONLY. It never writes.

Finds issues that are OPEN BY STATUS and DATED BY FIELD - the state a
re-opened issue was left in before IS-1 put an `else` in
fsr_commit_status_change, so the row is open and closed at once.

WHY YOU CANNOT FIND THESE IN THE APP. comments_report.html renders the
resolution date only when `data.status === 'Resolved'`, so the field is
hidden on exactly the rows where it is wrong. The module has always
looked right from the front end for that reason.

IT DOES NOT WRITE, BY DESIGN. The one live row on 9 Oct 2026 was
corrected by hand in the database. This script is what says whether
that worked, and what says so again on any day after.

    railway ssh python issue_date_check.py

Exit code 1 if it finds any, so it can sit in a check later if wanted.
"""
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from datetime import date                                  # noqa: E402

from pages.models import issues                            # noqa: E402

SENTINEL = date(1900, 1, 1)
RESOLVED = 'Resolved'


def main():
    bad, resolved_undated = [], []
    for i in issues.objects.all():
        st = (i.issues_status or '').strip()
        d = i.issues_resolution_date
        dated = d is not None and d != SENTINEL
        if st != RESOLVED and dated:
            bad.append(i)
        if st == RESOLVED and not dated:
            resolved_undated.append(i)

    print('')
    print('=' * 70)
    print('  OPEN BY STATUS, DATED BY FIELD - %d row(s)' % len(bad))
    print('=' * 70)
    if bad:
        print('  %-7s %-13s %-12s %-12s %s'
              % ('id', 'status', 'logged', 'resolution', 'heading'))
        print('  ' + '-' * 66)
        for i in bad:
            print('  %-7s %-13s %-12s %-12s %s'
                  % (i.issues_id, (i.issues_status or '').strip(),
                     i.issues_date_logged, i.issues_resolution_date,
                     (i.issues_heading or '')[:28]))
        print('')
        print('  Each of these is counted OPEN by status and counted as a')
        print('  CLOSURE by date in the same window. Set the resolution')
        print('  date to 1900-01-01 - the sentinel - not to NULL:')
        print('  issues.py:627 compares this field without a None guard.')
    else:
        print('  None. Every row that is not Resolved reads as undated.')

    print('')
    print('  RESOLVED WITH NO DATE - %d row(s)' % len(resolved_undated))
    print('  ' + '-' * 66)
    if resolved_undated:
        for i in resolved_undated:
            print('  %-7s %-12s %s'
                  % (i.issues_id, i.issues_date_logged,
                     (i.issues_heading or '')[:40]))
        print('')
        print('  His rule: every Resolved issue must have a resolution')
        print('  date. These break it. The add form can create one by')
        print('  posting status Resolved with the hidden 1900-01-01.')
    else:
        print('  None - every Resolved row carries a real date.')

    print('')
    return 1 if (bad or resolved_undated) else 0


if __name__ == '__main__':
    sys.exit(main())
