# -*- coding: utf-8 -*-
"""alv_tree.py - WHAT THE TEMPLATE TREE ACTUALLY IS.

WHY THIS FILE EXISTS, WHICH IS A FAILURE WORTH WRITING DOWN TWICE.

    Every census, patcher and suite in this repo has walked one directory:
    pages/templates. On 28 Sep, during the walkthrough, Demetri reported
    that the CRS Reporting screens were green. They are - and not one gate
    in this programme had ever seen them, because they do not live there.
    They live in crs/templates/crs/, a SEPARATE DJANGO APP, mounted at
    /crs/ by mysite/urls.py.

    This is the second time the same mistake has been paid for. In H7 the
    censuses used glob('pages/templates/*.html'), which sees 120 files and
    is blind to the 18 in six subdirectories; test_hub_bar.py's walking
    census caught it, and H7b was the round that cleaned up after it. The
    fix then was "walk, do not glob". That fix was correct and incomplete:
    it widened HOW we look and left WHERE we look hard-coded in 103 places.

    So the lesson is not "walk the tree". It is: THE SHAPE OF THE TREE IS
    A FACT ABOUT THE SYSTEM, AND A FACT ABOUT THE SYSTEM BELONGS IN ONE
    PLACE. When Django gains another app with templates, this list is the
    only thing that should have to change - and the gate in
    test_tree_roots.py exists to make sure a new census cannot quietly
    build its own root again.

WHAT A ROOT IS
    A directory Django's APP_DIRS loader will find templates under. Each
    entry is the path RELATIVE TO THE REPO ROOT, split into parts, so this
    file has no opinion about the separator and works from a scratch copy
    as happily as from the repo.

ON BASENAMES
    Measured 28 Sep: 146 templates across both roots, 146 distinct
    basenames - ZERO collisions. That is load-bearing. Dozens of suites
    key their expectations by basename, and they keep working across the
    wider tree only while that holds. It is asserted in test_tree_roots.py
    so that the day it stops holding, the programme is told, rather than a
    dict silently merging two different pages.
"""
import io
import os
import re
import tokenize

# The tree, in the order Django was told about the apps.
TEMPLATE_ROOTS = [
    (('pages', 'templates'),
     'the main app - every module except CRS'),
    (('crs', 'templates'),
     'the CRS reporting app, mounted at /crs/ by mysite/urls.py'),
]


# THE PAGES THE TREE USED TO HAVE, AND THE ROUND THAT TOOK EACH ONE.
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
    key = label.replace('\\', '/')
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


# WHAT IS NOT THE TREE - PG-3, 24 Oct 2026.
#
# A VIRTUALENV INSIDE THE REPOSITORY IS NOT PART OF IT. Demetri's
# lives at code/, with Lib/site-packages under it; mine lives outside
# the repo. Four instruments walked "the tree" pruning .git,
# __pycache__ and node_modules - the right list for the tree they
# were written against, and the wrong question for his. His push gate
# timed out at suite 448 of 448 on 24 October because of it.
#
# THE TEST IS pyvenv.cfg, NOT A NAME. His is called `code` and the
# next one will be called something else. Every virtualenv Python has
# made since 3.3 writes that file at its root - it is the marker the
# interpreter uses, so it is the one that cannot be wrong about a
# directory somebody named after their project.
#
# AND site-packages BY NAME, because a venv copied without its marker
# still has one, and a vendored system install has the directory and
# no cfg at all.
#
# ONE RULE, FOUR CALLERS. check_gates, alv_preflight, alv_run and
# stage_round all ask this. A list in four files is four places to
# forget the fifth name.
SKIP_DIRS = ('.git', '__pycache__', 'node_modules', 'media',
             'staticfiles', 'site-packages', '.mypy_cache',
             '.pytest_cache', '.ruff_cache')


def prune(folder, dirnames):
    """Drop what is not the tree, IN PLACE, for an os.walk.

    Called as `prune(dp, dn)` inside the loop, which is the only
    spelling that works: os.walk reads the list it was handed, so a
    function that returned a new one would be ignored.
    """
    keep = []
    for d in dirnames:
        if d in SKIP_DIRS:
            continue
        if os.path.isfile(os.path.join(folder, d, 'pyvenv.cfg')):
            continue
        keep.append(d)
    dirnames[:] = keep
    return dirnames


def walk_tree(base=None):
    """Every (folder, filenames) in the tree, with the rest left out."""
    base = base or os.getcwd()
    for dp, dn, fn in os.walk(base):
        prune(dp, dn)
        yield dp, fn


def roots(base=None):
    """Every template root that exists, absolute.

    A root that is not on disk is SKIPPED rather than raising: a suite may
    be run against a scratch copy that holds only the files it cares
    about, and that is a legitimate thing to do. test_tree_roots.py is the
    one place that insists both roots are really there.
    """
    base = base or os.getcwd()
    out = []
    for parts, _why in TEMPLATE_ROOTS:
        p = os.path.join(base, *parts)
        if os.path.isdir(p) and p not in out:
            out.append(p)
    return out


def walk(base=None):
    """(folder, filenames) for every directory under every root.

    A drop-in for the `for folder, _, names in os.walk(T)` that censuses
    already write - except it covers the whole tree.
    """
    for r in roots(base):
        for folder, _dirs, names in os.walk(r):
            yield folder, names


def path_of(label, base=None):
    """The absolute path for a label that rel() produced.

    THE INVERSE OF rel(), AND X0 SHOULD HAVE SHIPPED IT ON DAY ONE.

    X0 widened two things in each converted census: the WALK, and the
    LABEL it prints. What it did not look for was code that takes a label
    back and rebuilds a path from it - and test_secondary_visible does
    exactly that, twenty pages later, with

        os.path.join(T, rel.replace('/', os.sep))

    where T is still pages/templates. Given 'crs/country_list.html' that
    names a file which has never existed, and the suite died with a
    FileNotFoundError rather than a failed check. Demetri's push gate
    caught it; eight sweeps of mine had not, because the sweep script
    grepped stdout for a failure count and a TRACEBACK prints none.

    So: labels are reversible now, and a census that needs the file back
    asks for it here instead of assuming which root it came from.
    """
    rel_ = label.replace('/', os.sep)
    for r in roots(base):
        p = os.path.join(r, rel_)
        if os.path.isfile(p):
            return p
    ret = retired(label)
    if ret:
        raise IOError(
            'alv_tree.path_of: %r was retired by %s and is not in the '
            'tree any more. A claim about what a round DID to that page '
            'reads alv_tree.last_path(); a claim about the tree TODAY '
            'should not name it at all.' % (label, ret[1]))
    raise IOError('alv_tree.path_of: no template named %r under %s'
                  % (label, [os.path.basename(r) for r in roots(base)]))


