# -*- coding: utf-8 -*-
"""bundle_r5p1.py - release 5, push 1. Seven rounds, one push.

Demetri's testing feedback of 21 October, taken as one batch:

    PX-2  a floor under every display copy - the upscale done once,
          on the server, instead of badly in a browser on every load
    WF-1  the week band gets a fill that is not the pills' own colour
    RG-3  the printed week and day stop at the end of the food
    BM-1  one message loop, in base - and 55 pages that could not
          show a message now can
    MN-2  a menu is a span of days and lands where you say
    RO-1  a day dragged into order by its grip
    VR-1  the cooking schedule readout wears tokens, and the two
          tables that are NOT data tables say so

THE APPLIED LIST IS ENUMERATED FROM THE .bak FILES ON DISK, never
typed, and the CREATED list is read from each patcher's own CREATES.
None of these seven creates a file.

revert_all.sh RUNS NEWEST FIRST. All seven write to
Push-PendingChanges.ps1, alv_rounds.py, alv_tree.py and
test_waiting_down.py; three write to meal_planner.html and two to
meal_planning.py and test_recipe_photos.py's neighbours. Reverting
oldest-first restores the LATER round's text over the earlier one and
loses the original - the 18 October bug, which cost a hand repair.

BM-1 IS 89 FILES ON ITS OWN. It takes the message loop off 81 pages
and puts one in base, so the revert of that round touches more of the
tree than the other six together. It is also the one that must revert
LAST of its neighbours, because MN-2, RO-1 and VR-1 all edit files it
also edits.
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = '/mnt/user-data/outputs/R5P1'
SKIP = ('.git', '__pycache__', 'media', 'node_modules', 'staticfiles')

# NEWEST FIRST, which is also revert order.
ORDER = [
    ('.bak_recipetidy', 'VR-1', 'apply_recipe_tidy.py',
     'test_recipe_tidy.py', 'the schedule readout wears tokens'),
    ('.bak_dayorder', 'RO-1', 'apply_day_order.py',
     'test_day_order.py', 'a day dragged into order by its grip'),
    ('.bak_menurange', 'MN-2', 'apply_menu_range.py',
     'test_menu_range.py', 'a menu is a span, landing where you say'),
    ('.bak_msgbase', 'BM-1', 'apply_msg_base.py',
     'test_msg_base.py', 'one message loop, in base - 81 copies gone'),
    # THE APPLICATION ORDER WAS WF-1, RG-3, PX-2, BM-1, MN-2, RO-1,
    # VR-1, so the revert order is exactly that reversed. The first
    # draft of this list had RG-3 and WF-1 ABOVE PX-2 - which is the
    # 18 October bug a third time, and it was caught by hand on 21
    # October before it reached anybody: reverting out of order
    # restores an EARLIER round's backup over a LATER one and loses
    # the original. Four shared registration files went wrong that
    # way and had to be repaired from the staged copies.
    ('.bak_photofloor', 'PX-2', 'apply_photo_floor.py',
     'test_photo_floor.py', 'a floor under every display copy'),
    ('.bak_printcompact', 'RG-3', 'apply_print_compact.py',
     'test_print_compact.py', 'the printed week and day stop at the end'),
    ('.bak_weekfill', 'WF-1', 'apply_week_fill.py',
     'test_week_fill.py', 'the week band fills with moss'),
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

EXTRA = ('stage_round.py', 'bundle_r5p1.py')


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
          '# revert_all.sh - release 5 push 1. NEWEST ROUND FIRST.',
          '#',
          '# All seven write to Push-PendingChanges.ps1, alv_rounds.py,',
          '# alv_tree.py and test_waiting_down.py; three write to',
          '# meal_planner.html and two to meal_planning.py.',
          '# BM-1 alone touches 89 files, and MN-2, RO-1 and VR-1 all',
          '# edit files it edits too - so it must revert AFTER them.',
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
           'echo "all seven reverted. Backups still on disk (want 0):"',
           'find . \\( ' + ' -o '.join(
               '-name "*%s"' % s for s, _, _, _, _ in ORDER)
           + ' \\) -not -path "./.git/*" | wc -l']
    open(os.path.join(OUT, 'revert_all.sh'), 'w', newline='\n').write(
        '\n'.join(sh) + '\n')

    n_bak = sum(len(v) for v in per.values())
    n_new = sum(len(v) for v in NEW.values())
    print('R5P1 -> %s' % OUT)
    for suf, name, _ap, _su, why in ORDER:
        print('  %-5s %-2d file(s)%s  %s'
              % (name, len(per[name]) + len(NEW.get(name, ())),
                 ' (%d new)' % len(NEW[name]) if NEW.get(name) else '     ',
                 why))
    print('  %d file-edits across the seven, %d backups, %d files staged'
          % (n_bak + n_new, n_bak, len(files)))
    print('  revert_all.sh: newest first - %s'
          % ', '.join(n for _, n, _, _, _ in ORDER))
    return 0


if __name__ == '__main__':
    sys.exit(main())
