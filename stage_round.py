# -*- coding: utf-8 -*-
"""stage_round.py - put a round in /mnt/user-data/outputs, from its backups.

    python stage_round.py .bak_mealweek MW1 apply_meal_week.py test_meal_week.py

STEP 0, and the reason it exists: a round is staged the moment its
patcher and its suite are green, BEFORE the pre-flight - so what is
delivered is what was measured, not what the tree looked like later.

AND THE APPLIED LIST IS ENUMERATED FROM THE .bak FILES ON DISK, never
typed. The 17 October push shipped a list somebody wrote out by hand
and two files were missing from it; a round's own backups are the only
record of what it touched that cannot disagree with the tree.
"""
import os
import shutil
import sys

SKIP_DIRS = ('.git', '__pycache__', 'media', 'node_modules', 'staticfiles')


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    suffix, name, extra = argv[0], argv[1], argv[2:]
    root = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join('/mnt/user-data/outputs', name)
    if os.path.isdir(out):
        shutil.rmtree(out)

    baks = []
    for folder, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for n in names:
            if n.endswith(suffix):
                baks.append(os.path.join(folder, n))
    if not baks:
        raise SystemExit('stage_round: no %s files on disk - the round is '
                         'not applied, so there is nothing to stage and '
                         'nothing to enumerate from.' % suffix)

    # A BACKUP WITH NO LIVE FILE IS A DELETION, NOT AN ERROR.
    #
    # MV-2, 19 Oct 2026. A round that RETIRES something removes it
    # from the disk and leaves its backup - which is the only thing
    # that makes the removal reversible. MN-1 deleted two suites and
    # four templates the same way on 18 October.
    #
    # This refused the whole staging over it. The refusal was right to
    # exist: a backup beside a missing file is usually a half-applied
    # tree, and the 17 October push shipped one. So the two cases are
    # told apart by ASKING THE ROUND, not by guessing - a round that
    # means to delete says so in the register.
    applied = sorted(b[:-len(suffix)] for b in baks)
    gone = [p for p in applied if not os.path.isfile(p)]
    if gone:
        try:
            import alv_rounds
            known = suffix in alv_rounds.ROUNDS
        except Exception:
            known = False
        if not known:
            raise SystemExit(
                'stage_round: %d backup(s) have no live file beside '
                'them and %s is not a registered round, so this is a '
                'half-applied tree rather than a retirement: %s'
                % (len(gone), suffix, gone))
    live = [p for p in applied if os.path.isfile(p)]

    files = live + [os.path.join(root, e) for e in extra]
    for e in extra:
        if not os.path.isfile(os.path.join(root, e)):
            raise SystemExit('stage_round: %s is not in the tree' % e)

    for src in files + sorted(baks):
        rel = os.path.relpath(src, root)
        dst = os.path.join(out, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)

    print('%s -> %s' % (suffix, out))
    print('  APPLIED  %d' % len(live))
    print('  BACKUPS  %d' % len(baks))
    if gone:
        print('  RETIRED  %d (backup staged, no live file - this round '
              'removed it)' % len(gone))
    print('  ROUND    %d (patcher and suite)' % len(extra))
    for p in live:
        print('    %s' % os.path.relpath(p, root))
    for p in gone:
        print('    %s  (RETIRED)' % os.path.relpath(p, root))
    if len(live) + len(gone) != len(baks):
        raise SystemExit('stage_round: %d applied + %d retired against '
                         '%d backups - those must add up'
                         % (len(live), len(gone), len(baks)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