def join(*parts, **kw):
    """The path of the template named by `parts`, under whichever root
    holds it - path_of() for code that is composing a path rather than
    asserting a fact.

    WHY THIS IS FORGIVING AND path_of() IS NOT. X0 widened the walk and
    the label and left the way back on the narrow root: 155 sites across
    26 converted suites still read

        p = os.path.join(T, rel)

    with T fixed at pages/templates, so a CRS label resolved to a path
    that cannot exist. One of them crashed the laptop's gate. But dozens
    of the others sit inside `if os.path.exists(...)` - a guard ASKING
    whether a file is there - and path_of() raising would turn every one
    of those questions into a crash. So this returns the path under the
    first root when no root holds the file, which is exactly what
    os.path.join(T, ...) returned, and exists() answers False as before.

        join('properties.html')        pages/templates/properties.html
        join('crs/index.html')         crs/templates/crs/index.html
        join('projects', 'x.html')     pages/templates/projects/x.html
        join('not_a_file.html')        pages/templates/not_a_file.html

    Separators go either way, because the callers were written for
    os.path.join and some of them hand it a label with forward slashes.
    Use path_of() when the file MUST be there and a wrong answer should
    stop the run; use this when composing.
    """
    rel_ = os.path.join(*parts).replace('/', os.sep).replace('\\', os.sep)
    rs = roots(kw.get('base'))
    for r in rs:
        p = os.path.join(r, rel_)
        if os.path.isfile(p):
            return p
    return os.path.join(rs[0], rel_)


def walk3(base=None):
    """os.walk's OWN 3-tuple - (folder, dirs, names) - across every root.

    This exists so converting a census is a one-token edit. A suite that
    reads

        for d, _sub, fs in os.walk(T):

    becomes

        for d, _sub, fs in alv_tree.walk3():

    and nothing else about it moves: the loop keeps its own variable
    names, its arity, and its body. Sixty-three suites walk the tree, each
    having chosen its own names for those three; a two-tuple walker would
    have meant editing every loop header by hand, and a hand that is
    editing sixty-three loop headers is a hand that will get one wrong.
    """
    for r in roots(base):
        for triple in os.walk(r):
            yield triple


def templates(base=None, include_base=True):
    """Every .html in the tree: absolute, sorted, deduplicated."""
    out = set()
    for folder, names in walk(base):
        for n in names:
            if not n.endswith('.html'):
                continue
            if not include_base and n == 'base.html':
                continue
            out.add(os.path.join(folder, n))
    return sorted(out)


# ==========================================================================
# WHO LOOKS AT ALL OF IT - the conversion register.
#
# This lives here rather than in apply_tree_roots.py for a dull reason
# that cost a run: a patcher is a SCRIPT, and importing one to read a list
# off it executes the whole round. It lives here rather than in the suite
# because the patcher needs it too. The register is data about the tree,
# and the tree is what this module is for.
#
# Every walking suite in the repo belongs to exactly one of these four
# lists, and test_tree_roots.py fails if one belongs to none - which is
# how a future census that builds its own root gets caught on the day it
# is written rather than the day someone notices a module is missing.
# ==========================================================================

