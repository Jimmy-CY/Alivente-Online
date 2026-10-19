# -*- coding: utf-8 -*-
"""bundle_r4p1.py - Release 4, push 1, as one directory he can copy.

THE APPLIED LIST IS ENUMERATED FROM THE .bak FILES ON DISK, never
typed. The 17 October push shipped a hand-written list and two files
were missing from it; a round's own backups are the only record of what
it touched that cannot disagree with the tree.

AND revert_all.sh RUNS NEWEST FIRST. All three of these rounds write
to Push-PendingChanges.ps1, alv_tree.py, alv_rounds.py and
test_waiting_down.py. Reverting oldest-first restores the LATER
round's text over the earlier one and loses the original - the 18
October bug, which cost a hand repair of Push-PendingChanges.ps1 and a
programmatic undo of RT-1's alv_rounds blocks.

ONE FILE IN THIS PUSH IS DELETED AND NOT CHANGED:

    test_mini_grid.py                           retired by MV-2

MC-4 built it to render the mini calendar, and MV-2 deletes that
component. Its BACKUP is staged like any other, which is what makes
the retirement reversible, and revert_all.sh restores it.

So one backup has no live file beside it. That is a RETIREMENT and
not a half-applied tree - the distinction the 17 October push taught -
and stage_round tells the two apart by asking alv_rounds rather than
guessing. The exact numbers are printed below rather than written
here, because a number in a comment goes stale. revert_all.sh
DELETES them, because a revert that left them behind would leave a
migration Django would try to run against a table that still exists.
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = '/mnt/user-data/outputs/R4P1'
SKIP = ('.git', '__pycache__', 'media', 'node_modules', 'staticfiles')

# NEWEST FIRST, which is also revert order.
ORDER = [
    ('.bak_dayview', 'MV-4', 'apply_day_view.py',
     'test_day_view.py', 'one day in full, and the list of seven goes'),
    ('.bak_weekcols', 'MV-3', 'apply_week_cols.py',
     'test_week_cols.py', 'the week is seven columns'),
    ('.bak_monthview', 'MV-2', 'apply_month_view.py',
     'test_month_view.py', 'the month is the view, and the mini '
     'calendar is deleted'),
    ('.bak_viewswitch', 'MV-1', 'apply_view_switch.py',
     'test_view_switch.py', 'three zoom levels on one calendar'),
]

# WRITTEN BY A ROUND, BACKED UP BY NONE - there was no before.
NEW = {}

EXTRA = ('stage_round.py', 'bundle_r4p1.py')


def main():
    if os.path.isdir(OUT):
        for n in os.listdir(OUT):
            p = os.path.join(OUT, n)
            if os.path.isdir(p):
                shutil.rmtree(p)
            elif not (n.endswith('.png') or n.endswith('.html')):
                os.remove(p)
    os.makedirs(OUT, exist_ok=True)

    per, files = {}, set(EXTRA)
    for suf, name, ap, su, _why in ORDER:
        files.add(ap)
        files.add(su)
        baks = []
        for folder, dirs, names in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in SKIP]
            for n in names:
                if n.endswith(suf):
                    baks.append(os.path.join(folder, n))
        if not baks:
            raise SystemExit('bundle: %s (%s) is not applied' % (name, suf))
        applied = sorted(os.path.relpath(b[:-len(suf)], ROOT) for b in baks)
        # A BACKUP WITH NO LIVE FILE IS A RETIREMENT, not a
        # half-applied tree - MV-2 removes test_mini_grid.py with the
        # component it judged. The backup is staged either way, which
        # is what makes the removal reversible.
        missing = [p for p in applied
                   if not os.path.isfile(os.path.join(ROOT, p))]
        applied = [p for p in applied
                   if os.path.isfile(os.path.join(ROOT, p))]
        if missing:
            print('  %-5s retires %s' % (name, ', '.join(missing)))
        per[name] = applied
        files.update(applied)
        for extra in NEW.get(name, ()):
            if not os.path.isfile(os.path.join(ROOT, extra)):
                raise SystemExit('bundle: %s should have created %s'
                                 % (name, extra))
            files.add(extra)
        files.update(os.path.relpath(b, ROOT) for b in baks)

    for rel in sorted(files):
        src = os.path.join(ROOT, rel)
        if not os.path.isfile(src):
            raise SystemExit('bundle: %s is not in the tree' % rel)
        dst = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)

    sh = ['#!/bin/sh',
          '# revert_all.sh - Release 4, push 1. NEWEST ROUND FIRST.',
          '#',
          '# All four rounds write to Push-PendingChanges.ps1,',
          '# alv_tree.py, alv_rounds.py, test_waiting_down.py and',
          '# meal_planner.html.',
          '# Reverting oldest-first restores the LATER round\'s text over',
          '# the earlier one and loses the original. That is the 18 Oct',
          '# bug and it cost a hand repair.',
          '#',
          '# ONE FILE IS RESTORED rather than reverted: MV-2 retired',
          '# test_mini_grid.py and removed it from disk. Its backup is',
          '# here, so copying it back is the revert.',
          '#',
          '# Run from the repo root.',
          'set -e']
    for suf, name, _ap, _su, why in ORDER:
        sh += ['',
               'echo "reverting %s - %s"' % (name, why),
               'find . -name "*%s" -not -path "./.git/*" | while read b; do'
               % suf,
               '  f="${b%%%s}"; cp "$b" "$f"; rm "$b"' % suf,
               'done']
        for extra in NEW.get(name, ()):
            sh += ['rm -f "%s"   # created by %s, no before to restore'
                   % (extra, name)]
    sh += ['',
           'echo "all four reverted. Backups still on disk (want 0):"',
           'find . \\( ' + ' -o '.join(
               '-name "*%s"' % s for s, _, _, _, _ in ORDER)
           + ' \\) -not -path "./.git/*" | wc -l']
    open(os.path.join(OUT, 'revert_all.sh'), 'w', newline='\n').write(
        '\n'.join(sh) + '\n')

    n_bak = sum(len(v) for v in per.values())
    n_new = sum(len(v) for v in NEW.values())
    print('R4P1 -> %s' % OUT)
    for suf, name, _ap, _su, why in ORDER:
        print('  %-5s %-2d file(s)%s  %s'
              % (name, len(per[name]) + len(NEW.get(name, ())),
                 ' (%d new)' % len(NEW[name]) if name in NEW else '     ',
                 why))
    print('  %d file-edits across the four, %d backups, %d files staged'
          % (n_bak + n_new, n_bak, len(files)))
    print('  revert_all.sh: newest first - %s'
          % ', '.join(n for _, n, _, _, _ in ORDER))
    return 0


if __name__ == '__main__':
    sys.exit(main())
