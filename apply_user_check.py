"""IC-2 - THE OTHER HALF OF THE PAIR.

   IC-1 split fa-ban: Void kept it, Disable became fa-user-slash. The
   drift report then printed what had been hiding behind it:

       fa-check      icon-approve, icon-unlock

   One picture, two names, again. Approve an invoice and Enable a user
   are not the same act on the same kind of thing, and a reader looking
   at a row cannot tell which one a tick means.

   DEMETRI, 5 Oct 2026: ENABLE BECOMES fa-user-check. Approve keeps the
   plain tick, which is what a tick is for. It is the symmetric twin of
   the choice he made an hour earlier - Disable is a person with a line
   through them, Enable is a person with a tick - and the two now read as
   a pair on the one screen that carries both.

   THREE USES ON TWO PAGES, and the second is the one IC-1 taught this
   round to look for:

       user_administration.html          2   Enable      the desktop
                                             button and its phone twin
       household_member_management.html  1   Activate    inside a split
                                             glyph name, across a tag

   That third is the SAME LINE IC-1 edited. It reads

       fa-{% if m.is_active %}user-slash{% else %}check{% endif %}

   and IC-1 took the first half while the decision about the second had
   not been made. A census that only read whole names would have missed
   it twice; IC-1 built the census for the shape, and this round is the
   first thing it caught.

   APPROVE IS LEFT ALONE, and that is the decision, not an omission.
   .icon-approve is on five controls across invoices.html and
   physical_invoice_list.html, all of them meaning "this is now
   approved", and a tick is the right picture for that.

   FILES: user_administration.html, household_member_management.html,
          base.html.                                [test_user_check.py]
"""
import os
import sys

import alv_tree as T

SUFFIX = '.bak_usercheck'

PAGE = 'user_administration.html'
HM = 'household_member_management.html'

EDITS = [
    ('<i class="fas fa-check"></i>',
     '<i class="fas fa-user-check"></i>'),
    ('<i class="fas fa-check mobile-action-icon icon-color-unlock"></i>',
     '<i class="fas fa-user-check mobile-action-icon icon-color-unlock"></i>'),
]

HM_OLD = ('<i class="fas fa-{% if m.is_active %}user-slash{% else %}check'
          '{% endif %}"></i>')
HM_NEW = ('<i class="fas fa-{% if m.is_active %}user-slash{% else %}'
          'user-check{% endif %}"></i>')

# base names the glyph in the note explaining why .icon-reset-pw is not
# .icon-lock. IC-1 corrected the Disable half of that sentence.
BASE_OLD = ('Save is --alv-good, which .icon-approve and .icon-unlock '
            'already')
BASE_NEW = ('Save is --alv-good, which .icon-approve (fa-check) and\n'
            '         .icon-unlock (fa-user-check, IC-2) already')

KEEPS = ('invoices.html', 'physical_invoice_list.html')
KEEPS_N = 3


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    page, hm, base = T.path_of(PAGE), T.path_of(HM), T.path_of('base.html')
    for p, n in ((page, PAGE), (hm, HM), (base, 'base.html')):
        if not p:
            raise SystemExit('IC-2: %s is not in this checkout' % n)

    text = read(page)
    edits = 0
    if 'fa-user-check' not in text:
        for old, new in EDITS:
            k = text.count(old)
            if k != 1:
                raise SystemExit('IC-2: %r matched %d times on %s, expected 1'
                                 % (old, k, PAGE))
            text = text.replace(old, new, 1)
            edits += 1
        if 'fa-check' in text:
            raise SystemExit('IC-2: %s still carries a bare fa-check' % PAGE)

    htext = read(hm)
    hedit = 0
    if HM_NEW not in htext:
        k = htext.count(HM_OLD)
        if k != 1:
            raise SystemExit('IC-2: the split glyph on %s matched %d times, '
                             'expected 1. IC-1 left it reading user-slash on '
                             'one branch and check on the other; if it reads '
                             'otherwise, look at it.' % (HM, k))
        htext = htext.replace(HM_OLD, HM_NEW, 1)
        hedit = 1

    btext = read(base)
    bedit = 0
    if 'fa-user-check, IC-2' not in btext:
        k = btext.count(BASE_OLD)
        if k != 1:
            raise SystemExit("IC-2: base's note naming the two good-tone "
                             'classes matched %d times, expected 1' % k)
        btext = btext.replace(BASE_OLD, BASE_NEW, 1)
        bedit = 1

    # APPROVE KEEPS THE TICK, and the round proves it did not wander.
    kept = 0
    for name in KEEPS:
        s = read(T.path_of(name))
        if 'fa-user-check' in s:
            raise SystemExit('IC-2: %s has gained a fa-user-check - Approve '
                             'is not this round to change' % name)
        kept += s.count('icon-approve')
    # EXACTLY THREE, MEASURED. The first build asserted "more than four"
    # from memory and refused itself: invoices.html carries two - the
    # live button and its disabled twin - and physical_invoice_list one.
    # A guessed floor is not a gate, it is a hope.
    if kept != KEEPS_N:
        raise SystemExit('IC-2: %d .icon-approve control(s) across %s, '
                         'expected %d. Approve is not this round to change, '
                         'so a change in its count wants reading.'
                         % (kept, KEEPS, KEEPS_N))

    if not check:
        if edits:
            backup(page)
            write(page, text)
        if hedit:
            backup(hm)
            write(hm, htext)
        if bedit:
            backup(base)
            write(base, btext)

    print('IC-2  glyphs renamed  : %d' % (edits + hedit))
    print('IC-2  split name      : %d' % hedit)
    print('IC-2  base notes      : %d' % bedit)
    print('IC-2  approve controls: %d, untouched' % kept)
    if check:
        if edits or hedit or bedit:
            print('IC-2  NOT APPLIED')
            return 1
        print('IC-2  applied')
        return 0
    print('IC-2  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