# Converted by X0. Each was RUN with the wider tree first, under a
# sitecustomize that made os.walk on pages/templates also yield
# crs/templates - one file, rather than editing 63 to find out - and each
# PASSED. Then converted, and run again for real.
CONVERTED = [
    'test_accent_ink.py', 'test_accent_shades.py', 'test_action_bar.py',
    'test_admin_banner.py', 'test_admin_headings.py',
    'test_admin_repair.py', 'test_applies_from.py', 'test_avatar.py',
    'test_bar_top.py', 'test_body_backs.py', 'test_console_encoding.py',
    'test_deeper_teal.py', 'test_div_balance.py', 'test_entry_headings.py',
    'test_entry_panel.py', 'test_entry_sections.py', 'test_filter_field.py',
    'test_filter_gap.py', 'test_finance_headings.py',
    'test_form_components.py', 'test_heading_components.py',
    'test_heading_prefix.py', 'test_heading_standard.py',
    'test_house_header.py', 'test_hub_bar.py', 'test_label_fit.py',
    'test_last_menus.py', 'test_map_provider.py', 'test_more_css.py',
    'test_more_menu.py', 'test_named_bars.py', 'test_one_action_bar.py',
    'test_page_title.py', 'test_palette.py', 'test_panel_title.py',
    'test_print_buttons.py', 'test_projects_heading.py',
    'test_report_head.py', 'test_required_sweep.py', 'test_row_personal.py',
    'test_save_and_cancel.py', 'test_secondary_visible.py',
    'test_small_controls.py', 'test_table_admin.py', 'test_tap_target.py',
    'test_zoom_guards.py',
    # PQ-1, 10 Oct 2026 - off WAITING: the bare clause
    # it was waiting on is fixed, and it walks the whole
    # tree now.
    'test_print_queries.py',
    # PQ-1 - and this round's own suite, which walks
    # through alv_tree from the day it was written.
    'test_crs_print.py',
    # D-2, 9 Oct 2026 - written walking wide from the
    # start rather than converted to it. It belongs here
    # because it walks templates through walk3() and
    # builds no root of its own, which is what this list
    # means - not because any round widened it.
    'test_required_promise.py',
    # LB-1, 10 Oct 2026 - off WAITING. It was held because the
    # CRS forms carried plain field labels it had never seen,
    # being on a root it did not walk. The labels are bold now
    # and the walk is wide.
    'test_label_bold.py',
    # LB-1 - and this round's own suite, wide from birth.
    'test_label_weight.py',
    # IN-2, 11 Oct 2026 - wide from birth: it reads two named
    # templates and base through alv_tree, and builds no root.
    'test_lines_table.py',
    # FC-1, 11 Oct 2026 - wide from birth.
    'test_form_card_radius.py',
    # E-1a, 11 Oct 2026 - four off WAITING at once. Two were held
    # by a single dead .req rule on a CRS page; two by numbers
    # measured before the CRS module was in view.
    'test_req_marker.py',
    'test_required_marker.py',
    'test_line_soft.py',
    'test_subtree_tones.py',
    # E-1a - and this round's own suite.
    'test_held_four.py',
    # E-1b, 11 Oct 2026 - two more off WAITING. One needed no
    # application change at all; the other needed half of one
    # selector removed. test_modal_heads is not here - widened,
    # it still fails on the Recipe View close strip its entry
    # records - and nor is test_button_sweep, whose narrow root
    # rebuilds a pre-sweep tree and is a stated position.
    'test_contrast.py',
    'test_compound_rules.py',
    # E-1b - and this round's own suite.
    'test_held_contrast.py',
    # E-10, 11 Oct 2026 - it was never held by its own walk. Its
    # walk was fine; Show-ButtonDrift could not RESOLVE the names
    # the walk handed it, so eight CRS pages came back as
    # FileNotFoundError and the suite read eight crashes as eight
    # drifting buttons. Twelve really did drift, behind them.
    'test_disabled_state.py',
    # E-10 - and this round's own suite.
    'test_drift_root.py',
    # HL-1, 12 Oct 2026 - its one failure was a Help button on a
    # page in the second root, wearing the Back label class. D-2
    # fixed the identical span on workspace_management in
    # September and could not see this one.
    'test_small_three.py',
    # BL-2, same round - and not one application file changed for
    # it. All five of its failures were its reader: it asked
    # as_left_by for pages BL-1 never touched and got whichever
    # later round had opened them. Live, no page in either root
    # carries the rule it reported on seven.
    'test_back_label.py',
    # HL-1 - and this round's own suite.
    'test_help_label.py',
    # DB-5, 12 Oct 2026 - the Property Dashboard onto house
    # standards, and the round that found the page could not be
    # used from a keyboard at all.
    'test_dash_std.py',
    # MH-2, 13 Oct 2026 - the last held suite that was work. It
    # passed 13/0 while saying EVERY modal header in the system
    # wears the class, which was true of one root. Widened it
    # sees five more, four of them the round.
    'test_modal_heads.py',
    # MH-2's own suite.
    'test_modal_heads2.py',
    # E15, 13 Oct 2026 - the Python stripper gets an owner.
    'test_py_code.py',
    # F2b's own suite.
    'test_surface_border.py',
    # E11, 13 Oct 2026 - the script census gets an owner.
    'test_js_buttons.py',
    # RS-1a, 13 Oct 2026 - the recipe side starts catching up.
    'test_recipe_tones.py',
    # PX-1, 13 Oct 2026 - the recipe photos get an owner.
    'test_recipe_photos.py',
    # RS-1b, 14 Oct 2026 - the recipe side finishes and the drift
    # gate widens to all 142 pages. Wide from birth: it reads named
    # templates through alv_tree and builds no root of its own.
    'test_recipe_side_b.py',
    # VC-1, 14 Oct 2026 - the gate's VOCABULARY, after RS-1b widened
    # its page scope. Wide from birth, same shape as RS-1b's.
    'test_vocabulary.py',
    # PH-2, 14 Oct 2026 - the panel heads. Demetri asked why three
    # recipe screens were green; the answer was a status token used
    # as decoration. Wide from birth.
    'test_panel_heads.py',
    # VB-1, 15 Oct 2026 - the verb colours. Demetri asked why a selection
    # was green, why a confirmation bar was brown on brown, and why the
    # Edit button is one colour here and blue everywhere else. Three
    # questions, one answer. Wide from birth.
    'test_verb_colours.py',
    # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers retired onto the
    # component eleven other pages already share. Demetri asked why the
    # P&L viewer had no Share button; the answer was that it was a second
    # implementation. Wide from birth.
    'test_pdf_viewer.py',
    # CC-1, 15 Oct 2026 - the celebration grid. A month that showed each
    # event once, a table that clipped its own Saturday, cells that grew
    # with their content, and a key below the thing it explains.
    'test_calendar_grid.py',
    # PJ-1, 15 Oct 2026 - a project edit learns which of three pages it
    # was opened from, and Back and Save stop disagreeing about it.
    # Wide from birth.
    'test_project_origin.py',
    # PJ-2, 15 Oct 2026 - three stat tiles in a third of a column. The
    # label had a 28px box for an 82px word, and SL-1's break-word made
    # the wrap land mid-word. Wide from birth.
    'test_stat_cols.py',
    # TB-1a, 15 Oct 2026 - the Administration tabs are called what their
    # labels say, and six class names that styled nothing are gone.
    # Wide from birth.
    'test_tab_names.py',
    # TB-1b, 15 Oct 2026 - twenty-four Back controls name the tab they
    # want, the view resolves the key and the markup paints it on the
    # first frame. Wide from birth.
    'test_landing_tab.py',
    # NV-1a, 16 Oct 2026 - a granted permission module is a selection and
    # not a verdict, so it leaves --alv-good for the accent. The
    # active/inactive dot keeps the verdict token. Wide from birth.
    'test_perm_select.py',
    # NV-1b, 16 Oct 2026 - the title deeds table onto .alv-table, and
    # fifteen rule openings out of the page's own stylesheet. Wide from
    # birth.
    'test_deed_table.py',
    # NV-1c, 16 Oct 2026 - Notify joins the icon vocabulary as an ADVANCE
    # that someone will notice, and the two comment controls go
    # icon-only. Wide from birth.
    'test_notify_icon.py',
    # NV-1d, 16 Oct 2026 - Customers gains a View, and because there is
    # no detail route it opens a read-only sheet built as markup. Wide
    # from birth.
    'test_customer_view.py',
    # TD-2, 16 Oct 2026 - the title deeds table reads like the lease
    # agreements table: one action column, View always drawn, and the
    # two text-muted dashes become disabled twins. Wide from birth.
    'test_deed_one_column.py',
    # LV-1, 16 Oct 2026 - LEAVE stops being a silencer: ten register
    # entries become one, and the 25 Bootstrap-coloured buttons they were
    # hiding take the house tone. Wide from birth.
    'test_leave_decided.py',
    # DT-1, 16 Oct 2026 - the last two pages with a table standard of
    # their own. 13 tables built in JavaScript, 25 rule openings and 11
    # status chips, none of which a markup gate could ever see. Wide
    # from birth.
    'test_data_table.py',
    # AB-1, 16 Oct 2026 - the three Administration behaviours Demetri
    # asked for while testing: notification cards collapsed on arrival,
    # the list alphabetical, and the permissions action bar at the top
    # where every other screen puts it. Wide from birth.
    'test_admin_behaviour.py',
    # HM-4, 16 Oct 2026 - the Open label moves inside its own strip, so
    # the figures and the word they belong to read as one line. Wide
    # from birth.
    'test_home_open.py',
    # WM-1, 16 Oct 2026 - the Workspace member count becomes a control
    # on ALV POP v1, instead of a title= tooltip that a phone cannot
    # show. Wide from birth.
    'test_ws_members.py',
    # AE-4, 16 Oct 2026 - test_ae_line was measuring a date input it
    # built itself, 21px wider than the control it stood for. It clones
    # the control now, and asks it directly whether it clips. Wide from
    # birth.
    'test_ae_probe.py',
    # LF-1, 17 Oct 2026 - test_label_fit asserted an absolute text width
    # at the one viewport where this sandbox and his Chromium disagree.
    # PJ-2's wrap law replaces it there and nowhere else. Wide from
    # birth.
    'test_label_law.py',
    # GT-2, 17 Oct 2026 - the gate's suite loop moves into alv_run.py,
    # where it can be tested: parallel, planters serial, renders first,
    # and --Resume. Wide from birth.
    'test_gate_speed.py',
    # CC-2, 17 Oct 2026 - the contacts compact view opens a modal
    # instead of growing the card in place, and the emoji countdowns
    # take CC-1's wording. Wide from birth.
    'test_contact_modal.py',
    # SB-1, 17 Oct 2026 - the Actual Expenses Invoice icon is the same
    # icon whichever route reaches it. Wide from birth.
    'test_invoice_icon.py',
    # DG-1, 17 Oct 2026 - one script-built Delete button joins the
    # action-secondary action-danger pair, and the suite that counts
    # LV-1's work stops counting later rounds as LV-1's. Wide from
    # birth.
    'test_danger_pair.py',
    # RI-1, 17 Oct 2026 - every JPEG recipe upload failed, because the
    # reader re-encodes to PNG and then announced the media type from
    # the filename. Wide from birth.
    'test_image_wire.py',
    # NW-1, 17 Oct 2026 - E20. 87 browser suites fetched Bootstrap,
    # Font Awesome and jQuery from three CDNs on every page they
    # opened. Wide from birth.
    'test_offline.py',
    # PG-1, 18 Oct 2026 - E24. The gate reads the subject line and asks
    # the tree whether it has the rounds it names. Wide from birth.
    #
    # MP-1, 18 Oct 2026: this comment said PF-1, which is the 5 October
    # picker-lazy round. The pre-flight carried that name for an hour
    # before the collision was found; the register was corrected and
    # this was missed.
    'test_preflight.py',
    # MH-1, 18 Oct 2026 - the Meal Plans user guide. Seven tabs, and a
    # Help button on five screens that had none. Wide from birth.
    'test_meal_help.py',
    # MN-1, 18 Oct 2026 - release 3. The calendar IS the plan: MealEntry
    # replaces three tables and the planner replaces seven screens.
    # Wide from birth.
    'test_planner.py',
    # RT-1, 18 Oct 2026 - the retired register. Wide from birth: it
    # reads every suite in this list and asks each one whether it names
    # a page the tree no longer has.
    'test_retired.py',
    # MW-1, 19 Oct 2026 - release 3, push 2. The week moves. Wide from
    # birth: section 7 asks every page in both template roots whether
    # any of them grew a second copy of these three dialogs.
    'test_meal_week.py',
    # MO-1, 19 Oct 2026 - release 3, push 2. The day speaks. Wide from
    # birth: it asks every page in both roots whether any of them grew
    # a second copy of the two dialogs.
    'test_meal_day.py',
    # NF-1, 19 Oct 2026 - the name check reads the tree. Wide by
    # nature: the thing it tests is a walk of the toolchain.
    'test_name_free.py',
    # MH-3, 19 Oct 2026 - the guide catches up with the week. Wide
    # from birth: the promise gate reads every tab of the module.
    'test_meal_guide3.py',
    # MC-4's test_mini_grid.py was HERE - retired by MV-2, 19 Oct
    # 2026, with the component it judged.
    # PK-1, 19 Oct 2026 - the picker is a grid, and it filters by
    # course. Wide from birth: section 5 asks every page in both
    # roots whether any other one grew a copy of the filter strip.
    'test_picker_grid.py',
    # GS-1, 19 Oct 2026 - test_print_queries out of the pool. Its
    # section 4 re-derives the contended signature across every
    # suite, the way test_gate_speed does for the planters.
    'test_gate_serial.py',
    # MX-1, 19 Oct 2026 - the three dead models leave models.py and
    # 0101 drops their tables. Section 3 walks both template roots and
    # every view, url and admin file looking for a reader.
    'test_meal_drop.py',
    # PF-2, 19 Oct 2026 - Demetri's finding. The picker filters by
    # five things because the library already did, and they share one
    # function rather than two implementations in two languages.
    'test_pick_filter.py',
    # MV-1, 19 Oct 2026 - three zoom levels on one calendar, after
    # Demetri said the daily list was not required and asked for the
    # Monthly Calendar first, full page.
    'test_view_switch.py',
    # MV-2, 19 Oct 2026 - the month is the view. Section 4 walks every
    # page in both roots asking whether any other one still names a
    # mini-calendar class, because this round deleted the component.
    'test_month_view.py',
    # MV-3, 19 Oct 2026 - seven columns at full size, a day strip on a
    # phone. Section 3 measures the page height both ways, which is
    # the claim Demetri actually made.
    'test_week_cols.py',
    # MV-4, 19 Oct 2026 - one day card instead of seven, and the Day
    # view's own nav. Section 3 renders all three views and counts.
    'test_day_view.py',
    # RD-1, 19 Oct 2026 - the recipe modal and the shared read behind
    # it. Section 3 replays the block it replaced beside the helper
    # the rest of the package asks, over every ingredient.
    'test_recipe_modal.py',
    # RW-1, 19 Oct 2026 - and then the sum itself, in grams. The five
    # quantities it repairs are in the suite as cases, with the true
    # weight beside what the page used to show.
    'test_recipe_weight.py',
    # PB-2, 19 Oct 2026 - the regression push 1 shipped: eleven
    # redirects that kept the date and dropped the view.
    'test_planner_back.py',
    # RD-2, 19 Oct 2026 - the chip menu, and the move behind it.
    # Leftovers travel with their parent and cannot overtake it.
    'test_chip_menu.py',
    # MB-2, 19 Oct 2026 - the date bar, on celebration_calendar's
    # shape. Measured against the switcher it sits under.
    'test_month_bar.py',
    # WC-1, 19 Oct 2026 - the same gesture in Month and Week.
    'test_week_click.py',
    # DC-1, 19 Oct 2026 - the Day card on one line, with the tags the
    # planner was already fetching and never showing.
    'test_day_card.py',
    # PS-1, 19 Oct 2026 - the picker adds on click and stays open,
    # and shows the day so a mis-click can be undone.
    'test_picker_stays.py',
    # DB-1, 20 Oct 2026 - 88 rules come back out of a media query that
    # was never closed, and a suite starts asking what media a rule is
    # actually in.
    'test_date_bar.py',
    # CL-1, 20 Oct 2026 - the chip is a pill, and a later stylesheet
    # stops overruling the rule that draws it.
    'test_chip_pill.py',
    # RL-1, 20 Oct 2026 - a guard that asked "is jQuery here" when it
    # meant "will it be", and bound nothing for a day.
    'test_pick_reload.py',
    # PB-3, 20 Oct 2026 - the half of PB-2 that PB-2 said it was not
    # doing: the DATE a write returns you to.
    'test_back_date.py',
    # RD-3, 20 Oct 2026 - the photograph opens the recipe, and a
    # second recipe dialog that nobody could open goes out with it.
    'test_quick_look.py',
    # AP-1, 20 Oct 2026 - a recipe goes on a day from the library,
    # and base learns a toast.
    'test_add_planner.py',
    # FV-1, 20 Oct 2026 - the heart could not post for anybody who
    # may not edit recipes, because the token was behind that.
    'test_fav_token.py',
    # LO-1, 20 Oct 2026 - leftovers join the chip menu, so the verb
    # is reachable from every view rather than one.
    'test_chip_left.py',
    # NT-1, 20 Oct 2026 - and a note joins the picker, which is the
    # dialog that adds things to a day.
    'test_pick_note.py',
    # SL-7, 20 Oct 2026 - the shopping list range follows the view,
    # decided in one place rather than spelled in the markup.
    'test_list_range.py',
    # CE-1, 20 Oct 2026 - a suite stops writing into the tree it is
    # being run against, which cost a whole sweep.
    'test_ce_scratch.py',
    # PP-1, 20 Oct 2026 - the plan on paper, which the application
    # could not do at all.
    'test_print_plan.py',
    # MH-5, 20 Oct 2026 - the guide describes the calendar that is
    # there, rather than the one that was there on 19 October.
    'test_meal_guide5.py',
    # SC-1, 21 Oct 2026 - a label that disagreed with its own value.
    'test_say_today.py',
    # BO-1, 21 Oct 2026 - the planner bar in house order.
    'test_bar_first.py',
    # WT-1, 21 Oct 2026 - a row and the pills on it, told apart.
    'test_week_band.py',
    # SH-2, 21 Oct 2026 - one bar per page, and the range under it.
    'test_sl_range_row.py',
    # MG-1, 21 Oct 2026 - a page that writes a message can show one.
    'test_msg_bar.py',
    # HP-1, 21 Oct 2026 - a control nobody on a phone could reach.
    'test_help_phone.py',
    # BA-1, 21 Oct 2026 - the instrument that could not see the bar.
    'test_bar_audit.py',
    # CP-2, 21 Oct 2026 - Copy and Saved Menus, reachable at last.
    'test_copy_menus.py',
    # RG-1, 21 Oct 2026 - a printed day that was a week.
    'test_print_shape.py',
    # RG-2, 21 Oct 2026 - the range, and the second press explained.
    'test_print_range.py',
    # WF-1, 21 Oct 2026 - the fourth fill, found at the second ask.
    'test_week_fill.py',
    # RG-3, 21 Oct 2026 - a sheet as tall as what is on it.
    'test_print_compact.py',
    # PX-2, 21 Oct 2026 - the upscale done once, properly, here.
    'test_photo_floor.py',
    # BM-1, 21 Oct 2026 - the message bar, once, in base.
    'test_msg_base.py',
    # MN-2, 21 Oct 2026 - a menu is a span, and it lands where you say.
    'test_menu_range.py',
    # RO-1, 21 Oct 2026 - a day dragged into the order you want.
    'test_day_order.py',
    # VR-1, 21 Oct 2026 - the schedule readout, measured onto tokens.
    'test_recipe_tidy.py',
    # HG-1, 22 Oct 2026 - the guide and the page agree, both ways.
    'test_help_agrees.py',
    # WD-1, 22 Oct 2026 - the week drags too.
    'test_week_drag.py',
    # DP-1, 22 Oct 2026 - and the push finds out whether it deployed.
    'test_deploy_probe.py',
    # SD-1, 22 Oct 2026 - a rebuild replaces rather than accumulates.
    'test_photo_rebuild.py',
    # CF-1, 22 Oct 2026 - the configuration says what it really is.
    'test_config_truth.py',
    # WN-1, 22 Oct 2026 - the workspace list is two queries, not N.
    'test_ws_prefetch.py',
    # LK-1, 22 Oct 2026 - a killed planter leaves a lock behind.
    'test_planter_lock.py',
    # SB-2, 22 Oct 2026 - one primary on the shopping bar.
    'test_shop_bar2.py',
    # SI-1, 22 Oct 2026 - a copied recipe does not share its photo.
    'test_shared_image.py',
    # NL-1, 22 Oct 2026 - a generated name fits the column.
    'test_name_width.py',
    # PT-1, 22 Oct 2026 - the print sheet knows which view sent it.
    'test_print_origin.py',
    # RV-1, 23 Oct 2026 - the receipt has a screen for its record.
    'test_receipt_view.py',
    # IR-1, 23 Oct 2026 - one register for one kind of identifier.
    'test_ref_link.py',
    # ES-1, 23 Oct 2026 - the e-signing envelope and its audit trail.
    'test_esign_model.py',
    # ES-2, 23 Oct 2026 - the page images and the appended seal.
    'test_esign_pdf.py',
    # UO-1, 23 Oct 2026 - SI-1's rule reaches the lease and the deed.
    'test_upload_order.py',
    # CF-2, 23 Oct 2026 - one requirements file, not four.
    'test_one_list.py',
    # WK-1, 23 Oct 2026 - the sweep can be told its own width.
    'test_push_workers.py',
    # ES-3a, 23 Oct 2026 - the envelope register and the fourth tile.
    'test_lease_signing.py',
    # T2-1, 24 Oct 2026 - a tenancy can hold two people.
    'test_second_tenant.py',
    # T2-2, 24 Oct 2026 - and the screens that show the second one.
    'test_tenant_screens.py',
    # T2-3, 24 Oct 2026 - Generate reads the record and writes back.
    'test_generate_second.py',
    # T2-4, 24 Oct 2026 - sixteen screens name a joint tenancy one way.
    'test_report_names.py',
    # T2-5, 24 Oct 2026 - a joint tenant gets the invoice.
    'test_invoice_recipients.py',
    # PG-2, 24 Oct 2026 - the pre-flight can see a round name with a
    # digit in it, and check_gates catches a date mark that wraps.
    'test_preflight_names.py',
    # ES-2a, 24 Oct 2026 - a re-seal lands where the last one did.
    'test_sealed_name.py',
    # T2-6, 24 Oct 2026 - the contact person is a Company field.
    'test_contact_company.py',
    # PG-3, 24 Oct 2026 - the gate does not walk a virtualenv.
    'test_gate_walk.py',
    # T2-7, 24 Oct 2026 - the second tenant has contact details.
    'test_joint_contact.py',
    # ES-4, 24 Oct 2026 - a lease can be read and signed.
    'test_lease_sign.py',
    # ES-3b, 24 Oct 2026 - an envelope can be made.
    'test_send_lease.py',
    # T2-8, 25 Oct 2026 - one email address per person.
    'test_one_email.py',
    # ES-5, 25 Oct 2026 - what happens to an envelope after it is sent.
    'test_signing_lifecycle.py',
    # ES-6, 25 Oct 2026 - a signed lease is approved onto its tenant.
    'test_lease_approval.py',
    # ES-6b, 25 Oct 2026 - every drawn signature is blue.
    'test_blue_ink.py',
    # ES-6c, 25 Oct 2026 - a second tenant signs only when there is one.
    'test_second_signer.py',
    # ES-7, 25 Oct 2026 - his signature and the stamp; the address.
    'test_house_marks.py',
    # ES-7b, 25 Oct 2026 - deleting an envelope, superuser only.
    'test_envelope_delete.py',
    # ES-8, 25 Oct 2026 - Lease Signing finished.
    'test_signing_finish.py',
    # HK-1, 26 Oct 2026 - Release 19 housekeeping.
    'test_housekeeping.py',
]

