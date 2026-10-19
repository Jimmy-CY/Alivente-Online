# -*- coding: utf-8 -*-
"""apply_retired.py - round RT-1, 18 Oct 2026.

WHAT THE TREE DOES WITH A PAGE IT USED TO HAVE.

Demetri, 18 Oct, asked for a recommendation and took it: a register in
the toolchain rather than fifty-seven numbers filed down.

WHAT RAISED IT
--------------
MN-1 deleted four templates - meal_plans.html, meal_plan_calendar.html,
create_meal_plan.html and view_meal_plan.html - because the planner
replaced all four screens. test_planner.py was green at 156 checks and
the sweep of the tree came back EIGHTY RED OUT OF 370.

Not one of the eighty was a fault in the planner. Measured, not guessed:

    17   crashed in alv_tree.path_of() before their first check
    20   failed one shared check - sixteen rows of the $sentinels table
         point at the four pages
    53   reported a pinned number one short
     4   browser suites that only exceeded the probe's 90-second cap

(The three groups overlap; 80 distinct suites.)

THE FINDING UNDERNEATH THEM
---------------------------
A census that asks "how many pages carry MY backup?" is asking a
question about the PAST, and every one of them has been answering it by
reading today's disk. That worked for 290 rounds for exactly one
reason: nothing had ever been deleted.

    A census of what a round did is a claim about the past. Reading
    it off today's disk is correct only while the past is still on
    the disk.

So this round does three things and refuses to do a fourth.

WHAT IT DOES
------------
1. THE REGISTER. alv_tree.RETIRED names each page the tree used to have
   and the round that took it, and two accessors read around the hole:

       last_path(label)        the live file, or the retiring round's
                               backup - for a HISTORICAL claim
       bak_of(label, suffix)   <label><suffix>, whether the page is
                               live or gone

   path_of() keeps refusing - a page that must be there and is not
   should still stop the run - but its refusal now NAMES the round that
   retired the page instead of reading like a typo.

   ON WHY THE ACCESSORS ARE EXPLICIT AT THE CALL SITE. A silent
   fallback inside path_of() was written and measured first. It cleared
   the 17 crashes and broke test_label_weight.py, which composes
   path_of(label) + SUFFIX and so went looking for

       create_meal_plan.html.bak_planner.bak_lblwt

   Historical and present-tense reads are different questions, and the
   call site is the only place that knows which one is being asked.

   ON WHAT WAS ALREADY THERE. alv_rounds.as_left_by(path, suffix, read)
   has answered "the text of this page as round X left it" since the
   register was built, by walking ROUNDS forward to the next round's
   backup - and for a retired page it is ALREADY correct, because MN-1
   backed all four pages up rather than merely unlinking them. Every
   suite that reads through it was never at risk. The breakage is in
   PATH RESOLUTION, which is why this round adds paths and not a reader.

2. THE SIXTEEN DEAD SENTINELS. Rows of $sentinels in
   Push-PendingChanges.ps1 that guard the contents of the four deleted
   pages. A sentinel on a retired page is the push script asserting the
   shape of a file nothing serves - which is the failure -Message and
   -Checks were built to prevent, in the one place that cannot say so.

3. THE FIFTY-SEVEN CLAIMS, each judged on what it actually asserts:

       HISTORICAL   "this round cut 250 literals on 43 pages" - reads
                    through last_path/bak_of, and the NUMBER DOES NOT
                    MOVE, because the round really did that.

       PRESENT      "not one page in the tree still carries this" - the
                    count falls, because the tree genuinely is smaller,
                    and the note says which round took the page.

4. THE SELECTOR, WIDENED. alv_impact.select() under-reports a deletion.
   It names a suite that mentions a changed file, but
   test_recipe_side_b.py never writes 'create_meal_plan.html' anywhere -
   it learns the name from apply_recipe_side_b.py's payload at run time.
   So select() reads each suite's patcher too. Found the hard way: the
   selector said that suite was not at risk, and Demetri's gate would
   have found it.

WHAT IT REFUSES TO DO
---------------------
It does not lower a single historical number. Filing 31 class lists on
13 pages down to 30 on 12 would make test_recipe_side_b.py assert, for
ever, something that never happened.

Idempotent. Every file backed up to .bak_retired. Python is compiled
and PowerShell is brace-balanced before anything is written.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_retired'
TREE = 'alv_tree.py'
IMPACT = 'alv_impact.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
ME = 'test_retired.py'
PATCHER = 'apply_retired.py'
MARK = 'RT-1, 18 Oct 2026'
CHECK = False

# The four pages, as MN-1 left them: deleted, each with a .bak_planner
# beside the hole. This round does not delete anything.
GONE = ('meal_plans.html', 'meal_plan_calendar.html',
        'create_meal_plan.html', 'view_meal_plan.html')

# ========================================================== THE REGISTER
# Spliced in before roots(), because it is the same kind of fact as
# TEMPLATE_ROOTS above it: the shape of the tree, in one place.
REG_AT = """def roots(base=None):"""

REG = '''# THE PAGES THE TREE USED TO HAVE, AND THE ROUND THAT TOOK EACH ONE.
#
# WHY THIS EXISTS, WHICH IS THE SAME SHAPE OF FAILURE AS THE ROOTS ABOVE.
#
#     MN-1 deleted four templates on 18 Oct 2026 - the planner replaced
#     all four screens. Its own suite was green at 156 checks and the
#     sweep of the tree came back EIGHTY RED OUT OF 370. Not one of the
#     eighty was a fault in the planner. They were historical rounds
#     whose censuses still counted a page the tree no longer has:
#     seventeen crashed in path_of() before their first check, and
#     fifty-three reported a number one short.
#
#     The finding underneath them is worth writing down. A census that
#     asks "how many pages carry MY backup?" is asking a question about
#     the PAST, and every one of them has been answering it by reading
#     today's disk. That worked for 290 rounds for exactly one reason:
#     nothing had ever been deleted.
#
#         A census of what a round did is a claim about the past.
#         Reading it off today's disk is correct only while the
#         past is still on the disk.
#
#     So a retired page keeps its last text beside the hole it left -
#     the retiring round BACKS IT UP rather than merely unlinking it,
#     exactly as apply_remove_legacy_reports.py did with four root
#     modules on 25 Aug - and this register says where that text is and
#     which round took the page.
#
# WHAT THIS IS NOT. It is not a list of pages that may be missing. A
# label that is neither live nor in here is simply wrong, and both
# path_of() and last_path() still stop the run on one. The register
# changes WHAT THE REFUSAL SAYS, not whether there is one.
#
# Each entry is (the retiring round's backup suffix, which round and why).
RETIRED = {
    'meal_plans.html': (
        '.bak_planner',
        'MN-1, 18 Oct 2026 - the planner is the list'),
    'meal_plan_calendar.html': (
        '.bak_planner',
        'MN-1, 18 Oct 2026 - the planner IS the calendar'),
    'create_meal_plan.html': (
        '.bak_planner',
        'MN-1, 18 Oct 2026 - a plan is built on the calendar now'),
    'view_meal_plan.html': (
        '.bak_planner',
        'MN-1, 18 Oct 2026 - a week of the planner is the plan page'),
}


def retired(label):
    """(suffix, which round and why) for a page the tree used to have,
    or None.

    Keyed on the label first and the basename second, for the same
    reason the rest of this file keys on basenames: 146 templates
    across both roots and ZERO collisions, asserted in
    test_tree_roots.py so that the day it stops holding the programme
    is told rather than a dict silently merging two pages.
    """
    key = label.replace('\\\\', '/')
    return RETIRED.get(key) or RETIRED.get(os.path.basename(key))


def last_path(label, base=None):
    """The path of a page's LAST TEXT - the live file if it is there,
    the retiring round's backup if it is not.

    THIS IS WHAT A HISTORICAL CLAIM WANTS, AND WHAT path_of() CANNOT
    GIVE IT.

        "RS-1b changed 31 class lists on 13 pages."

    That is true. It was true the day RS-1b landed and it is true now.
    One of those 13 pages was create_meal_plan.html, which MN-1
    retired, so a census resolving the label against today's disk
    either crashes or answers 30 on 12 - a number describing a round
    that never happened.

    USE path_of() INSTEAD when the claim is about the tree TODAY. "Not
    one page still carries this literal" is present tense, and a
    retired page is no part of it. Such a census walks the tree and
    never names a page at all, so it gets the right answer by
    construction.

    NOT TO BE CONFUSED WITH alv_rounds.as_left_by(), which answers a
    narrower and older question - the TEXT of a page as one NAMED round
    left it, by walking ROUNDS forward to the next round's backup. That
    helper is already correct for a retired page, because the retiring
    round backed the page up. This one is about PATH RESOLUTION, which
    is where the eighty failures actually were.

    Raises when the label is neither live nor retired. Then the label
    is simply wrong, and that should stop the run exactly as path_of()
    does.
    """
    rel_ = label.replace('/', os.sep)
    rs = roots(base)
    for r in rs:
        p = os.path.join(r, rel_)
        if os.path.isfile(p):
            return p
    ret = retired(label)
    if ret:
        for r in rs:
            p = os.path.join(r, rel_) + ret[0]
            if os.path.isfile(p):
                return p
        raise IOError('alv_tree.last_path: %r was retired by %s, but its '
                      'backup %s is not beside it. A round that retires '
                      'a page must back it up, not merely unlink it.'
                      % (label, ret[1], ret[0]))
    raise IOError('alv_tree.last_path: no template named %r under %s, and '
                  'it is not in RETIRED either'
                  % (label, [os.path.basename(r) for r in rs]))


def touched_by(suffix, base=None):
    """Every page a round touched, found by ITS BACKUPS ON DISK.

    THE SAME RULE THE PRE-FLIGHT ALREADY LIVES BY. Demetri's standing
    instruction for a delivery is that the file list is enumerated from
    the .bak_<suffix> files on disk and never typed, because a typed
    list is a claim about the round rather than a reading of it. A
    round's own census is the same question asked later, and twenty of
    them were asking it the other way round:

        TOUCHED = [p for p in alv_tree.templates()
                   if os.path.exists(p + SUFFIX)]

    That enumerates the pages THAT ARE THERE NOW and keeps the ones
    with a backup. Retire a page and it is not in the walk, so it is
    not in the census, and the round's count comes back one short -
    four of the colour rounds reported exactly that on 18 Oct. The
    backup is still on the disk; nothing but the walk had forgotten
    the page.

    IT ANSWERS WITH THE PAGE'S OWN PATH, not with the retired page's
    last text, and that choice is what makes it a one-line change at
    every call site. A census built this way reads two texts:

        was(p)  ->  read(p + SUFFIX)        the round's own backup,
                    which is beside the page's own path whether the
                    page is still there or not
        now(p)  ->  as_left_by(p, SUFFIX)   which RT-1 taught to read
                    a retired page's last text at the end of its walk

    So both readers already work from the page's own path, and neither
    needed touching. Answer with the last text instead and every
    `read(p + SUFFIX)` in twenty suites would have had to move.
    """
    out = []
    for folder, names in walk(base):
        for n in names:
            if n.endswith(suffix) and not n.endswith(suffix + suffix):
                out.append(os.path.join(folder, n[:-len(suffix)]))
    return sorted(set(out))


def last_join(*parts, **kw):
    """join(), except that a retired page resolves to its last text.

    THE FORGIVING TWIN OF last_path(), FOR THE SUITES BUILT ON join().
    Those suites all do the same thing:

        p = alv_tree.join(rel)
        if not os.path.isfile(p):
            skip(rel, 'not on disk')
            continue

    which is a reasonable guard and the right one for a page that was
    never there. For a RETIRED page it is the wrong answer twice over:
    the page was there, this round did edit it, and the census quietly
    skips it and reports a total two literals short of what the round
    actually did. test_accent_ink.py said "the round was 120 literals
    in all" and answered 118.

    So this resolves a retired label to the text beside the hole, and
    anything else exactly as join() does - a path under the first root,
    so isfile() still answers False for a label that is simply wrong
    and the guard above still works.
    """
    p = join(*parts, **kw)
    return p if os.path.isfile(p) else last_of(p)



def retired_labels(base=None):
    """The labels in RETIRED that really are gone from the tree.

    FOR A CENSUS WHOSE SUBJECT IS THE TREE AS A ROUND FOUND IT. Several
    suites take their page list from a live walk - their own, or
    Show-ButtonDrift's templates() - and then ask a question about what
    some earlier round saw. The walk is right for a question about
    today and one page short for a question about then, so those
    censuses add this.

    It checks the disk rather than trusting the register, so that a
    page put BACK into the tree stops being counted twice the moment
    it returns.
    """
    out = []
    for label in sorted(RETIRED):
        rel_ = label.replace('/', os.sep)
        if not any(os.path.isfile(os.path.join(r, rel_))
                   for r in roots(base)):
            out.append(label)
    return out


def nominal(path):
    """A page's OWN path, with any retirement suffix taken off.

    last_path() answers with a retired page's backup, and that answer
    then travels - into was(), into alv_rounds.as_left_by(), into any
    code that composes a further suffix onto it. All of those want the
    page's own path, because what they build from it is

        <page>.bak_<some round>

    and never <page>.bak_planner.bak_<some round>, which has never
    existed. One function, so the stripping is spelt once and only
    ever removes a suffix this register put there.
    """
    for suf, _why in RETIRED.values():
        if path.endswith(suf):
            return path[:-len(suf)]
    return path


def last_of(path):
    """The path of a page's last text, given the page's OWN path.

    THE PATH-SIDE TWIN OF last_path(). last_path() takes a label and is
    what a suite calls at the top; this takes a path and is what the
    shared readers call at the bottom, where a label is long gone.
    """
    path = nominal(path)
    if os.path.isfile(path):
        return path
    ret = retired(os.path.basename(path))
    if ret and os.path.isfile(path + ret[0]):
        return path + ret[0]
    return path


def bak_path(path, suffix):
    """One round's backup of the page whose LAST TEXT is at `path`.

    THE PATH-SIDE OF bak_of(), FOR THE DOZENS OF SUITES THAT RESOLVE A
    LABEL ONCE AND THEN WORK IN PATHS. Almost every suite in this
    programme is built the same way:

        def now(p): return as_left_by(p, SUFFIX, read)
        def was(p): return read(p + SUFFIX)

    and both take a path the suite resolved at the top. Point that path
    at a retired page's last text and now() is right - as_left_by()
    finds no later backup and reads the file, which IS the page as the
    last round left it - while was() goes looking for

        create_meal_plan.html.bak_planner.bak_btntone

    So the backup of a retired page is found by dropping the
    RETIREMENT suffix and appending the round's own.
    """
    return nominal(path) + suffix


def bak_of(label, suffix, base=None):
    """The path of <label><suffix> - one round's backup of a page -
    whether that page is still live or has since been retired.

    WHY THIS IS NOT path_of(label) + suffix. That composition is
    written in dozens of suites and it is correct only while the page
    is live. Measured on test_label_weight.py, 18 Oct 2026: with
    create_meal_plan.html retired, a historical read answers

        pages/templates/create_meal_plan.html.bak_planner

    and the composition then goes looking for

        pages/templates/create_meal_plan.html.bak_planner.bak_lblwt

    a file that has never existed anywhere. The suite did not even
    crash on it - it reported that the page "has no .bak_lblwt backup",
    which is a sentence about a real round that was simply false.

    A retired page's backups stay exactly where they were, beside the
    hole the page left, so this resolves the NOMINAL path and appends
    the suffix.

    FORGIVING, like join() and unlike path_of(), because almost every
    caller asks os.path.isfile() about the answer. That is a QUESTION,
    and a question deserves False rather than a traceback.
    """
    rel_ = label.replace('/', os.sep)
    rs = roots(base)
    for r in rs:
        p = os.path.join(r, rel_) + suffix
        if os.path.isfile(p):
            return p
    return os.path.join(rs[0], rel_) + suffix


'''

# path_of's refusal, widened to name the round rather than the roots.
POF_WAS = """    raise IOError('alv_tree.path_of: no template named %r under %s'
                  % (label, [os.path.basename(r) for r in roots(base)]))


