# -*- coding: utf-8 -*-
"""CM-1 - ONE COLUMN, FIVE LIMITS, AND ONE OF THEM WAS NOTHING.

Demetri, 6 Oct 2026, looking at Issues (Comments): "I want to increase
the length of the Enter New Comment field. It would need to be almost 3
times its current length."

MEASURED BEFORE ANSWERING, because "length" could have been three things
and two of them have hard ceilings. The box renders 746 x 98 at 1280 and
830 x 98 at 1920; the card is capped at max-width 1200, so the WIDEST it
can get where it sits is about 830 - a gain of 11%, not 300%. Height was
free. Characters were the thing he meant, and the thing with a real
ceiling in the way:

    the database column        CharField(max_length=255)
    the NEW comment box        maxlength="250"     browser only
    the EDIT comment box       maxlength="255"     browser only
    the EDIT view              len > 255 -> rejected with a message
    the ADD view               NOTHING AT ALL

FOUR NUMBERS FOR ONE COLUMN, and the fifth was missing. maxlength is a
browser hint, not a guarantee: a POST from a script, a stale page or
anything that is not the form went to MySQL unchecked on the add path,
and under strict mode that is a 500 rather than a message. The edit path
had already been written properly. This round lands all five on 1000.

HE CHOSE 1000 FOR BOTH the column and the form, so they are equal and
there is no headroom - told to him in one line at the time. Nothing can
exceed the column because both views now refuse above the same number,
so equal is safe; it only means raising the form later needs a migration
too.

WHAT A LONGER COMMENT DOES ELSEWHERE, checked before building. The
comment prints on friday_status_report.html inside .detail-comment,
which is `display: block; width: 100%; word-break: break-word`, and in
fsr_email.html - the emailed report and its PDF - inside a plain div.
Neither is a table cell, so 1000 characters wrap to more lines and
nothing overflows.

FILES: pages/models.py, pages/views/issues.py,
       pages/templates/fsr_details.html, and one migration.
                                              [test_comment_length.py]
"""
import os
import re
import sys

SUFFIX = '.bak_cmlen'
MARK = 'CM-1, 6 Oct 2026'

OLD_COL = 255
NEW_COL = 1000
OLD_FORM_ADD = 250
OLD_FORM_EDIT = 255
NEW_FORM = 1000

ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(ROOT, 'pages', 'models.py')
VIEWS = os.path.join(ROOT, 'pages', 'views', 'issues.py')
PAGE = os.path.join(ROOT, 'pages', 'templates', 'fsr_details.html')
MIGRATION = 'pages/migrations/0098_comment_length.py'

CHECK = False

# ==========================================================================
# THE MIGRATION
# ==========================================================================
# WIDENING A CharField IS NOT A DATA CHANGE. MySQL rewrites the column
# definition; every existing value is already inside 255 and stays
# exactly as it is. Nothing is truncated, nothing is re-encoded. It is
# reversible, and the reverse is only unsafe once a row longer than 255
# exists - which is why the reverse is written out rather than left to
# Django's default, so the day somebody runs it they get told.
MIGRATION_PY = '''# -*- coding: utf-8 -*-
"""CM-1 - the issue comment column goes from 255 to 1000 characters.

Demetri asked for the Enter New Comment field to hold about three times
what it held. The browser said 250, the edit box said 255, the edit view
enforced 255 and the add view enforced nothing; the column was the real
ceiling at 255. All five now say 1000.

WIDENING IS NOT A DATA CHANGE. Every existing comment is already inside
255 and is left exactly as it is - no truncation, no re-encoding, no
backfill. MySQL rewrites the column definition and that is all.

THE REVERSE IS SAFE TODAY AND WILL NOT STAY SAFE. The moment one comment
longer than 255 exists, running this backwards truncates it. Django
would generate that reverse silently; it is written out here so that it
is a decision somebody makes rather than one that happens.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0097_passport_holder'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issues_details',
            name='issues_details_comment',
            field=models.CharField(blank=True, max_length=1000),
        ),
    ]
'''