# Passed the experiment, but walk the REPO, not the template directory.
# They already see every file there is; pointing them at the template tree
# would NARROW them.
ALREADY_WIDE = ['test_banner_pages.py',
                'test_standards_block.py',
                # Walks the repo for .py, not the template
                # roots: it censuses every Anthropic call
                # site, and one of those can be written in
                # any file. Pointing it at the template
                # tree would blind it. [R1]
                'test_ai_models.py',
                # TL-1, 4 Oct 2026 - same shape, same reason. It binds
                # every call made by bare name under pages/ against the
                # signature it reaches, so what it needs is every .py
                # there is. A template root would hide the views.
                'test_greek_arity.py',
                # LU-1, 5 Oct 2026 - it counts @login_required decorators,
                # which live in .py and in no template at all. A template
                # root would see none of them.
                #
                # AND IT IS NOT REPO-WIDE EITHER, which is the part worth
                # writing down. Walked over the whole repo the census
                # returns 307 rather than 282, because nine apply_*.py
                # patchers carry the decorator inside the text they
                # INSERT. Those are tooling, not views, and counting them
                # would overstate the thing the round is about. So it
                # walks pages/ and crs/ - the two Django apps - and that
                # narrowing is a stated position, not an oversight.
                'test_login_url.py',
                # PH-1, 5 Oct 2026 - it asks whether any VIEW or FORM
                # reads the new .holder key yet, and views and forms are
                # .py. alv_tree.templates() returns templates, so a
                # template root would answer "no" by being unable to
                # look. It walks pages/ and skips migrations and
                # __pycache__, which is the same stated narrowing
                # test_login_url makes two entries above.
                'test_passport_holder.py',
                # B-1, 5 Oct 2026 - its templates come from templates()
                # like everyone else's. The root it builds is for .py:
                # section 3 follows every non-browser render path in the
                # tree - render_to_string, render_to_pdf, get_template -
                # to the template it renders, and requires that template
                # to be standalone. Those calls live in views, which are
                # .py, so a template root would find no render paths at
                # all and the check that keeps a var() out of a PDF
                # would pass by being unable to look. It walks pages/,
                # the same stated narrowing as the three entries above.
                'test_colour_tokens.py']