def join(*parts, **kw):"""

POF_NOW = """    ret = retired(label)
    if ret:
        raise IOError(
            'alv_tree.path_of: %r was retired by %s and is not in the '
            'tree any more. A claim about what a round DID to that page '
            'reads alv_tree.last_path(); a claim about the tree TODAY '
            'should not name it at all.' % (label, ret[1]))
    raise IOError('alv_tree.path_of: no template named %r under %s'
                  % (label, [os.path.basename(r) for r in roots(base)]))


def join(*parts, **kw):"""

# ========================================================== THE SELECTOR
IMP_WAS = """def select(changed):
    \"\"\"(picked, named, why) for the files this round changed.

    A suite is picked if it names one of the changed files - by full
    relative path or by basename - or if it is one of the nine that
    count the whole repo.
    \"\"\"
    keys = set()
    for c in changed:
        c = c.replace('\\\\', '/')
        keys.add(c)
        keys.add(os.path.basename(c))
    named = set()
    for s in suites():
        with open(os.path.join(ROOT, s), encoding='utf-8',
                  errors='replace') as fh:
            text = fh.read()
        if any(k in text for k in keys):
            named.add(s)"""

IMP_NOW = """def patcher_of(suite):
    \"\"\"apply_X.py beside test_X.py, or None.

    RT-1, 18 Oct 2026 - see select().
    \"\"\"
    p = os.path.join(ROOT, 'apply_' + suite[len('test_'):])
    return p if os.path.isfile(p) else None


