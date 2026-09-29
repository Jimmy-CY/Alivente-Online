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
    'test_accent_ink.py', 'test_action_bar.py', 'test_admin_banner.py',
    'test_admin_headings.py', 'test_admin_repair.py', 'test_applies_from.py',
    'test_avatar.py', 'test_console_encoding.py', 'test_div_balance.py',
    'test_entry_sections.py', 'test_filter_field.py', 'test_filter_gap.py',
    'test_finance_headings.py', 'test_form_components.py',
    'test_house_header.py', 'test_hub_bar.py', 'test_label_fit.py',
    'test_last_menus.py', 'test_map_provider.py', 'test_more_css.py',
    'test_more_menu.py', 'test_named_bars.py', 'test_one_action_bar.py',
    'test_page_title.py', 'test_palette.py', 'test_print_buttons.py',
    'test_report_head.py', 'test_row_personal.py', 'test_secondary_visible.py',
    'test_small_controls.py', 'test_table_admin.py', 'test_tap_target.py',
    'test_zoom_guards.py',
]

# Passed the experiment, but walk the REPO, not the template directory.
# They already see every file there is; pointing them at the template tree
# would NARROW them.
ALREADY_WIDE = ['test_banner_pages.py', 'test_standards_block.py']

# FAILED with CRS in the tree, against the round that will fix the module
# and let the suite be widened. Their narrow root is a stated position,
# not an oversight. Each entry comes off this list in the round it names.
WAITING = {
    'test_accent_shades.py': 'X-hex   CRS keeps #17a2b8 in three pages',
    'test_back_label.py': 'X-bar   CRS writes its own .action-back-label rules',
    'test_bar_top.py': 'X-btn   CRS Back carries btn-success',
    'test_body_backs.py': 'X-btn   the same Back controls',
    'test_button_sweep.py': 'X-btn   24 btn-success/btn-warning across the 8',
    'test_compound_rules.py': 'X-form  4 CRS forms wrap fields in a third name',
    'test_contrast.py': 'X-hex   CRS colour pairs never measured',
    'test_deeper_teal.py': 'X-hex   #17a2b8 again',
    'test_disabled_state.py': 'X-btn   36 CRS buttons the classifier disagrees',
    'test_entry_headings.py': 'X-form  2 CRS forms state no mode line',
    'test_entry_panel.py': 'X-panel .crs-panel is a box of its own',
    'test_heading_components.py': 'X-head  8 CRS pages restyle .page-title-h2',
    'test_heading_prefix.py': 'X-head  4 CRS titles name the brand',
    'test_heading_standard.py': 'X-head  8 CRS pages unaccounted for',
    'test_label_bold.py': 'X-form  2 CRS pages, plain field labels',
    'test_line_soft.py': 'X-hex   CRS line literals',
    'test_modal_heads.py': 'X-modal no CRS modal wears .alv-modal-head',
    'test_panel_title.py': 'X-panel 3 CRS pages declare what base owns',
    'test_print_queries.py': 'X-print a bare max-width clause in CRS',
    'test_projects_heading.py': 'X-head  2 CRS forms unaccounted for',
    'test_req_marker.py': 'X-form  CRS dereferences a selector its markup lacks',
    'test_required_marker.py': 'X-form  4 CRS pages style .req',
    'test_required_sweep.py': 'X-form  1 unmarked required field in CRS',
    'test_save_and_cancel.py': 'X-form  2 CRS forms offer Cancel and Back both',
    'test_small_three.py': 'X-bar   CRS hide rules and Back labelling',
    'test_subtree_tones.py': 'X-count it asserts the walk finds 138; now 146',
    'test_surface_deep.py': 'X-hex   CRS background and border literals',
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
    'test_dead_files.py': 'X-panel it runs test_panel_title and reads its '
                          'verdict; its own walk is over pages/, not '
                          'pages/templates',
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
]


def crs_pages(base=None):
    """Every CRS template, by its rel() label."""
    return sorted(rel(p, base) for p in templates(base)
                  if (os.sep + 'crs' + os.sep + 'templates' + os.sep)
                  in os.path.abspath(p))


def crs_outstanding(base=None):
    """The CRS pages that have not had their round yet."""
    return [n for n in crs_pages(base) if n not in CRS_HOUSE]


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
