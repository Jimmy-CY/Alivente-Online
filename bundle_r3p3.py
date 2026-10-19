# -*- coding: utf-8 -*-
"""bundle_r3p3.py - Release 3, push 3, as one directory he can copy.

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

TWO FILES IN THIS PUSH ARE NEW AND HAVE NO BACKUP:

    pages/migrations/0101_drop_meal_plan.py     MX-1
    pages/views/recipes/_recipe_filter.py       PF-2

So the file-edit count is TWO HIGHER than the backup count. That is a
fact about the rounds, not a gap in them, and the pre-flight's
"N applied, N backups" line must be read with it in mind. The exact
numbers are printed below rather than written here, because a number
in a comment is a number that goes stale. revert_all.sh
DELETES them, because a revert that left them behind would leave a
migration Django would try to run against a table that still exists.
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = '/mnt/user-data/outputs/R3P3'
SKIP = ('.git', '__pycache__', 'media', 'node_modules', 'staticfiles')

# NEWEST FIRST, which is also revert order.
ORDER = [
    ('.bak_pickfilter', 'PF-2', 'apply_pick_filter.py',
     'test_pick_filter.py', 'the picker filters by five things, on one '
     'shared function'),
    ('.bak_mealdrop', 'MX-1', 'apply_meal_drop.py',
     'test_meal_drop.py', 'the old planner three tables go'),
    ('.bak_gateserial', 'GS-1', 'apply_gate_serial.py',
     'test_gate_serial.py', 'the contended suite leaves the pool'),
]

# WRITTEN BY A ROUND, BACKED UP BY NONE - there was no before.
NEW = {
    'MX-1': ('pages/migrations/0101_drop_meal_plan.py',),
    'PF-2': ('pages/views/recipes/_recipe_filter.py',),
}

EXTRA = ('stage_round.py', 'render_pf2.py', 'bundle_r3p3.py')


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
        missing = [p for p in applied
                   if not os.path.isfile(os.path.join(ROOT, p))]
        if missing:
            raise SystemExit('bundle: %s has backups with no live file '
                             'beside them: %s' % (name, missing))
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
          '# revert_all.sh - Release 3, push 3. NEWEST ROUND FIRST.',
          '#',
          '# All three rounds write to Push-PendingChanges.ps1,',
          '# alv_tree.py, alv_rounds.py and test_waiting_down.py.',
          '# Reverting oldest-first restores the LATER round\'s text over',
          '# the earlier one and loses the original. That is the 18 Oct',
          '# bug and it cost a hand repair.',
          '#',
          '# TWO FILES ARE DELETED, not restored: they were created by',
          '# these rounds and have no before. Leaving 0101 behind would',
          '# leave a migration Django tries to run against tables that',
          '# still exist.',
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
           'echo "all three reverted. Backups still on disk (want 0):"',
           'find . \\( ' + ' -o '.join(
               '-name "*%s"' % s for s, _, _, _, _ in ORDER)
           + ' \\) -not -path "./.git/*" | wc -l']
    open(os.path.join(OUT, 'revert_all.sh'), 'w', newline='\n').write(
        '\n'.join(sh) + '\n')

    n_bak = sum(len(v) for v in per.values())
    n_new = sum(len(v) for v in NEW.values())
    print('R3P3 -> %s' % OUT)
    for suf, name, _ap, _su, why in ORDER:
        print('  %-5s %-2d file(s)%s  %s'
              % (name, len(per[name]) + len(NEW.get(name, ())),
                 ' (%d new)' % len(NEW[name]) if name in NEW else '     ',
                 why))
    print('  %d written across the three, %d backups (%d file(s) are new '
          'and have no before), %d files staged'
          % (n_bak + n_new, n_bak, n_new, len(files)))
    print('  revert_all.sh: newest first - %s'
          % ', '.join(n for _, n, _, _, _ in ORDER))
    return 0


if __name__ == '__main__':
    sys.exit(main())
