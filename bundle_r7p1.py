# -*- coding: utf-8 -*-
"""bundle_r7p1.py - release 7, push 1. Four rounds, one push.

    SB-2  one primary per state on the shopping bar, and nothing
          offering to do something there is nothing to do. It also
          shipped an unclosed if-tag - a template tag inside a
          JavaScript // comment is still a template tag - which would
          have raised TemplateSyntaxError on the shopping list for
          anyone whose list had a missing conversion
    SI-1  a copied recipe takes its OWN photo. duplicate_recipe set
          pk to None and saved, which copies the PATH and not the
          picture, so changing the photo on either recipe deleted it
          for the other. 71 Cottage Pie and 336 Beans, Edamame lost
          theirs that way on Live. The delete now counts who else
          holds the file AND waits until the save commits, and
          check_recipe_files is the instrument that would have found
          it years ago
    NL-1  a generated name fits the column it is stored in. Four
          recipes on Live generated a display filename longer than
          100 characters and Django truncated the stem mid-timestamp
          and suffixed it, which left them permanently stale - so
          save() rebuilt them on every edit. The columns are 255 and
          the slug is bounded at 40
    PT-1  the print sheet knows which view sent it. Demetri's five
          findings on 22 October were one cause: the page took ?from=
          and ?to= and nothing else, so Back could not know where to
          return to. A day sheet and a one-day range are the same two
          dates

THE APPLIED LIST IS ENUMERATED FROM THE .bak FILES ON DISK, never
typed, and the CREATED list is read from each patcher's own CREATES.
SI-1 creates pages/management/commands/check_recipe_files.py and NL-1
creates pages/migrations/0102_nl1_name_width.py - two new files, and
the two things nothing that enumerates backups could ever see.

revert_all.sh RUNS NEWEST FIRST. All four write to
Push-PendingChanges.ps1, alv_rounds.py, alv_tree.py and
test_waiting_down.py; SI-1 and NL-1 both write check_recipe_files.py
and pages/models.py. Reverting oldest-first restores the LATER
round's text over the earlier one and loses the original - the
18 October bug, which cost a hand repair.

THE APPLICATION ORDER WAS SB-2, SI-1, NL-1, PT-1, so the revert order
below is exactly that reversed.

A MIGRATION SHIPS WITH THIS PUSH. 0102 widens three columns; Railway
runs migrations on deploy, so nothing is run by hand. Reverting NL-1
deletes the migration FILE, which does not un-widen a column that has
already been migrated.
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = '/mnt/user-data/outputs/R7P1'
SKIP = ('.git', '__pycache__', 'media', 'node_modules', 'staticfiles')

# NEWEST FIRST, which is also revert order.
ORDER = [
    ('.bak_printorigin', 'PT-1', 'apply_print_origin.py',
     'test_print_origin.py', 'the print sheet knows which view sent it'),
    ('.bak_namewidth', 'NL-1', 'apply_name_width.py',
     'test_name_width.py', 'a generated name fits its column'),
    # SI-1 AND NL-1 BOTH WRITE check_recipe_files.py AND models.py,
    # and SI-1 went first - it CREATES the detector that NL-1 then
    # teaches a fourth question. NL-1 must therefore revert BEFORE
    # it, or NL-1's backup lands on a file SI-1 has already deleted.
    ('.bak_sharedimage', 'SI-1', 'apply_shared_image.py',
     'test_shared_image.py', 'a copied recipe does not share its photo'),
    ('.bak_shopbar2', 'SB-2', 'apply_shop_bar2.py',
     'test_shop_bar2.py', 'one primary per state on the shopping bar'),
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

EXTRA = ('stage_round.py', 'bundle_r7p1.py')


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
          '# revert_all.sh - release 7 push 1. NEWEST ROUND FIRST.',
          '#',
          '# All four write to Push-PendingChanges.ps1, alv_rounds.py,',
          '# alv_tree.py and test_waiting_down.py. SI-1 and NL-1 both',
          '# write check_recipe_files.py and models.py, SI-1 first, so',
          '# NL-1 must revert BEFORE it.',
          '# Reverting oldest-first restores the LATER round\'s text over',
          '# the earlier one and loses the original. That is the 18 Oct',
          '# bug and it cost a hand repair.',
          '#',
          '# cp, NOT a text copy. A revert is a byte copy and a',
          '# helper that read backups as text crashed on a UTF-16 file',
          '# on 22 Oct and left three files reverted in an applied tree.',
          '# Reverting NL-1 deletes the migration FILE; it does not',
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
    print('R7P1 -> %s' % OUT)
    for suf, name, _ap, _su, why in ORDER:
        print('  %-5s %-2d file(s)%s  %s'
              % (name, len(per[name]) + len(NEW.get(name, ())),
                 ' (%d new)' % len(NEW[name]) if NEW.get(name) else '     ',
                 why))
    print('  %d file-edits across the four, %d backups, %d files staged'
          % (n_bak + n_new, n_bak, len(files)))
    print('  revert_all.sh: newest first - %s'
          % ', '.join(n for _, n, _, _, _ in ORDER))
    return 0


if __name__ == '__main__':
    sys.exit(main())