# FAILED with CRS in the tree, against the round that will fix the module
# and let the suite be widened. Their narrow root is a stated position,
# not an oversight. Each entry comes off this list in the round it names.
WAITING = {
    'test_button_sweep.py':
        'pages  narrow BY DESIGN - its MARKUP walk rebuilds a '
        'pre-sweep tree from .bak_btnsweep, so widening it would '
        'copy the second template root into a tree the sweep never '
        'covered. 117 in the markup scope against 151 in the '
        'tree, and that gap is a stated position. Its <script> '
        'census is NOT narrow: E11 gave that its own corpus of 142 '
        'pages, because a census that reports what is LEFT cannot '
        'have a scope. [reason replaced E11, 13 Oct 2026 - the 117 '
        'has not moved, but it was called the tool census and there '
        'are now two censuses with two numbers. Replaced E-10, 11 '
        'Oct 2026 - it said 120 and 146, and both numbers had moved]',
    'test_surface_deep.py':
        'pages  F2b took the 78 border uses on 13 Oct, so the DECISION is '
        'no longer what holds it. WIDENING is: as_left_by hands it second-root '
        'backups F2a never had a claim on - 6 phantom backgrounds and '
        '15 phantom borders - and BL-2 scoped reader fixes those but '
        'moves LEFT_BORDERS 93 to 56 and LEFT_CUSTOM 3 to 1. Both pins '
        'need re-deriving. [reason replaced F2b, 13 Oct 2026]',
}

