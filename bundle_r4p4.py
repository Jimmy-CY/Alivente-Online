# -*- coding: utf-8 -*-
"""bundle_r4p4.py - release 4, push 4. Ten rounds, one push.

Demetri's eleven pieces of testing feedback of 21 October, and the
two things that were already outstanding when they arrived. Asked
whether to split them: "Bundle it with all of the above."

    SC-1  Today, not Tonight - and This Saturday goes
    BO-1  the planner bar puts its verb first
    WT-1  the week band stops wearing the pills' own colour
    SH-2  the shopping list range row: 221px tall becomes 44px
    MG-1  a page that writes a message can show one
    HP-1  Help, reachable on a phone
    BA-1  the instrument that could not see the bar
    CP-2  Copy any span, and Saved Menus, on the bar at last
    RG-1  the printed sheet follows the range - and fits on one A4
    RG-2  From and To on the print page, and the second press explained

THE APPLIED LIST IS ENUMERATED FROM THE .bak FILES ON DISK, never
typed, and the CREATED list is read from each patcher's own CREATES.
None of these ten creates a file - PP-1 did, last push, and that is
why the mechanism is here.

revert_all.sh RUNS NEWEST FIRST. Every one of the ten writes to
Push-PendingChanges.ps1, alv_rounds.py, alv_tree.py and
test_waiting_down.py; four write to meal_planner.html and two to
meal_plan_print.html, meal_planning.py and test_pair_contrast.py.
Reverting oldest-first restores the LATER round's text over the
earlier one and loses the original - the 18 October bug, which cost
a hand repair.
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = '/mnt/user-data/outputs/R4P4'
SKIP = ('.git', '__pycache__', 'media', 'node_modules', 'staticfiles')

# NEWEST FIRST, which is also revert order.
ORDER = [
    ('.bak_printrange', 'RG-2', 'apply_print_range.py',
     'test_print_range.py', 'From and To on the printed plan'),
    ('.bak_printshape', 'RG-1', 'apply_print_shape.py',
     'test_print_shape.py', 'the sheet follows the range'),
    ('.bak_copymenus', 'CP-2', 'apply_copy_menus.py',
     'test_copy_menus.py', 'Copy any span, and Saved Menus'),
    ('.bak_baraudit', 'BA-1', 'apply_bar_audit.py',
     'test_bar_audit.py', 'the instrument that could not see the bar'),
    ('.bak_helpphone', 'HP-1', 'apply_help_phone.py',
     'test_help_phone.py', 'Help, reachable on a phone'),
    ('.bak_msgbar2', 'MG-1', 'apply_msg_bar.py',
     'test_msg_bar.py', 'a page that writes a message can show one'),
    ('.bak_slrangerow', 'SH-2', 'apply_sl_range_row.py',
     'test_sl_range_row.py', 'the range row: 221px becomes 44px'),
    ('.bak_weekband', 'WT-1', 'apply_week_band.py',
     'test_week_band.py', 'the week owns the edge, the meal the fill'),
    ('.bak_barfirst', 'BO-1', 'apply_bar_first.py',
     'test_bar_first.py', 'the planner bar puts its verb first'),
    ('.bak_saytoday', 'SC-1', 'apply_say_today.py',
     'test_say_today.py', 'Today, not Tonight'),
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

EXTRA = ('stage_round.py', 'bundle_r4p4.py')


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
        # half-applied tree. The backup is staged either way, which is
        # what makes the removal reversible.
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
          '# revert_all.sh - release 4 push 4. NEWEST ROUND FIRST.',
          '#',
          '# All ten write to Push-PendingChanges.ps1, alv_rounds.py,',
          '# alv_tree.py and test_waiting_down.py; four write to',
          '# meal_planner.html and two to meal_plan_print.html,',
          '# meal_planning.py and test_pair_contrast.py.',
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
           'echo "all ten reverted. Backups still on disk (want 0):"',
           'find . \\( ' + ' -o '.join(
               '-name "*%s"' % s for s, _, _, _, _ in ORDER)
           + ' \\) -not -path "./.git/*" | wc -l']
    open(os.path.join(OUT, 'revert_all.sh'), 'w', newline='\n').write(
        '\n'.join(sh) + '\n')

    n_bak = sum(len(v) for v in per.values())
    n_new = sum(len(v) for v in NEW.values())
    print('R4P4 -> %s' % OUT)
    for suf, name, _ap, _su, why in ORDER:
        print('  %-5s %-2d file(s)%s  %s'
              % (name, len(per[name]) + len(NEW.get(name, ())),
                 ' (%d new)' % len(NEW[name]) if NEW.get(name) else '     ',
                 why))
    print('  %d file-edits across the ten, %d backups, %d files staged'
          % (n_bak + n_new, n_bak, len(files)))
    print('  revert_all.sh: newest first - %s'
          % ', '.join(n for _, n, _, _, _ in ORDER))
    return 0


if __name__ == '__main__':
    sys.exit(main())
