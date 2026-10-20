# -*- coding: utf-8 -*-
"""bundle_r4p3.py - release 4, push 3. Nine rounds, one push.

Demetri, asked whether to send them in two pushes or one: "Send all
together."

    RD-3  the photo opens a quick look, and the dead modal goes
    AP-1  a recipe goes on a day from the library, with an Undo
    FV-1  the heart stops returning 403 for a read-only user
    LO-1  Leftovers, from Month and Week
    NT-1  a Note, from the picker
    SL-7  the shopping list covers what you are looking at
    CE-1  a suite stops writing into the tree it is run against
    PP-1  a meal plan you can print and put on the fridge
    MH-5  the guide catches up with the calendar

THE APPLIED LIST IS ENUMERATED FROM THE .bak FILES ON DISK, never
typed, and the CREATED list is read from each patcher's own CREATES.
PP-1 creates one file - the printable page - which has no backup,
so nothing that enumerates backups can see it: the bundle asks the
patcher instead.

revert_all.sh RUNS NEWEST FIRST. Seven of the nine write to
Push-PendingChanges.ps1, alv_rounds.py, alv_tree.py and
test_waiting_down.py, and four of them to meal_planner.html.
Reverting oldest-first restores the LATER round's text over the
earlier one and loses the original - the 18 October bug, which cost
a hand repair.
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = '/mnt/user-data/outputs/R4P3'
SKIP = ('.git', '__pycache__', 'media', 'node_modules', 'staticfiles')

# NEWEST FIRST, which is also revert order.
ORDER = [
    ('.bak_mealguide5', 'MH-5', 'apply_meal_guide5.py',
     'test_meal_guide5.py', 'the guide catches up with the calendar'),
    ('.bak_printplan', 'PP-1', 'apply_print_plan.py',
     'test_print_plan.py', 'a meal plan you can put on the fridge'),
    ('.bak_cescratch', 'CE-1', 'apply_ce_scratch.py',
     'test_ce_scratch.py', 'the probe writes outside the tree'),
    ('.bak_listrange', 'SL-7', 'apply_list_range.py',
     'test_list_range.py', 'the list covers what you are looking at'),
    ('.bak_picknote', 'NT-1', 'apply_pick_note.py',
     'test_pick_note.py', 'a Note, from the picker'),
    ('.bak_chipleft', 'LO-1', 'apply_chip_left.py',
     'test_chip_left.py', 'Leftovers, from Month and Week'),
    ('.bak_favtoken', 'FV-1', 'apply_fav_token.py',
     'test_fav_token.py', 'the heart stops returning 403'),
    ('.bak_addplanner', 'AP-1', 'apply_add_planner.py',
     'test_add_planner.py', 'a recipe onto a day from the library'),
    ('.bak_quicklook', 'RD-3', 'apply_quick_look.py',
     'test_quick_look.py', 'the photo opens a quick look'),
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

EXTRA = ('stage_round.py', 'bundle_r4p3.py')


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
          '# revert_all.sh - release 4 push 3. NEWEST ROUND FIRST.',
          '#',
          '# Seven of the nine write to Push-PendingChanges.ps1,',
          '# alv_rounds.py, alv_tree.py and test_waiting_down.py, and',
          '# four of them to meal_planner.html.',
          '# Reverting oldest-first restores the LATER round\'s text over',
          '# the earlier one and loses the original. That is the 18 Oct',
          '# bug and it cost a hand repair.',
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
           'echo "all nine reverted. Backups still on disk (want 0):"',
           'find . \\( ' + ' -o '.join(
               '-name "*%s"' % s for s, _, _, _, _ in ORDER)
           + ' \\) -not -path "./.git/*" | wc -l']
    open(os.path.join(OUT, 'revert_all.sh'), 'w', newline='\n').write(
        '\n'.join(sh) + '\n')

    n_bak = sum(len(v) for v in per.values())
    n_new = sum(len(v) for v in NEW.values())
    print('R4P3 -> %s' % OUT)
    for suf, name, _ap, _su, why in ORDER:
        print('  %-5s %-2d file(s)%s  %s'
              % (name, len(per[name]) + len(NEW.get(name, ())),
                 ' (%d new)' % len(NEW[name]) if name in NEW else '     ',
                 why))
    print('  %d file-edits across the nine, %d backups, %d files staged'
          % (n_bak + n_new, n_bak, len(files)))
    print('  revert_all.sh: newest first - %s'
          % ', '.join(n for _, n, _, _, _ in ORDER))
    return 0


if __name__ == '__main__':
    sys.exit(main())