def select(changed):
    \"\"\"(picked, named, why) for the files this round changed.

    A suite is picked if it names one of the changed files - by full
    relative path or by basename - or if it is one of the nine that
    count the whole repo.

    IT READS EACH SUITE'S PATCHER TOO, AND USED NOT TO. RT-1, 18 Oct
    2026: MN-1 deleted create_meal_plan.html, and this selector said
    test_recipe_side_b.py was not at risk. It was - RS-1b edited that
    page 31 times - but the suite never WRITES the name anywhere. It
    reads apply_recipe_side_b.EDITS at run time and learns the name
    from the payload. Four suites were invisible this way and Demetri's
    gate would have been the one to find them.

    A suite and its patcher are one instrument. The selector now reads
    both halves. Measured on this round's own change set: it costs a
    handful of extra suites, which is the price of not missing four.
    \"\"\"
    keys = set()
    for c in changed:
        c = c.replace('\\\\', '/')
        keys.add(c)
        keys.add(os.path.basename(c))
    named = set()
    for s in suites():
        with open(os.path.join(ROOT, s), encoding='utf-8',
                  errors='replace') as fh:
            text = fh.read()
        ap = patcher_of(s)
        if ap:
            with open(ap, encoding='utf-8', errors='replace') as fh:
                text += fh.read()
        if any(k in text for k in keys):
            named.add(s)"""

# ======================================================== THE FIFTY-SEVEN
#
# EVERY EDIT BELOW IS ONE OF THREE THINGS, AND NOTHING ELSE.
#
#   RESOLVE   alv_tree.path_of( -> alv_tree.last_path( in a suite whose
#             subject includes a retired page. The two are identical
#             for a page that is still live, so the swap is the whole
#             of it, and the count is pinned so a drift refuses.
#
#   BACKUP    p + SUFFIX -> alv_tree.bak_path(p, SUFFIX), or
#             path_of(x) + SUFFIX -> alv_tree.bak_of(x, SUFFIX). This
#             is the one that cannot be done by swapping the resolver:
#             see bak_path's docstring.
#
#   RESTATE   a claim whose WORDS are now wrong, re-stated. There are
#             few of these and each one is argued where it sits.
#
# NOT ONE PINNED NUMBER MOVES. That is the point of the round.

# THE CENSUS, in the spellings the tree actually uses. The comment
# goes in once, at the first one, because repeating it twenty times
# would be twenty places for it to drift.
C1_WAS = """TOUCHED = sorted(p for p in alv_tree.templates()
                 if os.path.exists(p + SUFFIX))"""
C1_NOW = """# RT-1, 18 Oct 2026 - THE BACKUPS, NOT THE WALK. This list was
# "the templates that are there now, with a backup of this round",
# so a page the tree has since retired dropped out of the round's
# own census and the count came back one short. The backup never
# went anywhere; only the walk had forgotten the page.
TOUCHED = @T@.touched_by(SUFFIX)"""

C1B_WAS = """TOUCHED = sorted(p for p in alv_tree.templates()
                 if os.path.exists(p + SUFFIX)
                 and alv_tree.rel(p) != 'base.html')"""
C1B_NOW = """# RT-1, 18 Oct 2026 - the backups, not the walk. See touched_by().
# base.html is excluded here as it always was: this round's census is
# about the pages, and base is where the tokens are defined.
TOUCHED = [p for p in @T@.touched_by(SUFFIX)
           if @T@.rel(p) != 'base.html']"""

C2_WAS = """TOUCHED = sorted(p for p in T.templates() if os.path.isfile(p + SUFFIX))"""
C2_NOW = """# RT-1, 18 Oct 2026 - the backups, not the walk. See touched_by().
TOUCHED = @T@.touched_by(SUFFIX)"""

C4_WAS = """touched = [p for p in T.templates() if os.path.isfile(p + SUFFIX)]"""
C4_NOW = """# RT-1, 18 Oct 2026 - the backups, not the walk. See touched_by().
touched = @T@.touched_by(SUFFIX)"""

# A one-line was()/before() that asks isfile() about the backup first.
W1_WAS = """    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''"""
W1_NOW = """    # RT-1, 18 Oct 2026 - the backup of a RETIRED page sits beside
    # the hole the page left, not beside its last text.
    b = @T@.bak_path(p, SUFFIX)
    return read(b) if os.path.isfile(b) else ''"""

# The two-line form: b = p + SUFFIX, then a decision about b.
W2_WAS = """    b = p + SUFFIX"""
W2_NOW = """    # RT-1, 18 Oct 2026 - see alv_tree.bak_path: a retired page's
    # backups stay where they were, beside the hole it left.
    b = @T@.bak_path(p, SUFFIX)"""

# The bare form.
W3_WAS = """    return read(p + SUFFIX)"""
W3_NOW = """    # RT-1, 18 Oct 2026 - see alv_tree.bak_path.
    return read(@T@.bak_path(p, SUFFIX))"""

RESOLVE_WAS = 'alv_tree.path_of('
RESOLVE_NOW = '@T@.last_path('

# THE THREE WAYS A SUITE TURNS A LABEL BACK INTO A PATH, all of which
# answer with a hole once the page is retired, and all of which become
# the same call.
#
#   alv_tree.path_of(    raises, which is where the seventeen crashes
#                        came from
#   alv_tree.join(       forgiving by design - it hands back a path
#                        under the first root whether the file is there
#                        or not, so the read that follows returns ''
#                        and the census quietly answers one short
#   os.path.join(T,      the pre-X0 narrow form. 155 of these are on
#                        the debt register test_waiting_down keeps;
#                        converting one is a small payment on it
#   p + SUFFIX           the backup, composed off a path that may now
#                        be a retired page's last text. Uniform across
#                        the tree and uniform to fix.
RESOLVE = ((RESOLVE_WAS, RESOLVE_NOW),
           ('alv_tree.join(', '@T@.last_join('),
           (r'(?<![\w.])p \+ SUFFIX(?!\w)', '@T@.bak_path(p, SUFFIX)'))

# The was() whose fallback is now(p) - the commonest shape in the tree.
WN_WAS = """    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)"""
WN_NOW = """    # RT-1, 18 Oct 2026 - a retired page's backups sit beside the
    # hole it left, not beside its last text. See alv_tree.bak_path.
    b = @T@.bak_path(p, SUFFIX)
    return read(b) if os.path.isfile(b) else now(p)"""

# filename -> (how many path_of sites to re-aim, [targeted edits first])
#
# The targeted edits run BEFORE the blanket re-aim, because several of
# them are path_of(x) + SUFFIX and must become bak_of(x, SUFFIX) rather
# than last_path(x) + SUFFIX.
SUITES = [
    ('test_btn_tone.py', (5, 0, 0), [(W1_WAS, W1_NOW, 1)]),
    ('test_dr2_values.py', (8, 0, 0), [
        (W3_WAS, W3_NOW, 1),
        ("nb = len([p for p in PAGES if os.path.exists("
         "alv_tree.path_of(p) + SUFFIX)])",
         "nb = len([p for p in PAGES\n"
         "          if os.path.exists(@T@.bak_of(p, SUFFIX))])", 1)]),
    ('test_from_calendar.py', (5, 0, 0), [
        ('for name in (\'meal_plan_calendar\', \'meal_plans\') + OUT:\n    ok("name=\'%s\'" % name in urls or \'name="%s"\' % name in urls,\n       \'url name %-24s exists\' % name)\n\nv = source(\'pages\', \'views\', \'recipes\', \'meal_planning.py\')\nok(v and "request.GET.get(\'week\')" in v,\n   \'and the calendar view reads week, so the trip home lands where it left\')', '# RT-1, 18 Oct 2026 - THE NAMES THE LIVE PAGES REVERSE, which is what\n# NoReverseMatch is a risk about. MN-1 retired four meal-plan screens\n# and the three names only they reversed - view_meal_plan,\n# edit_meal_plan and meal_plan_shopping_list - went with them. Sections\n# 1, 2, 4 and 5 above still read those pages, from the text MN-1 left\n# beside the hole, because BK-1\'s markup is still in them and the round\n# still did what it says. This section is the one that is about TODAY,\n# so it asks for today\'s names.\nfor name in (\'meal_plan_calendar\', \'meal_plans\', \'meal_planner\',\n             \'meal_shopping_list\'):\n    ok("name=\'%s\'" % name in urls or \'name="%s"\' % name in urls,\n       \'url name %-24s exists\' % name)\nfor name in OUT:\n    ok(("name=\'%s\'" % name not in urls\n        and \'name="%s"\' % name not in urls),\n       \'  and %-22s went with the screen that reversed it\' % name)\n\nv = source(\'pages\', \'views\', \'recipes\', \'meal_planning.py\')\nok(v and "request.GET.get(\'week\')" in v,\n   \'and the planner view reads week, so the trip home lands where it left\')\n\n# 3b. AND BK-1\'S STANDARD ON THE HOP THAT SURVIVED. RT-1, 18 Oct 2026 - \n#\n# BK-1 is not a round about three screens; it is a round about a rule -\n# THE ORIGIN TRAVELS IN THE URL, AND THE WEEK TRAVELS WITH IT. Two of\n# its screens are gone and the rule is not, so it is asked of the pair\n# that is left: the planner hands the week to the shopping list, and\n# the shopping list hands it back. Nothing above could have caught a\n# planner that dropped it.\n# READ, NOT now(). now() in this suite means \"as BK-1 left it\",\n# which is the right reading for every claim above and the wrong\n# one here: this is a claim about the pair as they stand today.\n_pl = alv_tree.code_only(read(alv_tree.last_path(\'meal_planner.html\')))\n_sh = alv_tree.code_only(read(SHOP))\n_out = re.search(r\'<a href="\\{% url \\\'meal_shopping_list\\\' %\\}([^"]*)"\',\n                 _pl)\nok(_out is not None, \'the planner links to the shopping list\')\nif _out:\n    ok(\'from=\' in _out.group(1) and \'to=\' in _out.group(1),\n       \'  carrying the week it is showing, as a date range\')\n    ok(\'&amp;\' in _out.group(1)\n       and not re.search(r\'&(?!amp;)\', _out.group(1)),\n       \'  and its separator is &amp;, not a bare ampersand\')\n_home = re.findall(r"\\{% url \'meal_planner\' %\\}\\?week=", _sh)\nok(_home, \'  and the shopping list hands the week back - %d link(s)\'\n   % len(_home))', 1),
        (W1_WAS, W1_NOW, 1),]),
    ('test_label_weight.py', (4, 0, 4), [(W2_WAS, W2_NOW, 1)]),
    ('test_lazy_images.py', (3, 0, 0), [
        ("ok(len(lazy) == 14, '%d image(s) wait, on %d page(s)' % (len(lazy), len(pages)),", "# RT-1, 18 Oct 2026 - 12 ON 7. Four lazy images went with the two meal-plan\n# screens MN-1 retired, and the planner that replaced them brought\n# two: 14 - 4 + 2. This counts the live tree, which is what a\n# reader's browser actually loads.\nok(len(lazy) == 12, '%d image(s) wait, on %d page(s)' % (len(lazy), len(pages)),", 1),
        ("ok(v and 'all_recipes = Recipe.objects.all()' in v,", "# RT-1, 18 Oct 2026 - THE FACT, NOT THE SPELLING. MN-1 rewrote this view\n# and the line now reads\n#\n#     'all_recipes': Recipe.objects.all().order_by('recipe_name'),\n#\n# which hands the modal every recipe exactly as before - the limit this\n# check names is unchanged and still owed a fix. A check that pins the\n# spelling of a line reports a limit as LIFTED the day somebody\n# reformats it.\nok(v and 'all_recipes' in v and 'Recipe.objects.all()' in v,", 1),
        (W1_WAS, W1_NOW, 1),
    ]),
    ('test_meal_plan_buttons.py', (2, 0, 0), [(W1_WAS, W1_NOW, 1)]),
    ('test_recipe_photos.py', (3, 0, 0), [
        ('        a, b = raw(now_p), raw(now_p + SUFFIX)', "        # RT-1, 18 Oct 2026 - this walk finds the round's BACKUPS and derives\n        # the page from each, so for a retired page it derives a\n        # path that is not there. Its last text is.\n        a, b = raw(alv_tree.last_of(now_p)), raw(now_p + SUFFIX)", 1),
        ('n_ser = 0\nfor rel, n in SER:\n    t = read(os.path.join(ROOT, rel))', "n_ser = 0\nfor rel, n in SER:\n    # RT-1, 18 Oct 2026 - AS PX-1 LEFT THE FILE, not as the tree has it now.\n    # MN-1 rewrote meal_planning.py and its four serialisers went with\n    # the view that had them: the planner renders\n    # entry.recipe.photo_url in the template instead, which is the\n    # property PX-1 built and one fewer place to get it wrong. PX-1 put\n    # four there and that does not stop being true, so the number stays\n    # and the READ moves. left() walks ROUNDS to the first later\n    # round's backup, which is this file as PX-1 left it.\n    t = left(rel)", 1),
        ("ok(n_ser == N_SERIALISERS, 'all %d serialiser(s)' % N_SERIALISERS, n_ser)", "ok(n_ser == N_SERIALISERS, 'all %d serialiser(s)' % N_SERIALISERS, n_ser)\n# AND THE PRESENT TENSE GETS A CHECK OF ITS OWN, RT-1, 18 Oct 2026 - \n# because the one above is historical now. The half that matters going\n# forward - that no view reaches for recipe_image.url itself - is asked\n# of every live view file, which is wider than the two SER names.\n_old_live = []\nfor _d, _ds, _fs in os.walk(os.path.join(ROOT, 'pages', 'views')):\n    for _f in sorted(_fs):\n        if not _f.endswith('.py'):\n            continue\n        if re.search(r'\\.recipe_image\\.url if \\w+\\.recipe_image',\n                     read(os.path.join(_d, _f))):\n            _old_live.append(_f)\nok(not _old_live,\n   '  and not one live view reaches for recipe_image.url itself - asked '\n   'of every file under pages/views, not just the two above', _old_live)", 1),
        (W2_WAS, W2_NOW, 1),
        # THE MESSAGE HAS TO MOVE WITH THE CHECK. The check itself is a
        # string holding 'alv_tree.path_of(' and the blanket re-aim
        # rewrites it, which is right - the suite should insist on the
        # house resolver it actually uses. Its SENTENCE does not have a
        # trailing paren, so it would have been left saying path_of.
        ("'  and this suite resolves labels through alv_tree.path_of'",
         "'  and this suite resolves labels through alv_tree.last_path'",
         1)]),
    ('test_recipe_side_b.py', (15, 0, 0), [
        ('GATE_WAS, GATE_NOW = 117, 142', 'GATE_WAS, GATE_NOW = 117, 139   # RT-1, 18 Oct 2026 - the wide census is four meal-plan screens smaller and one planner larger. The narrow half does not move.   # (GATE_NOW was 142)', 1),
        ('N_NAV_RULE_HITS, N_NAV_RULE_PRIMARY = 12, 10', "# RT-1, 18 Oct 2026 - 13 AND 11. This is the rule RS-1b REFUSED, measured\n# against the live corpus so that the refusal keeps being justified.\n# MN-1's planner has a Shopping List link in its action bar and it\n# ships as .action-primary, so the rule would now reverse eleven\n# shipped decisions instead of ten. The refusal gets stronger, not\n# weaker, which is why this count is read and not frozen.\nN_NAV_RULE_HITS, N_NAV_RULE_PRIMARY = 13, 11   # (was 12, 10)", 1),
        (W2_WAS, W2_NOW, 1),
        ("if not os.path.isfile(alv_tree.path_of(e[0]) + SUFFIX)]",
         "if not os.path.isfile(@T@.bak_of(e[0], SUFFIX))]", 1),
        ("if os.path.isfile(alv_tree.path_of(r) + SUFFIX)]",
         "if os.path.isfile(@T@.bak_of(r, SUFFIX))]", 1)]),
    ('test_recipe_tones.py', (6, 0, 0), [
        ("ok(len(sb.templates(False)) == 117 and len(sb.templates(True)) == 142,\n   '  which is %d of %d' % (117, 142),", "# RT-1, 18 Oct 2026 - 139, not 142. The gate still runs --strict over the\n# WHOLE census; the census is four meal-plan screens smaller and one\n# planner larger. The narrow half, 117, does not move.\nok(len(sb.templates(False)) == 117 and len(sb.templates(True)) == 139,\n   '  which is %d of %d' % (117, 139),", 1),
        ("   'the push gate runs --strict --recipes now - all 142 pages, which is '\n   'what RS-1a said RS-1b owed it')", "   'the push gate runs --strict --recipes now - all 139 pages, which is '\n   'what RS-1a said RS-1b owed it')", 1),
        ('def pages_of(side):\n    rels = sorted(alv_tree.rel(p) for p in alv_tree.templates())', 'def pages_of(side):\n    # RT-1, 18 Oct 2026 - AND THE PAGES THE TREE HAS SINCE RETIRED. Every\n    # count in section 2 is a statement about the handover from RS-1a,\n    # so the page list has to be the one RS-1a handed over - which\n    # includes four meal-plan screens MN-1 has since retired. The side\n    # test below still decides which of them belong to this half.\n    rels = sorted([alv_tree.rel(p) for p in alv_tree.templates()]\n                  + alv_tree.retired_labels())', 1),
        (W2_WAS, W2_NOW, 2),
        ("if os.path.isfile(alv_tree.path_of(p) + SUFFIX)],",
         "if os.path.isfile(@T@.bak_of(p, SUFFIX))],", 1),
        ("'  and this suite resolves labels through alv_tree.path_of, not a '",
         "'  and this suite resolves labels through alv_tree.last_path, "
         "not a '", 1)]),
    ('test_row_exempt.py', (4, 0, 0), [
        ("ok('NAMED, NOT IN A WRAPPER - 3 button(s) on 3 page(s)' in out,\n   'the report names all three', out[-500:])", "# RT-1, 18 Oct 2026 - TWO ON TWO. The report walks the live tree, as a\n# report should, so the line it prints followed the register down.\nok('NAMED, NOT IN A WRAPPER - 2 button(s) on 2 page(s)' in out,\n   'the report names both', out[-500:])", 1),
        ("# MD-1, 18 Oct 2026 - FIVE BECAME THREE. E33 collapsed the three copies\n# of the recipe row on create_meal_plan into one recipeRowHtml(), so\n# that page's entry went from three loose trashcans to one. Still three\n# pages; two fewer controls.\nok(total == 3, 'it names %d control(s) on %d page(s)'", "# MD-1, 18 Oct 2026 - FIVE BECAME THREE. E33 collapsed the three copies\n# of the recipe row on create_meal_plan into one recipeRowHtml(), so\n# that page's entry went from three loose trashcans to one. Still three\n# pages; two fewer controls.\n# RT-1, 18 Oct 2026 - THREE BECAME TWO, and the entry came OFF the register\n# rather than being read from a backup. An exemption names a control a\n# reader can find and a report can print; create_meal_plan.html is not\n# in the tree any more, so the entry was a line nobody could check.\n# The same argument took the placeholder card off\n# test_pair_contrast's WCAG exemption in this round.\nok(total == 2, 'it names %d control(s) on %d page(s)'", 1),
        (W3_WAS, W3_NOW, 1),
    ]),
    ('test_vocabulary.py', (22, 0, 0), [
        ("# MD-1, 18 Oct 2026 - still three pages, three controls now. E33 wrote\n# create_meal_plan's recipe row once instead of three times.\nok(len(ra.NAMED) == 3\n   and sum(v['count'] for v in ra.NAMED.values()) == 3,\n   '  which makes three such controls on three pages',", "# MD-1, 18 Oct 2026 - still three pages, three controls now. E33 wrote\n# create_meal_plan's recipe row once instead of three times.\n# RT-1, 18 Oct 2026 - TWO AND TWO. create_meal_plan's entry came OFF the\n# register in this round rather than being read from a backup: MN-1\n# retired the page, and an exemption for a control nobody can reach is\n# a line nobody can check. This counts the register as it stands.\nok(len(ra.NAMED) == 2\n   and sum(v['count'] for v in ra.NAMED.values()) == 2,\n   '  which makes two such controls on two pages',", 1),
        ("BOTH = sorted(alv_tree.rel(p) for p in alv_tree.templates()\n              if alv_tree.rel(p) != 'base.html')", "# RT-1, 18 Oct 2026 - AND THE PAGES THE TREE HAS SINCE RETIRED. Section 9\n# asks which templates VC-1 CHANGED, and one of the eight it changed is\n# create_meal_plan.html, which MN-1 has since retired. A list built\n# from the live walk alone reports VC-1 as a seven-page round.\nBOTH = sorted([alv_tree.rel(p) for p in alv_tree.templates()\n               if alv_tree.rel(p) != 'base.html']\n              + alv_tree.retired_labels())", 1),
        ('    for r in sb_before.templates(True):', '    # RT-1, 18 Oct 2026 - AND THE PAGES THE TREE HAS SINCE RETIRED. This\n    # count is a question about the tree VC-1 FOUND, asked of the old\n    # tool with its own vocabulary; the live walk under it answers a\n    # question about today and is one page short of this one.\n    for r in sb_before.templates(True) + alv_tree.retired_labels():', 1),
        (W2_WAS, W2_NOW, 1),
    ]),

    # ---- THE CENSUS FAMILY. One line each: a round's own page list
    # stops being "the templates that are there now, filtered" and
    # becomes "the backups this round wrote". See touched_by(), and
    # note that was() and now() needed nothing in any of these.
    ('test_colour_tokens.py', (1, 0, 2), [(C1_WAS, C1_NOW, 1)]),
    ('test_colour_neutrals.py', (1, 0, 1), [(C1_WAS, C1_NOW, 1)]),
    ('test_colour_tail.py', (3, 0, 1), [(C1_WAS, C1_NOW, 1)]),
    ('test_colour_good_bad.py', (1, 0, 2), [(C1B_WAS, C1B_NOW, 1)]),
    ('test_neutrals.py', (0, 0, 5), [
        ('for want in (\'MARKUP_STYLE = 87\', \'SCRIPT = 148\', \'PAGES = 35\',\n             "\'style-attr\': 22", "\'style-prop\': 8",\n             \'safe == 30\'):', '# RT-1, 18 Oct 2026 - AND THE FOUR THAT MOVED WITH THE TREE. This check\n# quotes test_cssrules_outside\'s own constants, which is the right\n# way to pin a sibling\'s census - a pin that only ever loosens\n# asserts nothing. Four of the six fell when four meal-plan screens\n# left the tree, and the arithmetic below is the reason they are\n# rewritten rather than relaxed: 118 = 27 + 91 still holds, because\n# every literal that went was a var-safe one.\nfor want in (\'MARKUP_STYLE = 86\', \'SCRIPT = 146\', \'PAGES = 33\',\n             "\'style-attr\': 20", "\'style-prop\': 8",\n             \'safe == 28\'):', 1),
        (C2_WAS, C2_NOW, 1),
        # AND THE ONE DIRECT READ. This census walks the round's own
        # pages and then the rest of the tree, and reads each one off
        # the disk. For a retired page the honest read is its last
        # text - identical to read(p) for every page that is still
        # there, which is why one call covers both halves of the loop.
        ('    code = T.code_only(read(p))',
         '    code = T.code_only(read(@T@.last_of(p)))', 1)]),
    # ---- THE join() FAMILY. These suites resolve a pinned page name
    # with the forgiving join() and then guard on isfile(), which is
    # the right guard for a page that was never there and the wrong
    # answer for one that was retired. See last_join().
    ('test_accent_ink.py', (0, 13, 3), [(WN_WAS, WN_NOW, 1)]),
    ('test_action_bar.py', (0, 8, 1), [(WN_WAS, WN_NOW, 1)]),
    ('test_bar_top.py', (0, 10, 0), [(WN_WAS, WN_NOW, 1)]),
    ('test_more_css.py', (0, 9, 0), [
        (WN_WAS, WN_NOW, 1),
        # H9's OWN 24 PAGES, enumerated from its backups rather than
        # from a walk of what is there now. SKIP and base.html are
        # excluded exactly as they were.
        ("""mine = [(rel, p) for rel, p in walked()
        if rel != 'base.html' and rel not in SKIP
        and os.path.isfile(p + SUFFIX)]""",
         """# RT-1, 18 Oct 2026 - the backups, not the walk. See