# FAILED the experiment WITHOUT walking a template root of its own - so
# widening is not a question this suite has.
#
#   test_dead_files.py walks the string 'pages' (it hunts unreferenced
#   FILES, not templates) and separately RUNS test_panel_title.py as a
#   subprocess, asserting it fails. Under the experiment that subprocess
#   inherited the patch, so what moved was the other suite's verdict, not
#   this one's census. It is listed so that it is accounted for rather
#   than looking like an omission, and it comes off when X-panel lands.
WAITING_INDIRECT = {
    'test_dead_files.py': 'it runs test_panel_title and reads ITS verdict; its own walk '
                          'is over pages/, not pages/templates',
}


# MENTIONS os.walk WITHOUT WALKING ANYTHING - the fifth category, and it
# exists because X0's net is deliberately crude and should stay that way.
#
#   Section 3 of test_tree_roots.py finds every walking suite with a plain
#   substring test, `'os.walk(' in text`, and fails if one is on none of
#   these lists. That crudeness is the point: a census built in a shape
#   nobody has thought of yet still lands in the net. X0's own detector
#   was once too clever and went blind to a list of roots.
#
#   test_waiting_down.py carries the words in two string LITERALS - the
#   detector it borrows from X0, and a CONTROL asserting that detector
#   finds a narrow walk. It never calls os.walk; its own suite proves that
#   from the parse tree, not by reading itself. Tightening the substring
#   test to spare it would have traded a real net for a comfortable one,
#   so the exception is named here instead.
MENTIONS_ONLY = {
    'test_waiting_down.py': 'X11  the words are in two string literals - a '
                            'borrowed detector and the CONTROL that proves '
                            'it works. No os.walk call in the parse tree.',
    'test_house_title.py': 'G3a  the same shape, one round later. It lifts '
                           'the detector out of X0 and runs it against four '
                           'CONTROL strings - one of which is a walk of a '
                           'template root, because the whole point is that '
                           'the detector still sees a real one. It reads the '
                           'tree through alv_tree and calls os.walk nowhere.',
}


