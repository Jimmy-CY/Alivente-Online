# -*- coding: utf-8 -*-
"""apply_help_label.py - round HL-1, 12 Oct 2026.

D-2 FIXED THIS IN SEPTEMBER. IT FIXED ONE OF THE TWO.

`apply_small_three.py`, 23 Sep, item 1, in its own words:

    WORKSPACE MANAGEMENT'S HELP BUTTON WEARS A BACK LABEL.
    `<span class="action-back-label"> Help</span>` on a button that is
    .action-secondary, not .action-back. Base's hide rule is scoped to
    .action-back, so nothing breaks TODAY - but 74 other pages carry
    their own UNSCOPED copy of that rule, and the day this page gains
    one, the word Help disappears on a phone and leaves a bare question
    mark. 18 of the system's 20 Help buttons write bare text. This one
    joins them.

Every word of that is still true, and there was a second one:

    crs/submission_detail.html
      <i class="fas fa-question-circle"></i>
      <span class="action-back-label"> Help</span>

D-2 could not see it. Its suite walks pages/templates, and the CRS
reporting screens live in crs/templates/crs - a second Django template
root, which is the fact alv_tree.py exists to hold. So the round was
correct and incomplete, for the same reason every round before X0 was
incomplete, and the held entry on test_small_three has recorded it since:
`a non-Back control still labelled as a Back`.

MEASURED, BOTH ROOTS, TODAY
---------------------------
  130  elements wear .action-back-label across 151 templates
  128  of them say Back
    1  says Greek-then-Back behind the language switch
    1  says Help            <- this one, and it is the whole round

  40  Help controls in the tree, counted the way D-2 counted them:
      a button whose data-target is a HelpModal, menu copies excluded
  39  write bare text
   1  does not

D-2 said "18 of the system's 20". Both numbers were true of one root.
The count has doubled since September and the exception is still one.

WHY IT IS NOT HARMLESS, AND WHY IT IS NOT URGENT
------------------------------------------------
Base hides the word inside a media query:

    @media screen and (max-width: 768px) {
      .action-back .action-back-label,
      .back-button .action-back-label { display: none; }
    }

scoped to a back button, so a Help button keeps its word on a phone and
renders exactly as the other 64 do. NOTHING ON SCREEN CHANGES TODAY, and
this round says so rather than selling a repaint.

What changes is that a trap is removed. That rule USED TO BE
`.page-action-buttons .action-back .action-back-label`, three ancestors
deep, and 77 pages each carried their own unscoped
`.action-back-label { display: none }` to make up the difference. D7
removed all 77. The scope has already been widened once; the day it
widens again, or the day one unscoped copy comes back on this page, the
word Help vanishes and leaves a question mark in a circle.

The suite measures that instead of arguing it: the same fixture, with
the unscoped rule the system carried 77 times, loses the word before
this round and keeps it after.

WHAT THIS ROUND DOES NOT DO
---------------------------
It does not touch base. It does not touch the Greek Back label, which is
a Back. It does not touch the 64 Help buttons that were already right.
And it does not widen the hide rule to cover `.action-secondary`, which
would be the opposite fix: the word Help is not the word Back, and 64
pages already agree that a Help button keeps its label on a phone.

AND IT RELEASES test_small_three, which is what has been holding it:
widened against alv_tree the suite is 108 passed, 1 failed, and the one
failure is this span.

THREE STILL HELD after this: test_back_label, test_modal_heads and
test_surface_deep - the last waiting on F2b, a decision that is parked -
with test_button_sweep beside them on a narrow root that is a decision.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SUFFIX = '.bak_helplabel'
SUITE = 'test_help_label.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
X0 = 'test_tree_roots.py'
ST3 = 'test_small_three.py'
CHECK = False

RELEASED = ('test_small_three.py', 'test_back_label.py')
BL = 'test_back_label.py'

# TN-1, 12 Oct 2026. A LIVE BUG, REPORTED FROM PRODUCTION, AND IT IS A
# MIGRATION THAT MOVED WITHOUT ONE ASSIGNMENT MOVING WITH IT.
#
#     Error duplicating tenant: (1048, "Column
#     'tenant_lease_agreement_status' cannot be null")
#
# Migration 0095_none_columns deliberately took a list of string columns
# from nullable to NOT NULL, and tenant_lease_agreement_status is on that
# list. duplicate_tenant_view still assigns None to it. Before 0095 the
# column took NULL and Duplicate worked; after it, MySQL refuses the row
# and the RENEWAL BUTTON IS DEAD on Live.
#
# IT WOULD NOT HAVE FAILED ON SQLITE, which is lax about this, so a
# local run of the same code passes. That is why it reached production.
#
# The value is '' rather than "No Lease Agreement". The field is
# blank=True with no default, so a tenant added through the form gets
# '' - and a duplicate should be indistinguishable from a fresh tenant,
# not carry a fourth spelling of "there is no document". Measured: the
# field is WRITTEN in three places and READ in none - not in a template,
# not in a view. The queries that ask whether a lease agreement exists
# read the FileField, not this label.
TENANTS = 'pages/views/tenants.py'
TN_OLD = ("        new_tenant.tenant_lease_agreement = None\r\n"
          "        new_tenant.tenant_lease_agreement_status = None")
TN_NEW = (
    "        new_tenant.tenant_lease_agreement = None\r\n"
    "        # TN-1, 12 Oct 2026 - WAS None, and migration\r\n"
    "        # 0095_none_columns made this column NOT NULL. MySQL answered\r\n"
    "        # (1048, \"Column 'tenant_lease_agreement_status' cannot be\r\n"
    "        # null\") and Duplicate died on Live. SQLite would have taken\r\n"
    "        # it, which is why a local run never showed it.\r\n"
    "        #\r\n"
    "        # '' is what a tenant added through the form gets - the field\r\n"
    "        # is blank=True with no default - so a duplicate now looks\r\n"
    "        # exactly like a fresh tenant rather than carrying a third\r\n"
    "        # spelling of \"no document\" beside \"No Lease Agreement\".\r\n"
    "        new_tenant.tenant_lease_agreement_status = ''")
PAGE = 'crs/submission_detail.html'
PRECEDENT = 'workspace_management.html'

# THE SPAN, AND WHAT THE PRECEDENT PUT IN ITS PLACE. Taken from
# apply_small_three.py line 114 rather than invented, so the two pages
# end up the same shape and not merely both correct.
SPAN = ('<i class="fas fa-question-circle"></i>'
        '<span class="action-back-label"> Help</span>')
BARE = '<i class="fas fa-question-circle"></i> Help'

# Measured across both roots. The patcher refuses rather than guessing.
LABELS_TOTAL = 130
LABELS_NOT_BACK = 1
HELP_TOTAL = 40
HELP_BARE_BEFORE = 39

CEILING_WAS, CEILING_NOW = 42, 40
CONVERTED_WAS, CONVERTED_NOW = 63, 66
WAITING_WAS, WAITING_NOW = 5, 3

# BL-2. Measured, not quoted: of the five failures test_back_label
# reports when it is widened, FIVE are its reader and NONE is a defect.
#
#   live pages carrying an unscoped `.action-back-label { display: none }`
#       0
#   the same scan through as_left_by(p, '.bak_backlabel')
#       7, every one of them a CRS page
#
# That suite reads every page as "the file as BL-1 left it", and for a
# page BL-1 never touched as_left_by returns the backup taken by the
# first LATER round that happened to open it. The seven are frozen at a
# pre-PQ-1 moment when they did still carry the rule; a later CRS round
# removed all seven.
#
# THIRD ROUND RUNNING. E-1b made this exact repair to test_contrast and
# wrote the rule down doing it: as_left_by is right for a page the round
# TOUCHED and wrong for one it did not, because the round's own backups
# define its scope.
BL_FROZEN_PAGES = 7
BL_LIVE_PAGES = 0


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('HL-1 REFUSED: %s' % msg)


def once(text, lit, where):
    n = text.count(lit)
    if n != 1:
        refuse('%s: %r appears %d time(s), expected exactly 1'
               % (where, lit[:60], n))


def widen(text, name):
    """test_small_three onto alv_tree - the walk, the label, and the way
    back from a label to a file.

    EVERY SHAPE, EVERY TIME. E-1a learned this the slow way, finding
    three narrow joins in three different spellings and each only once
    the one before it was fixed; E-10 found a fourth kind, a relpath
    split across two lines, in this very file. The count is returned so
    the caller can refuse a no-op - which is how a survey that assumed
    every suite calls its root T once reported "passes widened" about a
    file it had not altered.
    """
    n = 0
    if 'import alv_tree' not in text:
        once(text, 'import sys\n', name)
        text = text.replace('import sys\n', 'import sys\n\nimport alv_tree\n',
                            1)
        n += 1

    c = text.count('os.walk(T)')
    if not c:
        refuse('%s does not walk T' % name)
    text = text.replace('os.walk(T)', 'alv_tree.walk3()')
    n += c

    # The relpath, in three spellings: on one line, split across two,
    # and the one that normalises the separator itself -
    # `os.path.relpath(p, T).replace(os.sep, '/')`, which is what
    # alv_tree.rel does and which test_back_label writes six times.
    text, k = re.subn(
        r"os\.path\.relpath\(\s*os\.path\.join\(base_, f\),\s*T\)",
        'alv_tree.rel(os.path.join(base_, f))', text, flags=re.S)
    n += k
    text, k = re.subn(
        r"os\.path\.relpath\((\w+),\s*T\)\.replace\(os\.sep,\s*'/'\)",
        lambda m: 'alv_tree.rel(%s)' % m.group(1), text)
    n += k
    text, k = re.subn(
        r"os\.path\.relpath\(\n(\s*)os\.path\.join\(base_, f\), T\)",
        lambda m: 'alv_tree.rel(\n%sos.path.join(base_, f))' % m.group(1),
        text)
    n += k

    # join(T, 'a', 'b') before join(T, 'x'), or the two-part one is read
    # as a one-part one with a stray argument left behind.
    text, k = re.subn(r"os\.path\.join\(T,\s*'([^']+)',\s*'([^']+)'\)",
                      lambda m: "alv_tree.join('%s/%s')"
                      % (m.group(1), m.group(2)), text)
    n += k
    text, k = re.subn(r"os\.path\.join\(T,\s*'([^']+)'\)",
                      lambda m: "alv_tree.join('%s')" % m.group(1), text)
    n += k
    # AND THE ONE THAT TAKES A VARIABLE. test_back_label line 409 is
    # `p = os.path.join(T, name)`, where name comes off a list of
    # basenames - the same shape as the literal and invisible to a
    # pattern written for quotes. Found by the gate below, not by
    # reading, which is the fourth distinct spelling this programme has
    # had to learn and the reason that gate exists.
    text, k = re.subn(r'os\.path\.join\(T,\s*(\w+)\)',
                      lambda m: 'alv_tree.join(%s)' % m.group(1), text)
    n += k

    if 'os.walk(T)' in text:
        refuse('%s still walks its own root after widening' % name)
    if re.search(r'os\.path\.join\(\s*T\s*,', text):
        refuse('%s still resolves a label against its own root - '
               'test_waiting_down counts these' % name)
    if re.search(r'os\.path\.relpath\([^)]*,\s*T\)', text, re.S):
        refuse('%s still takes a label back against its own root' % name)
    return text, n


BL_READER_OLD = """def now(p):
    \"\"\"The file as THIS round left it. See alv_rounds.py.\"\"\"
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)"""

# GT-1's pre-flight, as PowerShell. Written as a list of lines because
# it is full of quotes and backslashes and a single literal holding both
# is how the first draft of this patcher stopped parsing.
GT_PREFLIGHT = '\n'.join([
    '',
    '# GT-1, 12 Oct 2026 - THE SAME REFUSAL, ASKED EARLY.',
    '#',
    "# The real check is beside `Head 'Commit'` at the bottom of this",
    '# file and is unchanged; it is what actually guards the commit.',
    '# This is a pre-flight with the same words, because the bottom of',
    '# this file is 330 suites, two drift guards, makemigrations and a',
    '# Django check away from the top. E-10 paid all of that and was',
    '# then refused for want of a one-line subject.',
    '#',
    '# A dry run is not blocked: it has no subject to want.',
    'if ($Apply -and -not $Message) {',
    "    Write-Host ''",
    "    Write-Host '  ! No commit subject, and this run would commit.'",
    "    Write-Host ''",
    "    Write-Host '    There is no default on purpose - a default "
    "describes the'",
    "    Write-Host '    previous change, not this one. Pass one:'",
    "    Write-Host ''",
    "    Write-Host '       .\\Push-PendingChanges.ps1 -Push -Message "
    "<what changed>'",
    "    Write-Host ''",
    "    Write-Host '    Asked here rather than after the suites, which is "
    "where'",
    "    Write-Host '    it used to be asked. See GT-1.'",
    "    Write-Host ''",
    '    exit 1',
    '}',
    ''])

# Built by concatenation rather than written as one literal: the text
# being inserted is itself a docstring, and a docstring inside a
# docstring is how the first draft of this patcher stopped parsing.
_Q = '"' * 3
BL_READER_NEW = (
    'def now(p):\n'
    '    ' + _Q + 'The file as THIS round left it - FOR A PAGE IT '
    'TOUCHED.\n'
    '\n'
    '    BL-2, 12 Oct 2026. as_left_by answers "the file as this round\n'
    '    left it", and for a page this round never opened that is the\n'
    '    backup taken by the first LATER round that happened to open\n'
    '    it - an arbitrary moment belonging to somebody else. Widened,\n'
    '    this suite read seven CRS pages at a pre-PQ-1 moment and\n'
    '    reported that each still carried an unscoped\n'
    '    .action-back-label rule. Live, not one page in either root\n'
    '    carries one.\n'
    '\n'
    "    THE ROUND'S OWN BACKUPS DEFINE ITS SCOPE. Where there is no\n"
    '    backup there is no claim, and the live file is what every\n'
    '    check below means.\n'
    '\n'
    '    Third time: E-1b made the identical repair to test_contrast\n'
    '    and wrote the rule down while doing it.\n'
    '    ' + _Q + '\n'
    '    if not os.path.isfile(p):\n'
    "        return ''\n"
    '    if not os.path.isfile(p + SUFFIX):\n'
    '        return read(p)\n'
    '    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)')

BL_PIN1_OLD = """        ok(before_on == [FIXED],
           'CONTROL: before this round exactly ONE page showed the word on '
           'a phone, and it is %s - the fault this round found' % FIXED,
           before_on)"""

BL_PIN1_NEW = """        # BL-2, 12 Oct 2026 - WAS `before_on == [FIXED]`. Across both
        # roots FIVE pages showed the word before: import_recipe,
        # lease_timeline, map_ingredients_nutrition, unit_conversions_
        # wizard and this one. The other four are real beneficiaries
        # BL-1 never counted - their Back sits outside a
        # .page-action-buttons bar, so old base's three-ancestors-deep
        # rule never reached them and scoping it to .action-back fixed
        # them silently. What BL-1 can claim forever is that THIS page
        # showed the word and does not now, and the check below measures
        # exactly that, on the page itself.
        ok(FIXED in before_on,
           'CONTROL: before this round %d page(s) showed the word on a '
           'phone, and %s is among them - the fault this round found'
           % (len(before_on), FIXED), before_on)"""

BL_PIN2_OLD = """        ok(land_before == [FIXED],
           'CONTROL: and sideways too, %s was the ONLY page showing it '
           'before' % FIXED, land_before)"""

BL_PIN2_NEW = """        ok(FIXED in land_before,
           'CONTROL: and sideways too, %s was among the %d showing it '
           'before' % (FIXED, len(land_before)), land_before)"""


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    sys.path.insert(0, root)
    import alv_tree as T

    page_p = T.path_of(PAGE)

    # ---------------------------------------------------------------- 0
    # A PATCHER VERIFIES, THEN WRITES, and the already-applied check runs
    # first - before any census that would be false on a tree this round
    # has finished with.
    if SPAN not in read(page_p):
        print('HL-1  already applied')
        return 0

    if not os.path.isfile(os.path.join(root, SUITE)):
        refuse('%s is not on disk - the suite ships with the round' % SUITE)

    # ---------------------------------------------------------------- 1
    # THE CENSUS THE ROUND RESTS ON, asked of the tree rather than taken
    # from the header.
    labels = notback = 0
    for p in T.templates():
        src = T.code_only(read(p))
        for m in re.finditer(r'<span class="action-back-label"[^>]*>'
                             r'(.*?)</span>', src, re.S):
            labels += 1
            txt = ' '.join(re.sub(r'\{%.*?%\}', '', m.group(1),
                                  flags=re.S).split())
            if 'back' not in txt.lower() and 'cancel' not in txt.lower():
                notback += 1
    if labels != LABELS_TOTAL or notback != LABELS_NOT_BACK:
        refuse('the back-label census is %d label(s) and %d not saying Back; '
               'this round was built on %d and %d'
               % (labels, notback, LABELS_TOTAL, LABELS_NOT_BACK))

    helps = bare = 0
    for p in T.templates():
        for m in re.finditer(r'<button[^>]*data-target="#\w*HelpModal"'
                             r'[^>]*>(.*?)</button>', read(p), re.S):
            if 'action-more-item' in m.group(0):
                continue
            helps += 1
            if 'action-back-label' not in m.group(1):
                bare += 1
    if (helps, bare) != (HELP_TOTAL, HELP_BARE_BEFORE):
        refuse('the Help census is %d control(s), %d of them bare; this '
               'round was built on %d and %d'
               % (helps, bare, HELP_TOTAL, HELP_BARE_BEFORE))

    # AND THE PRECEDENT MUST STILL BE THERE. This round copies a shape
    # rather than inventing one, so if D-2's page has moved, the shape
    # being copied is not the house shape any more.
    prec = read(T.path_of(PRECEDENT))
    if BARE not in prec:
        refuse('%s does not carry the bare shape this round copies - D-2 '
               'has been undone or rewritten' % PRECEDENT)
    if 'action-back-label' not in prec:
        refuse('%s has no back label at all, so it cannot be the control '
               'that the class is still used correctly' % PRECEDENT)

    # ---------------------------------------------------------------- 2
    page = read(page_p)
    once(page, SPAN, PAGE)
    npage = page.replace(SPAN, BARE, 1)
    if 'action-back-label' not in npage:
        refuse('%s: removing the Help span took the Back label with it'
               % PAGE)
    if npage.count('action-back-label') != page.count('action-back-label') - 1:
        refuse('%s: the label count did not fall by exactly one' % PAGE)

    # ---------------------------------------------------------------- 3
    st3 = read(os.path.join(root, ST3))
    nst3, n = widen(st3, ST3)
    # A NO-OP IS NOT A CONVERSION.
    if n < 10:
        refuse('%s: widening changed %d thing(s) - this file carried '
               'sixteen when it was surveyed' % (ST3, n))

    # ---------------------------------------------------------------- 3b
    # BL-2. THE READER, WHICH IS THE WHOLE OF IT.
    #
    # Before touching the file, PROVE the premise against the tree: no
    # page carries the unscoped rule live, and seven do through
    # as_left_by. If either number has moved, the thing this round says
    # is the matter is not the matter any more.
    def unscoped(text):
        """A rule whose WHOLE selector is .action-back-label.

        NOT a substring and NOT a lookbehind. The first control written
        for this used `(?<![-\\w\\s])\\.action-back-label\\s*\\{` and
        could not fire at all - the lookbehind excludes a space, so an
        indented rule never matched - while dropping the \\s matched
        base's own SCOPED `.action-back .action-back-label`. Neither
        reads a selector; both read characters near one. This splits the
        selector list on commas and compares a whole token, which is the
        shape D7 removed 77 times.
        """
        hits = []
        for mm in re.finditer(r'(?m)^[ \t]*([^\n{}]+?)\s*\{([^{}]*)\}',
                              text):
            for sel in mm.group(1).split(','):
                if sel.strip() == '.action-back-label':
                    hits.append(' '.join(mm.group(2).split())[:40])
        return hits

    def page_css(text):
        return '\n'.join(
            re.sub(r'/\*.*?\*/', '', text[a:b], flags=re.S)
            for a, b in __import__('alv_cssrules').style_spans(text))

    import alv_rounds as R
    live_hits, frozen_hits = [], []
    for q in T.templates():
        rel = T.rel(q)
        if rel == 'base.html':
            continue
        if unscoped(page_css(read(q).replace('\r\n', '\n'))):
            live_hits.append(rel)
        froz = R.as_left_by(q, '.bak_backlabel',
                            lambda x: read(x).replace('\r\n', '\n'))
        if unscoped(page_css(froz)):
            frozen_hits.append(rel)
    if len(live_hits) != BL_LIVE_PAGES:
        refuse('%d page(s) carry an unscoped .action-back-label rule LIVE, '
               'and this round was built on %d: %s'
               % (len(live_hits), BL_LIVE_PAGES, live_hits[:4]))
    if len(frozen_hits) != BL_FROZEN_PAGES:
        refuse('as_left_by reports %d page(s) carrying it, and this round '
               'was built on %d: %s'
               % (len(frozen_hits), BL_FROZEN_PAGES, frozen_hits[:4]))
    if not all(r.startswith('crs/') for r in frozen_hits):
        refuse('the frozen pages are not all CRS, so the reader is not the '
               'whole story: %s' % frozen_hits)

    bl = read(os.path.join(root, BL))
    nbl, k = widen(bl, BL)
    if k < 6:
        refuse('%s: widening changed %d thing(s) - this file carried ten '
               'when it was surveyed' % (BL, k))
    for old, new, what in ((BL_READER_OLD, BL_READER_NEW, 'reader'),
                           (BL_PIN1_OLD, BL_PIN1_NEW, 'portrait pin'),
                           (BL_PIN2_OLD, BL_PIN2_NEW, 'landscape pin')):
        once(nbl, old, '%s (%s)' % (BL, what))
        nbl = nbl.replace(old, new, 1)
    if 'FOR A PAGE IT TOUCHED' not in nbl:
        refuse('%s: the scoped reader did not land' % BL)

    # ---------------------------------------------------------------- 3c
    # TN-1. THE LIVE BUG.
    tn_p = os.path.join(root, TENANTS.replace('/', os.sep))
    tn = read(tn_p)
    once(tn, TN_OLD, TENANTS)
    ntn = tn.replace(TN_OLD, TN_NEW, 1)
    if 'tenant_lease_agreement_status = None' in ntn:
        refuse('%s still assigns None to a NOT NULL column' % TENANTS)
    # AND THE COLUMN REALLY IS NOT NULL, asked of the migration rather
    # than of the error message. If 0095 ever relaxes it again, this
    # round is fixing something that is no longer broken.
    mig = os.path.join(root, 'pages', 'migrations', '0095_none_columns.py')
    if not os.path.isfile(mig):
        refuse('0095_none_columns.py is not on disk, so the claim that the '
               'column is NOT NULL cannot be checked')
    mg = read(mig)
    if "('tenant', 'tenant_lease_agreement_status')" not in mg:
        refuse('0095_none_columns does not list tenant_lease_agreement_'
               'status, so this is not the fault this round describes')

    # ---------------------------------------------------------------- 4
    # THE REGISTERS.
    tree = read(os.path.join(root, TREE))
    for name in RELEASED:
        line = [l for l in tree.split('\n')
                if l.strip().startswith("'%s':" % name)]
        if len(line) != 1:
            refuse('%s is not on alv_tree.WAITING exactly once' % name)
        start = tree.index(line[0])
        end = tree.index("',\n", start) + 3
        tree = tree[:start] + tree[end:]

    conv = "    'test_drift_root.py',\n]"
    once(tree, conv, TREE)
    ntree = tree.replace(
        conv,
        "    'test_drift_root.py',\n"
        "    # HL-1, 12 Oct 2026 - its one failure was a Help button on a\n"
        "    # page in the second root, wearing the Back label class. D-2\n"
        "    # fixed the identical span on workspace_management in\n"
        "    # September and could not see this one.\n"
        "    'test_small_three.py',\n"
        "    # BL-2, same round - and not one application file changed for\n"
        "    # it. All five of its failures were its reader: it asked\n"
        "    # as_left_by for pages BL-1 never touched and got whichever\n"
        "    # later round had opened them. Live, no page in either root\n"
        "    # carries the rule it reported on seven.\n"
        "    'test_back_label.py',\n"
        "    # HL-1 - and this round's own suite.\n"
        "    'test_help_label.py',\n]", 1)

    rounds = read(os.path.join(root, ROUNDS))
    r_anchor = "    '.bak_driftroot',\n"
    once(rounds, r_anchor, ROUNDS)
    nrounds = rounds.replace(r_anchor, r_anchor + "    '%s',\n" % SUFFIX, 1)

    ps = read(os.path.join(root, PS1))

    # GT-1. THE SUBJECT IS ASKED FOR AT THE TOP, NOT AFTER 37 MINUTES.
    #
    # `if (-not $Message)` sits beside `Head 'Commit'`, the very last
    # thing this script does. On 12 Oct that let E-10 run all 330
    # suites, two drift guards, makemigrations and the Django check -
    # and then refuse for want of a one-line subject the script could
    # have asked for before the first suite started.
    #
    # THE REAL CHECK STAYS EXACTLY WHERE IT IS. It is what actually
    # guards the commit, and a round that moves a control rather than
    # putting one in front of it has removed a control. What goes in at
    # the top is a pre-flight with the same words, so forgetting costs
    # three seconds instead of three quarters of an hour.
    #
    # Only when something will be committed. A dry run has no subject to
    # want, and blocking one would be a new rule rather than an earlier
    # one.
    gt_anchor = 'if ($Push) { $Apply = $true }\n'
    once(ps, gt_anchor, PS1)
    ps = ps.replace(gt_anchor, gt_anchor + GT_PREFLIGHT, 1)
    if ps.count("Bad 'No commit subject.'") != 1:
        refuse('%s: the real subject check is not there exactly once - '
               'GT-1 adds a pre-flight, it does not move the guard' % PS1)

    p_anchor = "    'test_drift_root.py'\n)"
    once(ps, p_anchor, PS1)
    nps = ps.replace(
        p_anchor, "    'test_drift_root.py',\n    '%s'\n)" % SUITE, 1)

    # A SENTINEL. The last row of a PowerShell array literal carries no
    # comma - E-10 shipped one that did and the gate would not parse, so
    # the structure is read back below rather than assumed.
    s_anchor = (
        "    # NO SENTINEL ON 'border-radius: 6px'. One was written and")
    once(nps, s_anchor, PS1)
    nps = nps.replace(
        s_anchor,
        "    # -------------------------------------------- HL-1, 12 Oct 2026\n"
        "    # A Help button is not a Back button. Base hides the back\n"
        "    # label below 768px, and 77 pages once carried their own\n"
        "    # unscoped copy of that rule; the day one comes back here,\n"
        "    # the word Help becomes a bare question mark.\n"
        "    @{ File = 'crs\\templates\\crs\\submission_detail.html'; "
        "Text = '<span class=\"action-back-label\"> Help</span>'; "
        "What = 'the CRS Help button writes bare text, like the other 39'; "
        "Absent = $true; Code = $true }\n"
        + s_anchor, 1)

    blk = nps[nps.index('$sentinels = @('):]
    blk = blk[:blk.index('\n)\n')]
    body = [l.rstrip() for l in blk.split('\n')
            if l.strip() and not l.strip().startswith('#')]
    if body[-1].endswith(','):
        refuse('%s: the last thing in $sentinels ends in a comma - %r. That '
               'is a ParserError before the closing paren, and the script '
               'will not run AT ALL.' % (PS1, body[-1][-40:]))

    # A ROUND THAT CONVERTS A CENSUS OWNS EVERY NUMBER THAT COUNTS IT.
    x0 = read(os.path.join(root, X0))
    old_c = 'WALKERS_OWN_ROOT_MAX = %d' % CEILING_WAS
    once(x0, old_c, X0)
    nx0 = x0.replace(
        old_c,
        'WALKERS_OWN_ROOT_MAX = %d   # HL-1, 12 Oct 2026 - one more\n'
        '# census converted, and it may only FALL.   # (was %d)'
        % (CEILING_NOW, CEILING_WAS), 1)

    wd = read(os.path.join(root, WD))
    for was, now, why in (
            ('CONVERTED_N = %d' % CONVERTED_WAS,
             'CONVERTED_N = %d   # HL-1, 12 Oct 2026 - one released plus '
             'this round own suite   # (was %d)'
             % (CONVERTED_NOW, CONVERTED_WAS), 'CONVERTED_N'),
            ('WAITING_N = %d' % WAITING_WAS,
             'WAITING_N = %d   # HL-1, 12 Oct 2026 - one off   # (was %d)'
             % (WAITING_NOW, WAITING_WAS), 'WAITING_N'),
            ('CEILING = %d' % CEILING_WAS,
             'CEILING = %d   # HL-1, 12 Oct 2026 - one more census   '
             '# (was %d)' % (CEILING_NOW, CEILING_WAS), 'CEILING')):
        once(wd, was, WD)
        wd = wd.replace(was, now, 1)
    nwd = wd

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('')
        print('HL-1  check only - nothing written')
        print('HL-1  would take the Back label class off the one Help')
        print('HL-1  button in %d that still wears it, on %s' % (HELP_TOTAL,
                                                                 PAGE))
        print('HL-1  %d element(s) wear that class across both roots; %d of'
              % (LABELS_TOTAL, LABELS_TOTAL - LABELS_NOT_BACK))
        print('HL-1  them say Back, and after this round all of them do')
        print('HL-1  would widen and release %s' % ', '.join(RELEASED))
        print('HL-1  WAITING %d -> %d, CONVERTED %d -> %d, ceiling %d -> %d'
              % (WAITING_WAS, WAITING_NOW, CONVERTED_WAS, CONVERTED_NOW,
                 CEILING_WAS, CEILING_NOW))
        return 0

    for p, txt in [(page_p, npage),
                   (tn_p, ntn),
                   (os.path.join(root, ST3), nst3),
                   (os.path.join(root, BL), nbl),
                   (os.path.join(root, TREE), ntree),
                   (os.path.join(root, ROUNDS), nrounds),
                   (os.path.join(root, WD), nwd),
                   (os.path.join(root, X0), nx0),
                   (os.path.join(root, PS1), nps)]:
        backup(p)
        write(p, txt)

    print('')
    print('HL-1  the CRS Help button writes bare text now, the same shape')
    print('HL-1  D-2 gave %s in September.' % PRECEDENT)
    print('HL-1  %d element(s) wear .action-back-label across both roots'
          % (LABELS_TOTAL - LABELS_NOT_BACK))
    print('HL-1  now - one fewer than before - and every one says Back.')
    print('HL-1  NOTHING ON SCREEN MOVES. Base hides that class only')
    print('HL-1  inside a back button, so the word Help rendered then and')
    print('HL-1  renders now. What goes is the trap: 77 pages once carried')
    print('HL-1  an unscoped copy of the hide rule, and the day one comes')
    print('HL-1  back here the word becomes a bare question mark.')
    print('HL-1  %s widened and released.' % ', '.join(RELEASED))
    print('HL-1  WAITING %d -> %d, CONVERTED %d -> %d, ceiling %d -> %d'
          % (WAITING_WAS, WAITING_NOW, CONVERTED_WAS, CONVERTED_NOW,
             CEILING_WAS, CEILING_NOW))
    print('HL-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
