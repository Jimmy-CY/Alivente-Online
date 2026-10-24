# -*- coding: utf-8 -*-
"""bundle_r11p1.py - release 11, push 1. Two rounds, one push.

    T2-1   a tenancy can have two people, and the database has only
           ever held one. Three columns, one migration, the form field
           list and the admin search. NOT A NEW FEATURE - a stored one
           that was being thrown away: generate_lease_agreement asks
           for a second tenant in full, six fields, and keeps none of
           them. Somebody types a joint tenant for every lease
           generated and the system forgets them the moment the .docx
           downloads
    T2-2   and the screens that show the second one. Add Tenant and
           Edit Tenant take a joint tenant behind a button, the
           register names both people, and the model refuses one on a
           Company tenancy - which Generate has refused since long
           before these columns existed

ONE DECISION OF HIS UNDER EACH, taken 23 and 24 October:
    "The default must be one tenant, one email, one telephone number.
     But the user must have the choice to add a second tenant."
A joint tenant who SIGNS AND IS LIABLE, not a non-signing occupant -
which is why it is worth a migration rather than a text box on the
lease form. Three columns and not six, because the FIRST tenant has
no passport and no address stored either. Individual tenancies only,
mirroring Generate. And both names in the register's Tenant cell, the
way the four reports will print them.

NOTHING CHANGES ABOUT WHO GETS EMAILED. That is T2-5, it was decided
as BOTH TENANTS, and it is a behaviour change on a job that runs
every five minutes - so it is its own round with its own gate.
send_physical_invoices still reads tenant_email and this push proves
it does.

ONE REAL DEFECT OF MINE, AND A TOOL FOUND IT. Show-ButtonDrift asked
for action-danger on Remove Second Tenant and four suites failed over
it. I argued: the button only clears three unsaved boxes, so red
would be a lie. That is true on ADD and false on EDIT, where Remove
followed by Save takes a jointly liable person off a tenancy. The
heuristic was right about the screen I had not thought about.

A SECOND DEFECT THE PHONE RENDER FOUND. At 390px every field is its
own line, and the page read: Contact Person, Contact Number, Email
Address(es), Second Tenant, Contact Number, Email Address(es) - two
identical pairs with nothing saying whose they are. The second set
now names its owner. Both spellings were measured in a col-md-4 at
1280 and at 390 BEFORE either was written.

AND A CONTROL REFUTED A CLAIM IN THE ROUND'S OWN COMMENTS. T2-2 said
a hard-coded `display: block` would stack the three fields into a
column. The suite measured it: it does not - the wrapper's display is
block anyway. The claim was corrected in the patcher rather than the
control being softened, and the control now measures the computed
value.

THREE EXPIRY-DATED CLAIMS REPAIRED RATHER THAN BUMPED, which is the
fifth round running to carry this repair:
    test_label_fit       LF-1's ids, names, placeholders and column
                         classes compared against the LIVE file, so
                         every future round adding a field to either
                         tenant screen broke it
    test_entry_sections  section 10 kept the spelling section 3 of
                         the same file gave up on 5 October
    test_second_tenant   T2-1's own "no template shows a second
                         tenant yet - that is T2-2". This is T2-2.
All three now read through as_left_by. Bumping a number would only
have moved the failure to T2-3.

THE APPLIED LIST IS ENUMERATED FROM THE .bak FILES ON DISK, never
typed, and the CREATED list is read from each patcher's own CREATES.
T2-1 creates its migration; T2-2 creates nothing.
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = '/mnt/user-data/outputs/R11P1'
SKIP = ('.git', '__pycache__', 'media', 'node_modules', 'staticfiles')

# NEWEST FIRST, which is also revert order.
#
# BOTH ROUNDS WRITE Push-PendingChanges.ps1, alv_rounds.py,
# alv_tree.py and test_waiting_down.py. They were applied T2-1 then
# T2-2, so they revert in the opposite order: reverting oldest-first
# restores the LATER round's text over the earlier one and loses the
# original. That is the 18 October bug and it cost a hand repair.
#
# AND BOTH WRITE pages/models.py AND test_second_tenant.py, which
# makes the order load-bearing here rather than merely tidy: T2-2
# edits the file T2-1 wrote, and the suite T2-1 wrote.
ORDER = [
    ('.bak_t2screens', 'T2-2', 'apply_tenant_screens.py',
     'test_tenant_screens.py',
     'the screens that show a second tenant'),
    ('.bak_secondtenant', 'T2-1', 'apply_second_tenant.py',
     'test_second_tenant.py',
     'a tenancy can hold two people'),
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

EXTRA = ('stage_round.py', 'bundle_r11p1.py')


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
          '# revert_all.sh - release 11 push 1. NEWEST ROUND FIRST.',
          '#',
          '# Both write Push-PendingChanges.ps1, alv_rounds.py,',
          '# alv_tree.py, test_waiting_down.py, pages/models.py and',
          '# test_second_tenant.py. Applied T2-1 then T2-2 - so they',
          '# revert T2-2, then T2-1.',
          '#',
          '# Reverting oldest-first restores the LATER round\'s text over',
          '# the earlier one and loses the original. That is the 18 Oct',
          '# bug and it cost a hand repair.',
          '#',
          '# cp, NOT a text copy. A revert is a byte copy and a',
          '# helper that read backups as text crashed on a UTF-16 file',
          '# on 22 Oct and left three files reverted in an applied tree.',
          '#',
          '# T2-1 CREATES its migration, which a revert deletes -',
          '# there was no before to restore. Nothing here is retired.',
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
    print('R11P1 -> %s' % OUT)
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