# THE CRS MODULE'S OWN PROGRESS, for the same reason the lists above
# exist: a count written as a literal in one round's suite is a count the
# NEXT round breaks. X1 asserted "the other 7 CRS pages still carry the
# local palette"; X2 made it 6, and X1's suite failed - correctly, and
# uselessly, because the thing it was guarding had not regressed.
#
# So the suites assert against this list instead of a number. A round
# that finishes a page adds it here, and every CRS suite keeps passing
# without any of them being edited.
CRS_HOUSE = [
    'crs/country_list.html',    # X1 - list, row actions, empty, view modal
    'crs/country_form.html',    # X2 - the Add / Edit entry screen
    'crs/fi_list.html',         # X3 - the Reporting FI list and view modal
    'crs/fi_form.html',         # X4 - the Add / Edit FI screen and IN editor
    'crs/index.html',           # X5 - the hub: panel KEPT, and retoned
    'crs/submission_list.html', # X6 - the Submissions list and its badges
    'crs/submission_start.html',  # X7 - the Start Submission entry screen
    'crs/submission_detail.html',  # X8 colour, X9 sections+tables, X10 rest
]


def crs_pages(base=None):
    """Every CRS template, by its rel() label."""
    return sorted(rel(p, base) for p in templates(base)
                  if (os.sep + 'crs' + os.sep + 'templates' + os.sep)
                  in os.path.abspath(p))


def crs_outstanding(base=None):
    """The CRS pages that have not had their round yet."""
    return [n for n in crs_pages(base) if n not in CRS_HOUSE]


def code_only(text):
    """Markup with every comment blanked, line for line, so a gate reads
    CODE and not the record of code.

    ALL THREE SYNTAXES, AND THE CSS ONE ONLY WHERE IT IS A COMMENT.
    A template carries Django comments, HTML comments and CSS/JS block
    comments. An instrument that strips two of the three reads prose as
    code - that lesson cost four rounds. This one strips all three, and
    strips the block syntax ONLY inside <style> and <script>, which is
    the other half of the same lesson:

        `/*` IS NOT A COMMENT OPENER IN MARKUP.

    accept="image/*" puts one inside an attribute value, and blanking
    from there to the next `*/` anywhere in the file costs:

        passport_management.html   3,362 characters - 94 lines of the
                                   Add Passport form, five inputs, the
                                   Holder field and the file upload
        edit_asset.html              881
        property_assets.html         806

    SG-2's gate reported a class as absent on property_assets while grep
    found it on line 355. That is what this is.

    BLANKED LINE FOR LINE, not merely to the same length. A comment that
    spans lines must leave its newlines behind, or every line number a
    gate reports after it is wrong - and gates in this tree report line
    numbers.

    For PYTHON source see python_code_only in the suites that scan .py
    files: it is a different job on a different language and it used to
    share this name.                                 [CO-1, 3 Oct 2026]
    """
    def blank(m):
        return re.sub(r'[^\n]', ' ', m.group(0))

    text = re.sub(r'<!--.*?-->', blank, text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', blank, text, flags=re.S)

    def inner(m):
        return (m.group(1)
                + re.sub(r'/\*.*?\*/', blank, m.group(2), flags=re.S)
                + m.group(3))

    return re.sub(r'(<(?:style|script)\b[^>]*>)(.*?)(</(?:style|script)>)',
                  inner, text, flags=re.S)


def code_only_js(text):
    """code_only, plus the // line comments inside a <script>.

    Three suites need this and the rest must not have it: // inside an
    https:// URL is not a comment, and an href is not a script.
                                                     [CO-1, 3 Oct 2026]
    """
    text = code_only(text)

    def inner(m):
        body = re.sub(r'(?m)^([ \t]*)//.*$',
                      lambda x: x.group(1) + ' ' * (len(x.group(0))
                                                    - len(x.group(1))),
                      m.group(2))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<script\b[^>]*>)(.*?)(</script>)', inner, text,
                  flags=re.S)



