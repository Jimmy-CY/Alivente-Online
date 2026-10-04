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
import os
import re

# The tree, in the order Django was told about the apps.
TEMPLATE_ROOTS = [
    (('pages', 'templates'),
     'the main app - every module except CRS'),
    (('crs', 'templates'),
     'the CRS reporting app, mounted at /crs/ by mysite/urls.py'),
]


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
                'test_greek_arity.py']

# FAILED with CRS in the tree, against the round that will fix the module
# and let the suite be widened. Their narrow root is a stated position,
# not an oversight. Each entry comes off this list in the round it names.
WAITING = {
    'test_back_label.py': 'pages  no page defines .action-back-label any more',
    'test_button_sweep.py':
        'pages  its own census says 120 templates, not 146',
    'test_compound_rules.py':
        'pages  one page still wraps its fields in a third name',
    'test_contrast.py': 'pages  colour pairs on the pages side never measured',
    'test_disabled_state.py':
        'pages  12 buttons the classifier disagrees with',
    'test_label_bold.py': 'pages  plain field labels the sweep has not named',
    'test_line_soft.py':
        'pages  the six literals it counts are a pages-side figure',
    'test_modal_heads.py':
        'pages  the Recipe View close strip, recorded but unresolved',
    'test_print_queries.py': 'pages  a bare max-width clause outside base',
    'test_req_marker.py':
        'pages  a selector dereferenced with no markup behind it',
    'test_required_marker.py':
        'pages  a .req RULE survives somewhere, though the markup went',
    'test_small_three.py':
        'pages  a non-Back control still labelled as a Back',
    'test_subtree_tones.py':
        'count  it asserts a walk finds 138; it now finds 146',
    'test_surface_deep.py':
        'pages  background literals survive, and its 93 border uses wait on F2b',
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
