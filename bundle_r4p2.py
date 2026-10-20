# -*- coding: utf-8 -*-
"""bundle_r4p2.py - Release 4, push 2, as one directory he can copy.

EIGHT ROUNDS. The calendar answers back: a recipe opens without
leaving it, a meal has a menu, a write leaves you where you were, the
date bar is a bar, a day is a day in every view, the Day card uses its
width, and the picker adds on click and stays open.

THE APPLIED LIST IS ENUMERATED FROM THE .bak FILES ON DISK, never
typed, and the CREATED list is read from each patcher's own CREATES -
RD-1 taught stage_round that on the 19th, after PF-2 shipped a module
the day before only because somebody happened to type its name.

revert_all.sh RUNS NEWEST FIRST. Seven of these eight write to
Push-PendingChanges.ps1, alv_tree.py, alv_rounds.py and
test_waiting_down.py, and five of them write to meal_planner.html.
Reverting oldest-first restores the LATER round's text over the
earlier one and loses the original - the 18 October bug, which cost a
hand repair.

AND THE THREE FILES RD-1 CREATES ARE DELETED BY THE REVERT, not
restored: a module nothing imports and two templates nothing renders
are what a revert that only reads backups would leave behind.
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = '/mnt/user-data/outputs/R4P2'
SKIP = ('.git', '__pycache__', 'media', 'node_modules', 'staticfiles')

# NEWEST FIRST, which is also revert order.
ORDER = [
    ('.bak_pickerstays', 'PS-1', 'apply_picker_stays.py',
     'test_picker_stays.py',
     'the picker adds on click and stays open'),
    ('.bak_daycard', 'DC-1', 'apply_day_card.py',
     'test_day_card.py', 'the Day card uses its width'),
    ('.bak_weekclick', 'WC-1', 'apply_week_click.py',
     'test_week_click.py', 'a day is a day in every view'),
    ('.bak_monthbar', 'MB-2', 'apply_month_bar.py',
     'test_month_bar.py', 'the date bar is a bar'),
    ('.bak_chipmenu', 'RD-2', 'apply_chip_menu.py',
     'test_chip_menu.py', 'a meal in the calendar has a menu'),
    ('.bak_viewback', 'PB-2', 'apply_planner_back.py',
     'test_planner_back.py',
     'a write on the planner leaves you where you were'),
    ('.bak_recipeweight', 'RW-1', 'apply_recipe_weight.py',
     'test_recipe_weight.py', 'the weight is worked out in grams'),
    ('.bak_recipemodal', 'RD-1', 'apply_recipe_modal.py',
     'test_recipe_modal.py',
     'a recipe opens without leaving the calendar'),
]

# WRITTEN BY A ROUND, BACKED UP BY NONE - there was no before.
#
# READ FROM THE PATCHER, not typed here. RD-1 taught stage_round to do
# this and the same rule applies to the bundle: a file a round creates
# has no backup, so nothing that enumerates backups can see it, and
# PF-2 shipped _recipe_filter.py on 19 Oct only because its name
# happened to get typed on a command line.
def _creates(patcher):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        patcher[:-3], os.path.join(ROOT, patcher))
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, ROOT)
    spec.loader.exec_module(mod)
    return tuple(getattr(mod, 'CREATES', ()))


NEW = {}

EXTRA = ('stage_round.py', 'bundle_r4p2.py')


def main():
    if os.path.isdir(OUT):
        for n in os.listdir(OUT):
            p = os.path.join(OUT, n)
            if os.path.isdir(p):
                shutil.rmtree(p)
            elif not (n.endswith('.png') or n.endswith('.html')):
                os.remove(p)
    os.makedirs(OUT, exist_ok=True)

    for _suf, _name, _ap, _su, _why in ORDER:
        NEW[_name] = _creates(_ap)

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
          '# revert_all.sh - Release 4, push 2. NEWEST ROUND FIRST.',
          '#',
          '# Seven of the eight write to Push-PendingChanges.ps1,',
          '# alv_tree.py, alv_rounds.py and test_waiting_down.py, and',
          '# five of them write to meal_planner.html.',
          '# Reverting oldest-first restores the LATER round\'s text over',
          '# the earlier one and loses the original. That is the 18 Oct',
          '# bug and it cost a hand repair.',
          '#',
          '# THREE FILES ARE DELETED, NOT RESTORED: RD-1 creates',
          '# _recipe_read.py, recipe_quicklook.html and its shell, and',
          '# there is no before to put back. A revert that read only',
          '# backups would leave a module nothing imports and two',
          '# templates nothing renders.',
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
           'echo "all eight reverted. Backups still on disk (want 0):"',
           'find . \\( ' + ' -o '.join(
               '-name "*%s"' % s for s, _, _, _, _ in ORDER)
           + ' \\) -not -path "./.git/*" | wc -l']
    open(os.path.join(OUT, 'revert_all.sh'), 'w', newline='\n').write(
        '\n'.join(sh) + '\n')

    n_bak = sum(len(v) for v in per.values())
    n_new = sum(len(v) for v in NEW.values())
    print('R4P2 -> %s' % OUT)
    for suf, name, _ap, _su, why in ORDER:
        print('  %-5s %-2d file(s)%s  %s'
              % (name, len(per[name]) + len(NEW.get(name, ())),
                 ' (%d new)' % len(NEW[name]) if name in NEW else '     ',
                 why))
    print('  %d file-edits across the eight, %d backups, %d files staged'
          % (n_bak + n_new, n_bak, len(files)))
    print('  revert_all.sh: newest first - %s'
          % ', '.join(n for _, n, _, _, _ in ORDER))
    return 0


if __name__ == '__main__':
    sys.exit(main())
