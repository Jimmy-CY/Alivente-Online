# -*- coding: utf-8 -*-
"""alv_rounds.py - the file as a round LEFT it.

Most suites check that their round changed exactly what it said it would:
the file now is its backup plus the change. A later round that edits the
same file breaks that check, although nothing is wrong - it has done its
own job. Four rounds on 21 Sep each had to patch older suites by hand for
exactly this, one at a time, and the laptop's gate found each of them.

The answer is the same every time. The file as round R left it is the
BACKUP TAKEN BY THE FIRST LATER ROUND that touched it - that backup is,
by definition, the file just before that later round began. If no later
round touched it, it is the file as it is now.

ROUNDS is that order, oldest first. A new round appends its backup suffix
here, once, and every suite that asks as_left_by() keeps judging only its
own round without being edited.
"""
import os

ROUNDS = [
    '.bak_zoomguard',
    '.bak_smallctl',
    '.bak_printq',
    '.bak_printbtn',
    '.bak_divbal',
    '.bak_histpurge',
    '.bak_modalhead',
    '.bak_eimodal',
    '.bak_reporthead',
    '.bak_appliesfrom',
    '.bak_oldrounds',
    '.bak_stddoc',
    '.bak_csmall',
    '.bak_tap',
    '.bak_chip',
    '.bak_quad',
    '.bak_lease',
    '.bak_dead',
    '.bak_three',
    '.bak_rowact',
    '.bak_field',
    '.bak_series',
    '.bak_modal',
    '.bak_backlabel',
    '.bak_horizon',
    '.bak_avatar',
    '.bak_contrast',
    '.bak_pershead',
    '.bak_purple',
    '.bak_actionbar',
    '.bak_namedbars',
    '.bak_palette',
    '.bak_linesoft',
    '.bak_accentink',
    '.bak_surfdeep',
    '.bak_pagetitle',
    '.bak_bartop',
    '.bak_reqmarker',
    '.bak_personalteal',
    '.bak_celebrations',
    '.bak_bodybacks',
    '.bak_barmobile',
    '.bak_tablepersonal',
    '.bak_rowpersonal',
    '.bak_tablepreview',
    '.bak_tablebreakdown',
    '.bak_househeader',
    '.bak_hubbar',
    '.bak_goodwarn',
    '.bak_moremenu',
    '.bak_subtree',
    '.bak_morecss',
    '.bak_lastmenu',
    '.bak_walk1',
    '.bak_walk2',
    '.bak_filtergap',
    '.bak_treeroots',
    '.bak_crscountry',
    '.bak_crsform',
    '.bak_crsfi',
    '.bak_crsfiform',
    '.bak_crshub',
    '.bak_crssub',
    '.bak_crsstart',
    '.bak_crsdetc',
    '.bak_crsdets',
    '.bak_crsdetr',
    '.bak_waitdown',
    '.bak_crscomment',
    '.bak_celfilter',
    '.bak_futuretab',
    '.bak_celaz',
    '.bak_filterbox',
    '.bak_zoommk',
    '.bak_tabedge',
    '.bak_evtone',
    '.bak_msgbar',
    '.bak_ctlaccent',
    '.bak_countdown',
    '.bak_recfilter',
    '.bak_recchips',
    '.bak_crspill',
    '.bak_applyclose',
    '.bak_housetitle',
    '.bak_subh5',
    '.bak_filterframe',
    '.bak_retone',
    '.bak_reportback',
    '.bak_rowform',
    '.bak_statsfold',
    '.bak_leasefilter',
    '.bak_nonecols',
    '.bak_reportarrow',
    '.bak_fieldadd',
    '.bak_projtable',
    '.bak_dashback',
    '.bak_livesearch',
    '.bak_barstretch',
    '.bak_secscope',
    '.bak_tasktable',
    '.bak_searchhint',
    '.bak_analysisorder',
    '.bak_detailpills',
    '.bak_projpills',
    '.bak_stats3up',
    '.bak_authflow',
    '.bak_filterget',
    '.bak_pwnotify',
    '.bak_loginemail',
    '.bak_filtersinrc',
    '.bak_importmodel',
    '.bak_aeline',
    '.bak_filterdistinct',
    '.bak_tabs',
    '.bak_plicon',
    '.bak_jsescape',
    '.bak_issuestats',
    '.bak_barorder',
    '.bak_compactcard',
    '.bak_jshandlers',
    '.bak_btntone',
    '.bak_sentinels',
    '.bak_mealrow',
    '.bak_favtag',
    '.bak_leaserule',
    '.bak_tenantpast',
    '.bak_favnote',
    '.bak_ingfilter',
    '.bak_renewalwin',
    '.bak_convpills',
    '.bak_fixedpop',
    '.bak_printguard',
    '.bak_shopbar',
    '.bak_shoptone',
    '.bak_mealbtn',
    '.bak_recipebar',
    '.bak_popscroll',
    '.bak_seccomment',
    # Section MC, 3 Oct 2026 - the Meal Plans / Calendar programme.
    # ORDER IS CHRONOLOGICAL AND LOAD BEARING: MC-1 moved the switch,
    # MC-2 converted the two action strips, MC-3 swept what was left.
    # MC-3 reads MC-2's output on the same file, so a swap here would
    # make as_left_by hand a round the wrong text.
    '.bak_viewseg',
    '.bak_calactions',
    '.bak_caltone',
    '.bak_emailrev',
    # TC-1. A FIXTURE REPAIR, NOT A PRODUCT CHANGE - the password
    # reset boundary was measuring the suite's own runtime, and only
    # said so with six processes on the machine. No suite of its own:
    # the fixture it repairs, test_auth_flow.py, is the suite.
    '.bak_tokclock',
    # Section FG / FL / UC / SG, 3 Oct 2026 - the filter programme
    # finished and the last hand-rolled segmented controls taken.
    # ORDER IS LOAD BEARING: FG-1 puts the capped track list in base
    # and FL-1 and UC-2 inherit it - a panel built before FG-1 lands
    # stacks its fields one per row at the full width of the panel.
    '.bak_filtergrid',
    '.bak_reffilter',
    '.bak_convfilter',
    '.bak_plseg',
    # The three repair rounds this bundle needed. None has a suite of
    # its own: each one REPAIRS existing suites, so those suites are
    # the test. ORDER IS LOAD BEARING - PM-1 moves pins onto what
    # PN-1 left, and PN-1 reads the classifier CN-1 did not touch.
    '.bak_filtercensus',
    '.bak_noprimary',
    '.bak_movedpins',
    # Section CO, 3 Oct 2026 - code_only had been written out at module
    # level in 47 files, and 45 of them read `/*` as a comment opener in
    # MARKUP. accept="image/*" put one inside an attribute value and the
    # blanking ran to the next */ anywhere in the file: 94 lines of the
    # Add Passport form were invisible to every gate in this tree. It
    # lives in alv_tree now. The two that read PYTHON source are
    # python_code_only - a different job on a different language that
    # happened to share a name.
    '.bak_codeonly',
    # Section LZ / IB / MB / MP / BK / DD, 3 Oct 2026 - the walkthrough
    # bundle: the Calendar hang, the Category filter that was never
    # rendered, the phone action bar, the meal plan form bar, Back to the
    # Calendar, and the dropdown a table was clipping.
    # ORDER IS LOAD BEARING: IB-2 moves the script and MB-1 then writes
    # CSS into the same page; BK-1 edits the Back control MP-2 relabels.
    '.bak_lazyimg',
    '.bak_stranded',
    '.bak_donebadge',
    '.bak_mealbartop',
    '.bak_fromcal',
    '.bak_escapedrop',
]