# ==========================================================================
# THE SERVER-SIDE GUARD THE ADD PATH NEVER HAD
# ==========================================================================
ADD_OLD = """        # Validate comment exists
        if not comment_text:
            messages.error(request, "Comment cannot be empty")
            return redirect(redirect_url)
"""

ADD_NEW = """        # Validate comment exists
        if not comment_text:
            messages.error(request, "Comment cannot be empty")
            return redirect(redirect_url)

        # AND THAT IT FITS. [CM-1, 6 Oct 2026]
        # This path had no length check at all. maxlength on the textarea
        # is a browser hint, not a guarantee - a POST from a script, a
        # stale page or anything that is not the form reached
        # objects.create() unchecked, and under MySQL strict mode a value
        # over the column width is a DataError, which is a 500 and not a
        # message. fsr_comment_edit has always done this properly; this
        # is the same check, with the same wording, on the other door.
        if len(comment_text) > COMMENT_MAX_LENGTH:
            messages.error(request, "Comment must be %d characters or "
                           "fewer." % COMMENT_MAX_LENGTH)
            return redirect(redirect_url)
"""

EDIT_OLD = """    if len(new_text) > 255:
        messages.error(request, "Comment must be 255 characters or fewer.")
        return redirect(detail_url)
"""

EDIT_NEW = """    if len(new_text) > COMMENT_MAX_LENGTH:
        messages.error(request, "Comment must be %d characters or fewer."
                       % COMMENT_MAX_LENGTH)
        return redirect(detail_url)
"""

# ONE NAME, NOT FIVE LITERALS. The whole defect this round fixes is that
# the number was written out by hand in five places and drifted in four
# of them. The views now read it from the model field itself, so it
# cannot drift from the column again - change the column and the checks
# follow.
CONST_ANCHOR = 'logger = logging.getLogger(__name__)\n'
CONST_BLOCK = '''
# THE LIMIT, READ FROM THE COLUMN RATHER THAN RETYPED.
# [CM-1, 6 Oct 2026]
# Before this round the number 255 was written out by hand in five
# places and three of them disagreed: the textarea said 250, the edit
# textarea said 255, the edit view said 255, the column said 255, and
# the add view said nothing. Reading it off the model field means the
# checks can never again say something the database does not.
COMMENT_MAX_LENGTH = issues_details._meta.get_field(
    'issues_details_comment').max_length


'''


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


def fit(text, block):
    if '\r\n' in text:
        return block.replace('\r\n', '\n').replace('\n', '\r\n')
    return block.replace('\r\n', '\n')


def planned(path, edits, label):
    """The file as this round would leave it - WITHOUT WRITING IT.

    NOTHING IS WRITTEN UNTIL EVERY FILE HAS BEEN BUILT AND EVERY CHECK
    HAS PASSED. My first version of this patcher wrote each file as it
    went and verified afterwards, and twice it left the tree half-done
    on an assertion that fired at the end - once with a syntax error in
    issues.py. A round refuses or it completes; it does not do four
    files out of five. [the house rule, learned again]

    THE ANCHOR IS FITTED TOO, not only the replacement. pages/views/
    issues.py is CRLF and the templates are LF; an anchor written with
    \n here matches nothing in the CRLF one, and the round refuses with
    "matched 0 times" on a file that plainly contains the lines.
    """
    text = read(path)
    edits = [(fit(text, o), fit(text, n), w) for o, n, w in edits]
    if all(new in text for _o, new, _w in edits):
        return text, '%-38s already done' % label, 0
    for old, _new, what in edits:
        n = text.count(old)
        if n != 1:
            raise SystemExit('CM-1: %s - the anchor for %s matched %d '
                             'time(s), not once' % (label, what, n))
    for old, new, _w in edits:
        text = text.replace(old, new, 1)
    return text, '%-38s %d edit(s)' % (label, len(edits)), len(edits)


def new_file(rel, body, what):
    path = os.path.join(ROOT, rel.replace('/', os.sep))
    if os.path.isfile(path):
        if MARK in read(path) or 'CM-1' in read(path):
            print('  %-38s already there' % rel)
            return
        raise SystemExit('CM-1: %s exists and this round did not write it'
                         % rel)
    if not CHECK:
        write(path, body)
    print('  %-38s NEW  %s' % (rel, what))


