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
    # Section PA, 3 Oct 2026 - Passports. Four lists written out twice
    # each (two of them already on the model, and the two copies had
    # drifted), and a filter panel that reloaded the page on every
    # select. Holder is the Household Members now, which is what the
    # register is for.
    '.bak_passfilter',
    # PA-2, 3 Oct 2026 - the Passports row. Ten Bootstrap badges (five of
    # which drew nothing, because this app never defined badge-primary,
    # badge-dark or badge-secondary) become two pills and three, with
    # every label from the model. One .row-actions wrapper, six hexes on
    # tokens. The mobile action bar is LEFT ALONE - 23 pages use it.
    '.bak_passpills',
    # PA-3, 3 Oct 2026 - PA-1's Holder filter matched NOTHING. It joined
    # HouseholdMember.name to Passport.holder_name, and the two share not
    # one value: the household uses familiar names (Angy) and a passport
    # carries the name printed on the document (Angela Manias). The
    # options are the recorded holders now, so they cannot fail to match
    # the rows they narrow.
    '.bak_passholders',
    # PJ-6, 4 Oct 2026 - the Task List tree on a phone. The depth cue was
    # not weak there, it was GONE: base's card rule writes `border: 1px
    # solid` and `background` as SHORTHANDS later in the cascade, so the
    # 4px type bar and the tint were thrown away and all three cards
    # measured identical. The card steps 14px a level now, the bar is
    # back, and the three colours are the house CATEGORY family.
    '.bak_taskdepth',
    # Section TL, 4 Oct 2026 - the Task List. TL-1 is a LIVE 500: the
    # Greek list called a two-argument stub with three arguments, six
    # times, every one behind `if language == 'greek'` - which is why
    # English worked 100% and Greek never reached the template. The
    # module docstring had recorded it as a "known latent issue" that
    # would "only manifest when re-enabled". It had already manifested.
    '.bak_greekarity',
    # TL-2, 4 Oct 2026 - Demetri: "Within the Task List, if I press to
    # Edit a Task or Subtask, and I then press the Back Button or the
    # Update Task button, then I need to be taken back to the Task List,
    # not the Project." The machinery was there with ONE origin in it -
    # the Gantt chart - and an else branch pointing at the Project, which
    # every link on the Task List fell down. It carries the assignee and
    # the language too: the list you left, not that project's default.
    # ORDER: after PJ-6, which rewrote the same four rows' markup.
    '.bak_taskorigin',
    # CR-1, 4 Oct 2026 - Demetri, of the Generate Task List modal: "I
    # don't like the Blue on the Radio Button." base.html carried ZERO
    # rules naming .custom-control, so bootstrap 4.1.3 had been drawing
    # thirteen controls on three pages in #007bff since the day it was
    # linked. Bootstrap writes that colour THREE times at two
    # specificities and the first build of this round only beat one of
    # them - the radio turned and the checkboxes stayed blue.
    '.bak_customctl',
    # FA-1, 4 Oct 2026 - Demetri, of the Projects filter panel: "The
    # filters are not in line...." He saw one page; measured at 1280 it
    # was TEN of seventeen, and one declaration caused all of them.
    # `align-items: end` aligns the BOTTOMS of the groups, so a select
    # 2px taller than an input parted their tops by 2px and a search
    # HINT under its control parted Projects' by 25. start, and all
    # seventeen measure label top 0, control top 27.
    '.bak_filteralign',
    # RA-1, 4 Oct 2026 - Demetri: "I think that we should put the Delete
    # Action Item on the right hand side of all the icons. We should
    # define a standard order that we place all icons in all tables."
    # LOOK, CHANGE, COPY, ADVANCE, DESTROY - 5 of 21 action columns were
    # out of it. And .icon-view was carrying FOUR pictures, which
    # matters because the order sorts on the NAME: a lease agreement
    # wearing icon-view sorts as "view this record".
    '.bak_rowactorder',
    # AG-1, 4 Oct 2026 - Demetri, of the Outstanding Invoices Report: "I
    # don't like these colours any more. They don't fit within our team
    # and grey theme... I have decided that I don't need a green and red
    # scale. Also, the total outstanding figures must not be in blue."
    # Five hues become one warm neutral deepening through five steps,
    # and the drill-down figure stops being the pencil blue on the
    # desktop and a raw #007bff on the phone.
    '.bak_agetone',
    # Section PD, 4 Oct 2026 - property_detail.html, the last big page the
    # standard never reached: 1,992 lines, 227 local CSS rules, and the
    # action bar the only house component on it.
    # PD-1 takes the palette. SEVEN table headers wore a dark bar - five
    # in #343a40 on the cell, two in #2c3e50 on the ROW, which is why the
    # census found five and the render found the other two. And two COUNTS
    # were drawn as a green pill and a red pill, one of them a hex written
    # on the element.
    '.bak_pdpalette',
    # PD-2, 4 Oct 2026 - the seven tables come to base. The page had
    # REBUILT base's phone card by hand: 23 of the 35 table rules in its
    # phone block were declaration-for-declaration what .alv-table says,
    # and every one of the seven already carried data-label on every
    # cell, which is the only reason this was a class change rather than
    # a rewrite. ORDER: after PD-1, whose consolidated header rule this
    # round deletes outright once base owns the header.
    '.bak_pdtables',
    # Section CS, 4 Oct 2026 - base.html's component stylesheet moves out
    # of the body and into the head. It sat AFTER {% block content %}, so
    # in the rendered document it came later than every page's own CSS and
    # beat it at equal specificity. Eleven pages wrote their own
    # .filter-grid columns and all eleven were dead - which is what
    # Demetri photographed on Actual Expenses. The move also hands back 57
    # stale declarations that earlier rounds tokenised in base and left
    # standing in the pages, so CS-1 prunes those in the same breath.
    # FIRST IN THIS BUNDLE: it changes which rules win tree-wide, so every
    # render taken after it is taken under the new order.
    '.bak_cssorder',
    # SL-1 - .alv-stat-label gets overflow-wrap. ΟΛΟΚΛΗΡΩΜΕΝΕΣ is one
    # word with nothing to break on and drew 41px past its own tile.
    # Demetri: "The Completed Box Cuts off in Greek."
    '.bak_statlabel',
    # TD-1 - the overdue date and its warning, kept on one line.
    # project_task_list only; .date-value is used by no other page.
    '.bak_overduedate',
    # TR-1 - translate_to_greek_service returned the English from its
    # except clause and translate_text stamped success: True on it, so a
    # failure arrived as a green tick with English in the Greek box.
    # googletrans out, deep-translator in, and the failure now arrives.
    # Touches pages/views/projects.py and requirements.txt, not templates.
    '.bak_translate',
    # RB-1 - preview_imported_recipe.html, which serves /create_recipe/
    # too. Eleven buttons off Bootstrap and onto the action standard,
    # including the Check Spelling blue and the red block deletes Demetri
    # asked about, plus the JS selector that hunted one of them by its old
    # class.
    '.bak_recipebtn',
    # Section DR, 4 Oct 2026 - the first slice of the drift CS-1's section
    # 5b surveyed. Twenty-two pages wrote .btn-info in hex where base
    # writes it in tokens, and --alv-accent IS #0e7c8b: 82 declarations
    # that spelled out the answer the token already gives. Removed, with
    # all 22 pages painted before and after to show nothing moved.
    '.bak_btninfo',
    # TR-2, 4 Oct 2026 - translation moves onto the Anthropic Messages API.
    # TR-1 swapped googletrans for deep-translator and Railway could not
    # reach Google; Demetri got the honest amber bar TR-1 was built for and
    # asked "Can we not use our AI API for translation?". It is the API
    # invoice_verification already calls, with a key already set, over
    # urllib - which takes a timeout, so TR-1's thread pool goes with the
    # scraper. The (ok, text, reason) contract does not move.
    '.bak_trapi',
    # SE-1, 4 Oct 2026 - SECRET_KEY and USDA_API_KEY stop being literals in
    # mysite/settings.py and read the environment instead. The setting
    # NAMES survive, because usda_client and Django read them through
    # settings rather than through os. ANTHROPIC_API_KEY was already an
    # environment read - I said otherwise once, from my own broken
    # redaction, and was wrong.
    '.bak_setenv',
    # DR-1b, 4 Oct 2026 - the shorthand DR-1 could not touch. base declares
    # border-color and the page declared `border`, so DR-1's property-for-
    # property census never saw it and left fifteen rules setting the
    # accent again by another route. Bootstrap supplies the width and the
    # style once the shorthand goes; proved by painting all fifteen before
    # and after, border width and style included.
    '.bak_btnborder',
    # PF-1, 5 Oct 2026 - Demetri: "the Ingredients page is very sluggish."
    # Not USDA, which the page never calls on load: 374 rows x two inline
    # edit selects x 50 options = 18,700 <option> elements, every one of
    # them hidden behind .edit-mode and only ever wanted one row at a
    # time. The options move into a <template> rendered once and are
    # cloned in on first use; the selected value comes back from
    # data-original-value, which cancelEdit has always relied on.
    '.bak_pickerlazy',
    # RA-2, 5 Oct 2026 - the drift report only ever looked inside
    # .row-actions wrappers, so 37 of the tree's 119 icon buttons - a
    # third - were never examined. Widening it to every icon button found
    # three one-picture defects it had been blind to: icon-view wearing
    # four different glyphs across pages, icon-approve drawing an UNDO
    # arrow on Cash Receipts, and four bare icon-disabled buttons on
    # Passports that said they were disabled without saying what they do.
    '.bak_iconnames',
    # LU-1, 5 Oct 2026 - Demetri, minutes after rotating SECRET_KEY:
    # "Logged Out... Got this error." The rotation ended every session at
    # once, he pressed Logout, @login_required redirected to
    # settings.LOGIN_URL - and that line was COMMENTED OUT, so Django used
    # its own default of /accounts/login/, which this project has never
    # routed. Not a Logout bug: all 282 @login_required views across 34
    # modules answered a dead session that way, and had for the life of
    # the project. It never showed because sessions here never died.
    # LOGIN_URL is set, and @login_required comes off logout_user, because
    # logging out when you are already out is a no-op, not an error.
    '.bak_loginurl',
    # PD-3, 5 Oct 2026 - property_detail stops carrying its own palette
    # and stops scrolling sideways. The page's mobile block narrowed the
    # wrapper to 8px while Bootstrap's .row still pulled -15px, so every
    # width from 320 to 768 overflowed by exactly 7px - invisible to the
    # eye, visible to the scrollbar, and invisible to any text check
    # because the subtraction happens in the browser. The rows come in to
    # -8px to meet the wrapper, which keeps the tighter gutters the page
    # was given on purpose. With it: 90 hex literals onto base's tokens,
    # one 41px select to 44, and 15 rules that restated Bootstrap's own
    # .text-* utilities word for word. The other 25 !important flags stay
    # - 19 of them changed nothing when dropped, but a fixture with a
    # fraction of the rows cannot prove a negative, and this round does
    # not claim what it could not check.
    '.bak_pd3',
    # SV-1, 5 Oct 2026 - Demetri: "If I edit an asset and I then select an
    # invoice document and then press Save, nothing happens." Nothing
    # happened because the button was not in the form: Save sat on line 23
    # of edit_asset.html and <form id="editAssetForm"> opened on line 37,
    # so the button belonged to no form and the browser swallowed the
    # click. It looked like a file bug because of implicit submission -
    # Enter in a text field always submitted, and every save ever made on
    # that page went through Enter. Censusing the shape found a second,
    # unreported one: Generate Lease Agreement, whose form holds no submit
    # control at all and whose page has no text input to press Enter in.
    '.bak_submitform',
    # WS-1, 5 Oct 2026 - the left stripe that means warning, said
    # eleven ways by hand. PD-3 put property_detail's onto
    # var(--alv-warn) and printed on every run how many were still
    # spelt out; this takes them. The first census returned EIGHT,
    # because it asked for the shorthand only - three pages paint the
    # same stripe with border-left-color, which is precisely the hole
    # DR-1 fell into and DR-1b had to exist a day later to fill. The
    # pattern was widened before the patcher was written this time.
    # Fifteen stripes now agree. It does NOT claim #ffc107 is gone:
    # the colour is still used 60 times in other families, and the
    # suite prints that count so the claim cannot quietly grow.
    '.bak_warnstripe',
    # RA-3, 5 Oct 2026 - 24 of the 37 loose icon buttons get the
    # wrapper the ORDERING standard is read from. Order is a property
    # of a group and there was no group. SPLIT BY PAGE, NOT BY SHAPE:
    # three pages mix plain markup with forms, and converting by shape
    # would have left a .row-actions holding one action while two
    # siblings stood outside - the report would then check the order
    # of a fragment and call it clean. Nine pages whole; four held
    # back whole. It also revealed that crs/fi_form had been drawing
    # its delete button at 15.5px, squashed by a 40px grid column; the
    # column goes to 44px, the house tap floor, and it draws at 34.
    '.bak_rowwrap',
    # CW-1, 5 Oct 2026 - found while rendering RA-3, not reported. The
    # Ingredients page overflowed by 128px at 320 and 58px at 390,
    # because base's card pattern lays each cell out as a flex row
    # with the label at flex-shrink: 0 and no wrap. A value wider than
    # the room the label leaves has nowhere to go. One declaration -
    # flex-wrap: wrap - and six of the eight card tables painted do
    # not move at all. In base, because the defect is the pattern.
    '.bak_cardwrap',
    # FN-1, 5 Oct 2026 - Demetri, of the six finance screens: "The
    # Action Buttons ... do not conform to our standards. I also don't
    # want the Revenue table to be Green and the Expense table to be
    # red." The buttons were NOT drift: .btn-row-edit and
    # .btn-row-delete were declared in BASE and worn on exactly these
    # six pages, so the app had two sanctioned row-action
    # vocabularies and these pages looked different because base said
    # two things. 22 controls become .icon-action-btn, ten of which
    # had no title because the word Edit was beside them; the twelve
    # that did keep their sentences. The header rows go neutral. Yes
    # and No stay green and red, on tokens, because that colour means
    # yes and no rather than revenue and expenses.
    '.bak_finrows',
    # PL-1, 5 Oct 2026 - Demetri, of the P&L drill-down: "to view a
    # copy of a specific invoice I need to click the little black
    # tick. This is not intuitive." The tick is verify_badge, a
    # STATUS glyph, and it was the only way to open the document. An
    # Invoice column is added to the branch the modal scrapes, in the
    # shape of the Actual Expenses screen he named. Nothing is taken
    # away - the tick still works. The drill-down's handler listened
    # for .verify-icon alone, so it is widened too; without that the
    # new column would have been a button that did nothing.
    '.bak_plinvcol',
    # AI-1, 5 Oct 2026 - Demetri: "The add file to the Edit Asset works
    # perfectly. However, I need to add the functionality to remove an
    # attached file." REPLACE was the only verb the field had. The
    # Remove button names a hidden form outside editAssetForm, because
    # HTML does not allow a form inside a form and the control has to sit
    # beside the file - the photos on that page solved this first, and
    # SV-1 spent a round on what a submit button with no form owner does,
    # which is nothing, silently. The view calls .delete(save=False), so
    # the bytes leave storage rather than the link being cut.
    '.bak_assetinv',
    # LA-1, 5 Oct 2026 - Demetri: "Step 3 needs to say click the button
    # above - since we moved the buttons to the top." One word. The suite
    # is worth more than the change: it censuses every template for prose
    # that points at a control by DIRECTION, because a sentence telling
    # somebody where to look goes stale the moment a layout moves and
    # nothing here was watching for them.
    '.bak_leaseabove',
    # RA-3b, 5 Oct 2026 - the ten buttons RA-3 held back because each
    # sits in its OWN form. A run of buttons was the wrong unit: between
    # these there is a </form> and a <form>, so wrapping the buttons
    # would have put a .row-actions inside each form and left three
    # groups of one. The unit is the CELL, and all three pages put their
    # whole action column in a single <td>.
    '.bak_formwrap',
    # RA-4, 5 Oct 2026 - the order RA-3b made readable. The report said
    # physical_invoice_list ran approve, unapprove, send, duplicate,
    # delete, pdf. Checked against which controls can appear TOGETHER -
    # a draft shows approve, duplicate, delete, pdf; an approved one
    # shows unapprove, send, duplicate, pdf - so the PDF really was last
    # and Delete really did come before it. Five blocks reordered, not
    # one character rewritten. The first build moved the wrapper's
    # opening tag along with the block it was glued to and put the PDF
    # outside the group; every gate passed, because it WAS a permutation.
    '.bak_invorder',

    # 5 Oct 2026, the A-list rounds. CO-2 first because it changes the
    # gate itself and nothing else in this bundle depends on it; then
    # IC-1, AE-4, OI-1 and RA-5 in the order they were applied, which is
    # the order their backups were taken.
    #
    # CO-2 - Push-PendingChanges.ps1's own comment stripper learned
    # CO-1's rule: `/*` is not a comment opener in markup. It was
    # destroying 3,268 characters of passport_management and 776 of
    # property_assets, which carries a Code sentinel. No sentinel was
    # wrong yet, which is why it was worth doing now.
    '.bak_ps1comment',

    # IC-1 - fa-ban was worn by Disable and by Void. Demetri: Void keeps
    # it, Disable becomes fa-user-slash. Three uses on two pages, and the
    # third was invisible to the drift report because
    # household_member_management writes the glyph name across a template
    # tag - fa-{% if %}ban{% else %}check{% endif %}.
    '.bak_userslash',

    # AE-4 - PL-1 built the Invoice column inside the drill-down branch,
    # so the full Actual Expenses page - the screen Demetri named as the
    # intuitive one - never had it. The condition is gone and two widths
    # moved with it, because revealing a 10% column on a table already
    # summing to 100 makes a browser normalise every other column down.
    '.bak_actinvcol',

    # OI-1 - open_invoices_report's 27 hex literals over 10 colours onto
    # base's tokens, the green empty-state panel included. Mapped by what
    # each declaration MEANS, not by its value: #6c757d appeared six
    # times meaning quieter text and #2c3e50 seven meaning the value you
    # came to read.
    '.bak_oireport',

    # RA-5 - the register of controls that are not action columns. The
    # slot was RA-3c, wrap the last four; the markup says each is a lone
    # Remove button beside the thing it removes and wrapping one would
    # invent a column to satisfy a census. The report says NAMED now,
    # with the reason, and refuses a fifth.
    '.bak_rowexempt',

    # IC-2 - the other half of IC-1's pair. fa-check was worn by
    # icon-approve and icon-unlock; Approve keeps the tick, Enable
    # becomes fa-user-check. After it, NO glyph in the tree is worn by
    # two names - the one-picture rule holds in both directions for the
    # first time. The third use was inside the same split glyph name
    # IC-1 edited, which is what IC-1's census was built to find.
    '.bak_usercheck',

    # DR-2a - twelve declarations on five pages that said what base
    # already said, in different words: 6px for var(--alv-radius-sm),
    # #f8f9fa for var(--alv-surface), 1fr 1fr 1fr for repeat(3, 1fr).
    # Every one resolved identically, and the suite paints all five
    # pages at four widths to prove nothing moved. What it buys is that
    # five pages are back on the tokens and will follow when the house
    # moves. The 59 that really differ are not this round.
    '.bak_dr2spell',

    # CS-2 - twelve templates do not extend base, so base's stylesheets
    # are not in the document and they cannot override it. CS-1's census
    # had been counting six of manual_pdf's declarations as drift; it is
    # rendered by render_to_string and handed to xhtml2pdf, and has no
    # choice but to style itself. alv_tree.standalone() reads it off the
    # {% extends %} tag with comments stripped, so the list cannot go
    # stale. The gate's verdict does not move - what moves is the number
    # the survey prints, and that the next drift round does not begin by
    # rediscovering this.
    '.bak_standalone',

    # DR-2b - the 51 declarations that beat base with a DIFFERENT value,
    # across 15 pages. Demetri: base wins. The page declaration is
    # deleted rather than rewritten as a token, because a page that
    # stops declaring a property is on base's value by inheritance and
    # one fewer declaration is better than one more. Four are KEPT and
    # named: a phone bar with six actions and one with two are not the
    # three-column bar base describes. Live drift against base's head
    # stylesheets: 140 -> 4, and the four have reasons.
    #
    # The first build cut a grouped rule twice. rule_spans reports
    # `.a:hover, .a:active { ... }` under both names with the same body
    # span, so two entries produced one identical cut twice - the second
    # removed whatever had slid into those offsets. title_deeds went
    # from 37 rules to 23. The cuts are a set now, overlaps are refused,
    # and a rule emptied of everything is removed rather than left as
    # braces with nothing in them.
    '.bak_dr2val',

    # PH-1 - the passport holder becomes a person. PA-3 logged it on
    # 4 Oct: holder_name is a CharField, nothing ties it to
    # HouseholdMember, and the register and the household can drift
    # apart. A NULLABLE foreign key beside the string, not instead of
    # it: holder_name keeps every row and every view keeps reading it,
    # so the migration adds a column that is NULL everywhere and nothing
    # depends on. on_delete is PROTECT, because a register whose subject
    # can be deleted out from under it is not a register.
    #
    # No data migration. backfill_passport_holder reports who matches
    # and how - exact, or case-and-space folded - and writes only with
    # --write, and never writes an ambiguous one. PA-3: "no safe
    # automatic mapping for Angy". This round does not invent one.
    '.bak_passholder',

    # PH-1b - a command that explodes is a bad command. PH-1's backfill
    # walked into a query against a column it had no reason to assume
    # existed and returned two hundred lines of traceback ending in
    # pymysql. It now asks the table what columns it has first, and if
    # holder_id is not there it names the alias and the engine, says the
    # migration has not been applied to THAT database, points at
    # showmigrations and tells the local and production cases apart -
    # then exits non-zero having read and written nothing.
    #
    # Introspection, not a caught exception: 1054 is also what a typo in
    # a field name raises, and a handler that turned every unknown
    # column into "run your migrations" would be lying half the time.
    #
    # Its suite does what PH-1's could not: it builds sqlite databases
    # from the MODELS' own metadata and runs the real command against
    # them through manage.py, so the matching logic is proved end to end
    # - exact, loose, no match, another workspace, the write, and the
    # second write that finds nothing left to do.
    '.bak_passguard',

    # PH-1c - four names, written down, because nobody can infer them.
    # The backfill ran against production and matched NOTHING: 21
    # passports, four holder names, zero hits. The members were seeded
    # with first names (migration 0072 - Demetri, Angy, Erene,
    # Alexandra) and the passports carry full names. Three of the four
    # are the same person written two ways; Angela Manias against Angy
    # is a different name, which is what PA-3 meant by "no safe
    # automatic mapping for Angy".
    #
    # Demetri chose an explicit map over a first-word rule - a rule that
    # catches three of these four and stops looking safe the day a
    # household holds a Demetri and a Demetris - and confirmed that
    # Angela and Angy are one person. `named` is a third kind of match
    # and IS written, because a person decided it rather than a string
    # comparison landing. A map entry pointing at a member who is not in
    # that workspace is reported under its own heading, not skipped.
    #
    # And the unmatched list now prints the members available beside it:
    # the first run said "these need a person" and could not be acted on
    # without reading a migration.
    '.bak_passalias',

    # B-1, 5 Oct 2026 - 957 literals on 102 templates became a var(),
    # and every one of them was ALREADY the byte-identical value of the
    # token that replaced it. Tier A of the Section B colour map: the
    # patcher reads base's :root and refuses the whole round unless each
    # of the thirteen substitutions resolves to the literal it is
    # replacing, character for character.
    #
    # THE PROOF IS IN THE VALUE, NOT THE PICTURE - the two renders are
    # the same render - so the suite's render is smoke on the ten
    # busiest pages and section 5 is the gate.
    #
    # The twelve standalone templates are EXEMPT and must stay so: with
    # no {% extends %} there is no :root in the document, so a var()
    # there resolves to nothing, and xhtml2pdf - which renders four of
    # them - does not support var() at all. The suite follows every
    # non-browser render path in the tree to the template it renders and
    # requires it to be in that set.
    #
    # The census read 981 until the grouped-rule bodies were deduped:
    # rule_spans reports `.a, .b { ... }` under both names with the same
    # body span, which is DR-2b's bug counting instead of cutting.
    '.bak_coltok',

    # B-2, 6 Oct 2026 - the four neutrals. 758 literals on 93 templates
    # became a var(), and UNLIKE B-1 THESE MOVED: between 9 and 25 RGB
    # units. #6c757d -> --alv-ink-soft, #dee2e6 -> --alv-line, #2c3e50
    # -> --alv-ink, #495057 -> --alv-ink-strong.
    #
    # THE GATE IS BOUNDED, NOT AN EQUALITY. Every substitution must move
    # by EXACTLY the distance the map records, to a tenth of a unit -
    # "within 25" would let a changed token slide 277 declarations
    # somewhere nobody looked at.
    #
    # Demetri looked at all four side by side at phone and desktop width
    # before this ran. Two read measurably better: the muted grey goes
    # 4.69:1 to 5.53:1 on paper, and 4.69 cleared the AA floor for
    # normal text by four hundredths on 229 uses of which a third are
    # set at 11px or 12px. The 201 borders go the OTHER way, 1.30 to
    # 1.24, and that was his decision: --alv-line is already what every
    # base-styled table draws with, so these pages now agree with base.
    '.bak_coltok2',

    # B-2b, 6 Oct 2026 - the tail of tier B. 342 literals on 68
    # templates, 105 pairs in six families, every one inside 25 RGB
    # units and gated the same way B-2 is: exactly the move the map
    # records, or the round refuses.
    #
    # THE FINDING IS THE SHAPE. Twenty-one ways of writing a pale teal
    # and fifty-three greys - a long tail is not a programme nobody got
    # to, it is the same decision made separately by whoever was
    # writing that page that day.
    #
    # FOUR ENTRIES WERE OVERRULED BY HAND. #ecf0f1 is a grey five units
    # wide that the hue band called a pale teal; #e8f4ff and #e8f4fd
    # are pale blues the same band called greys. And #f8f9fa as a LINE
    # was DROPPED rather than corrected - on that one page it is the
    # page's own background, a border invisible on purpose, and making
    # it visible is a decision nobody has made.
    '.bak_coltok3',

    # E-2b, 6 Oct 2026 - THE 403 PAGE STOPS BEING AN f-STRING.
    #
    # E-2 put the first gate on the tree that compiles templates and
    # resolves names (test_url_names.py, no patcher - it is a census).
    # The first question it asked that nobody had asked before was
    # whether every template a Python module NAMES actually exists, and
    # the answer was no, once: pages/middleware.py rendered
    # 'access_denied.html', which had never been written.
    #
    # THE BARE except: IS WHY IT SURVIVED. The render sat inside one, so
    # TemplateDoesNotExist was swallowed and the fallback ran instead -
    # eighty lines of HTML in an f-string, a purple gradient with two
    # emoji on it. No 500, ever; and no custom page either. 172 URL
    # prefixes in ModuleAccessMiddleware's map land there.
    #
    # AND BECAUSE IT WAS A STRING, NO ROUND COULD SEE IT. The twelve
    # standalone templates are at least templates. This round makes it a
    # file - extending base, built from base's classes, carrying no
    # <style> block and no hex literal of its own, so the colour rounds
    # need not re-measure anything.
    #
    # The OUTER except Exception stays. A bare except around a render
    # hides a missing template for years; a logged one around the whole
    # method is the difference between a 403 and a 500 the day base
    # itself breaks.
    '.bak_denied',

    # E-2c, 6 Oct 2026 - SEVEN SUITES GET THE REAL URLconf BACK.
    #
    # They resolved against 'pages.urls' instead of mysite.urls,
    # and the reason was never a fact about the product: the
    # SANDBOX MIRROR was missing crs/forms.py, which
    # crs/views/config.py imports, so importing the real root died
    # there. The laptop has always had the file. E-2's first
    # measurement reported 260 of 260 URL names as broken on the
    # strength of that gap and had to be corrected.
    #
    # IT WAS NOT A FREE SUBSTITUTION. Measured both ways: under
    # pages.urls /crs/ answers 404 and crs:index does not reverse
    # at all. Seven gates were blind to every URL the project
    # mounts outside that one include, and answered 404 where the
    # app answers 200.
    #
    # Six carried the line with no comment, inside the block that
    # swaps DATABASES to sqlite. The seventh explained itself and
    # named the price in its own words - that it could not see
    # whether some OTHER include answers /accounts/login/ - so
    # that suite also stops reading mysite/urls.py as a stand-in
    # and asks the whole project instead.
    '.bak_rooturl',

    # B-3, 6 Oct 2026 - TIER C BEGINS: THE GREEN AND THE RED.
    #
    # B-1 asserted equality, B-2 and B-2b a bounded move of 25 RGB
    # units. This one moves up to 88, and the defence is not that it
    # is invisible - it is that the app gets MORE readable. Seven of
    # the 23 pairs cross the AA line for normal text. Bootstrap's
    # success green was the worst colour left in the tree at 3.13:1
    # on paper, where AA wants 4.5; --alv-good reads 5.12.
    #
    # THE FAMILIES ARE TAKEN WHOLE, which is not what was first
    # proposed. 179 was the count of the two solids alone; ten of the
    # other greens and reds are HOVER STATES of them, and --alv-good
    # is darker than Bootstrap's hover green - so a button converted
    # without its hover would get LIGHTER under the pointer. The map
    # sends every hover-dark to the family's -ink token and the round
    # refuses unless all 21 rest/hover pairs are still darker after.
    #
    # TWO PAIRS LOSE A LITTLE and are named in the patcher rather
    # than let through by a loosened rule: #0f5132 9.36 -> 8.57 and
    # #721c24 11.01 -> 8.91, both still near twice what AA asks.
    #
    # NOT IN IT, although a hue test sweeps them up: the recipe
    # browns, a pink, a burnt orange and Bootstrap's teal.
    '.bak_goodbad',

    # CM-1, 6 Oct 2026 - ONE COLUMN, FIVE LIMITS, ONE OF THEM NOTHING.
    #
    # Demetri asked for the Enter New Comment field to hold about
    # three times what it held. Measured first, because length could
    # have meant three things: the box renders 746x98 at 1280 and the
    # card caps at 1200, so the widest it can get where it sits is
    # 830 - a gain of 11 percent, not 300. Characters were the thing.
    #
    # WHAT THE MEASUREMENT FOUND. The column was CharField(255), the
    # new box said maxlength 250, the edit box said 255, the edit view
    # enforced 255 - and the ADD view enforced NOTHING. maxlength is a
    # browser hint, so a POST from a script or a stale page reached
    # objects.create() unchecked, and under MySQL strict mode that is
    # a DataError: a 500 rather than a message.
    #
    # All five now say 1000, and both views read the number off the
    # model field rather than retyping it, so it cannot drift from the
    # column again. issues_heading and issues_description keep their
    # own 255 - two different columns, and the patcher refuses if they
    # move.
    '.bak_cmlen',
    # CR-1, 7 Oct 2026 - alv_cssrules learns to read colour
    # outside a <style> block, because decision 9 put inline style=
    # attributes and <script> bodies into the colour programme and B-4
    # cannot be built to that scope until the tooling can see them.
    #
    # IT CONVERTS NOTHING. Five functions, a suite, and a census. The
    # one that earns the round is js_colour_context: 257 colour
    # literals live inside <script>, and 118 of them must NOT become
    # var() - 27 are Chart.js options, where a canvas cannot resolve a
    # custom property and the series would simply vanish, and 91 cannot
    # be classified at all. A round refuses what it cannot classify.
    '.bak_outside',    # IM-1, 7 Oct 2026 - decision 8 closed by measurement, and the
    # measurement made into a gate. 1,001 !important live in page
    # stylesheets and NOT ONE beats base on the same selector and the
    # same property; the other 951 are beating Bootstrap, which is what
    # !important is for here. An answer that cost an afternoon decays
    # the moment a round writes one, so the push now watches it.
    #
    # The same round repoints cs1_census.py, which has measured nothing
    # since CS-1 moved base's stylesheet into the head and reported its
    # own blindness as a clean bill of health.
    '.bak_impguard',    # DW-1, 7 Oct 2026 - 177 declarations on 36 pages that stated
    # exactly what base already stated: same selector, same property,
    # same value. Copies of base sitting in page stylesheets, which is
    # what happens when a page is built by copying another page.
    #
    # 50 of the 227 found were NOT touched, because they carry
    # !important and an !important may be beating a higher-specificity
    # rule that base plain declaration would lose to.
    '.bak_deadweight',    # PM-1, 7 Oct 2026 - found by DW-1 refusing to cut something.
    # passport_management carried HALF of a base rule: the plain
    # display:none for the two mobile filter labels, and not the
    # @media that shows them on a phone. Page CSS renders later, so
    # the half-copy was the last rule standing and base override
    # never applied - Filters and Clear showed their icons with no
    # words, on that page only. Both lines deleted; base supplies
    # both halves.
    '.bak_pmlabels',    # B-4, 7 Oct 2026 - the amber, at the scope decision 9 set.
    # 70 conversions on 24 pages: 52 in CSS, 14 in inline style=
    # attributes and 4 inside <script>. TEN MORE IN <script> ARE
    # REFUSED, because js_colour_context cannot classify them and a
    # round refuses what it cannot classify.
    #
    # The pills are RESTRUCTURED, not substituted - warn-soft fill,
    # warn ink, and a border ADDED where four of the six had none.
    # Their SHAPE is untouched: .alv-pill-attn is a modifier on
    # .alv-pill, which carries the padding and the radius, so adding
    # the class would have resized seven pills nobody asked to resize.
    #
    # Left alone: the Bootstrap oranges (decision 4), the dashboard
    # chart series and its legend, the Gantt bar, the spell-check
    # highlighter - brightness IS its function - and act_expense's
    # anTok('warn', '#8e6207'), which reads the token and keeps the
    # literal as its FALLBACK. That is the correct pattern.
    '.bak_amber',    # B-4b, 8 Oct 2026 - one declaration, and the instrument that
    # should have caught it. B-4 moved .btn-edit:hover's FILL to
    # --alv-warn and left the #000 ink where it was: 9.77:1 became
    # 3.90:1 on a hover state that ships. The ink is now
    # --alv-on-accent at 5.38:1, which is base's own .badge-warning
    # pairing.
    #
    # A rule's colour is a PAIR, and a round that moves half a pair
    # has changed the pair. B-4's gate checked ink conversions and
    # never fill conversions against their companion ink, so it could
    # not see this. test_pair_contrast.py is the census that can: 701
    # pairs tree-wide, 54 below AA - 21 of them inactive controls,
    # which WCAG 1.4.3 exempts, and 32 live ones PINNED BY NAME so a
    # later round cannot add one by swapping a different one out.
    '.bak_editink',    # B-5a, 8 Oct 2026 - the grey neutrals. 158 literals on 32
    # pages become ink-ramp tokens: 106 in inline style= attributes,
    # 50 inside <script>, and TWO in a page stylesheet. That split is
    # the whole argument for decision 9 - B-1, B-2 and B-2b had
    # already taken the greys out of the CSS, and Section B could not
    # see the markup or the script at all until CR-1.
    #
    # ROLE PICKS THE TOKEN, DISTANCE ONLY BREAKS TIES INSIDE IT. A
    # distance-only map got twelve wrong: color:#dee2e6 -> --alv-line
    # is the right colour under a line's name, and the name is the
    # meaning. #fff as ink takes --alv-on-accent, not --alv-paper.
    #
    # AND ONE LITERAL CAN SIT IN TWO TIERS. #6c757d is 16.8 units from
    # --alv-neutral as ink and 198 from --alv-line as a border, so the
    # want table is keyed on (literal, role) - a dict keyed on the
    # literal alone collapses the two and converts the border with the
    # ink token.
    #
    # Refused: 5 canvas literals (a 2D context cannot resolve a custom
    # property and the chart would vanish) and 9 js_colour_context
    # cannot classify. Left: the black S-a settled, and 81 tier C uses
    # that are changes of appearance - B-5b, with renders.
    '.bak_neutrals',    # AD-1, 8 Oct 2026 - the System tab, at his ask: "It must look
    # and behave exactly like the Functional Tab with regards to
    # colours." Two page-local tokens carry most of it - --future-dark
    # and --future-light repoint at --alv-accent and
    # --alv-accent-soft - and three rules that do not read them are
    # changed by hand, including the inactive hover, which was a
    # different colour from Functional's and so was false on hover too.
    #
    # ONE NUMBER GOES DOWN AND IT IS MEANT TO. The System tile was
    # white on --alv-ink-soft at 5.53:1 and is now white on
    # --alv-accent at 4.91:1, which is what Functional has always
    # read. Matching it is the instruction.
    #
    # THIS OVERTURNS test_personal_teal.py, WHICH DECIDED THE GREY.
    # PT's claim is moved rather than deleted, with his words and the
    # date beside it. B-4 overturned a decision in silence and had to
    # be backed out.
    #
    # The two Coming Soon tiles become RESERVED CELLS - no fill, no
    # border, no shadow, no hover, aria-hidden, pointer-events off -
    # so the panel keeps its height and growth lands in a space
    # already drawn. .btn-future-disabled goes with them, and with it
    # the last #adb5bd on the page that was not a live permission
    # state.
    #
    # And the pair census learns page-local :root tokens, because
    # every tab rule in the tree is written in one and not a single
    # one of them was being counted. 701 pairs became 714.
    '.bak_systeal',    # PR-1, 8 Oct 2026 - a COMPLIANCE tab on Personal, at his ask,
    # and CRS Reporting moved onto it. The tile, its markup and its
    # perms_map.crs gate travel together and are not copied: the page
    # holds exactly one CRS link before and after.
    #
    # IT INVERTS P6. P2 commented out the FUTURE tab on 29 Sep, which
    # took the shared right edge with it and left the Personal tab
    # open on one side; P6 removed `border-right: none` so the tab
    # drew its own. Compliance puts a neighbour back, so the
    # declaration comes back and the Compliance tab draws the line
    # through border-left-color. P6's own note on the page said the
    # rule follows the NEIGHBOUR COUNT - this round is the other half
    # of what that note anticipated.
    #
    # P6's suite is RE-POINTED, not edited into agreement: its claim
    # was "the Personal tab has a right border" and is now "the shared
    # edge is there and is drawn once", measured the same way at the
    # same two widths. That claim is true of both arrangements.
    # test_future_tab_off.py's "exactly ONE panel" becomes "no FUTURE
    # panel", which is what it meant.
    #
    # SAME LOOK AND FEEL MEANS THE SAME RULES. Compliance cannot reuse
    # .future-tab - that is grey on this page and test_personal_teal
    # still says so - and it does not get its own copy of the accent
    # rules either, because two copies drift. The four .personal-tab
    # selectors each gain .compliance-tab, so the tabs match by
    # construction.
    '.bak_compliance',    # TB-1, 8 Oct 2026 - ONE TAB TREATMENT, IN BASE, FOR EVERY
    # LANDING PAGE THAT WEARS ONE. admin_apms.html and personal.html
    # each had a copy and Finance was about to be the third; B-4b's
    # note set the rule that a third use is the signal to promote.
    #
    # THE TWO COPIES HAD ALREADY DRIFTED IN TEN RULES, eight of them
    # in the mobile block - padding 11px against 10px, icon 1rem
    # against 0.9rem, a panel radius on one and not the other. Nobody
    # chose any of it. Administration's mobile tuning wins because it
    # was deliberate; where one copy was more DEFENSIVE than the other
    # - personal's tile padding and h6 line-height - the defensive one
    # wins instead, and that is said out loud in base.
    #
    # THE SHARED EDGE IS NOW DERIVED:
    #     .admin-tab:not(:last-child) { border-right: none; }
    # Written out by hand it cost two defects on the same page ten
    # days apart - P6 on 29 Sep when P2 removed the neighbour, PR-1 on
    # 8 Oct when a new tab inherited the declaration and had none. The
    # browser can count. The cross-classes alivente-active,
    # future-active, personal-active and compliance-active went with
    # it: they only ever coloured the OTHER tab's edges, which one
    # treatment has no use for.
    #
    # NOT TO BE CONFUSED WITH ALV TABS v1, which base already had -
    # .alv-tab and .nav-tabs .nav-link, panel-level tabs. This round
    # nearly appended over it and its own marker guard caught it.
    #
    # Four suites re-pointed, each a claim about an arrangement this
    # round replaces: AD-1's --future-* tokens, P6's border-right on
    # admin_apms, X5's house panel and tile, and the pair census -
    # where FOUR copies of the same --alv-accent on --alv-accent-soft
    # at 4.31 became ONE, 716 pairs down to 712.
    '.bak_housetabs',    # FN-2, 8 Oct 2026 - Finance adopts the house tabs. Reports and
    # Configuration were two side-by-side cards; they are two tabs
    # now, Configuration behind Reports, six tiles each, at his ask:
    # "the only difference will be that the Finance modules Tabs will
    # have 6 buttons instead of the 4 buttons of Administration."
    #
    # THIS IS THE ROUND TB-1 EXISTED FOR. Finance adds no tab CSS at
    # all - it writes the markup base's block documents and deletes
    # 170 lines of card styling. Twelve destinations, twelve icons and
    # twelve labels unchanged; only the container moved.
    #
    # AND A BOOTSTRAP BRIGHT RETIRES EARLY. The Reports card header
    # was background: #007bff, one of the ten test_pair_contrast pins
    # for B-7, so B-7's list is one shorter and this round owns that
    # number. The Configuration header was var(--alv-ink-soft), the
    # last grey header in the module.
    '.bak_fintabs',    # TB-2, 8 Oct 2026 - THE LINES THAT TURN A TAB OFF, PUT BACK.
    # TB-1 retired the alivente-active / future-active cross-classes by
    # deleting the two lines that carried them, and those lines also
    # carried 'active' - the only thing that took it OFF a tab. Click
    # the second tab and both carried it; click back and both still
    # did. The panels were removed correctly, so the content was always
    # right and only the tabs were wrong. Demetri found it in the
    # deployed page within the hour, on Administration and Personal
    # both. finance.html was never affected: FN-2 wrote its switchTab
    # fresh, and this fix takes that shape so all three read alike.
    #
    # AND THE SUITES ALL PASSED. Every tab suite adds .active in its own
    # probe and measures the CSS; not one ever called switchTab. A class
    # nobody applies is a class nobody tested. test_tab_switch.py clicks.
    '.bak_tabswitch',    # B-5b, 8 Oct 2026 - the grey tail, read rather than counted.
    # B-5a logged 81 uses at 56 and 33 RGB units. That is a true
    # sentence about distance and a useless one about the work: the 81
    # are muted text, an empty-state watermark, disabled states, input
    # borders and some chevrons, and they want different answers.
    #
    # THIS ROUND TAKES TWO. 18 muted-text uses go to --alv-ink-soft,
    # 2.07:1 to 5.53:1 - which is not a new decision but the finishing
    # of B-2, whose own table called #6c757d "muted and small text" and
    # moved it to the same token. At 11-12px AA is 4.5, so ink-faint at
    # 3.00 would not have done.
    #
    # And the .empty-state i watermark is drawn in TWO greys across
    # twelve pages; the four strays join the ten. That one stays a
    # LITERAL on purpose - the house has no token for a watermark, the
    # nearest is --alv-line which is a line token used as ink, and
    # inventing one is a base change. The gap is logged.
    #
    # LEFT, WITH REASONS: 6 disabled (AD-1 settled that), 19 #ced4da
    # borders (every neutral line token is LIGHTER, so every move makes
    # an input border fainter - --alv-line-strong is logged instead),
    # 4 chevrons, 4 hover border-colours, 8 standalone.
    '.bak_greytail',    # HM-1, 8 Oct 2026 - two Home pages, and the one without income
    # never has it built. The audience is can_access_financials, his
    # call: the tree already governs income with that permission.
    #
    # THE CACHE WOULD HAVE SERVED ONE BRIEF TO BOTH. _brief_fingerprint
    # hashed the figures only, so whichever brief was written first
    # would have been served to both audiences out of cache. The
    # audience is the first thing in that payload now.
    #
    # AND REMOVING THE CARD IS NOT REMOVING THE DATA. home.html put
    # every month's rent into the page source for the chart's hover, so
    # the SERVICE takes the audience and forward_projection is not
    # called at all when it may not be shown. `income` is keyword-only
    # with NO default: a caller who forgets gets a TypeError.
    #
    # IT ALSO CLOSES A WIDER HOLE, at his ask. The view filtered the
    # Today BUTTONS by permission and then embedded the WHOLE payload -
    # overdue invoices and both expense lists, amounts and all - for
    # every user with dashboard access. The filter reads the same
    # _TODAY_CANDIDATES table the buttons do, and fails closed.
    #
    # The vacancy drill-down moved from the rent-roll card to Lease
    # expiries, for both audiences: it is occupancy, not income, and it
    # would have left with the card.
    '.bak_homesplit',    # HM-2, 9 Oct 2026 - the Issues panel, for both audiences, in the
    # grid cell HM-1's rent-roll card leaves for a reader without
    # income. Counts by status, open and logged and closed against the
    # previous 3 months and the same 3 months last year, and an ageing
    # line.
    #
    # THE CENSUS CHANGED THE DESIGN TWICE. `Issue` - his severity for
    # "unresolved AND a problem" - has NEVER been used on the live
    # data, so the warning line is AGE rather than severity; the
    # problem count is still computed and appears the moment somebody
    # uses it. And 1900-01-01 is "no date": the column is never NULL,
    # eleven places in the tree compare against the sentinel, and the
    # first census run asked the wrong question and reported all 154
    # rows as resolved-dated, the ten open ones included.
    #
    # The open count over time is RECONSTRUCTED - logged <= D and (not
    # Resolved or resolved after D) - because no status history exists
    # to read. A Resolved row with no date cannot be placed in time: it
    # is in the status totals and out of the series, and the panel says
    # how many.
    '.bak_issuepanel',
    # RC-2, 9 Oct 2026 - the recipe module's warm literals
    # sorted into the two families their own grounds declare.
    '.bak_spice',
    # IS-1, 9 Oct 2026 - a re-opened issue stops carrying
    # the date it was closed on.
    '.bak_issuedates',
    # B-7, 9 Oct 2026 - the Bootstrap brights that survived
    # B-3 by living outside a stylesheet.
    '.bak_brights',
    # HM-3, 9 Oct 2026 - the Issues card stops using one
    # header for a level and a rate.
    '.bak_isscard',
    # HM-4, 9 Oct 2026 - the chips come off and the
    # figures centre.
    '.bak_isscentre',
    # D-12 and D-7, 9 Oct 2026 - the 6px radius becomes
    # a token, and the dead comment-author class goes.
    '.bak_radtoken',
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
