"""IC-1 - ONE PICTURE, ONE NAME: fa-ban.

   The house rule, written into base when .icon-edit broke it:

       A class carries ONE PICTURE. Alias the colour, never the name.

   The drift report has been enforcing that direction since RA-1 and has
   been printing the OTHER direction, under NOTED NOT DRIFT, ever since:

       fa-ban        icon-lock, icon-void

   Two names, one picture. A reader looking at a row cannot tell Disable
   this user from Void this receipt, and neither can anyone reading the
   markup. RA-1 declined to guess, correctly - picking a replacement
   glyph is a decision, not a repair.

   DEMETRI DECIDED, 5 Oct 2026: VOID KEEPS fa-ban, DISABLE BECOMES
   fa-user-slash. The universal no-entry mark stays on the action that
   really is a refusal, and the account action gets a glyph that says
   whose account. Font Awesome 6.0.0 is what base loads, so fa-user-slash
   is there.

   THREE USES ON TWO PAGES, AND THE OTHER FOUR STAY PUT:

       user_administration.html          2   Disable     -> fa-user-slash
       household_member_management.html  1   Deactivate  -> fa-user-slash
       cash_receipts.html                4   Void        -> unchanged

   The two on user_administration are the same control at two widths -
   the desktop .icon-lock button and its .mobile-action-btn twin. A round
   that changed one of them would leave a phone and a laptop drawing
   different pictures for one action, which is the same defect pointing
   sideways.

   THE THIRD WAS NOT IN THE DRIFT REPORT, AND THE FIRST BUILD OF THIS
   ROUND SHIPPED WITHOUT IT. household_member_management wears .icon-lock
   too, and it builds the glyph name ACROSS a template tag:

       <i class="fas fa-{% if m.is_active %}ban{% else %}check{% endif %}">

   The report's census reads `fa-` followed by a name. Here `fa-` is
   followed by `{%`, so the page contributes nothing to the census and
   .icon-lock looked like it had one picture when it had two. Renaming
   only user_administration would have LEFT .icon-lock drawing
   fa-user-slash on one page and fa-ban on another - this round breaking
   the exact rule it exists to enforce, invisibly, because the instrument
   that would have caught it cannot read that line.

   Deactivate a household member and Disable a user are the same act on
   the same kind of thing, so they take the same picture. The `check`
   half is .icon-unlock and is not this round's.

   ONE SPLIT NAME IN 150 TEMPLATES, and section 4 censuses for it, so the
   next one is found rather than discovered.

   AND BASE'S OWN NOTE IS PART OF THE ROUND. .icon-reset-pw carries a
   comment explaining why it did not reuse .icon-lock, and it names the
   glyph: ".icon-lock is fa-ban (Disable)". Leaving that behind would
   leave the record of the rule contradicting the rule.

   NOT THIS ROUND: Show-RowActionDrift.py's note saying the two names are
   pre-existing and unrepaired. RA-5 owns that file in this bundle and
   corrects it there, so one round owns one file.

   FILES: user_administration.html, base.html.     [test_user_slash.py]
"""
import os
import sys

import alv_tree as T

SUFFIX = '.bak_userslash'

PAGE = 'user_administration.html'
OLD_GLYPH = 'fa-ban'
NEW_GLYPH = 'fa-user-slash'

# Matched in full, with the class beside it, so this cannot touch a
# fa-ban that means something else if one is ever added to this page.
EDITS = [
    ('<i class="fas fa-ban"></i>',
     '<i class="fas fa-user-slash"></i>'),
    ('<i class="fas fa-ban mobile-action-icon icon-color-lock"></i>',
     '<i class="fas fa-user-slash mobile-action-icon icon-color-lock"></i>'),
]

BASE_OLD = '.icon-lock is fa-ban (Disable); this is fa-envelope.'
BASE_NEW = ('.icon-lock is fa-user-slash (Disable, IC-1); this is\n'
            '   fa-envelope.')

# The split name. Matched whole, because half of it is not this round's.
HM = 'household_member_management.html'
HM_OLD = ('<i class="fas fa-{% if m.is_active %}ban{% else %}check'
          '{% endif %}"></i>')
HM_NEW = ('<i class="fas fa-{% if m.is_active %}user-slash{% else %}check'
          '{% endif %}"></i>')

KEEPS = 'cash_receipts.html'
KEEPS_N = 4


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

    page = T.path_of(PAGE)
    base = T.path_of('base.html')
    keeps = T.path_of(KEEPS)
    for p, n in ((page, PAGE), (base, 'base.html'), (keeps, KEEPS)):
        if not p:
            raise SystemExit('IC-1: %s is not in this checkout' % n)

    text = read(page)
    done = text.count(NEW_GLYPH) >= len(EDITS)

    edits = 0
    if not done:
        # EXACT COUNTS, OR REFUSE. If the page has grown a third fa-ban
        # since this was measured it is a different control and wants
        # looking at, not renaming.
        n = text.count(OLD_GLYPH)
        if n != len(EDITS):
            raise SystemExit('IC-1: %s carries %d %s, expected %d'
                             % (PAGE, n, OLD_GLYPH, len(EDITS)))
        for old, new in EDITS:
            k = text.count(old)
            if k != 1:
                raise SystemExit('IC-1: %r matched %d times on %s, expected 1'
                                 % (old, k, PAGE))
            text = text.replace(old, new, 1)
            edits += 1
        if text.count(OLD_GLYPH) != 0:
            raise SystemExit('IC-1: %s still carries a %s after the edits'
                             % (PAGE, OLD_GLYPH))

    hpath = T.path_of(HM)
    if not hpath:
        raise SystemExit('IC-1: %s is not in this checkout' % HM)
    htext = read(hpath)
    hedit = 0
    if HM_NEW not in htext:
        k = htext.count(HM_OLD)
        if k != 1:
            raise SystemExit('IC-1: the split glyph on %s matched %d times, '
                             'expected 1' % (HM, k))
        htext = htext.replace(HM_OLD, HM_NEW, 1)
        hedit = 1

    btext = read(base)
    bedit = 0
    if BASE_NEW.split('\n')[0] not in btext:
        k = btext.count(BASE_OLD)
        if k != 1:
            raise SystemExit("IC-1: base's note about .icon-lock matched %d "
                             'times, expected 1' % k)
        btext = btext.replace(BASE_OLD, BASE_NEW, 1)
        bedit = 1

    # AND THE ONE THAT KEEPS THE GLYPH STILL HAS IT. The round is a
    # rename of one meaning, not a purge of a picture.
    k = read(keeps).count(OLD_GLYPH)
    if k != KEEPS_N:
        raise SystemExit('IC-1: %s carries %d %s, expected %d - Void is not '
                         'this round to change' % (KEEPS, k, OLD_GLYPH,
                                                   KEEPS_N))

    if not check:
        if edits:
            backup(page)
            write(page, text)
        if hedit:
            backup(hpath)
            write(hpath, htext)
        if bedit:
            backup(base)
            write(base, btext)

    print('IC-1  glyphs renamed  : %d' % (edits + hedit))
    print('IC-1  split name fixed: %d' % hedit)
    print('IC-1  base notes      : %d' % bedit)
    print('IC-1  %s keeps  : %d' % (KEEPS, k))
    if check:
        if edits or hedit or bedit:
            print('IC-1  NOT APPLIED')
            return 1
        print('IC-1  applied')
        return 0
    print('IC-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