# ==========================================================================
# AND THE SECOND, WHICH IS A CLAIM THAT COULD ONLY EVER BE TRUE ONCE
# ==========================================================================
# test_passport_holder.py asserts its own migration "is the latest":
#
#     ok(names[-1] == '0097_passport_holder', ...)
#
# That was true the day PH-1 shipped and false the moment any round
# added a migration - which is this one. It is not a scope bug; it is a
# claim that was never about PH-1 at all. What PH-1 can honestly say is
# that ITS migration is on disk and that nothing in the chain before it
# is missing, and that is what it says now.
PH = 'test_passport_holder.py'
PH_OLD = """    names = sorted(n for a, n in loader.disk_migrations if a == 'pages')
    ok(names[-1] == '0097_passport_holder',
       '  and 0097_passport_holder is the latest', names[-3:])
"""
PH_NEW = """    names = sorted(n for a, n in loader.disk_migrations if a == 'pages')
    # ITS OWN MIGRATION, NOT THE LAST ONE. [CM-1, 6 Oct 2026]
    # This read names[-1] == '0097_passport_holder' - true the day PH-1
    # shipped and false the moment any later round added a migration,
    # which CM-1 did. A round can only speak for its own work: that the
    # migration is on disk, and that the chain up to it is unbroken.
    ok('0097_passport_holder' in names,
       '  and 0097_passport_holder is on disk', names[-3:])
    nums = sorted(int(n.split('_')[0]) for n in names)
    mine = nums.index(97)
    ok(nums[:mine + 1] == list(range(nums[0], 97 + 1)),
       '  with no gap in the chain before it',
       nums[max(0, mine - 3):mine + 1])
"""


def patch_ph():
    path = os.path.join(ROOT, PH)
    text = read(path)
    if 'ITS OWN MIGRATION, NOT THE LAST ONE' in text:
        print('  %-38s already restated' % PH)
        return
    n = text.count(fit(text, PH_OLD))
    if n != 1:
        raise SystemExit('CM-1: %s - the latest-migration claim matched %d '
                         'time(s), not once' % (PH, n))
    text = text.replace(fit(text, PH_OLD), fit(text, PH_NEW), 1)
    if not CHECK:
        backup(path)
        write(path, text)
    print('  %-38s stops claiming to be the last migration' % PH)


# ==========================================================================
# THE ONE SUITE THIS ROUND BREAKS, AND IT IS THE SAME SCOPE BUG AGAIN
# ==========================================================================
# test_ei_modal.py section 1 counts maxlength="255" on fsr_details.html
# and requires 3 - the heading, the description and the comment edit
# box - to prove the EI-modal round left those attributes alone. CM-1
# moves one of the three to 1000, so it reads 2 and the suite goes red.
#
# THE ASSERTION IS NOT WRONG. The READ is: line 193 is NOW = read(FD),
# the LIVE page, where it should be the page as EI-MODAL left it. Read
# at its own scope it still counts 3, because that is what the page said
# when that round ran. This is the fourth suite caught doing it -
# test_tab_right_edge, test_table_admin, test_celebration_az and now
# this one - and the fix is the same every time.
#
# NOT A NUMBER BUMP. Changing 3 to 2 would make it pass and quietly turn
# a statement about the EI-modal round into a statement about whatever
# ran last.
EI = 'test_ei_modal.py'
EI_OLD = 'NOW = read(FD)\n'
EI_NEW = ('# AS THIS ROUND LEFT IT, NOT AS THE PAGE STANDS. [CM-1, 6 Oct 2026]\n'
          '# Section 1 counts attributes on fsr_details.html and compares\n'
          '# them with the backup, to show this round changed only its own\n'
          '# six blocks. Read live, any LATER round that touches the page\n'
          "# breaks it - CM-1 moved one maxlength and the count went 3 to 2.\n"
          '# A gate reads the page as ITS OWN round left it.\n'
          'try:\n'
          '    from alv_rounds import as_left_by as _as_left_by\n'
          'except Exception:\n'
          '    _as_left_by = None\n'
          'NOW = _as_left_by(FD, SUFFIX, read) if _as_left_by else read(FD)\n')


