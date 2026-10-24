# -*- coding: utf-8 -*-
"""bundle_r12p1.py - release 12, push 1. Three rounds, one push.

    T2-3   Generate stops asking for what it already knows, and stops
           throwing away what it is told. It prefills the three
           columns the record holds, still asks for the three that
           are per-document, and saves the three back - silently when
           the record is empty, after a confirm that names both
           people when it is not, and NEVER on Remove
    T2-4   the application names a joint tenancy ONE WAY, on sixteen
           screens. Thirty-seven display sites changed; ten match
           sites enumerated and asserted untouched
    T2-5   a joint tenant gets the invoice, and the mailer stops
           keeping its own copy of the address parser

T2-4 WAS SCOPED TWICE BY A SENTENCE AND ONCE BY A CENSUS, AND ONLY
THE CENSUS WAS RIGHT. It began as "the four reports show both names".
Demetri then asked four questions in a row and each found a screen it
missed: the Reports menu on Tenants carries Lease Timeline and
Payment Behaviour; Physical Invoices and Receipts put a tenant name
on a FINANCIAL DOCUMENT; the Cash Flow Forecast lists every tenant by
name. So the scope was finally measured - 88 sites, 29 of them MATCH,
about 30 DISPLAY, across sixteen screens.

THE MATCH SITES ARE THE WHOLE DIFFICULTY AND NOTHING ANNOUNCES THEM.
Put a joined name into one and the filter returns nothing, the join
finds nothing, the lookup opens an empty panel. The screen does not
fail - it stops mentioning somebody. Every one is written out in the
patcher and asserted untouched, including three in files these rounds
never open, which the suite proves by their having no backup at all.

HIS OWN DATA IS THE ARGUMENT. Two tenancies are already joint and
already worked around by typing both people into the one name field -
Mr. Dorian Tirouard and Mr. Antoine Madelbos, and Chrystalla Katelari
and Antigoni Andreou. They read that way on the register and in the
forecast breakdown today.

T2-5 IS THE ONLY ROUND OF THE FIVE THAT CHANGES WHAT LEAVES THE
BUILDING, so its suite proves a NEGATIVE: it reads the OLD expression
out of the backup rather than retyping it, runs both parsers over
eight real input shapes, and requires every address that reached
somebody yesterday to reach them today in the same order. A tenancy
already crammed into the first box is unaffected; the same address in
both columns is one recipient.

TWO DEFECTS THE SUITES CAUGHT THAT WOULD OTHERWISE HAVE SHIPPED.
T2-4's rebuild for sixteen screens DROPPED the .only() edit; section 4
counts queries against a real database and came back 2 where it
wanted 1, on both lists. And a control refuted a claim in T2-2's own
comments about `display: block`, which was corrected in the patcher
rather than softened in the control.

THREE MORE EXPIRY-DATED CLAIMS REPAIRED, and one of them deliberately
NOT with as_left_by: "the model refuses a joint tenant on a Company
tenancy" is a LIVE invariant and must be true today, so it was
widened to ask the class rather than read off a backup. The other
two - T2-1's two-parsers claim and its "no scheduled mail reaches
anybody new" - became a one-parser claim and an as_left_by read.

THE APPLIED LIST IS ENUMERATED FROM THE .bak FILES ON DISK, never
typed. None of these three creates a file.
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = '/mnt/user-data/outputs/R12P1'
SKIP = ('.git', '__pycache__', 'media', 'node_modules', 'staticfiles')

# NEWEST FIRST, which is also revert order.
#
# ALL THREE WRITE Push-PendingChanges.ps1, alv_rounds.py, alv_tree.py
# and test_waiting_down.py, and the order is LOAD-BEARING beyond
# that: T2-4 edits pages/models.py after T2-3 did, and T2-5 edits
# test_second_tenant.py, which T2-2 already edited in the last push.
# Reverting oldest-first restores the LATER round's text over the
# earlier one and loses the original. That is the 18 October bug and
# it cost a hand repair.
ORDER = [
    ('.bak_invrecip', 'T2-5', 'apply_invoice_recipients.py',
     'test_invoice_recipients.py',
     'a joint tenant gets the invoice'),
    ('.bak_reportnames', 'T2-4', 'apply_report_names.py',
     'test_report_names.py',
     'sixteen screens name a joint tenancy one way'),
    ('.bak_t2gen', 'T2-3', 'apply_generate_second.py',
     'test_generate_second.py',
     'Generate reads the record and writes back to it'),
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

EXTRA = ('stage_round.py', 'bundle_r12p1.py')


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
          '# revert_all.sh - release 12 push 1. NEWEST ROUND FIRST.',
          '#',
          '# All three write Push-PendingChanges.ps1, alv_rounds.py,',
          '# alv_tree.py and test_waiting_down.py; T2-4 also edits',
          '# models.py after T2-3 did. Applied T2-3, T2-4, T2-5 - so',
          '# they revert T2-5, T2-4, T2-3.',
          '#',
          '# Reverting oldest-first restores the LATER round\'s text over',
          '# the earlier one and loses the original. That is the 18 Oct',
          '# bug and it cost a hand repair.',
          '#',
          '# cp, NOT a text copy. A revert is a byte copy and a',
          '# helper that read backups as text crashed on a UTF-16 file',
          '# on 22 Oct and left three files reverted in an applied tree.',
          '#',
          '# None of these three CREATES a file, and nothing is',
          '# retired, so a revert is purely a restore.',
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
    print('R12P1 -> %s' % OUT)
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
