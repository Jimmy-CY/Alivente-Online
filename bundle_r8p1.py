# -*- coding: utf-8 -*-
"""bundle_r8p1.py - release 8, push 1. Two rounds, one push.

    RV-1  G2, outstanding since 16 October: the receipt has a screen
          that shows the RECORD, not only the document. The pdf icon
          has opened the receipt itself since RC-1; what nothing in
          this application ever showed was who voided it and why, who
          edited it and when, when it was emailed, the property, the
          method, the bank reference and the payer's address,
          telephone and email. void_reason in particular was captured
          on every void, stored, and displayed nowhere at all
    IR-1  G1, outstanding since 16 October: one register for one kind
          of identifier. The receipt number was grey monospace and not
          a link; the invoice number was a teal link. Both pages now
          take ONE .alv-ref-link rule from base, and the dead
          monospace rule is deleted rather than left behind

THE NOTE THAT BLOCKED G1 FOR A WEEK WAS WRONG. It said `.alv-table
.ref` is a base component "so this reaches every .ref in the
application". Measured on 23 October: it was worn on EXACTLY ONE CELL
of ONE page. True of the rule, false of the practice.

AND G1 AND G2 WERE ONE DECISION. The receipt number was not a link
because there was nowhere for it to go. RV-1 builds the destination,
IR-1 points at it - which is why they are two rounds in one push and
not one round: a screen built in one and reached in the other is two
claims that can each be checked.

ELEVEN CENSUSES MOVED. Adding one page to this tree touches the bar
control count, the receipt route list, the back-label count, the
house-title count in BOTH of its places, the JS-escape total, four
button-scanner numbers, the lead-card pin, the template walk, MAIN_N,
and the same "117 of 142" pair written out in three separate suites.
Every one moved with the round that moved it. One of them - base's
house-title note saying 120 while its suite said 121 - had been
lying since 20 October and was repaired on the way past.

AND ONE REAL DEFECT OF MINE, caught by the sweep: the new screen
shipped with no {% block title %}, so its browser tab would have said
whatever base defaults to. test_heading_prefix said "1 of 116 bad".
The round now gates itself on it.

THE APPLIED LIST IS ENUMERATED FROM THE .bak FILES ON DISK, never
typed, and the CREATED list is read from each patcher's own CREATES.
RV-1 creates pages/templates/cash_receipt_detail.html - the only new
file in the push, and the one thing nothing that enumerates backups
could ever see.

revert_all.sh RUNS NEWEST FIRST. Both write to Push-PendingChanges.ps1,
alv_rounds.py, alv_tree.py and test_waiting_down.py, and both write
base.html - RV-1 for the house-title note, IR-1 for the register.
Reverting oldest-first restores the LATER round's text over the
earlier one and loses the original: the 18 October bug.

THE APPLICATION ORDER WAS RV-1, IR-1, so the revert order below is
exactly that reversed.

NO MIGRATION. Every field RV-1 reads already existed.
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = '/mnt/user-data/outputs/R8P1'
SKIP = ('.git', '__pycache__', 'media', 'node_modules', 'staticfiles')

# NEWEST FIRST, which is also revert order.
ORDER = [
    ('.bak_reflink', 'IR-1', 'apply_ref_link.py',
     'test_ref_link.py', 'one register for one kind of identifier'),
    # IR-1 AND RV-1 BOTH WRITE base.html - RV-1 repairs the
    # house-title note, IR-1 replaces the register - and RV-1 went
    # first. IR-1 must therefore revert BEFORE it, or RV-1's backup
    # lands on a file IR-1 has not yet undone.
    ('.bak_receiptview', 'RV-1', 'apply_receipt_view.py',
     'test_receipt_view.py',
     'the receipt has a screen that shows the record'),
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

EXTRA = ('stage_round.py', 'bundle_r8p1.py')


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
          '# revert_all.sh - release 8 push 1. NEWEST ROUND FIRST.',
          '#',
          '# Both write to Push-PendingChanges.ps1, alv_rounds.py,',
          '# alv_tree.py and test_waiting_down.py - and BOTH write',
          '# base.html, RV-1 first, so IR-1 must revert BEFORE it.',
          '#',
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
           'echo "both reverted. Backups still on disk (want 0):"',
           'find . \\( ' + ' -o '.join(
               '-name "*%s"' % s for s, _, _, _, _ in ORDER)
           + ' \\) -not -path "./.git/*" | wc -l']
    open(os.path.join(OUT, 'revert_all.sh'), 'w', newline='\n').write(
        '\n'.join(sh) + '\n')

    n_bak = sum(len(v) for v in per.values())
    n_new = sum(len(v) for v in NEW.values())
    print('R8P1 -> %s' % OUT)
    for suf, name, _ap, _su, why in ORDER:
        print('  %-5s %-2d file(s)%s  %s'
              % (name, len(per[name]) + len(NEW.get(name, ())),
                 ' (%d new)' % len(NEW[name]) if NEW.get(name) else '     ',
                 why))
    print('  %d file-edits across the two, %d backups, %d files staged'
          % (n_bak + n_new, n_bak, len(files)))
    print('  revert_all.sh: newest first - %s'
          % ', '.join(n for _, n, _, _, _ in ORDER))
    return 0


if __name__ == '__main__':
    sys.exit(main())