def patch_ei():
    path = os.path.join(ROOT, EI)
    text = read(path)
    if 'AS THIS ROUND LEFT IT, NOT AS THE PAGE STANDS' in text:
        print('  %-38s already scoped' % EI)
        return
    n = text.count(EI_OLD)
    if n != 1:
        raise SystemExit('CM-1: %s - the live read matched %d time(s), not '
                         'once' % (EI, n))
    text = text.replace(EI_OLD, fit(text, EI_NEW), 1)
    if not CHECK:
        backup(path)
        write(path, text)
    print('  %-38s now reads at its own round scope' % EI)


# ==========================================================================
# SE-1'S TRIPWIRE, WHICH THIS ROUND MOVES BY ONE
# ==========================================================================
# apply_settings_env.py keeps an EXACT count of the suites that boot
# Django, deliberately: a floor would let a suite with no throwaway key
# of its own in silently, and that suite would then fail on any machine
# without a .env. test_comment_length.py boots Django and migrates a
# fresh sqlite database to drive both views with real POSTs, so the
# number goes up by one - raised HERE, by the round that added the
# suite, rather than by whoever next runs the sweep and finds it red.
SE = 'apply_settings_env.py'
SE_OLD = 'BOOT_COUNT = 12\n'
SE_NEW = ('# 13 since 6 Oct 2026: Section CM round CM-1 added\n'
          '# test_comment_length.py, which boots Django and migrates an\n'
          '# in-memory database so it can POST 1000 and 1001 characters at\n'
          '# both comment doors. It carries its own setdefault; this\n'
          '# number is what proves that rather than assuming it.\n'
          'BOOT_COUNT = 13\n')


