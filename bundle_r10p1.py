# -*- coding: utf-8 -*-
"""bundle_r10p1.py - release 10, push 1. Three rounds, one push.

    CF-2   four requirements files became one, and it is the one that
           deploys. railway.json AND the Dockerfile both install
           mysite/cron-requirements.txt; the other three were
           decoration and had drifted - seven packages differ in
           membership, six in version. The one at the repo root, the
           one a person types by habit, could not even be installed:
           it pinned httpcore==0.9.1 against an httpx that requires
           httpcore==1.*, with anthropic sitting on the same chain
    WK-1   the push script can be told how many suites to run at once.
           alv_run has had --workers since GT-2 and the push script
           could not pass it, so sweeping at 3 meant running alv_run by
           hand first. rc=3221227274 - 0xC0000374, Windows heap
           corruption under pool contention - killed three sweeps on
           23 October, and every one of them passed when re-run alone
    ES-3a  the fourth Administration tile, and the envelope register
           behind it. ONE ROW PER ENVELOPE, not per tenant, which is
           the whole reason it is not a tab on Manage Lease Agreements:
           that screen is one row per tenant and has to be, and a
           tenant with four attempts can only appear once on it

READ ONLY, ALL THREE. CF-2 removes files nothing reads, WK-1 adds a
parameter that does nothing unless asked, and ES-3a draws a register
whose eye, resend and cancel controls are deliberately inert - ES-3b
builds what they point at. Nothing here creates, sends or signs an
envelope.

NINETEEN CENSUSES MOVED FOR ES-3a, across nine suites. That is what
one new template costs in this tree, measured rather than discovered:
RV-1 moved eleven for one screen on 23 October. Every one was found by
running the suites BEFORE delivery rather than by a push being
refused - which is the change these rounds are trying to make
permanent, after Release 9 was refused twice for censuses I had
missed.

AND TWO CLAIMS WERE REPAIRED RATHER THAN BUMPED. test_landing_tab tied
a historical control to a live census twice - `len(b2) == N_BACKS - 1`
and `len(b2) == total - 1` - so both broke for EVERY future round and
not only this one. A page created after a round also cannot be in that
round's past, so there is a named CREATED_LATER exclusion rather than a
loosened count.

ONE DEFECT OF MINE THAT A SUITE CAUGHT. CF-2 first registered the
three retired files in alv_tree.RETIRED. That register is for retired
PAGES - alv_tree resolves a label under the template roots - and it is
keyed by BASENAME, so `cron-requirements.txt` collided with the file
in mysite/ that must never be thought retired. test_recipe_tones died
on it outright. The entries are gone; .bak_onelist in
alv_rounds.ROUNDS is the whole registration a non-template retirement
needs, which is what stage_round checks.

THE APPLIED LIST IS ENUMERATED FROM THE .bak FILES ON DISK, never
typed, and the CREATED list is read from each patcher's own CREATES.
ES-3a creates the register view and its template; CF-2 and WK-1 create
nothing. CF-2's three retirements are backups with no live file beside
them, which stage_round reads as a retirement because .bak_onelist is
in the register.
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = '/mnt/user-data/outputs/R10P1'
SKIP = ('.git', '__pycache__', 'media', 'node_modules', 'staticfiles')

# NEWEST FIRST, which is also revert order.
#
# ALL THREE WRITE Push-PendingChanges.ps1, alv_rounds.py, alv_tree.py
# and test_waiting_down.py. They were applied CF-2, then WK-1, then
# ES-3a, so they revert in the opposite order: reverting oldest-first
# restores the LATER round's text over the earlier one and loses the
# original. That is the 18 October bug and it cost a hand repair.
#
# AND CF-2 REVERTS LAST FOR A SECOND REASON: it is the one that
# RETIRES files, and a revert puts three of them back. Doing that
# before WK-1 and ES-3a had undone their own edits would be restoring
# into a tree that still thinks it is three rounds later.
ORDER = [
    ('.bak_leasesigning', 'ES-3a', 'apply_lease_signing.py',
     'test_lease_signing.py',
     'the fourth tile and the envelope register'),
    ('.bak_pushworkers', 'WK-1', 'apply_push_workers.py',
     'test_push_workers.py',
     'the sweep can be told how many workers to use'),
    ('.bak_onelist', 'CF-2', 'apply_one_list.py',
     'test_one_list.py',
     'one requirements file, and it is the one that deploys'),
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

EXTRA = ('stage_round.py', 'bundle_r10p1.py')


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
          '# revert_all.sh - release 10 push 1. NEWEST ROUND FIRST.',
          '#',
          '# All three write Push-PendingChanges.ps1, alv_rounds.py,',
          '# alv_tree.py and test_waiting_down.py. Applied CF-2, WK-1,',
          '# ES-3a - so they revert ES-3a, WK-1, CF-2.',
          '#',
          '# Reverting oldest-first restores the LATER round\'s text over',
          '# the earlier one and loses the original. That is the 18 Oct',
          '# bug and it cost a hand repair.',
          '#',
          '# cp, NOT a text copy. A revert is a byte copy and a',
          '# helper that read backups as text crashed on a UTF-16 file',
          '# on 22 Oct and left three files reverted in an applied tree.',
          '# CF-2 retires three UTF-16 files, so this matters here more',
          '# than anywhere: their backups ARE the only copies.',
          '#',
          '# ES-3a CREATES two files, which a revert deletes - there',
          '# was no before to restore.',
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
    print('R10P1 -> %s' % OUT)
    for suf, name, _ap, _su, why in ORDER:
        print('  %-5s %-2d file(s)%s  %s'
              % (name, len(per[name]) + len(NEW.get(name, ())),
                 ' (%d new)' % len(NEW[name]) if NEW.get(name) else '     ',
                 why))
    print('  %d file-edits across the three, %d backups, %d files staged'
          % (n_bak + n_new, n_bak, len(files)))
    print('  revert_all.sh: newest first - %s'
          % ', '.join(n for _, n, _, _, _ in ORDER))
    return 0


if __name__ == '__main__':
    sys.exit(main())