# touched_by(): this is H9's census of the pages H9 changed, and a
# page the tree has since retired is still one of them.
mine = [(@T@.rel(p).replace(os.sep, '/'), p)
        for p in @T@.touched_by(SUFFIX)
        if @T@.rel(p).replace(os.sep, '/') != 'base.html'
        and @T@.rel(p).replace(os.sep, '/') not in SKIP]""", 1),
        # AND THE BROWSER SECTION STAYS ON THE LIVE PAGES. A rendered
        # claim is a claim about a page a server will serve, and a
        # retired page is not one. The SOURCE census above keeps all
        # 24; the probe drives the 23 that are still there and says so.
        ("""    res = drive([(rel, now(p)) for rel, p in mine], 390, False, 'after')
    for rel, _ in mine:""",
         """    # RT-1, 18 Oct 2026 - the live ones. See above.
    shown = [(rel, p) for rel, p in mine if os.path.isfile(p)]
    res = drive([(rel, now(p)) for rel, p in shown], 390, False, 'after')
    for rel, _ in shown:""", 1),
        ("""    widths = {res[rel][2]['mw'] for rel, _ in mine
              if res[rel][0] == 'driven'}
    ok(widths == {HOUSE_MENU_WIDTH},
       '  and all twenty-four are the SAME box now - %s' % sorted(widths),
       sorted(widths))""",
         """    widths = {res[rel][2]['mw'] for rel, _ in shown
              if res[rel][0] == 'driven'}
    ok(widths == {HOUSE_MENU_WIDTH},
       '  and all %d still served are the SAME box now - %s'
       % (len(shown), sorted(widths)), sorted(widths))""", 1)]),
    ('test_page_title.py', (0, 21, 2), [(WN_WAS, WN_NOW, 1)]),
    ('test_back_label.py', (0, 2, 3), [
        (WN_WAS, WN_NOW, 1),
        # AND now()'S OWN GUARD. BL-2 gave this suite a now() that
        # answers '' for a page that is not in the checkout, so that a
        # widened scope could not read a CRS page at some other
        # round's moment. That is still exactly right for a page this
        # checkout has never had - and a retired page is not one of
        # those. Its last text is on the disk, and every check below
        # means that text.
        ("""    if not os.path.isfile(p):
        return ''
    if not os.path.isfile(p + SUFFIX):
        return read(p)""",
         """    # RT-1, 18 Oct 2026 - a retired page stands in for itself.
    p = @T@.last_of(p)
    if not os.path.isfile(p):
        return ''
    if not os.path.isfile(@T@.bak_path(p, SUFFIX)):
        return read(p)""", 1),
        # THE WALK, FILTERED, BECOMES THE BACKUPS. Both of these loops
        # are BL-1's census of its own 77 pages, and both were written
        # as "every template, keep the ones with my backup" - so a
        # retired page left the census and the control answered 73.
        # See touched_by().
        ("""for p in templates():
    if not os.path.isfile(p + SUFFIX):
        continue""",
         """for p in @T@.touched_by(SUFFIX):""", 2),
        # SECTION 2 ASKS TWO QUESTIONS IN ONE LOOP, and they are not
        # the same question. `left` is present tense - no page defines
        # the rule any more - and `had` is the control, which is a
        # claim about what BL-1 found. So the loop widens to the
        # retired pages for the control's sake, and the present-tense
        # half is asked only of pages the server still serves.
        ("""for p in templates():
    rel = alv_tree.rel(p)
    if rel == 'base.html':
        continue
    a = nocomment(css_of(now(p)))
    if PAGE_RULE.search(a):
        left.append(rel)""",
         """for p in templates() + [q for q in @T@.touched_by(SUFFIX)
                        if not os.path.isfile(q)]:
    rel = @T@.rel(p)
    if rel == 'base.html':
        continue
    if os.path.isfile(p):
        a = nocomment(css_of(now(p)))
        if PAGE_RULE.search(a):
            left.append(rel)""", 1)]),
    # ---- PRESENT TENSE, AND IT MOVES. Each of these counts the tree
    # as it stands, so the register is no help and none is wanted: the
    # tree really is four pages smaller and one page larger. Every
    # number was measured, and each note says what left with the page
    # so that nobody later reads the smaller number as the round's own.
    ('test_house_title.py', (3, 5, 0), [
        ('ok(len(wearers) == 122,\n'
         "   '122 templates now wear the class, which is the number "
         "base\\'s note '\n   'states', len(wearers))",
         '# 120 SINCE RT-1, 18 Oct 2026. MN-1 retired four meal-plan screens,\n'
         '# three of which wore the house title, and the planner that\n'
         '# replaced them wears it too: 122 - 3 + 1. base.html\'s note\n'
         '# moves in the same round, because the sentence above is the\n'
         '# one thing keeping the two honest.\n'
         'ok(len(wearers) == 120,\n'
         "   '120 templates now wear the class, which is the number "
         "base\\'s note '\n   'states', len(wearers))", 1)]),
    ('test_modal_heads2.py', (0, 13, 1), [
        ('PRECEDENTS = 16',
         'PRECEDENTS = 13   # RT-1, 18 Oct 2026 - three of the sixteen '
         'were written on pages MN-1 retired. This is a count of the '
         'live tree, not of what MH-2 did.   # (was 16)', 1)]),
    ('test_heading_standard.py', (0, 2, 0), [
        # NOT A RE-PIN AT ALL - A BAR THIS ROUND MOVED BY TWO LETTERS,
        # and the suite had already written down why the bar exists.
        #
        # HS-1 separates an h4 MODE LABEL (ADD NEW PROPERTY, which
        # shouts because a label shouts) from an h4 that carries DATA
        # (a record name, a date range) by how many literal letters the
        # line has, and it chose six because of this exact page: the
        # Shopping List subtitle read "... {{ n }} day{{ |pluralize }}",
        # three letters of literal, and at a three-letter bar it counted
        # as a label and failed for not shouting.
        #
        # MN-1 reworded that subtitle to carry a meal count as well, so
        # its literal went from "day" to "day meal" - seven letters -
        # and crossed the bar HS-1 set for it. The page has not changed
        # what it is. It is still data with a unit on it.
        #
        # So the bar moves to eight. The shortest real label in the
        # corpus is ADD EXPENSE at ten, which keeps two letters of
        # margin either side, and the count it feeds goes back to the
        # 52 labels and 1 record the corpus held before MN-1.
        ("""_labels = [(r, t) for r, t in H4
           if len([c for c in literal(t) if c.isalpha()]) >= 6]
_records = [(r, t) for r, t in H4
            if len([c for c in literal(t) if c.isalpha()]) < 6]""",
         """# EIGHT SINCE RT-1, 18 Oct 2026 - six was chosen for the
# Shopping List subtitle and MN-1 reworded that subtitle from
# "day" to "day meal", seven letters, which crossed it. The line
# is still data with a unit on it; only its units multiplied.
# ADD EXPENSE, the shortest real label in the corpus, is ten.
_labels = [(r, t) for r, t in H4
           if len([c for c in literal(t) if c.isalpha()]) >= 8]