def as_left_by(path, suffix, read):
    """The text of `path` as the round whose backups end in `suffix` left
    it - the earliest later round's backup of it, or the file itself.

    A round in ROUNDS is placed by the list. A round OLDER than the list
    is placed by its backups' times: see later_backup()."""
    if suffix in ROUNDS:
        for s in ROUNDS[ROUNDS.index(suffix) + 1:]:
            if os.path.isfile(path + s):
                return read(path + s)
        return read(path)
    return read(later_backup(path, suffix) or path)


def later_backup(path, suffix):
    """For a round older than ROUNDS: of the file's backups, the one
    written FIRST AFTER this round's own - by modification time, which is
    when the next round saved the file before touching it, so its content
    is the file exactly as this round left it. None when no later round
    touched the file (the file itself is then the answer), or when this
    round left no backup to date it by."""
    own = path + suffix
    if not os.path.isfile(own):
        return None
    return backup_after(path, os.path.getmtime(own), own)


def backup_after(path, when, skip=None):
    """The file's first backup written after `when`, or None."""
    folder, name = os.path.split(path)
    best = None
    for n in os.listdir(folder or '.'):
        p = os.path.join(folder, n)
        if not n.startswith(name + '.bak_') or p == skip:
            continue
        t = os.path.getmtime(p)
        if t > when and (best is None or t < best[0]):
            best = (t, p)
    return best[1] if best else None


def as_of(path, when, read):
    """The text of `path` as it stood at time `when` - for a file a round
    READ but did not back up: its first backup written after `when`, or
    the file itself if nothing has touched it since."""
    return read(backup_after(path, when) or path)