def patch_se():
    path = os.path.join(ROOT, SE)
    text = read(path)
    if 'BOOT_COUNT = 13' in text:
        print('  %-38s already at 13' % SE)
        return
    n = text.count(SE_OLD)
    if n != 1:
        raise SystemExit('CM-1: %s - BOOT_COUNT = 12 matched %d time(s), '
                         'not once' % (SE, n))
    text = text.replace(SE_OLD, fit(text, SE_NEW), 1)
    if not CHECK:
        backup(path)
        write(path, text)
    print('  %-38s boot count 12 -> 13' % SE)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)

    # THE PREMISE, CHECKED BEFORE ANYTHING IS WRITTEN. If the tree does
    # not hold the five numbers this round was measured against, it is
    # not the tree this round was written for.
    m = read(MODELS)
    v = read(VIEWS)
    p = read(PAGE)
    done = MARK in v

    if not done:
        premise = [
            (m, "issues_details_comment = models.CharField(max_length=%d, "
                "blank=True)" % OLD_COL, 'the column at %d' % OLD_COL),
            (p, 'maxlength="%d"' % OLD_FORM_ADD,
             'the new-comment box at %d' % OLD_FORM_ADD),
            (v, 'if len(new_text) > %d:' % OLD_COL,
             'the edit view guard at %d' % OLD_COL),
        ]
        for text, needle, what in premise:
            n = text.count(needle)
            if n != 1:
                raise SystemExit('CM-1: %s matched %d time(s), not once - '
                                 'this is not the tree this round was '
                                 'measured against' % (what, n))
        # The add path really did have no guard. The round exists partly
        # for this, so it is proved rather than assumed.
        # THE BODY OF fsr_comment_add, from its def to the first line
        # that is plainly past the validation, read for any length check
        # at all. The round exists partly because there was none, so it
        # is proved rather than remembered.
        d = v.index('def fsr_comment_add(request, issues_id):')
        head = v[d:v.index('user_initials = ', d)]
        if 'len(comment_text)' in head:
            raise SystemExit('CM-1: fsr_comment_add already checks the '
                             'length - re-read the view before adding a '
                             'second check')

    # ------------------------------------------------------------------
    # BUILD EVERYTHING, CHECK EVERYTHING, THEN WRITE
    # ------------------------------------------------------------------
    plans = []
    m2, m_say, _n = planned(MODELS, [(
        "issues_details_comment = models.CharField(max_length=%d, "
        "blank=True)" % OLD_COL,
        "issues_details_comment = models.CharField(max_length=%d, "
        "blank=True)" % NEW_COL,
        'the column')], 'pages/models.py')
    plans.append((MODELS, m2, m_say))

    v2, v_say, _n = planned(VIEWS, [
        (CONST_ANCHOR, CONST_ANCHOR + CONST_BLOCK, 'the constant'),
        (ADD_OLD, ADD_NEW, 'the guard the add path never had'),
        (EDIT_OLD, EDIT_NEW, "the edit path's own guard"),
    ], 'pages/views/issues.py')
    plans.append((VIEWS, v2, v_say))

    # ONLY OUR FIELD'S BOX. Lines 203 and 207 of this page are
    # issues_heading and issues_description - two DIFFERENT columns that
    # really are 255 and are no business of this round. My first version
    # of the final check banned maxlength="255" page-wide and refused on
    # those two. A check that cannot tell one field from another is how
    # a patcher edits something nobody meant.
    p2, p_say, _n = planned(PAGE, [
        ('maxlength="%d"' % OLD_FORM_ADD, 'maxlength="%d"' % NEW_FORM,
         'the new-comment box'),
        ('id="ec_text" name="issues_details_comment" class="form-control" '
         'rows="4" maxlength="%d" required' % OLD_FORM_EDIT,
         'id="ec_text" name="issues_details_comment" class="form-control" '
         'rows="4" maxlength="%d" required' % NEW_FORM,
         'the edit box')], 'pages/templates/fsr_details.html')
    plans.append((PAGE, p2, p_say))

    # --- the five numbers agree, before a byte is written ---------------
    if ('max_length=%d' % NEW_COL) not in m2:
        raise SystemExit('CM-1: the column did not move')
    if v2.count('COMMENT_MAX_LENGTH') < 4:
        raise SystemExit('CM-1: the views do not read the limit off the '
                         'column')
    if 'if len(new_text) > %d:' % OLD_COL in v2:
        raise SystemExit('CM-1: the edit guard still says %d' % OLD_COL)
    if 'if len(new_heading) > 255' not in v2:
        raise SystemExit("CM-1: the heading and description guard was "
                         "disturbed - those are not this round's fields")
    if p2.count('maxlength="%d"' % NEW_FORM) != 2:
        raise SystemExit('CM-1: the two comment boxes do not both say %d'
                         % NEW_FORM)
    if p2.count('maxlength="255"') != 2:
        raise SystemExit('CM-1: the heading and description boxes should '
                         'still say 255 - they are other columns')
    if 'maxlength="%d"' % OLD_FORM_ADD in p2:
        raise SystemExit('CM-1: the old %d survives on the page'
                         % OLD_FORM_ADD)
    import ast
    for name, src in (('models.py', m2), ('issues.py', v2)):
        try:
            ast.parse(src)
        except SyntaxError as e:
            raise SystemExit('CM-1: %s would not parse - %s' % (name, e))

    # --- only now ------------------------------------------------------
    print('')
    print('  NEW FILES')
    print('  ' + '-' * 70)
    new_file(MIGRATION, MIGRATION_PY,
             'the column, %d -> %d' % (OLD_COL, NEW_COL))

    print('')
    print('  CHANGED FILES')
    print('  ' + '-' * 70)
    for path, text, say in plans:
        if not CHECK and text != read(path):
            backup(path)
            write(path, text)
        print('  ' + say)
    patch_se()
    patch_ei()
    patch_ph()

    print('')
    print('CM-1  column : %d -> %d' % (OLD_COL, NEW_COL))
    print('CM-1  boxes  : %d and %d -> %d both'
          % (OLD_FORM_ADD, OLD_FORM_EDIT, NEW_FORM))
    print('CM-1  guards : the add path gains one, the edit path keeps its '
          'own, both read the column')
    if CHECK:
        print('CM-1  NOT APPLIED')
        return 1
    print('CM-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