def python_code_only(text, payloads=True):
    """Python with its comments AND its docstrings blanked, line for line.

    THE PYTHON TWIN OF code_only, and it arrives late: nine private
    copies under four names and three algorithms had accumulated by
    13 Oct, and every one of the three was wrong.

        the regex one      blanked EVERY triple-quoted string, so a
                           patcher's payload - 1,540 lines in
                           apply_auth_flow - read as prose; and it
                           missed trailing comments entirely, because
                           `^[ \t]*#.*$` only matches a comment that
                           owns its line
        the tokeniser one  dropped a STRING whenever the previous token
                           was a line break, so every key in a
                           multi-line dict literal vanished
        the third          did not touch docstrings at all

    A STRING IS A DOCSTRING WHEN IT IS THE WHOLE STATEMENT: bracket
    depth 0, preceded by a statement boundary, and followed by NEWLINE.
    All three conditions are load-bearing. Requiring NEWLINE alone fixes
    the dict keys and breaks the module docstring of every file that
    opens with a coding comment, because that STRING is then preceded by
    NL. Depth is what tells an NL inside brackets from one between
    statements.

    `payloads` is not a bug fix, it is a second question. A gate asking
    "what does this code DO" needs a triple-quoted payload to survive; a
    census asking "does THIS FILE walk a narrow root" must not count a
    walk written into a string. With payloads=False the census
    reproduces, file for file, what the old regex reported - minus one
    false positive it had been carrying.

    For MARKUP see code_only and code_only_js above. This is a different
    job on a different language, and it used to share their name.
                                                      [E15, 13 Oct 2026]
    """
    lines = text.split('\n')
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except Exception:
        # A file that will not tokenise is returned whole rather than
        # half-blanked. A stripper that silently mangles unparsable
        # source is worse than one that declines.
        return text
    opens, closes = {'(', '[', '{'}, {')', ']', '}'}
    bound = (tokenize.NEWLINE, tokenize.NL, tokenize.COMMENT,
             tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING)
    kill, depth, prev = [], 0, None
    for i, tok in enumerate(toks):
        if tok.type == tokenize.OP:
            if tok.string in opens:
                depth += 1
            elif tok.string in closes:
                depth -= 1
        drop = tok.type == tokenize.COMMENT
        if tok.type == tokenize.STRING:
            nxt = toks[i + 1].type if i + 1 < len(toks) else None
            doc = (depth == 0 and (prev is None or prev in bound)
                   and nxt == tokenize.NEWLINE)
            triple = tok.string.lstrip('rbufRBUF')[:3] in ('"""', "'''")
            drop = doc or (not payloads and triple)
        if drop:
            (r1, c1), (r2, c2) = tok.start, tok.end
            for r in range(r1, r2 + 1):
                a = c1 if r == r1 else 0
                b = c2 if r == r2 else len(lines[r - 1])
                kill.append((r - 1, a, b))
        prev = tok.type
    # BLANKED LINE FOR LINE, not merely to the same length - the same
    # rule code_only follows, and for the same reason: gates in this
    # tree report line numbers.
    for r, a, b in kill:
        ln = lines[r]
        lines[r] = ln[:a] + ' ' * (b - a) + ln[b:]
    return '\n'.join(lines)

def house_filter_pages(base=None):
    """Every page carrying the house filter: a Filter button AND the panel.

    OUTSTANDING ITEM 4, CLOSED - CN-1, 3 Oct 2026. Four suites each typed
    this number. FL-1 and UC-2 took the tree from fifteen filtered pages
    to eighteen and all four went red at once, which is the third time
    this list has moved and the first time anyone has had to change four
    files to record it.

    The function itself is lifted unchanged from test_filters_in_rc.py,
    which has derived it correctly since 2 Oct while the suites beside it
    went on typing a digit. Its own note said where this belonged:
    "outstanding item 4 is about where the NUMBER lives, not about
    loosening any of them."

    MARKUP ONLY. A page NAMING .alv-filter in a comment or a stylesheet
    does not carry one - a gate reads code, not the record of code - so
    <style>, <script> and HTML comments come out before looking. base is
    excluded: it DEFINES the control and wears none.
    """
    out = []
    for p in templates(base):
        if os.path.basename(p) == 'base.html':
            continue
        with open(p, encoding='utf-8', errors='replace') as fh:
            s = fh.read()
        s = re.sub(r'<style\b.*?</style>', '', s, flags=re.S)
        s = re.sub(r'<script\b.*?</script>', '', s, flags=re.S)
        s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
        if 'action-filter' in s and 'alv-filter' in s:
            out.append(rel(p, base))
    return sorted(out)


def standalone(base=None):
    """Templates that do NOT extend base.html, so base cannot reach them.

    CS-2, 5 Oct 2026. Found while measuring DR-2a: CS-1's drift census
    reported six declarations on manual_pdf.html as a page beating base's
    stylesheets with a different value. It is not. manual_pdf is rendered
    by render_to_string and handed straight to xhtml2pdf - it never sees
    a browser and it never sees base. It has no choice but to style
    itself, and a census that compares it against a stylesheet which is
    not in the document is comparing against nothing.

    TWELVE OF THEM, and they are not an accident. PDF bodies, an email
    body, a modal shell, detail fragments injected into a page that
    already has base, and the connectivity error page, which has to
    render when the database is down and so cannot afford a parent
    template that queries it.

    THE TEST IS THE TAG, NOT A LIST. A list would need editing every time
    a page is added, and the thing that makes a page standalone is
    exactly that it has no {% extends %}. Read off the markup with the
    comments stripped, because a page explaining in a comment that it
    does not extend base is still not extending base.

    base.html itself is not standalone - it is the thing not extended -
    and is excluded.
    """
    out = []
    for p in templates(base):
        if os.path.basename(p) == 'base.html':
            continue
        with open(p, encoding='utf-8', errors='replace') as fh:
            s = code_only(fh.read())
        if not re.search(r'\{%\s*extends\b', s):
            out.append(rel(p, base))
    return sorted(out)


def inherits_base(path, base=None):
    """Does this one template get base's stylesheets at all?"""
    return rel(path, base) not in standalone(base)


def rel(path, base=None):
    """A stable, printable label for a template.

    'properties.html', 'projects/project_task_list.html', 'crs/index.html'
    - the path below its own root, with forward slashes whatever the
    platform. Suites print this rather than an absolute path, so their
    output reads the same on the laptop and in the sandbox, and so a CRS
    page is immediately recognisable as one.
    """
    ap = os.path.abspath(path)
    for r in roots(base):
        if ap.startswith(r + os.sep):
            return os.path.relpath(ap, r).replace(os.sep, '/')
    return os.path.basename(ap)
