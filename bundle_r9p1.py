# -*- coding: utf-8 -*-
"""bundle_r9p1.py - release 9, push 1. Three rounds, one push.

    ES-1  the e-signing envelope, its parties and its append-only
          audit trail. Three tables and a migration, and nothing else -
          no view, no screen, no route. With no certificate, decided
          23 October, that trail and the sha256 taken at sealing ARE
          the evidence, which is why nothing in it is ever updated
    ES-2  the two things the flow does to a PDF: the lease rendered to
          page images so the signing page can show it INSIDE itself,
          and the sealer that appends ONE signature page and hashes
          the result. The original is never touched - that is the
          whole design, and it is why this works on a PDF nobody here
          produced
    UO-1  two document uploads destroyed the old file BEFORE the new
          one was safe. A save that raised left the lease agreement
          gone and the row still naming it. SI-1 fixed this shape on
          22 October and swept recipes; the tenant lease agreement and
          the property title deed were never swept

NOTHING IN THIS PUSH HAS A SCREEN. Three tables, a service module and
a two-line reordering. That is deliberate: it puts the migration and
two new pins through a real Railway build BEFORE the signing page is
built on top of them. If pymupdf will not install on Nixpacks, this
is the push to find out on.

AND UO-1 IS HERE RATHER THAN IN ES-6 because it is live now, on the
screen Demetri uses most, and it has nothing to do with e-signing. A
data-loss bug does not wait three pushes behind a feature.

TWO DEFECTS OF MINE, CAUGHT BEFORE DELIVERY.

The signature page was drawn in Helvetica - a PDF Base-14 font with
no Greek glyphs - so a tenant called Ανδρέας Γεωργίου printed as
`······· ········`. It did not raise. It produced a page that looked
finished and named nobody. This is a Cyprus letting company.

And page_name built a storage key with os.path.join, which gives
backslashes on Windows and slashes on Linux: the same page written
under one key and looked for under another, on Live only, never on
the machine it was written on.

AND ONE NAME COLLISION. UO-1 was called LU-1 for about ten minutes
until check_gates refused it - apply_login_url.py already owns that
name and is registered in four files. Caught by the gate rather than
by a careful undo three days later.

THE APPLIED LIST IS ENUMERATED FROM THE .bak FILES ON DISK, never
typed, and the CREATED list is read from each patcher's own CREATES.
ES-1 creates its migration and ES-2 creates the service module;
neither has a backup, because there was nothing there before.
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = '/mnt/user-data/outputs/R9P1'
SKIP = ('.git', '__pycache__', 'media', 'node_modules', 'staticfiles')

# NEWEST FIRST, which is also revert order.
#
# ALL THREE WRITE Push-PendingChanges.ps1, alv_rounds.py, alv_tree.py
# and test_waiting_down.py. They were applied ES-1, then ES-2, then
# UO-1, so they must revert in the opposite order: reverting
# oldest-first restores the LATER round's text over the earlier one
# and loses the original. That is the 18 October bug and it cost a
# hand repair.
ORDER = [
    ('.bak_uploadorder', 'UO-1', 'apply_upload_order.py',
     'test_upload_order.py',
     'the lease and the deed survive a failed save'),
    ('.bak_esignpdf', 'ES-2', 'apply_esign_pdf.py',
     'test_esign_pdf.py',
     'the lease renders to page images and the seal appends'),
    ('.bak_esignmodel', 'ES-1', 'apply_esign_model.py',
     'test_esign_model.py',
     'the envelope, its parties and its audit trail'),
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

EXTRA = ('stage_round.py', 'bundle_r9p1.py')


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
          '# revert_all.sh - release 9 push 1. NEWEST ROUND FIRST.',
          '#',
          '# All three write Push-PendingChanges.ps1, alv_rounds.py,',
          '# alv_tree.py and test_waiting_down.py. Applied ES-1, ES-2,',
          '# UO-1 - so they revert UO-1, ES-2, ES-1.',
          '#',
          '# Reverting oldest-first restores the LATER round\'s text over',
          '# the earlier one and loses the original. That is the 18 Oct',
          '# bug and it cost a hand repair.',
          '#',
          '# cp, NOT a text copy. A revert is a byte copy and a',
          '# helper that read backups as text crashed on a UTF-16 file',
          '# on 22 Oct and left three files reverted in an applied tree.',
          '#',
          '# ES-1 and ES-2 each CREATE a file, which a revert deletes -',
          '# there was no before to restore.',
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
    print('R9P1 -> %s' % OUT)
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
