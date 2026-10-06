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