_records = [(r, t) for r, t in H4
            if len([c for c in literal(t) if c.isalpha()]) < 8]""", 1)]),
    ('test_last_menus.py', (0, 5, 0), [
        (WN_WAS, WN_NOW, 1),
        ("ok(len(pages) == 32, '32 pages carry a More menu', len(pages))",
         "# 31 SINCE RT-1, 18 Oct 2026. This counts the pages that carry\n"
         "# a More menu TODAY. view_meal_plan.html carried one and MN-1\n"
         "# retired it; the planner that replaced it has no More menu.\n"
         "# H8 still bound 32 of them, and that is section 2's claim,\n"
         "# read from the backups.\n"
         "ok(len(pages) == 31, '31 pages carry a More menu', len(pages))",
         1)]),
    ('test_more_menu.py', (0, 9, 0), [
        (WN_WAS, WN_NOW, 1),
        ("ok(len(pages) == 32, '32 pages carry the More menu in markup', "
         "len(pages))\nok(len(mine) == 27, '  27 of them are this round\\'s'"
         ", len(mine))",
         "# 31 AND 26 SINCE RT-1, 18 Oct 2026. Both are readings of the\n"
         "# tree as it stands, not of what this round did - the round\n"
         "# converted 27 pages and MN-1 has since retired one of them,\n"
         "# view_meal_plan.html. Nobody should read 26 as the size of\n"
         "# this round; section 3 reads that from the backups.\n"
         "ok(len(pages) == 31, '31 pages carry the More menu in markup', "
         "len(pages))\nok(len(mine) == 26, '  26 of them are this round\\'s'"
         ", len(mine))", 1)]),

    # ---- THE TAIL, one at a time.
    ('test_entry_sections.py', (0, 0, 2), [
        ('    for suf in LATER_BACKUPS.get(n, ()):\n        if os.path.isfile(p + suf):\n            return read(p + suf)\n    return read(p)', '    # RT-1, 18 Oct 2026 - THE PAGE\'S OWN PATH, AND ITS LAST TEXT AT THE END.\n    # This is alv_rounds.as_left_by\'s walk, hand-rolled, and it took\n    # the same two corrections in this round for the same reasons: `p`\n    # may arrive as a RETIRED page\'s last text, and <that text> plus\n    # .bak_sect2 has never existed; and the end of the walk means "no\n    # later push touched it, so the file itself is the answer", which\n    # for a retired page is the text beside the hole.\n    p = alv_tree.nominal(p)\n    for suf in LATER_BACKUPS.get(n, ()):\n        if os.path.isfile(p + suf):\n            return read(p + suf)\n    return read(alv_tree.last_of(p))', 1),
        ("ROOT = os.path.join(os.getcwd(), 'pages', 'templates')", "ROOT = os.path.join(os.getcwd(), 'pages', 'templates')\n\n# RT-1, 18 Oct 2026 - THE PAGE'S LAST TEXT, UNDER THIS SUITE'S OWN ROOT.\n#\n# This suite predates alv_tree and composes every path from one\n# directory. Widening it to the whole tree would change what it\n# counts, and that is not this round's business: it sits on the\n# debt register test_waiting_down keeps, and the round that widens\n# it owns that number. All this does is let a page the tree has\n# RETIRED still be read, from the text MN-1 left beside the hole.\nimport alv_tree\n\n\ndef _tpl(*parts):\n    # Composed this way on purpose: the spelling this round swaps\n    # for _tpl is the join with ROOT as its first argument, and a\n    # helper that used it would call itself.\n    return alv_tree.last_of(os.path.join(*((ROOT,) + parts)))\n", 1),
        ('os.path.join(ROOT, ', '_tpl(', 23),
    ]),
    ('test_js_escape.py', (0, 1, 5), [
        ('moved = []\nfor rel, p in sorted(PATHS.items()):\n    if not os.path.isfile(p + SUFFIX):', 'moved = []\n# RT-1, 18 Oct 2026 - j1_tree, not PATHS - see section 1. Two of the pages\n# this round edited have since been retired, and a claim about what it\n# wrote has to be asked of them too.\nfor rel, p in sorted(j1_tree):\n    if not os.path.isfile(p + SUFFIX):', 1),
        ('ok(len([r for r in PATHS if os.path.isfile(PATHS[r] + SUFFIX)]) == len(EXPECT),', 'ok(len([r for r, q in j1_tree\n        if os.path.isfile(alv_tree.bak_path(q, SUFFIX))]) == len(EXPECT),', 1),
        ('bare_n = 0\nfor rel, p in sorted(PATHS.items()):', 'bare_n = 0\n# RT-1, 18 Oct 2026 - j1_tree, for the same reason as section 1: this is a\n# count of what J-1 left alone, over the tree J-1 saw.\nfor rel, p in sorted(j1_tree):', 1),
        ('for rel in sorted(EXPECT, key=lambda r: -EXPECT[r]):\n    b, s = census(read(PATHS[rel]))', "for rel in sorted(EXPECT, key=lambda r: -EXPECT[r]):\n    # RT-1, 18 Oct 2026 - EXPECT is J-1's own list and two of its pages have\n    # since been retired, so this print reads each one's last text.\n    b, s = census(read(alv_tree.last_path(rel)))", 1),
        ('    if as_of is not None and J1_RAN is not None:\n        return as_of(p, J1_RAN, read)\n    return read(p)', '    # RT-1, 18 Oct 2026 - AND THE SECOND CLAUSE IS RESOLVED BY THE ROUND\n    # ORDER, NOT BY FILE TIMESTAMPS.\n    #\n    # The warning above stays true where it applies: as_left_by()\n    # answers "as the round LEFT it", which is the opposite of a\n    # control, and that is why the FIRST clause reads J-1\'s own backup.\n    # The second clause only ever runs for a page J-1 NEVER TOUCHED -\n    # it has no .bak_jsescape - and for such a page before and after\n    # are the same text, so the two helpers agree by construction.\n    #\n    # What they do not agree on is how they find it. as_of() picks the\n    # first backup by MODIFICATION TIME, and in a rebuilt mirror every\n    # backup carries today\'s date, so the answer depends on the order\n    # the files happened to be written. Measured 18 Oct: this control\n    # read 43 in the mirror and 45 on the laptop, for the same tree.\n    # as_left_by() walks ROUNDS, which is a fact about the programme\n    # rather than a fact about the filesystem.\n    if as_left_by is not None:\n        return as_left_by(p, SUFFIX, read)\n    return read(alv_tree.last_of(p))', 1),
        ("""left, safe_now, bad_was, safe_was = [], 0, 0, 0
for rel, p in sorted(PATHS.items()):
    # left_by_j1, NOT read - this is J-1's census and it must stay J-1's.
    b, s = census(left_by_j1(p))
    safe_now += s
    if b:
        left.append('%s: %d' % (rel, b))
    wb, ws = census(was(p))
    bad_was += wb
    safe_was += ws""",
         """# RT-1, 18 Oct 2026 - TWO QUESTIONS, TWO PAGE LISTS, AND THEY WERE ONE.
#
# `left` is the claim that matters and it is present tense: not one
# interpolation anywhere in the tree is unprotected. It walks every
# live template, which is the whole point of this section's heading.
#
# The three counts under it are J-1's OWN arithmetic, and that holds
# over THE TREE J-1 LEFT - which is not the tree today in two
# directions. Two of J-1's pages were retired by MN-1, which pulled the
# total below the sum; and MN-1's planner arrived with eight |escapejs
# sites of its own, which pushed it above. Neither is a fault in J-1.
#
# A PAGE THAT DID NOT EXIST YET IS NO PART OF A ROUND'S CENSUS, and it
# has to be NAMED, because nothing in this programme records when a
# page ARRIVED. alv_tree.RETIRED says which pages have left; if the
# other half of that register is ever built, this is its first entry.
SINCE_J1 = ('meal_planner.html',)

j1_tree = [(r, p) for r, p in sorted(PATHS.items())
           if r not in SINCE_J1]
j1_tree += [(r, alv_tree.join(r)) for r in alv_tree.retired_labels()]

left, safe_now, bad_was, safe_was = [], 0, 0, 0
for rel, p in sorted(PATHS.items()):
    # left_by_j1, NOT read - this is J-1's census and it must stay J-1's.
    b, _s = census(left_by_j1(p))
    if b:
        left.append('%s: %d' % (rel, b))
