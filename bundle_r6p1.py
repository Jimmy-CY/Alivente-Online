# -*- coding: utf-8 -*-
"""bundle_r6p1.py - release 6, push 1. Seven rounds, one push.

    HG-1  the Help guide and the pages agree, both ways - a promise
          the guide makes that the page does not keep is a failure,
          and so is a control the page has that the guide never names
    WD-1  the week's seven columns drag into order, through RO-1's
          endpoint, because a column IS a date
    DP-1  the push asks the live site for its own commit SHA instead
          of announcing a deploy it never checks - and the photo
          command says what it wrote
    SD-1  --rebuild --write really replaces the file. It did not:
          Django storage does not overwrite, so every rebuild left an
          orphan and every row permanently stale
    CF-1  the configuration says what it really is - a dead Django
          5.1 setting gone, the file Railway actually installs in
          UTF-8 and bounded, and pillow-heif added to it
    WN-1  the workspace list is two queries, whatever N is - the
          round WM-1 named on 16 October
    LK-1  a planter killed mid-plant leaves a lock that names every
          file it did not put back

THE APPLIED LIST IS ENUMERATED FROM THE .bak FILES ON DISK, never
typed, and the CREATED list is read from each patcher's own CREATES.
LK-1 creates alv_plant.py - the only new file in the push, and the one
thing nothing that enumerates backups could ever see.

revert_all.sh RUNS NEWEST FIRST. All seven write to
Push-PendingChanges.ps1, alv_rounds.py, alv_tree.py and
test_waiting_down.py; DP-1 and SD-1 both write to
convert_recipe_photos.py. Reverting oldest-first restores the LATER
round's text over the earlier one and loses the original - the 18
October bug, which cost a hand repair, and which a bundle ORDER list
got wrong again on 21 October before it was caught by hand.

THE APPLICATION ORDER WAS HG-1, WD-1, DP-1, SD-1, CF-1, WN-1, LK-1,
so the revert order below is exactly that reversed.

CF-1's BACKUP IS UTF-16LE, and the revert is a byte copy. The shell
script uses cp, which does not care; the tooling that reads backups as
text crashed on it on 22 October and left three files reverted in a
tree that was meant to be applied. Fixed there; said here because the
next person to write a revert helper will meet the same file.
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = '/mnt/user-data/outputs/R6P1'
SKIP = ('.git', '__pycache__', 'media', 'node_modules', 'staticfiles')

# NEWEST FIRST, which is also revert order.
ORDER = [
    ('.bak_planterlock', 'LK-1', 'apply_planter_lock.py',
     'test_planter_lock.py', 'a killed planter leaves a lock behind'),
    ('.bak_wsprefetch', 'WN-1', 'apply_ws_prefetch.py',
     'test_ws_prefetch.py', 'the workspace list is two queries, not N'),
    ('.bak_configtruth', 'CF-1', 'apply_config_truth.py',
     'test_config_truth.py', 'the configuration says what it really is'),
    ('.bak_photorebuild', 'SD-1', 'apply_photo_rebuild.py',
     'test_photo_rebuild.py', 'a rebuild replaces the file it rebuilds'),
    ('.bak_deployprobe', 'DP-1', 'apply_deploy_probe.py',
     'test_deploy_probe.py', 'the push finds out whether it deployed'),
    # SD-1 AND DP-1 BOTH WRITE convert_recipe_photos.py, and DP-1 went
    # first. SD-1 must therefore revert BEFORE it, or DP-1's backup -
    # which is the file as it stood before DP-1, with no write report
    # in it at all - lands on top of a file SD-1 has not yet undone.
    ('.bak_weekdrag', 'WD-1', 'apply_week_drag.py',
     'test_week_drag.py', 'the week columns drag into order'),
    ('.bak_helpagrees', 'HG-1', 'apply_help_agrees.py',
     'test_help_agrees.py', 'the guide and the page agree, both ways'),
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

EXTRA = ('stage_round.py', 'bundle_r6p1.py')


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
          '# revert_all.sh - release 6 push 1. NEWEST ROUND FIRST.',
          '#',
          '# All seven write to Push-PendingChanges.ps1, alv_rounds.py,',
          '# alv_tree.py and test_waiting_down.py. DP-1 and SD-1 both',
          '# write convert_recipe_photos.py and DP-1 went first, so',
          '# SD-1 must revert BEFORE it.',
          '# Reverting oldest-first restores the LATER round\'s text over',
          '# the earlier one and loses the original. That is the 18 Oct',
          '# bug and it cost a hand repair.',
          '#',
          '# cp, NOT a text copy. CF-1 backup of',
          '# mysite/cron-requirements.txt is UTF-16LE and a revert is a',
          '# byte copy. A helper that read it as text crashed on 22 Oct',
          '# and left three files reverted in an applied tree.',
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
    print('R6P1 -> %s' % OUT)
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
