# base.html standards block, updated 22 Sep 2026

The full text of the Django comment block at the top of base.html once this round is applied. The browser never receives it.

```text
===============================================================================
  ALIVENTE ONLINE - THE SYSTEM STANDARD
  Revised 22 September 2026.
===============================================================================

  WHY THIS IS HERE, AND NOT IN A README

  Because this is the file you have open when you are about to break one of
  these rules. Every standard below is owned by base.html; a page that wants
  to look different from the rest of the system almost always does it by
  redefining something here, locally, in its own style block. Six months of
  that is how one component came to exist in five colours without anyone
  deciding it should.

  ONE RULE ABOUT THIS BLOCK ITSELF: IT MUST NOT CONTAIN ANYTHING SHAPED
  LIKE AN HTML TAG. More than a hundred suites parse base.html with regular
  expressions, and several of them find a stylesheet by matching an opening
  style tag, then anything, then a closing one. A sentence in here containing
  a literal style tag opens such a match at the prose and closes it at base's
  first REAL closing tag, swallowing an entire stylesheet - which is what
  happened the first time this block was pushed, and took seven checks in
  test_table_standard.py down with it. That suite's own notes had already
  warned: "English prose inside a comment has impersonated markup". So this
  document writes `style block`, `h2 > center`, `br` - never the tags
  themselves. The suite that guards this block enforces it.

  This block is a Django comment tag. It is stripped when the template
  compiles - the browser never receives a byte of it, and the compile cost is
  paid once per worker process, measured at under half a millisecond. It
  costs a visitor nothing. (Contrast the CSS comments further down this file:
  those live inside style tags and DO ship, on every page load. 38KB of them.)

-------------------------------------------------------------------------------
  HOW TO READ IT
-------------------------------------------------------------------------------

  Every standard is marked one of two ways:

    [test_NAME.py]       A suite checks this. Break it and the push gate
                         stops you. The suite is the real standard; this
                         text is a description of it.

    [CONVENTION]         Nothing checks this. It is true today because
                         people have been careful. It will drift.

  That distinction is the most important thing in this document. A written
  standard nothing verifies is a wish. Where you see [CONVENTION], treat the
  rule as real but assume it is already slightly wrong somewhere, and expect
  a scan to find exceptions - because every scan run on this codebase has.

  EVERY SUITE IN THE REPO RUNS ON THE PUSH GATE - 108 of them on 22 Sep -
  and `Push-PendingChanges.ps1` holds the list. SINCE 22 SEP NONE IS KNOWN
  TO FAIL. Five had failed on every run for weeks, and not one of them had
  found a fault in a page: each judged its own round against a file that a
  later, agreed round had changed. They judge their own rounds again and
  sit on the gate. So a FAIL line is always news now - keep it that way.

-------------------------------------------------------------------------------
  1. HOW A CHANGE IS MADE
-------------------------------------------------------------------------------

  Every change to this system goes through the same six steps. They are not
  ceremony; each one exists because skipping it once cost something.

  1. SURVEY.  Measure the actual shape before proposing anything. Never "this
     looks like about twenty places" - count them, in every directory,
     including subdirectories. Numbers from a survey have been wrong by a
     factor of two in both directions: 140 required markers were 112; 19
     banner rules were 3 pages; 11 broken action bars were 6.

  2. AGREE.  Propose the round and its scope, and get a decision, before
     writing a patcher. Decisions belong to Demetri, not to whoever is
     holding the keyboard.

  3. PATCH.  One `apply_*.py` per round. It must be:
       - IDEMPOTENT - running it twice changes nothing the second time
       - ANCHORED - every anchor asserted to match exactly once, and the
         script exits rather than guessing
       - BACKED UP - a `.bak_NAME` per file, never overwritten
       - `--check` - a dry run that writes nothing
       - SELF-CHECKING BEFORE WRITING - if the checks fail, no byte is
         written. Not "written then reverted". Never written.
       - LINE ENDINGS KEPT - a CRLF file stays CRLF, and its backup is
         written with the ORIGINAL's line endings, not the patcher's.
       - REGISTERED - its backup suffix appended to ROUNDS in
         `alv_rounds.py`, oldest first. See step 4.

  4. TEST.  One `test_*.py` per round, and it must contain CONTROLS: checks
     that deliberately break the change and confirm the suite notices. A
     suite with no control has, on this codebase, shipped a 500, silently
     done nothing against a CRLF file, and agreed with a bug it shared.

     Run it against the REVERTED tree as well. It must FAIL there - and
     fail, not crash: a crash blocks a push exactly as hard and says far
     less about why.

     JUDGE THE ROUND ON THE FILE AS THE ROUND LEFT IT, never on the file
     as it is now. Later rounds WILL change that file, on purpose, and a
     suite reading it now turns their work into its own failure - that
     happened in almost every round of 21 Sep before it was solved once.
     `alv_rounds.as_left_by` answers it: the file as round R left it is the
     next round's backup of it. A round in ROUNDS is placed by the list; an
     older one by its backups' modification times. `alv_rounds.as_of`
     gives a file as it stood at a moment, for a file a round read but did
     not back up.

  5. PUSH.  `Push-PendingChanges.ps1` runs every suite on the gate first
     and stages nothing if any fails. BEFORE IT, THE ALL-SUITES SWEEP: every
     suite run to the end, because the gate stops at the first failure and
     hides the rest. Compare the sweep's FAIL lines with the sweep before the
     round - lines, not exit codes. The commit message says what changed and WHY,
     including what was considered and rejected.

  6. TEST ON LIVE.  A person opens the screens. This step has caught things
     no suite could: a 500, missing map tiles, a red figure on a page of good
     news, and three headings that disagreed with each other. It is not
     optional, and it is why Personal - which has never had it - is not
     "done" merely because it compiles.

-------------------------------------------------------------------------------
  2. WHAT base OWNS
-------------------------------------------------------------------------------

  54 design tokens and the component classes below. A page should reach
  for these and define almost nothing of its own.

  COLOUR TOKENS - never write a hex in a page.               [CONVENTION]

    Accent     --alv-accent  --alv-accent-ink  --alv-accent-soft
               --alv-accent-line  --alv-on-accent
    Ink        --alv-ink  --alv-ink-strong  --alv-ink-soft  --alv-ink-faint
    Surface    --alv-paper  --alv-surface  --alv-neutral  --alv-neutral-soft
    Lines      --alv-line  --alv-line-soft
    Meaning    --alv-good  --alv-warn  --alv-bad  --alv-info  --alv-danger
               (each with a -soft companion for backgrounds)
    Ageing     --alv-age-1 .. --alv-age-4  (+ -soft)
    Grading    --alv-grade-1 .. --alv-grade-5  (+ -soft)
    Tag inks   --alv-tag-clay/moss/plum/sky/slate-ink
    Action     --alv-edit  --alv-view
    Shape      --alv-radius  --alv-radius-sm  --alv-font-ui

  COMPONENTS

    Tables       .alv-table  .table-container  .alv-matrix (+ scroll, blend,
                 total, row-head, absent)
    Status       .alv-pill (+ -good -attn -bad -info -neutral)
                 .alv-tag (+ -clay -moss -plum -sky -slate)
                 .alv-age-0..4 (+ -pill -dot -cell -fill)
                 .alv-grade-1..5 (+ -dot -cell)
    Figures      .alv-stats  .alv-stat  .alv-stat-value  .alv-stat-label
                 (+ -good -attn -bad -age)
    Cards        .alv-card (+ -head -body -title -aside -lead)
    Actions      .page-action-buttons  .action-primary  .action-secondary
                 .action-danger  .action-back  .action-filter
                 .action-more-btn/-menu/-item  .disabled-btn  .back-button
    Row actions  .row-actions  .cell-actions  .desktop-action-cell
                 .mobile-action-bar/-btn/-icon/-label  .icon-action-btn
                 .icon-edit/-view/-delete/-send/-upload/-approve/-manage/
                 -duplicate/-unapprove  .icon-disabled  .status-btn
    Menus        .ui-menu  .ui-menu-toggle  .ui-menu-panel  .ui-menu-item
    Filters      .alv-filter  .alv-filter-active  .action-filter-count
    Headings     .page-title-h2  .page-subtitle-h4
    Reports      .alv-report-head  .alv-report-titles  .alv-report-title
                 .alv-report-sub  .alv-report-brand
    Pop-ups      .alv-modal-head (+ --danger)
    Forms        .alv-req  .form-card  .form-section-title  .form-group
                 .form-text  .form-control
                 .alv-applies  .alv-applies-help
                 .alv-choice (+ --danger -note -when)
    Print        .print-keep
    Empty        .alv-empty  .alv-empty-title  .alv-empty-hint
    Segmented    .alv-seg
    A11y         .alv-visually-hidden

-------------------------------------------------------------------------------
  3. THE STANDARDS
-------------------------------------------------------------------------------

  3.1 COLOUR MEANS SOMETHING. IT IS NOT DECORATION.                [CONVENTION]

      --alv-good   on time, healthy, active
      --alv-warn   needs attention soon
      --alv-bad    overdue, failed, required
      --alv-info   informational, neutral emphasis
      --alv-accent the system's own colour: primary actions, selection

      A colour must not mean two things at once. Financials once painted its
      Revenue headings green and its Expense headings red - a sensible idea
      on its own, and impossible beside a figure that is green because it is
      not late. That colour coding was retired on 8 Sep for exactly this
      reason.

      NEVER: a hex in a page's own style block. NEVER: a colour keyword (`red`,
      `white`) - those are invisible to a hex-based audit and hid a defect
      for weeks. NEVER: a semantic token used for decoration.

  3.2 PAGE HEADINGS      [test_heading_standard.py, test_heading_prefix.py]

      A page heads itself with up to three lines. THE KIND OF CONTENT IS THE
      RULE; the tag follows it, and two kinds share a tag.

          h2 > center      PAGE NAME
          h4 > center      ADD NEW PROPERTY                    (mode label)
          h4 > center      INV-042 - Apolloneon                (record name)
          h5 > center      A sentence describing the page      (descriptive)
          br

      h2  THE TITLE. Capitals, NO BRAND PREFIX. Every page has one. It is a
          LABEL: two to four words, scanned rather than read.

          THE BRAND IS IN THE BROWSER TAB, not the heading. base.html builds
          the tab from the page's own title block followed by a pipe and the
          brand, so every page that extends base gets it for free and no page
          states it twice. A page sets only its own name in that block, in
          Title Case.

          (The block tag is not spelled out here on purpose. Django's comment
          tag swallows it, so the template is fine - but anything that WALKS
          Django tags sees an opening block that never closes, and reported
          base's own tags as unbalanced. Same family as prose shaped like an
          HTML tag or a CSS comment: the third kind, found the same way.)

          WHY IT MOVED, 8 Sep 2026. It headed 66 pages, identical on all of
          them, so it distinguished nothing - and there are 53 distinct
          title lines, every one already unique without it. On a phone the
          content column is about 360px and those seventeen characters
          filled the whole first line before the title began. The brand was
          meanwhile already on screen three times: the sidebar logo image
          plus the word ALIVENTE, the top-nav brand image, and the footer
          copyright.

          And on the pages that name a record it was the first of three
          dashes. SEVEN OF THE TWELVE real property names contain a dash
          already, so the old rule produced, on live data,
          `ALIVENTE ONLINE - PROPERTY ASSETS - ATHENS - SECOND FLOOR`.

          THE ARGUMENT AGAINST, kept because it is a real one. Reports print
          and are emailed. base's mobile override reads
          `@media (max-width: 991px)` with no `screen` keyword, and A4
          portrait is about 718 CSS px, so IT FIRES ON PAPER and hides the
          sidebar: the logo does vanish from a printed page. What survives
          is the footer copyright, which is inside the content div and not
          marked no-print. A brand at the TOP of a printed report belongs in
          the report title component, not on 66 screens.
          (Same accidental-media-query bug as the one the print block
          records at 768px. Two instances, one cause.)

          KNOWN EXCEPTION, one page: `error_pages/connectivity_error` heads
          itself `ALIVENTE ONLINE` and nothing else. It is shown when the
          database is unreachable, where the brand is the content and the
          chrome is not guaranteed to render. It keeps its heading.

      h4  TWO THINGS, WHICH IS WHY THE TAG IS NOT THE RULE.

          A MODE LABEL, on a screen that is one mode of something else:
          ADD NEW PROPERTY, EDIT EXISTING SUPPLIER, ADD VALUATION,
          UPLOAD / VIEW / DELETE. CAPITALS, because it is a label - two or
          three words naming which mode you are in. 15 pages, all agreeing.

          Or a RECORD NAME, saying which record is on screen: an invoice
          number and a customer, a receipt number. Its case belongs to the
          DATA, so no rule here can set it. 3 pages.

      h5  THE DESCRIPTIVE LINE. Sentence case. It is a SENTENCE - often
          eight words or more, and ALL-CAPS measurably slows reading by
          removing the word shapes that let you recognise a word without
          spelling it out. 8 pages use it.

      A page has an h4 or an h5, not both. Settled 8 Sep 2026.

      THE MARKUP, since 16 Sep: base declares the heading, so a page writes
      h2.page-title-h2 and h4.page-subtitle-h4 and styles neither. 66 pages
      do. 22 list pages still write h2 > center, which renders the same and
      is a mechanical tidy for a later round, not a second standard.

      KNOWN EXCEPTION: `customer_invoice_form` reads `New invoice` in its
      else branch - a mode label in sentence case where every other one
      shouts. One word, found by the suite, left for a round that agrees to
      touch that page.

      NO ICON:   not one compliant heading in the system carries one.
      NO BAND:   a heading is text on paper, never a filled colour block.

      THE GENERAL RULE, which applies well beyond headings:
      CAPITALS FOR LABELS, SENTENCE CASE FOR PROSE. base already did this
      without saying so - `.alv-stat-label` is uppercase and letter-spaced
      because it is a label, and nothing else in base shouts.

      HOW THE h4 RULE CAME TO BE WRITTEN DOWN, because it is a warning. The
      round that set this standard surveyed the subtitles by looking for an
      h5 immediately after the h2, found six, and concluded the corpus was
      too small to settle the question. There are forty-three. Eighteen are
      h4 and were invisible to that scan. The round changed only
      h5s and so left every mode label correctly in capitals - the right
      outcome, reached because the scan could not see them rather than
      because anyone had understood the rule. Had those pages used h5, it
      would have lowercased fourteen labels that should shout.

      A RECORD NAME GOES ON THE h4, NEVER THE h2. Settled 9 Sep after the
      projects/ module was measured with real data in it.

          h2 > center      PROJECTS
          h4 > center      EDIT TASK - Replace the flat-roof membrane

      The h2 answers WHERE AM I - the module, stable, scanned. The h4
      answers WHAT AM I DOING AND TO WHAT. The separator between the mode
      label and the record is an EM DASH, and that is not a style choice:
      SEVEN OF THE TWELVE real property names contain a hyphen already
      (`Athens - Second Floor`, `Apolloneon - Demetri`), so a hyphen there
      is not a separator, it is a coin toss. `customer_invoice_form` had
      already worked this out on its own.

      THE ONE PLACE THE CONSTRUCTION DOES NOT FIT, and what was chosen. On a
      screen that adds a child to a parent, the record is the PARENT, so
      `ADD TASK - Apolloneon Roof Replacement` reads as though Apolloneon
      were the task. There the preposition stays and there is NO dash:

          h4 > center      ADD TASK TO Apolloneon Roof Replacement

      THE CASE CHANGE IS THE SEPARATOR - `ADD TASK TO` shouts because it is
      a label, the name does not because it is data. Which is the general
      rule below doing the work a dash would otherwise do. Two pages:
      `project_tasks_add` and `project_subtasks_add`.

      KNOWN GAP: 8 pages still carry a record name on the h1 or h2, and
      each belongs to a round already planned rather than to this rule -
      three Administration pages waiting on that module's test pass; two
      left-aligned page headers where the record IS the title and the header
      wants restructuring; one report, lease_agreement_report, now on base's
      report title (3.10) but still naming its record in it; and an email
      body and a PDF, neither of which has chrome to inherit a brand from.
      Two more report screens were on this list - the title-deed pair - and
      were deleted on 21 Sep: nothing rendered either of them usefully.

  3.3 TABLES                                     [test_table_standard.py,
                                                  test_card_standard.py]

      Use `.alv-table` inside `.table-container`. Give every cell a
      `data-label` so the phone layout can turn rows into cards. Numbers get
      `.num`. Headings stick on scroll and stop sticking on paper. An empty
      table shows `.alv-empty`, not a blank rectangle.

  3.4 ACTION BARS                                [test_action_standard.py,
                                                  test_button_reach.py,
                                                  test_button_sweep.py]

      One `.page-action-buttons` row per page. Exactly one `.action-primary`
      - the page's verb. Help is never the verb. Destructive actions are
      `.action-danger`, outlined at rest and filled only on hover. Back is
      quiet, sits right, and keeps a 44px target on a phone.

      Below 768px the primary takes the width, Back becomes a square, and
      secondaries move into the More menu - BUT ONLY WHERE THERE IS ONE.
      `.action-secondary` is hidden only inside a bar that actually contains
      an `.action-more-btn`.                     [test_secondary_visible.py]

      That conditional exists because the unconditional version silently
      deleted Cancel from six Add/Edit forms that have no Back button either.
      If you add a More menu to a bar, its secondaries start hiding on
      phones again - that is the intent, but check the menu lists them.

      THE BAR IS THE FIRST THING IN THE FORM. Settled 16 Sep: Save sits
      above the fields, and nothing sits above the bar.
                                                 [test_one_action_bar.py,
                                                  test_save_and_cancel.py]
      The Applies-from panel sat above it on five Financials screens until
      21 Sep, invisible to both suites because its date was not a
      .form-control. It is directly under the bar now (3.6).

  3.5 ROW ACTIONS                                [test_action_standard.py,
                                                  test_detail_property.py]

      Icons in table rows, never words. One cell holds them all
      (`.cell-actions` / `.desktop-action-cell`), and the Actions heading
      sits over its buttons. On a phone they become `.mobile-action-bar`.
      A disabled action is still rendered, disabled - never dropped, or the
      row's shape changes depending on who is looking at it.

  3.6 FORMS                                     [test_required_sweep.py,
                                                 test_control_height.py]

      A FIELD LOOKS LIKE THIS. Drawn from New Customer Invoice and
      properties_add, which agreed with each other before it was written
      down:

          label > strong        the field name, bold
          span.alv-req          the asterisk, if the field is required
          input.form-control    the control

      THE LABEL IS BOLD. Settled 9 Sep, from a 545-label count that split
      338 plain to 207 bold - the majority was plain and the standard is
      bold anyway, because the model page and the two biggest Add screens
      already agreed, and because a label is a LABEL: the same reason
      headings and `.alv-stat-label` shout. Only three screens mix the two
      styles, so this is a per-page decision to sweep, not drift inside a
      page. THE SWEEP HAPPENED on 16 Sep: 218 labels on 40 pages. Six are
      named and deliberately untouched - three that JavaScript
      rewrites, two carrying a hint that is not part of the name, and
      one that is a sentence of instruction rather than a field name.
      test_label_bold.py holds the corpus to it.

      AND base NOW DECLARES THE FIELD, not only names it. The panel is
      .form-card and its heading .form-section-title; the field is
      .form-group, its label and .form-text; the control is
      .form-control, focused in the accent token. 34 pages wrote those
      rules out in two dialects before base said them once. Rows are
      still Bootstrap's grid and base does not touch them.

      EVERY REQUIRED FIELD IS MARKED, in one spelling, in a colour base
      owns - the .alv-req class, coloured from the bad token, and no brace
      is written here on purpose: see the note below. One round normalised
      the
      112 asterisks that already existed, in seven spellings; a second found
      81 required fields that said NOTHING AT ALL and marked them, including
      the Properties and Tenants Add and Edit screens - 9 and 15 required
      fields each, none of them marked, in signed-off modules.

      INCLUDING ON FORMS WHERE EVERY FIELD IS REQUIRED. Four screens are
      entirely required and an asterisk distinguishes nothing there. They
      are marked anyway: a reader moving between screens learns ONE rule and
      does not have to notice that this form happens to be all-required.
      An exception that seems obviously right is how a rule stops being one.

      A LABEL MAY OWN ITS CONTROL TWO WAYS. A label carrying a `for`
      attribute naming the control's id is the explicit form. Several pages
      instead put a label with NO `for` immediately before the control -
      which works visually, does not work for a screen reader, and made a
      sweep report twenty already-marked fields as unmarked until it learned
      to read both. The `for` attribute is the one to write.

      (This paragraph deliberately does not spell either element out. Prose
      shaped like markup breaks every tool that finds markup by regex,
      including our own harness - a sentence in this document once swallowed
      an entire stylesheet and took seven checks down with it.

      FOUR KINDS HAVE NOW DONE IT, each found by a different suite days
      after the sentence was written: an HTML tag, the two characters that
      close a CSS comment, a Django block tag, and A CSS DECLARATION WITH
      BRACES. The last one cost a push. A suite looked for a component name
      followed by an opening brace, found the name in this document's
      inventory, ran seven thousand characters forward to the ONE pair of
      braces in the whole document - a rule written out in a sentence - and
      read the token inside it as that component's colour.

      SO: NO BRACES IN THIS DOCUMENT AT ALL. Name a class, name a token,
      never write the declaration. test_standards_block.py enforces it.)

      A MARKER WITH NOTHING BEHIND IT is the mirror image, and 15 of them
      exist: a label saying required beside a control that does not enforce
      it. NOT SWEPT - adding `required` changes what a form ACCEPTS, which
      is behaviour rather than styling, and wants somebody who knows the
      business rule.

      Controls must not be pinned to a fixed height; Bootstrap 4.1.3 does
      this and shaves the descenders off the value.

      SIXTEEN PIXELS ON A PHONE. Every text input, select and textarea is
      16px below 768px, from one base rule marked important - the only way
      a stylesheet outranks an inline style - because iOS zooms the whole
      page on anything smaller. 64 controls on 16 pages were under it on
      21 Sep.                                    [test_small_controls.py]

      ONE FIELD, ONE NAME. The date a Financials figure takes effect from is
      Applies from on every screen - Valuations labelled it differently
      until 21 Sep. Its panel is .alv-applies, straight under the Save bar,
      with the guidance in .alv-applies-help; its date is a .form-control.
      Where a pop-up offers stopping something from a date or removing it
      completely, the two radios are .alv-choice cards, the destructive one
      .alv-choice--danger.                       [test_applies_from.py]

  3.7 PRINT                                      [test_print_leaks.py,
                                                  test_card_standard.py]

      base hides the furniture on paper: action bars, More menus, filter
      panels, `.no-print`. Tables stop sticking, pills lose their tint and
      gain an outline, and card edges darken enough to survive an empty
      cartridge. A page should not need its own print block. If it does,
      say why in a comment - and expect a later round to take it away when
      base grows the same rule.

      NO BUTTON PRINTS, unless it carries .print-keep - one base print rule
      since 21 Sep, the opt-out for the few that are content, not
      controls.                                  [test_print_buttons.py]
      A PHONE RULE NEVER REACHES PAPER. A4 portrait is about 718 CSS px, so
      a max-width query without screen fires on paper; every one in the
      system says screen since 21 Sep - 106 clauses on 82 pages.
                                                 [test_print_queries.py]
      A printed report carries ALIVENTE ONLINE above its title (3.10).

  3.8 MOBILE                                                [CONVENTION]

      768px is the breakpoint, `@media screen and (max-width: 768px)` so it
      cannot also apply to paper. Tables become cards, action bars collapse,
      44px is the minimum touch target on a phone. Two phone claims ARE
      measured now - text size and paper, in 3.6 and 3.7 - and every Add/Edit
      screen has been rendered at 375. The rest of mobile has still never
      been reviewed systematically: treat any other mobile claim in this
      file as untested unless a suite is named beside it.

  3.9 POP-UPS                                    [test_modal_heads.py,
                                                  test_ei_modal.py]

      A pop-up is a Bootstrap modal, and its header is .alv-modal-head: the
      teal banner, a white title, a white close. A pop-up that deletes
      something is .alv-modal-head--danger, in red - that, and only that.
      Settled 21 Sep: 51 headers on 31 business templates had been sixteen
      different looks. The Personal side's 36 wait for its own round.

      base owns the HEADER only - no dialog, overlay or body component. The
      one hand-built overlay left, the Issues analysis drill-down, is
      deliberate and is not a modal header.

  3.10 REPORTS                                   [test_report_head.py,
                                                  test_old_rounds.py]

      A report heads itself with .alv-report-head: the title in capitals on
      the left (.alv-report-title), what it covers underneath
      (.alv-report-sub), Back or a headline figure on the right. On a phone
      the row stacks and centres. On paper, and only on paper, ALIVENTE
      ONLINE (.alv-report-brand) sits above the title - the one place the
      brand is content rather than chrome. Ten reports, settled 21 Sep; they
      had built it three ways, in four greys.

-------------------------------------------------------------------------------
  4. THE RULES THAT KEEP BEING RELEARNED
-------------------------------------------------------------------------------

  These are not style preferences. Each one is here because ignoring it cost
  a defect, a broken push, or a wrong number.

  * A CONTROL THAT CANNOT FAIL IS WORSE THAN NO CONTROL. A tag-balance check
    that ended in `or True` shipped a 500. A control that searched for "\n"
    against a CRLF file reported a clean pass on an untouched tree.

  * ONE WRONG RULE IMPLEMENTED TWICE IS STILL WRONG. A patcher and its
    scanner shared a bug, so the cross-check between them agreed and three
    files shipped corrupted. Two implementations of one rule do not drift -
    but checking them against each other tests agreement, not correctness.

  * A WHOLE-FILE CLAIM FOR A COMPONENT-LEVEL ROUND FAILS CORRECT WORK. "No
    gradient anywhere in this file" failed twenty correct patches, because
    those pages legitimately keep a gradient on a modal. Scope the claim to
    the component; report the rest with a floor.

  * A MEASUREMENT NEEDS THE RIGHT REFERENT. Reading `rgba(0,0,0,0)` as black
    and calling a 21:1 chip illegible. Counting distinct `top` values as
    "rows" when a nowrap flex line holds buttons of different heights.
    Measuring a block heading's BOX centre when the question was about its
    TEXT. When a check fails, ask first whether it measures the right thing.

  * RENDER IT. Twelve times a browser has caught what no text check could:
    a colour that moved rather than left, a dangling dash, a title inset by
    padding whose edge no longer existed, a chip orphaned left under a
    centred heading. And its limit: the map round could not be rendered, and
    said so, rather than implying otherwise.

  * MEASURE THE SHAPE BEFORE GENERALISING, AND WALK EVERY DIRECTORY. Two
    surveys read only the top level of pages/templates and missed six
    subdirectories. One was named after a colour and therefore found only
    that colour. EVERY SCANNER MUST WALK THE SUBDIRECTORIES TOO, AND NONE
    SHOULD BE NAMED AFTER A SYMPTOM.

    (The glob for that is not written here on purpose. An earlier draft
    spelled it out, and the two characters that end a CSS comment sat in
    the middle of it - so two suites that hunt for a comment spelling a tag
    matched from an earlier opener right through this line, and had been
    failing since the day this block was written. Neither was on the push
    gate, so nothing said so. Prose that looks like markup breaks the tools
    that read the file, and CSS comment syntax counts as markup.)

  * A CHECK THAT READS TEXT CATCHES PROSE. Twenty-four times, including
    three where the prose was the patcher's own explanation of the thing it
    was checking. Strip comments before asking a question of code.

  * A GATE THAT CANNOT FINISH BLOCKS A PUSH AS HARD AS ONE THAT FAILS. A
    suite that waited on a CDN, and one that raced Chromium for a file
    handle on Windows, each stopped a push for a reason that had nothing to
    do with the code. Renders are hermetic; cleanup reports instead of
    raising.

  * BEFORE REDESIGNING A RULE, CHECK ANYTHING RENDERS IT - and before adding
    one, check it reaches something. Dead rules have been found in double
    figures, including one that had been overridden by an inline style in
    the same file.

  * SCOPE GUARDS MOVE. Fourteen times. When a guard fails on correct work,
    do not re-point it at the new string and do not add an exception: ask
    what the claim is ABOUT and rewrite it to check that. Six of the
    fourteen were guards this project wrote that named the very round that
    would invalidate them. Since 21 Sep the usual answer is one line:
    judge the round on the file as it left it (step 4, `alv_rounds`).

  * A FAILING SUITE IS NOT ALWAYS A FAILING PAGE. Five suites failed on
    every sweep for weeks and were carried as known failures. Four were
    judging their round against a file later rounds had changed; the fifth
    had been wrong about its own round from the first day. A known-failure
    list hides the next real failure among the old ones - keep it at zero.

  * A STANDARD CAN BE ESCAPED BY A MISSING CLASS. The Applies-from panel
    sat above Save on five screens for weeks because its date was not a
    .form-control, so the suites that keep the bar first never saw it.
    Giving it the class surfaced the fault. Ask, do not exempt.

  * A SURVEY COUNT MUST BE OF THE EXACT TOKEN. "26 templates use the
    action-bar class" was a substring count that also caught
    mobile-action-bar; the real number was seven, all on the Personal side.

  * DUPLICATED CAN MEAN DEAD. Two title-deed templates looked like a copy to
    merge; reading their views showed neither was rendered usefully by
    anything, and they were deleted instead. Read the view before planning
    the merge.

-------------------------------------------------------------------------------
  5. WHERE THE PLAN LIVES
-------------------------------------------------------------------------------

  The outstanding work, the decisions still open, and the history of every
  round are kept in the project docs, not here -
  `claude/outstanding_review_21_sep.md` is the current list, which replaced
  `claude/running_list.md`, and `claude/RESUME_HERE.md` says where things
  stand. This file describes the standard; that file describes how
  far the system has got towards it, and neither should try to be the other.

  Two things worth knowing without opening it:

  * PERSONAL HAS NEVER BEEN REVIEWED OR TESTED. Not styling, not
    behaviour, not on Live. Assume unknown defects, not untidy CSS. It is
    the next section of work once the outstanding list is done.
    Administration was brought into line with every other module on
    20 Sep and has been tested on Live.

  * THE RECIPE / MEAL-PLAN SIDE IS DELIBERATELY OUTSIDE EVERY SWEEP, by a
    hardcoded exclusion list in `Show-ButtonDrift.py`. It is not on the push
    gate. That list is NAME-based and has at least one hole.

-------------------------------------------------------------------------------
  6. CHANGING A STANDARD
-------------------------------------------------------------------------------

  A standard changes the same way anything else does: survey, agree, patch,
  test, push, test on Live. Two extra obligations:

  1. UPDATE THIS BLOCK IN THE SAME ROUND. A standards document that lags the
     code is worse than none, because people trust it.

  2. IF YOU ARE PROMOTING A [CONVENTION] TO ENFORCED, WRITE THE SUITE FIRST
     AND WATCH IT FAIL. A suite written after the fix, that has never seen
     the defect, is a suite you are guessing about.

  And if you are about to add something to a page's own style block that base
  could own instead: that is how this system acquired five colours of one
  component, thirty local copies of one action row, and four drifting copies
  of one report title. Put it in base, or write down why it could not go
  there.
```