for rel, p in sorted(j1_tree):
    _b, s = census(left_by_j1(p))
    safe_now += s
    wb, ws = census(was(p))
    bad_was += wb
    safe_was += ws""", 1),
    ]),
    ('test_css_order.py', (0, 0, 1), [
        ("        with open(q + SUFFIX, 'rb') as fh:\n            if b'\\r\\n' in fh.read():\n                crlf_bak += 1\n        with open(q, 'rb') as fh:", "        # RT-1, 18 Oct 2026 - a retired page's backup sits beside the hole,\n        # and its last text stands in for the file.\n        with open(alv_tree.bak_path(q, SUFFIX), 'rb') as fh:\n            if b'\\r\\n' in fh.read():\n                crlf_bak += 1\n        with open(alv_tree.last_of(q), 'rb') as fh:", 1),
        ('    for q in alv_tree.templates():\n        if os.path.exists(q + SUFFIX):\n            baks.append(q)', '    # RT-1, 18 Oct 2026 - the backups, not the walk. See touched_by(): the\n    # claim is that CS-1 backed up 27 files, which it did, and one of\n    # them is a page the tree has since retired.\n    baks.extend(alv_tree.touched_by(SUFFIX))', 1),
        ('def page(name):\n    hits = [p for p in alv_tree.templates() if alv_tree.rel(p) == name]\n    return hits[0] if len(hits) == 1 else None', 'def page(name):\n    # RT-1, 18 Oct 2026 - AND A PAGE THE TREE USED TO HAVE. Every caller of\n    # this is a claim about what CS-1 pruned, which is a claim about\n    # the past: one of the pages it pruned is create_meal_plan.html,\n    # and MN-1 has retired it. A live-only lookup answers None and the\n    # round reports itself two declarations short of what it did.\n    hits = [p for p in alv_tree.templates() if alv_tree.rel(p) == name]\n    if len(hits) == 1:\n        return hits[0]\n    if alv_tree.retired(name):\n        return alv_tree.last_path(name)\n    return None', 1),
    ]),
    ('test_row_wrap.py', (1, 0, 4), [
        ("HELD_BACK = ['create_meal_plan.html', 'household_member_management.html',\n             'invoices.html', 'physical_invoice_list.html']", "# RT-1, 18 Oct 2026 - THREE, NOT FOUR - see WHY below for the reason\n# create_meal_plan.html came off this list rather than onto a backup.\nHELD_BACK = ['household_member_management.html',\n             'invoices.html', 'physical_invoice_list.html']", 1),
        ("head('5. the four pages held back, held back whole')", "head('5. the three pages held back, held back whole')", 1),
        ("    'create_meal_plan.html': 'built inside a JavaScript template literal',\n", '    # RT-1, 18 Oct 2026 - create_meal_plan.html came OFF this list, not\n    # onto a backup. It was held back because its one trashcan is built\n    # inside a JavaScript template literal; MN-1 retired the page, and a\n    # page that is held back from a conversion it can never receive is a\n    # line nobody can check. Its entry in alv_rowactions.NAMED went in\n    # the same round, for the same reason.\n', 1),
        ('LOOSE_NOW = 3   # MD-1, 18 Oct 2026', "LOOSE_NOW = 2   # RT-1, 18 Oct 2026 - create_meal_plan's one loose trashcan went with the page. The report walks the live tree, as a report should.   # (was 3)   # MD-1, 18 Oct 2026", 1),
    ]),
    ('test_row_action_order.py', (2, 1, 2), [
        ('def scan(getter):\n    """[(page, seq, unfixable)] and {class: {glyphs}} over the tree."""\n    rows, glyphs = [], {}\n    for p in sorted(alv_tree.templates()):', 'def scan(getter, pages=None):\n    """[(page, seq, unfixable)] and {class: {glyphs}} over the tree.\n\n    `pages` ADDED BY RT-1, 18 Oct 2026 - so that the two scans below can\n    ask different questions. ROWS is about the tree TODAY. OLDROWS is\n    the CONTROL - what the columns looked like BEFORE this round - and\n    that tree had four meal-plan screens MN-1 has since retired, so a\n    live walk answers it three columns short.\n    """\n    rows, glyphs = [], {}\n    for p in sorted(pages if pages is not None\n                    else alv_tree.templates()):', 1),
        ('OLDROWS, OLDGLYPHS = scan(lambda p: was(p) or now(p))', '# RT-1, 18 Oct 2026 - the control reads the tree this round found, which\n# includes the pages it has since lost. Nominal paths, so rel() still\n# names the page and was() still finds the backup beside it.\nOLDROWS, OLDGLYPHS = scan(lambda p: was(p) or now(p),\n                          list(alv_tree.templates())\n                          + [alv_tree.join(r)\n                             for r in alv_tree.retired_labels()])', 1),
        ("ok(len(multi) >= 20,\n   'there are %d multi-action columns to judge' % len(multi))", "# RT-1, 18 Oct 2026 - 18, not 20. One multi-action column went with the\n# four meal-plan screens MN-1 retired. This is a floor, not a count -\n# it is here so a scanner that went quiet cannot pass - and 19 is\n# still plenty of corpus to be a rule rather than a coincidence.\nok(len(multi) >= 18,\n   'there are %d multi-action columns to judge' % len(multi))", 1),
    ]),
    ('test_retone.py', (1, 11, 0), [
        ("    p = alv_tree.join(rel.replace('/', os.sep)) + SUFFIX", "    # RT-1, 18 Oct 2026 - a retired page's backups sit beside the hole it\n    # left, which is what bak_of resolves; join() plus the suffix\n    # would ask for <page>.bak_planner.bak_retone.\n    p = alv_tree.bak_of(rel, SUFFIX)", 1),
    ]),
    ('test_recipe_spice.py', (0, 0, 0), [
    ]),
    ('test_zoom_guards.py', (0, 0, 3), [
        ("ROOT = os.path.join(os.getcwd(), 'pages', 'templates')", "ROOT = os.path.join(os.getcwd(), 'pages', 'templates')\n\n# RT-1, 18 Oct 2026 - THE PAGE'S LAST TEXT, UNDER THIS SUITE'S OWN ROOT.\n# This suite composes its paths from one directory and renders the\n# markup it reads into a fixture rather than asking a server for\n# it, so a page the tree no longer serves can still be measured -\n# from the text MN-1 left beside the hole it made. Widening the\n# suite to the whole tree is a different round's business; it is\n# on the register test_waiting_down keeps.\nimport alv_tree\n\n\ndef _tpl(*parts):\n    # Composed this way on purpose: the literal spelling that this\n    # round swaps for _tpl is the one with ROOT as its first\n    # argument, and a helper that used it would call itself.\n    return alv_tree.last_of(os.path.join(*((ROOT,) + parts)))", 1),
        ('os.path.join(ROOT, ', '_tpl(', 9),
        ("touched = []\nfor dp, _d, ns in alv_tree.walk3():\n    for n in sorted(ns):\n        if n.endswith('.html') and os.path.isfile(os.path.join(dp, n)\n                                                  + SUFFIX):\n            touched.append(alv_tree.rel(os.path.join(dp, n)).replace(os.sep, '/'))", "# RT-1, 18 Oct 2026 - the backups, not the walk. See touched_by(): this is\n# the round's own list of the pages it touched, and six of them are\n# pages the tree has since retired.\ntouched = [alv_tree.rel(p).replace(os.sep, '/')\n           for p in alv_tree.touched_by(SUFFIX)]", 1),
    ]),
    ('test_user_slash.py', (1, 0, 2), [
    ]),
    ('test_js_buttons.py', (15, 0, 1), [
        ('CENSUS_NARROW, CENSUS_WIDE = 117, 142', '# RT-1, 18 Oct 2026 - the application is 139 pages. Four meal-plan screens\n# were retired and the planner replaced them: 142 - 4 + 1. The SWEEP\n# SCOPE does not move - 117 was and is the narrow half, and the pages\n# the flag hides are still the recipe and meal-plan side.\nCENSUS_NARROW, CENSUS_WIDE = 117, 139   # (wide was 142)', 1),
        ('HITS_LOOSE, HITS_TIGHT = 706, 704', 'HITS_LOOSE, HITS_TIGHT = 673, 671   # RT-1, 18 Oct 2026 - thirty-three scanner hits went with the four retired screens, and both matchers fall by the same thirty-three.   # (was 706, 704)', 1),
    ]),
    ('test_drift_root.py', (4, 0, 1), [
        ('N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 89, 88   # CC-2, 17 Oct 2026', 'N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 83, 82   # RT-1, 18 Oct 2026 - six .modal-footer wrappers went with the four meal-plan screens MN-1 retired, and the planner brought none. BOTH matchers fall by the same six, which is the point of keeping the pair: the wrappers that left were ordinary ones.   # (was 89, 88)   # CC-2, 17 Oct 2026', 1),
    ]),
    ('test_radius_token.py', (0, 0, 4), [
        ('converted = 0\nfor p in sorted(T.templates()):\n    b = p + SUFFIX\n    if os.path.isfile(b):', '# RT-1, 18 Oct 2026 - the backups, not the walk. See touched_by(): what\n# THIS round converted is a claim about the past, and three of the\n# declarations it converted are on pages the tree has since retired.\nconverted = 0\nfor p in sorted(T.touched_by(SUFFIX)):\n    b = p + SUFFIX\n    if os.path.isfile(b):', 1),
        ('N_PRE = 13            # already tokenised before it, by the B rounds', "N_PRE = 13            # already tokenised before it, by the B rounds\n# RT-1, 18 Oct 2026 - AND THREE OF THE 158 ARE NO LONGER IN THE CORPUS. The\n# corpus total used to be simply this round's plus the pre-existing\n# ones; it cannot be any more, because three of this round's\n# conversions were on meal-plan screens MN-1 retired. The round still\n# converted 158 - that is what the loop below reads from the backups -\n# and the live corpus carries 168.\nN_RETIRED = 3", 1),
        ('N_TOTAL = N_RADIUS + N_PRE', 'N_TOTAL = N_RADIUS + N_PRE - N_RETIRED', 1),
        ('N_STYLE, N_ATTR, N_SCRIPT = 156, 6, 9', 'N_STYLE, N_ATTR, N_SCRIPT = 155, 4, 9   # RT-1, 18 Oct 2026 - one <style> rule and two style attributes went with the retired screens   # (was 156, 6, 9)', 1),
    ]),
    ('test_css_standalone.py', (3, 0, 1), [
        ("    ok(int(m.group(1)) == 134,\n       '  and it is %s, which is 140 less manual_pdf\\'s six'", "    # RT-1, 18 Oct 2026 - 133. One of the page declarations 5b counts was\n    # on a meal-plan screen MN-1 retired. 5b reads the LIVE tree, as\n    # it should - what it reports is what beats base today.\n    ok(int(m.group(1)) == 133,\n       '  and it is %s, which is 140 less manual_pdf\\'s six and one '\n       'retired page\\'s'", 1),
        ("    print('      5b now reports %s, down from 140 - the six manual_pdf '\n          'carried' % m.group(1))", "    print('      5b now reports %s, down from 140 - the six manual_pdf '\n          'carried and one on a page MN-1 retired' % m.group(1))", 1),
    ]),
    ('test_dead_files.py', (0, 0, 0), [
        ('import os\nimport re\nimport subprocess\nimport sys', "import os\nimport re\nimport subprocess\nimport sys\n\n# RT-1, 18 Oct 2026 - SECTION 2 IS A SAFETY ARGUMENT ABOUT THE PAST, AND IT\n# HAS TO BE READ THAT WAY NOW. DF-1 deleted four EMPTY templates, one of\n# them edit_meal_plan.html, and section 2 is how it proved that deletion\n# safe: the edit_meal_plan VIEW existed and rendered create_meal_plan.html,\n# never the empty file. MN-1 has since removed the view AND the page it\n# rendered, so asked of today's tree the argument reads as four failures\n# about a round that was right. as_left_by walks the round order to the\n# first later backup, which is these files as DF-1 left them.\nfrom alv_rounds import as_left_by", 1),
        ("    v = read(VIEW)\n    m = re.search(r'def edit_meal_plan\\(.*?(?=\\ndef )', v, re.S)", "    # AS DF-1 LEFT IT - RT-1, 18 Oct 2026 - see the import above.\n    v = as_left_by(VIEW, SUFFIX, read)\n    m = re.search(r'def edit_meal_plan\\(.*?(?=\\ndef )', v, re.S)", 1),
        ('if os.path.isfile(URLS):\n    ok(re.search(r"path\\(\'meal_plans/<int:meal_plan_id>/edit/\',\\s*"\n                 r"views\\.edit_meal_plan", read(URLS)) is not None,\n       \'the URL still points at that view\')', 'if os.path.isfile(URLS):\n    ok(re.search(r"path\\(\'meal_plans/<int:meal_plan_id>/edit/\',\\s*"\n                 r"views\\.edit_meal_plan",\n                 as_left_by(URLS, SUFFIX, read)) is not None,\n       \'the URL pointed at that view, and not at the empty file\')\n\n# AND IT IS GONE NOW, WHICH DOES NOT WEAKEN THE ARGUMENT ABOVE.\n# RT-1, 18 Oct 2026 - MN-1 retired create_meal_plan.html and removed the view\n# that rendered it. The empty file DF-1 deleted is still deleted, which\n# is section 1 and is still asked of the live tree; this records that\n# nothing reaches it from the live application either, by a second\n# route and for a second reason.\nok(\'def edit_meal_plan(\' not in read(VIEW),\n   \'  and MN-1 has since removed the view as well - the planner edits a \'\n   \'meal where it sits\')', 1),
    ]),
    ('test_tree_roots.py', (0, 0, 0), [
        ("    if 'alv_tree.walk3()' not in t:\n        bad_walk.append(n)", "    # RT-1, 18 Oct 2026 - OR touched_by, WHICH IS ALSO alv_tree WALKING.\n    # X0's claim is that none of the 33 builds a root of its own, and\n    # walk3() was the only way it had to say so. touched_by() is\n    # another: it walks the roots and keeps the files that carry a\n    # round's backup, which is exactly what one of these suites was\n    # doing by hand around a walk3(). test_zoom_guards calls it now.\n    if ('alv_tree.walk3()' not in t\n            and 'alv_tree.touched_by(' not in t):\n        bad_walk.append(n)", 1),
        ("ok(not bad_walk, '  every one walks via alv_tree.walk3()', bad_walk)", "ok(not bad_walk, '  every one walks via alv_tree - walk3 or touched_by', bad_walk)", 1),
        ('MAIN_N = 143', 'MAIN_N = 140   # RT-1, 18 Oct 2026 - MN-1 retired four meal-plan screens and the planner replaced them: 143 - 4 + 1. This is the shape of the tree, which is what this file is for.   # (was 143)', 1),
    ]),
    ('test_subtree_tones.py', (10, 0, 2), [
        ("ok(len(tree) == 151, 'a WALK finds 151 templates', len(tree))", "# RT-1, 18 Oct 2026 - 148. Four retired, one added: see alv_tree.RETIRED.\nok(len(tree) == 148, 'a WALK finds 148 templates', len(tree))", 1),
        ("ok(len(top) == 125, '  a flat listing finds 125 - 120 was what H7 counted',", "ok(len(top) == 122, '  a flat listing finds 122 - 120 was what H7 counted',", 1),
    ]),
    ('test_important_base.py', (0, 0, 1), [
        ('IMP_TREE = 826   # SB-1, 17 Oct 2026', 'IMP_TREE = 806   # RT-1, 18 Oct 2026 - twenty went with the four meal-plan screens MN-1 retired, and the planner that replaced them declares none: measured, not deduced.   # (was 826)   # SB-1, 17 Oct 2026', 1),
    ]),
    ('test_surface_border.py', (0, 2, 1), [
        ('N_CONVERT, N_PAGES, N_FALLBACK, N_OTHER = 78, 43, 3, 96', '# RT-1, 18 Oct 2026 - N_OTHER was 96. Three of those non-border uses were on\n# pages MN-1 retired. This is a count of the live corpus, so it falls\n# with the corpus; F2a still settled 96 of them.\nN_CONVERT, N_PAGES, N_FALLBACK, N_OTHER = 78, 43, 3, 93', 1),
        ('    return [p for p in alv_tree.templates() if os.path.isfile(p + SUFFIX)]', '    # RT-1, 18 Oct 2026 - the backups, not the walk. See touched_by().\n    return alv_tree.touched_by(SUFFIX)', 1),
    ]),
    ('test_cssrules_outside.py', (0, 0, 1), [
        ("ok(safe == 30,\n   '30 of the 148 may become var() - and 118 may not, which is '", "# RT-1, 18 Oct 2026 - 28 OF 146. The two style-attr writes that went\n# with the retired meal-plan screens were both var-safe ones, so the\n# safe half falls by two and the 118 that may NOT become var() does\n# not move at all - which is the half this round is about.\nok(safe == 28,\n   '28 of the 146 may become var() - and 118 may not, which is '", 1),
        ("CTX = {'style-attr': 22, 'style-prop': 8, 'css-text': 0,   # VC-1", "CTX = {'style-attr': 20, 'style-prop': 8, 'css-text': 0,   # RT-1, 18 Oct 2026 - two style-attr writes were in the scripts of meal-plan screens MN-1 retired   # (style-attr was 22)   # VC-1", 1),
        ('MARKUP_STYLE = 87      # colour literals in inline style= attributes   # PH-2, 14 Oct 2026', 'MARKUP_STYLE = 86      # colour literals in inline style= attributes   # RT-1, 18 Oct 2026 - one was on a meal-plan screen MN-1 retired   # (was 87)   # PH-2, 14 Oct 2026', 1),
        ('SCRIPT = 148            # colour literals inside <script> bodies   # VC-1, 14 Oct 2026', 'SCRIPT = 146            # colour literals inside <script> bodies   # RT-1, 18 Oct 2026 - two were in the scripts of meal-plan screens MN-1 retired   # (was 148)   # VC-1, 14 Oct 2026', 1),
        ('PAGES = 35              # real pages carrying any of them   # PH-2', 'PAGES = 33              # real pages carrying any of them   # RT-1, 18 Oct 2026 - two of them were meal-plan screens MN-1 retired   # (was 35)   # PH-2', 1),
    ]),
    ('test_custom_control.py', (1, 0, 2), [
        ("ok(len(users) == 5, 'the component is used on %d pages, base aside'", "# RT-1, 18 Oct 2026 - FIVE BECAME TWO. D28 had put the control on the\n# Duplicate dialogs of the Meal Plans list and the calendar as well as\n# the plan page; MN-1 retired all three screens, and the planner has no\n# Duplicate dialog because a plan is no longer a thing to duplicate.\n# MD-1 really did put it on five. This counts the live tree.\nok(len(users) == 2, 'the component is used on %d pages, base aside'", 1),
        ('ok(sum(users.values()) == 15,', 'ok(sum(users.values()) == 12,', 1),
    ]),
    ('test_help_label.py', (4, 0, 1), [
        ("check('  which is the live file when the round left no backup',\n      re.search(r'if not os\\.path\\.isfile\\(p \\+ SUFFIX\\):\\s*\\n'\n                r'\\s*return read\\(p\\)', bl) is not None)", "# RT-1, 18 Oct 2026 - THE SPELLING OF THE BACKUP'S PATH MOVED, AND THE\n# CLAIM DID NOT. test_back_label now asks alv_tree.bak_path for its\n# own backup, because a retired page's backups sit beside the hole it\n# left rather than beside its last text. What this check is about is\n# the FALLBACK - that a page the round never touched is read LIVE -\n# so it accepts either spelling of the question above it.\ncheck('  which is the live file when the round left no backup',\n      re.search(r'if not os\\.path\\.isfile\\(\\s*(?:p \\+ SUFFIX'\n                r'|alv_tree\\.bak_path\\(p, SUFFIX\\))\\):\\s*\\n'\n                r'\\s*return read\\(p\\)', bl) is not None)", 1),
        ('LABELS_TOTAL = 129   # PJ-1, 15 Oct 2026', 'LABELS_TOTAL = 126   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026', 1),
        ('HELP_TOTAL = 46   # MH-1, 18 Oct 2026', 'HELP_TOTAL = 43   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026', 1),
    ]),
    ('test_personal_heads.py', (0, 0, 3), [
        ("T = os.path.join(ROOT, 'pages', 'templates')", "T = os.path.join(ROOT, 'pages', 'templates')\n\n# RT-1, 18 Oct 2026 - THE PAGE'S LAST TEXT, UNDER THIS SUITE'S OWN ROOT.\n#\n# This suite predates alv_tree and composes every path from one\n# directory. Widening it to the whole tree would change what it counts,\n# and that is not this round's business: it sits on the debt register\n# test_waiting_down keeps, and the round that widens it owns that\n# number. All this does is let a page the tree has RETIRED still be\n# read, from the text MN-1 left beside the hole it made.\nimport alv_tree\n\n\ndef _tpl(*parts):\n    # Composed this way on purpose: the literal spelling\n    # that this round swaps for _tpl is the one with T as its\n    # first argument, and a\n    # helper that used it would call itself.\n    return alv_tree.last_of(os.path.join(*((T,) + parts)))\n", 1),
        ('os.path.join(T, ', '_tpl(', 8),
    ]),
    ('test_surface_deep.py', (0, 0, 5), [
        ('LEFT_BORDERS = 93', 'LEFT_BORDERS = 89   # RT-1, 18 Oct 2026 - four of the kept border uses were on meal-plan screens MN-1 retired. F2a left 93 of them alone and F2b still decides the rest; this counts the live corpus.   # (was 93)', 1),
        ("T = os.path.join(ROOT, 'pages', 'templates')", "T = os.path.join(ROOT, 'pages', 'templates')\n\n# RT-1, 18 Oct 2026 - THE PAGE'S LAST TEXT, UNDER THIS SUITE'S OWN ROOT.\n#\n# This suite predates alv_tree and composes every path from one\n# directory. Widening it to the whole tree would change what it counts,\n# and that is not this round's business: it sits on the debt register\n# test_waiting_down keeps, and the round that widens it owns that\n# number. All this does is let a page the tree has RETIRED still be\n# read, from the text MN-1 left beside the hole it made.\nimport alv_tree\n\n\ndef _tpl(*parts):\n    # Composed this way on purpose: the literal spelling\n    # that this round swaps for _tpl is the one with T as its\n    # first argument, and a\n    # helper that used it would call itself.\n    return alv_tree.last_of(os.path.join(*((T,) + parts)))\n", 1),
        ('os.path.join(T, ', '_tpl(', 13),
    ]),
    ('test_crs_print.py', (0, 0, 2), [
        ('N_TEMPLATES_MIN = 151', '# RT-1, 18 Oct 2026 - 148. A FLOOR, NOT A COUNT - it is here so that a\n# reader of the CRS guard which had gone back to one root could\n# not pass. MN-1 retired four meal-plan screens and added the\n# planner, so the tree is 148; the narrow root alone is 140, and\n# the floor still separates the two by eight.\nN_TEMPLATES_MIN = 148   # (was 151)', 1),
    ]),
    # ---- THREE MORE OF THE SAME SHAPE, found by the final sweep and
    # not by the first: they were counted as cleared by the sentinel
    # cut, in a measurement taken while the path_of fallback this
    # round rejected was still in place. The fallback went; these
    # three came back. Bookkeeping, and worth writing down: a
    # measurement is only as good as the tree it was taken on.
    ('test_bar_order.py', (8, 0, 0), [
        (W1_WAS, W1_NOW, 1),
    ]),
    ('test_calendar_actions.py', (4, 0, 0), [
        (W1_WAS, W1_NOW, 1),
    ]),
    ('test_calendar_tone.py', (4, 0, 0), [
        (W1_WAS, W1_NOW, 1),
    ]),
    ('test_meal_bar_top.py', (1, 0, 0), [
        (W1_WAS, W1_NOW, 1),
    ]),
    ('test_meal_row.py', (2, 0, 0), [
        (W1_WAS, W1_NOW, 1),
    ]),
    ('test_palette.py', (0, 3, 2), [
        ("STILL_BROKEN = {\n    'celebration_dashboard.html': ('Back', 1.66),\n    'meal_plan_calendar.html': ('Back', 1.13),\n}", "STILL_BROKEN = {\n    'celebration_dashboard.html': ('Back', 1.66),\n    # RT-1, 18 Oct 2026 - meal_plan_calendar.html was here at 1.13, a Back\n    # label this round named rather than hid. MN-1 retired the page.\n    # A recorded defect on a page nobody can reach is a line nobody\n    # can check, and this register exists to be checked - the same\n    # argument took three exemptions off three other registers in\n    # this round. The planner's own Back is measured by\n    # test_planner.py, on the page that is actually served.\n}", 1),
    ]),
    ('test_small_three.py', (0, 8, 3), [
        ("_cml = read(alv_tree.join('create_meal_plan.html')) \\\n    if os.path.isfile(alv_tree.join('create_meal_plan.html')) else ''", "# RT-1, 18 Oct 2026 - THE CONTROL READS THE PAGE'S LAST TEXT. This is a\n# claim about what SM-3 deliberately left alone, which is a claim\n# about the past; MN-1 has since retired the page, and a control\n# that answers '' is not a control.\n_cml = read(alv_tree.last_join('create_meal_plan.html')) \\\n    if os.path.isfile(alv_tree.last_join('create_meal_plan.html')) \\\n    else ''", 1),
    ]),
    ('test_view_seg.py', (3, 0, 0), [
        (W1_WAS, W1_NOW, 1),
    ]),
    ('test_pair_contrast.py', (0, 0, 0), [
        (C4_WAS, C4_NOW, 1),
        # PRESENT TENSE, AND IT MOVES. These two are counts of the
        # LIVE tree, not of what a round did, so the register is no
        # help and no help is needed: the tree really is four pages
        # smaller and one page larger, and the numbers follow it.
        ('EXPECT_PAIRS = 698   # DT-1, 16 Oct 2026',
         'EXPECT_PAIRS = 694   # RT-1, 18 Oct 2026 - four rules that '
         'set both a background and a colour went with the four pages '
         'MN-1 retired, and the planner that replaced them brought '
         'its own already on tokens. Measured, not deduced: every '
         'pair below AA this table names is untouched, and the gross '
         'count is what moved.   # (was 698)   # DT-1, 16 Oct 2026', 1),
        ('EXPECT_INACTIVE = 25   # E-10',
         'EXPECT_INACTIVE = 24   # RT-1, 18 Oct 2026 - '
         'create_meal_plan.html went, and its placeholder card went '
         'with it. The exemption below loses the same one entry.   '
         '# (was 25)   # E-10', 1),
        # AND THE PIN COMES OFF THE LIST, because the list is the
        # exemption and an exemption for a selector that cannot be
        # reached is not an exemption, it is a line nobody can check.
        ("    ('create_meal_plan.html', "
         "'.recipe-selector-card-placeholder', 2.53),\n",
         "    # RT-1, 18 Oct 2026 - create_meal_plan.html's placeholder\n"
         "    # card was here at 2.53:1 under the WCAG 1.4.3 exemption.\n"
         "    # MN-1 retired the page; the planner picks a recipe from a\n"
         "    # list on the calendar and has no placeholder card.\n", 1),
    ]),
]

# ================================================== THE ONE SHARED WALK
#
# alv_rounds.as_left_by() IS THE ONLY PLACE IN THE PROGRAMME THAT WALKS
# ROUNDS, and sixty-odd suites read through it as now(). Teaching it
# about a retired page is worth more than ninety call sites, and it was
# very nearly free - the walk ALREADY finds a retired page's last text,
# because .bak_planner is in ROUNDS like any other round's backup.
#
# What it could not do was take a retired page's last text AS ITS
# ARGUMENT, which is what a suite hands it after last_path(), and what
# it could not do at the END of the walk was read a file that is not
# there. Two lines.
#
# MEASURED FIRST, on test_btn_tone.py: with the argument left alone,
# now() returned the page as MN-1 found it - thirteen house roles - and
# was() returned the eight BT-1 started from, so the suite reported
# "13 now, 8 before" on a round that changed neither. Both numbers were
# real texts of that page; neither was the pair the claim is about.
AL_WAS = """def as_left_by(path, suffix, read):
    \"\"\"The text of `path` as the round whose backups end in `suffix` left
    it - the earliest later round's backup of it, or the file itself.

    A round in ROUNDS is placed by the list. A round OLDER than the list
    is placed by its backups' times: see later_backup().\"\"\"
    if suffix in ROUNDS:
        for s in ROUNDS[ROUNDS.index(suffix) + 1:]:
            if os.path.isfile(path + s):
                return read(path + s)
        return read(path)
    return read(later_backup(path, suffix) or path)"""

AL_NOW = """def as_left_by(path, suffix, read):
    \"\"\"The text of `path` as the round whose backups end in `suffix` left
    it - the earliest later round's backup of it, or the file itself.

    A round in ROUNDS is placed by the list. A round OLDER than the list
    is placed by its backups' times: see later_backup().

    RT-1, 18 Oct 2026 - AND IT WORKS ON A PAGE THE TREE NO LONGER HAS.
    Two calls into alv_tree do the whole of it:

        nominal()  because a suite that resolved its label with
                   alv_tree.last_path() hands in a RETIRED page's last
                   text, and the walk below builds <page>.bak_<round>
                   from its argument - never <page>.bak_planner.bak_...

        last_of()  because the end of the walk means "no later round
                   touched it, so the file itself is the answer", and
                   for a retired page the file itself is not there. Its
                   last text is, beside the hole it left.

    The walk in the middle needed nothing: a retiring round's backup is
    in ROUNDS like any other, so it was already the right answer for
    every round older than it.\"\"\"
    path = alv_tree.nominal(path)
    if suffix in ROUNDS:
        for s in ROUNDS[ROUNDS.index(suffix) + 1:]:
            if os.path.isfile(path + s):
                return read(path + s)
        return read(alv_tree.last_of(path))
    return read(later_backup(path, suffix) or alv_tree.last_of(path))"""

AL_IMP_WAS = """import os"""
AL_IMP_NOW = """import os

# RT-1, 18 Oct 2026 - for the two calls in as_left_by(). alv_tree
# imports nothing of this programme, so there is no cycle to make.
import alv_tree"""

RA_WAS = '''    'create_meal_plan.html': {
        'count': 1,
        'classes': ('icon-delete',),
        # AND `since`, FOR THE SAME REASON VC-1 ADDED THE KEY.
        # test_row_exempt reads a named page AS THE ROUND THAT NAMED IT
        # LEFT IT, which for this entry is RA-5's era - and there were
        # three then. Without this the count would be read against a
        # snapshot taken before E33 existed and the register would be
        # called wrong for being right.
        'since': '.bak_mealdisplay',
        'why': 'Remove this recipe - one control at the end of each recipe '
               'row, beside the name and the servings box. Built inside a '
               'JavaScript template literal, written once since MD-1.',
    },
'''

RA_NOW = '''    # RT-1, 18 Oct 2026 - create_meal_plan.html's ENTRY IS GONE, not moved
    # to a backup. It named one loose trashcan - 'Remove this recipe',
    # at the end of each recipe row - and MN-1 retired the page: a plan
    # is built on the calendar now. An exemption names a control a
    # reader can find and Show-RowActionDrift can print, so an
    # exemption for a page that is not in the tree is a line nobody can
    # check. The entry carried `since: .bak_mealdisplay`, which VC-1's
    # key existed for; the history is in MD-1's round, not here.
'''

# ===================================================== THE REGISTRATIONS
RD_WAS = """    '.bak_planner',
]"""
RD_NOW = """    '.bak_planner',
    # RT-1, 18 Oct 2026 - what the tree does with a page it used to
    # have. MN-1 retired four templates and eighty of the 370 suites
    # went red, none of them on the planner. A census of what a round
    # did is a claim about the past.
    '.bak_retired',
]"""

CV_WAS = """    'test_planner.py',
]"""
CV_NOW = """    'test_planner.py',
    # RT-1, 18 Oct 2026 - the retired register. Wide from birth: it
    # reads every suite in this list and asks each one whether it names
    # a page the tree no longer has.
    'test_retired.py',
]"""

WD_WAS = "CONVERTED_N = 105   # MN-1, 18 Oct 2026"
WD_NOW = ("CONVERTED_N = 106   # RT-1, 18 Oct 2026 - this round own suite"
          "   # (was 105)   # MN-1, 18 Oct 2026")


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def read_ps1(p):
    with open(p, encoding='utf-8-sig', newline='') as f:
        return f.read()


def write_ps1(p, t):
    with open(p, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(t)


def backup(p, reader=read):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, reader(p))


def refuse(msg):
    raise SystemExit('RT-1 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def swap_re_all(text, pattern, new, n, where):
    """swap_all for the one edit that cannot be done on a literal.

    `p + SUFFIX` IS A SUBSTRING OF OTHER PEOPLE'S EXPRESSIONS. Written
    as a literal swap it turned

        if os.path.isfile(_p + SUFFIX):

    into _alv_tree.bak_path(p, SUFFIX), because the `_` in front of the
    `p` was not part of what was matched and stayed exactly where it
    was. Two suites died with a NameError on an identifier that had
    never existed. So this one is anchored: the `p` must not be
    preceded by a word character or a dot.
    """
    rx = re.compile(pattern)
    got = len(rx.findall(text))
    if got != n:
        refuse('%s: %s matches %d time(s), expected exactly %d'
               % (where, pattern, got, n))
    return rx.sub(new.replace('\\', '\\\\'), text)


def swap_all(text, old, new, n, where):
    """Replace every occurrence, having first proved there are exactly n.

    A count pinned here is the difference between a round that re-aimed
    sixteen call sites and a round that re-aimed fifteen and said
    nothing.
    """
    got = text.count(fit(text, old))
    if got != n:
        refuse('%s: %r appears %d time(s), expected exactly %d'
               % (where, old[:60], got, n))
    return text.replace(fit(text, old), fit(text, new))


def before(text, anchor, block, where):
    """Splice `block` in immediately before `anchor`."""
    once(text, anchor, where)
    a = fit(text, anchor)
    return text.replace(a, fit(text, block) + a)


def dead_sentinels(text):
    """The $sentinels rows that guard one of the four retired pages.

    A ROW IS FOUND BY ITS File FIELD, NOT BY A SUBSTRING OF THE LINE.
    Three of the sixteen quote a What that names another page, and one
    of them quotes 'meal_plansHelpModal' - a MODAL id, not a file. A
    line match would take rows that are still live and leave one that
    is not.
    """
    out = []
    for i, line in enumerate(text.split('\n')):
        s = line.strip()
        if not s.startswith('@{ File ='):
            continue
        m = re.match(r"@\{\s*File\s*=\s*'([^']+)'", s)
        if not m:
            continue
        if os.path.basename(m.group(1).replace('\\', '/')) in GONE:
            # THE ROW MUST BE WHOLE ON ITS LINE. That is the property
            # that makes cutting lines safe, and it is cheaper to
            # assert than to reason about. A counted-brace check was
            # written first and rejected a correct cut: row 221 is
            #
            #     Text = 'onclick="confirmDelete('
            #
            # whose payload holds an unbalanced parenthesis inside a
            # string. The row is perfectly well formed; the counting
            # was the thing that was wrong.
            if not (s.startswith('@{') and s.rstrip().rstrip(',')
                    .endswith('}')):
                refuse('%s line %d is a sentinel row on a retired page '
                       'but it does not open and close on its own line, '
                       'so it cannot be cut by line: %r'
                       % (PS1, i + 1, s[:90]))
            out.append(i)
    return out


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pt = os.path.join(root, TREE)
    t = read(pt)

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED IS ASKED OF THE TREE, FIRST.
    if 'RETIRED = {' in t:
        print('RT-1  already applied - the register is in alv_tree.')
        return 0

    # ---------------------------------------------------------------- 1
    # MN-1 MUST BE APPLIED. This round is about the hole MN-1 left; run
    # against a tree that still has the four pages it would register
    # four live templates as retired, which is a lie the gate would
    # then enforce.
    for name in GONE:
        live = os.path.join(root, 'pages', 'templates', name)
        if os.path.isfile(live):
            refuse('%s is still in the tree. RT-1 registers the pages '
                   'MN-1 retired; apply MN-1 first.' % name)
        if not os.path.isfile(live + '.bak_planner'):
            refuse('%s has no .bak_planner beside it. A retired page '
                   'must leave its last text on the disk - without it '
                   'the register would point at nothing.' % name)

    # ---------------------------------------------------------------- 2
    # THE REGISTER AND THE TWO ACCESSORS.
    t = before(t, REG_AT, REG, '%s (the register)' % TREE)
    t = swap(t, POF_WAS, POF_NOW, '%s (path_of names the round)' % TREE)
    t = swap(t, CV_WAS, CV_NOW, '%s (CONVERTED)' % TREE)
    out[pt] = t

    # ---------------------------------------------------------------- 3
    # THE SELECTOR READS BOTH HALVES OF AN INSTRUMENT.
    pi = os.path.join(root, IMPACT)
    out[pi] = swap(read(pi), IMP_WAS, IMP_NOW, '%s (select)' % IMPACT)

    # ---------------------------------------------------------------- 4
    # THE SIXTEEN DEAD SENTINELS, AND THIS ROUND'S SUITE ON THE GATE.
    pp = os.path.join(root, PS1)
    ps = read_ps1(pp)

    dead = dead_sentinels(ps)
    if len(dead) != 16:
        refuse('%s: %d dead sentinel row(s) found, expected exactly 16. '
               'The table has moved since this round was measured.'
               % (PS1, len(dead)))
    lines = ps.split('\n')
    cut = set(dead)
    ps = '\n'.join([L for i, L in enumerate(lines) if i not in cut])
    # SIXTEEN WHOLE LINES CAME OUT, AND NOTHING ELSE DID.
    # dead_sentinels() has already proved each one opens and closes on
    # its own line; this proves the cut took only those sixteen.
    if len(lines) - len(ps.split('\n')) != 16:
        refuse('%s: the cut removed %d line(s), not 16'
               % (PS1, len(lines) - len(ps.split('\n'))))
    for nm in GONE:
        if "File = 'pages\\templates\\%s'" % nm in ps or \
           "File = 'pages/templates/%s'" % nm in ps:
            refuse('%s: a sentinel row on %s survived the cut.' % (PS1, nm))
    # LAST IN $suites, AND THE LAST ENTRY CARRIES NO COMMA. The array
    # closes on the line after it, so the new name takes the comma and
    # the closing paren stays where it is.
    ps = swap(ps, "    'test_planner.py'\n)",
              "    'test_planner.py',\n"
              "    # RT-1, 18 Oct 2026 - what the tree does with a page it\n"
              "    # used to have. Sixteen rows of the table above guarded\n"
              "    # the four pages MN-1 retired; they are gone, and this\n"
              "    # suite is why they cannot come back.\n"
              "    'test_retired.py'\n)", '%s ($suites)' % PS1)
    out[pp] = ps

    # ---------------------------------------------------------------- 4b
    # THE FIFTY-SEVEN. Targeted edits first, then the blanket re-aim -
    # several of the targeted ones are path_of(x) + SUFFIX and must
    # become bak_of(x, SUFFIX), not last_path(x) + SUFFIX.
    for name, n_resolve, edits in SUITES:
        ps_ = os.path.join(root, name)
        if not os.path.isfile(ps_):
            refuse('%s is not on disk - this round re-aims it.' % name)
        s_ = read(ps_)
        # EVERY SUITE CALLS alv_tree BY ITS OWN NAME. Roughly a third
        # of them import it as T, and a payload that says alv_tree.
        # lands in those as a NameError at run time rather than a
        # failed check - which is how test_neutrals.py died on the
        # first pass of this round. The payloads are written with a
        # placeholder and the suite's own spelling is read off its
        # import line.
        # ASKED TWICE, BECAUSE A TARGETED EDIT CAN ADD THE IMPORT.
        # Three suites in this round predate alv_tree and never import
        # it; their first edit is the one that does. Reading the alias
        # only once, before the edits, refused those three for not
        # importing a module the same call was about to give them.
        def alias_of(text):
            if re.search(r'(?m)^\s*import alv_tree as T\b', text):
                return 'T'
            if re.search(r'(?m)^\s*import alv_tree\b', text):
                return 'alv_tree'
            return None

        pre = alias_of(s_)
        for old, new, cnt in edits:
            if '@T@' in new and pre is None:
                refuse('%s never imports alv_tree, so this round cannot '
                       'name it in a payload for that suite.' % name)
            s_ = swap_all(s_, old, new.replace('@T@', pre or 'alv_tree'),
                          cnt, '%s (targeted)' % name)
        alias = alias_of(s_)
        if any(n_resolve) and alias is None:
            refuse('%s never imports alv_tree, so this round cannot name '
                   'it in a payload for that suite.' % name)
        alias = alias or 'alv_tree'
        for i_, ((old, new), cnt) in enumerate(zip(RESOLVE, n_resolve)):
            if not cnt:
                continue
            # The last one is anchored - see swap_re_all.
            f_ = swap_re_all if i_ == len(RESOLVE) - 1 else swap_all
            s_ = f_(s_, old, new.replace('@T@', alias), cnt,
                    '%s (resolve)' % name)
        out[ps_] = s_

    # ---------------------------------------------------------------- 4c
    # AND base's OWN NOTE, because test_house_title.py says in as many
    # words that "the number and base's note move together or one of
    # them is lying". The number moved; so does the note. This is the
    # only line of markup this round touches.
    pb = os.path.join(root, 'pages', 'templates', 'base.html')
    out[pb] = swap(read(pb),
                   """      h2.page-title-h2 and h4.page-subtitle-h4 and styles neither. 122 pages
      do.""",
                   """      h2.page-title-h2 and h4.page-subtitle-h4 and styles neither. 120 pages
      do - 122 until MN-1 retired four meal-plan screens on 18 Oct 2026,
      three of which wore it, and the planner that replaced them wears
      it too.""",
                   'base.html (the house title count)')

    # ------------------------------------------------------------- 4d
    # THE EXEMPTION REGISTER LOSES ONE ENTRY.
    pra = os.path.join(root, 'alv_rowactions.py')
    out[pra] = swap(read(pra), RA_WAS, RA_NOW,
                    'alv_rowactions.py (the retired entry)')

    # ---------------------------------------------------------------- 5
    # THE REGISTERS.
    pr = os.path.join(root, ROUNDS)
    r_ = read(pr)
    r_ = swap(r_, RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)
    r_ = swap(r_, AL_IMP_WAS, AL_IMP_NOW, '%s (import)' % ROUNDS)
    r_ = swap(r_, AL_WAS, AL_NOW, '%s (as_left_by)' % ROUNDS)
    out[pr] = r_

    pw = os.path.join(root, WD)
    out[pw] = swap(read(pw), WD_WAS, WD_NOW, '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------------- 6
    # COMPILE THE PYTHON AND BALANCE THE POWERSHELL BEFORE WRITING ONE
    # BYTE. E25 shipped a patcher that patched a plant; this one proves
    # the result parses first.
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.basename(k), e.lineno, e.msg))

    if CHECK:
        print('RT-1 --check')
        print('  files to write : %d' % len(out))
        print('  dead sentinels : %d' % len(dead))
        print('  retired pages  : %s' % ', '.join(GONE))
        print('--check: nothing written.')
        return 0

    for k, val in sorted(out.items()):
        backup(k, read_ps1 if k.endswith('.ps1') else read)
        (write_ps1 if k.endswith('.ps1') else write)(k, val)
        print('  wrote %s' % os.path.relpath(k, root))

    print('RT-1  %d file(s) written, backups end %s' % (len(out), SUFFIX))
    print('Now run:  python test_retired.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
