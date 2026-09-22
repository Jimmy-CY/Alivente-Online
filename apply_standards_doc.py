# -*- coding: utf-8 -*-
"""apply_standards_doc.py - base.html's standards block records the
decisions of 16-22 Sep.

    python apply_standards_doc.py --check     dry run, nothing written
    python apply_standards_doc.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

Asked for on 22 Sep: bring the comments in base.html up to our latest
decisions and standards. ONLY the Django comment block at the top of base
changes - it never reaches a browser. Recorded:

  - the gate: every suite on it, none known to fail
  - how a change is made: line endings kept, rounds registered in
    alv_rounds, the revert test, judging a round on the file as it left it,
    the all-suites sweep before the push
  - what base owns: 54 tokens, and the heading, report, pop-up, form and
    print components added since 8 Sep
  - headings: the page-title-h2 / page-subtitle-h4 markup; the KNOWN GAP
    now 8 pages
  - action bars: the bar is first in the form
  - forms: 16px on a phone; Applies from, .alv-applies, .alv-choice
  - print: no button prints; no phone rule reaches paper; the brand
  - mobile: what is now measured
  - new 3.9 POP-UPS and 3.10 REPORTS
  - four more rules that keep being relearned
  - where the plan lives; Personal is the part never reviewed
"""
# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

import os
import re
import sys

CHECK = '--check' in sys.argv
BASE = os.path.join('pages', 'templates', 'base.html')
if not os.path.isfile(BASE):
    sys.exit('! pages/templates/base.html not found - run from the repo root')
SUFFIX = '.bak_stddoc'
SUITE = 'test_standards_doc.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS_FILE = 'alv_rounds.py'

EDITS = [
    ('  Revised 8 September 2026.',
     '  Revised 22 September 2026.'),
    ('LIKE AN HTML TAG. Forty-one suites parse base.html with regular\n  expressions,',
     'LIKE AN HTML TAG. More than a hundred suites parse base.html with regular\n  expressions,'),
    ('  41 suites run on the push gate. `Push-PendingChanges.ps1` holds the list.',
     '  EVERY SUITE IN THE REPO RUNS ON THE PUSH GATE - 108 of them on 22 Sep -\n  and `Push-PendingChanges.ps1` holds the list. SINCE 22 SEP NONE IS KNOWN\n  TO FAIL. Five had failed on every run for weeks, and not one of them had\n  found a fault in a page: each judged its own round against a file that a\n  later, agreed round had changed. They judge their own rounds again and\n  sit on the gate. So a FAIL line is always news now - keep it that way.'),
    ('       - SELF-CHECKING BEFORE WRITING - if the checks fail, no byte is\n         written. Not "written then reverted". Never written.',
     '       - SELF-CHECKING BEFORE WRITING - if the checks fail, no byte is\n         written. Not "written then reverted". Never written.\n       - LINE ENDINGS KEPT - a CRLF file stays CRLF, and its backup is\n         written with the ORIGINAL\'s line endings, not the patcher\'s.\n       - REGISTERED - its backup suffix appended to ROUNDS in\n         `alv_rounds.py`, oldest first. See step 4.'),
    ('     suite with no control has, on this codebase, shipped a 500, silently\n     done nothing against a CRLF file, and agreed with a bug it shared.',
     "     suite with no control has, on this codebase, shipped a 500, silently\n     done nothing against a CRLF file, and agreed with a bug it shared.\n\n     Run it against the REVERTED tree as well. It must FAIL there - and\n     fail, not crash: a crash blocks a push exactly as hard and says far\n     less about why.\n\n     JUDGE THE ROUND ON THE FILE AS THE ROUND LEFT IT, never on the file\n     as it is now. Later rounds WILL change that file, on purpose, and a\n     suite reading it now turns their work into its own failure - that\n     happened in almost every round of 21 Sep before it was solved once.\n     `alv_rounds.as_left_by` answers it: the file as round R left it is the\n     next round's backup of it. A round in ROUNDS is placed by the list; an\n     older one by its backups' modification times. `alv_rounds.as_of`\n     gives a file as it stood at a moment, for a file a round read but did\n     not back up."),
    ('  5. PUSH.  `Push-PendingChanges.ps1` runs all 41 suites first and stages\n     nothing if any fails.',
     "  5. PUSH.  `Push-PendingChanges.ps1` runs every suite on the gate first\n     and stages nothing if any fails. BEFORE IT, THE ALL-SUITES SWEEP: every\n     suite run to the end, because the gate stops at the first failure and\n     hides the rest. Compare the sweep's FAIL lines with the sweep before the\n     round - lines, not exit codes."),
    ('     optional, and it is why Administration and Personal - which have never\n     had it - are not "done" merely because they compile.',
     '     optional, and it is why Personal - which has never had it - is not\n     "done" merely because it compiles.'),
    ('  52 design tokens and 109 component classes. A page should reach for these\n  and define almost nothing of its own.',
     '  54 design tokens and the component classes below. A page should reach\n  for these and define almost nothing of its own.'),
    ('    Forms        .alv-req\n',
     '    Headings     .page-title-h2  .page-subtitle-h4\n    Reports      .alv-report-head  .alv-report-titles  .alv-report-title\n                 .alv-report-sub  .alv-report-brand\n    Pop-ups      .alv-modal-head (+ --danger)\n    Forms        .alv-req  .form-card  .form-section-title  .form-group\n                 .form-text  .form-control\n                 .alv-applies  .alv-applies-help\n                 .alv-choice (+ --danger -note -when)\n    Print        .print-keep\n'),
    ('      A page has an h4 or an h5, not both. Settled 8 Sep 2026.',
     '      A page has an h4 or an h5, not both. Settled 8 Sep 2026.\n\n      THE MARKUP, since 16 Sep: base declares the heading, so a page writes\n      h2.page-title-h2 and h4.page-subtitle-h4 and styles neither. 66 pages\n      do. 22 list pages still write h2 > center, which renders the same and\n      is a mechanical tidy for a later round, not a second standard.'),
    ("      KNOWN GAP: 10 pages still carry a record name on the h1 or h2, and\n      each belongs to a round already planned rather than to this rule -\n      three Administration pages waiting on that module's test pass; two\n      left-aligned page headers where the record IS the title and the header\n      wants restructuring; three report screens that share the report title\n      component and should be settled when it is hoisted; and an email body\n      and a PDF, neither of which has chrome to inherit a brand from.",
     "      KNOWN GAP: 8 pages still carry a record name on the h1 or h2, and\n      each belongs to a round already planned rather than to this rule -\n      three Administration pages waiting on that module's test pass; two\n      left-aligned page headers where the record IS the title and the header\n      wants restructuring; one report, lease_agreement_report, now on base's\n      report title (3.10) but still naming its record in it; and an email\n      body and a PDF, neither of which has chrome to inherit a brand from.\n      Two more report screens were on this list - the title-deed pair - and\n      were deleted on 21 Sep: nothing rendered either of them usefully."),
    ('      If you add a More menu to a bar, its secondaries start hiding on\n      phones again - that is the intent, but check the menu lists them.',
     '      If you add a More menu to a bar, its secondaries start hiding on\n      phones again - that is the intent, but check the menu lists them.\n\n      THE BAR IS THE FIRST THING IN THE FORM. Settled 16 Sep: Save sits\n      above the fields, and nothing sits above the bar.\n                                                 [test_one_action_bar.py,\n                                                  test_save_and_cancel.py]\n      The Applies-from panel sat above it on five Financials screens until\n      21 Sep, invisible to both suites because its date was not a\n      .form-control. It is directly under the bar now (3.6).'),
    ('      Controls must not be pinned to a fixed height; Bootstrap 4.1.3 does\n      this and shaves the descenders off the value.',
     '      Controls must not be pinned to a fixed height; Bootstrap 4.1.3 does\n      this and shaves the descenders off the value.\n\n      SIXTEEN PIXELS ON A PHONE. Every text input, select and textarea is\n      16px below 768px, from one base rule marked important - the only way\n      a stylesheet outranks an inline style - because iOS zooms the whole\n      page on anything smaller. 64 controls on 16 pages were under it on\n      21 Sep.                                    [test_small_controls.py]\n\n      ONE FIELD, ONE NAME. The date a Financials figure takes effect from is\n      Applies from on every screen - Valuations labelled it differently\n      until 21 Sep. Its panel is .alv-applies, straight under the Save bar,\n      with the guidance in .alv-applies-help; its date is a .form-control.\n      Where a pop-up offers stopping something from a date or removing it\n      completely, the two radios are .alv-choice cards, the destructive one\n      .alv-choice--danger.                       [test_applies_from.py]'),
    ('      gain an outline, and card edges darken enough to survive an empty\n      cartridge. A page should not need its own print block. If it does,\n      say why in a comment - and expect a later round to take it away when\n      base grows the same rule.',
     '      gain an outline, and card edges darken enough to survive an empty\n      cartridge. A page should not need its own print block. If it does,\n      say why in a comment - and expect a later round to take it away when\n      base grows the same rule.\n\n      NO BUTTON PRINTS, unless it carries .print-keep - one base print rule\n      since 21 Sep, the opt-out for the few that are content, not\n      controls.                                  [test_print_buttons.py]\n      A PHONE RULE NEVER REACHES PAPER. A4 portrait is about 718 CSS px, so\n      a max-width query without screen fires on paper; every one in the\n      system says screen since 21 Sep - 106 clauses on 82 pages.\n                                                 [test_print_queries.py]\n      A printed report carries ALIVENTE ONLINE above its title (3.10).'),
    ('      768px is the breakpoint, `@media screen and (max-width: 768px)` so it\n      cannot also apply to paper. Tables become cards, action bars collapse,\n      44px is the minimum touch target. MOBILE HAS NEVER BEEN REVIEWED\n      SYSTEMATICALLY - treat any mobile claim in this file as untested unless\n      a suite is named beside it.',
     "      768px is the breakpoint, `@media screen and (max-width: 768px)` so it\n      cannot also apply to paper. Tables become cards, action bars collapse,\n      44px is the minimum touch target on a phone. Two phone claims ARE\n      measured now - text size and paper, in 3.6 and 3.7 - and every Add/Edit\n      screen has been rendered at 375. The rest of mobile has still never\n      been reviewed systematically: treat any other mobile claim in this\n      file as untested unless a suite is named beside it.\n\n  3.9 POP-UPS                                    [test_modal_heads.py,\n                                                  test_ei_modal.py]\n\n      A pop-up is a Bootstrap modal, and its header is .alv-modal-head: the\n      teal banner, a white title, a white close. A pop-up that deletes\n      something is .alv-modal-head--danger, in red - that, and only that.\n      Settled 21 Sep: 51 headers on 31 business templates had been sixteen\n      different looks. The Personal side's 36 wait for its own round.\n\n      base owns the HEADER only - no dialog, overlay or body component. The\n      one hand-built overlay left, the Issues analysis drill-down, is\n      deliberate and is not a modal header.\n\n  3.10 REPORTS                                   [test_report_head.py,\n                                                  test_old_rounds.py]\n\n      A report heads itself with .alv-report-head: the title in capitals on\n      the left (.alv-report-title), what it covers underneath\n      (.alv-report-sub), Back or a headline figure on the right. On a phone\n      the row stacks and centres. On paper, and only on paper, ALIVENTE\n      ONLINE (.alv-report-brand) sits above the title - the one place the\n      brand is content rather than chrome. Ten reports, settled 21 Sep; they\n      had built it three ways, in four greys."),
    ('  * SCOPE GUARDS MOVE. Fourteen times. When a guard fails on correct work,\n    do not re-point it at the new string and do not add an exception: ask\n    what the claim is ABOUT and rewrite it to check that. Six of the\n    fourteen were guards this project wrote that named the very round that\n    would invalidate them.',
     '  * SCOPE GUARDS MOVE. Fourteen times. When a guard fails on correct work,\n    do not re-point it at the new string and do not add an exception: ask\n    what the claim is ABOUT and rewrite it to check that. Six of the\n    fourteen were guards this project wrote that named the very round that\n    would invalidate them. Since 21 Sep the usual answer is one line:\n    judge the round on the file as it left it (step 4, `alv_rounds`).\n\n  * A FAILING SUITE IS NOT ALWAYS A FAILING PAGE. Five suites failed on\n    every sweep for weeks and were carried as known failures. Four were\n    judging their round against a file later rounds had changed; the fifth\n    had been wrong about its own round from the first day. A known-failure\n    list hides the next real failure among the old ones - keep it at zero.\n\n  * A STANDARD CAN BE ESCAPED BY A MISSING CLASS. The Applies-from panel\n    sat above Save on five screens for weeks because its date was not a\n    .form-control, so the suites that keep the bar first never saw it.\n    Giving it the class surfaced the fault. Ask, do not exempt.\n\n  * A SURVEY COUNT MUST BE OF THE EXACT TOKEN. "26 templates use the\n    action-bar class" was a substring count that also caught\n    mobile-action-bar; the real number was seven, all on the Personal side.\n\n  * DUPLICATED CAN MEAN DEAD. Two title-deed templates looked like a copy to\n    merge; reading their views showed neither was rendered usefully by\n    anything, and they were deleted instead. Read the view before planning\n    the merge.'),
    ('  round are kept in the project docs, not here - `claude/running_list.md` is\n  the current one.',
     '  round are kept in the project docs, not here -\n  `claude/outstanding_review_21_sep.md` is the current list, which replaced\n  `claude/running_list.md`, and `claude/RESUME_HERE.md` says where things\n  stand.'),
    ('  * ADMINISTRATION AND PERSONAL HAVE NEVER BEEN REVIEWED OR TESTED. Not\n    styling, not behaviour, not on Live. Assume unknown defects, not untidy\n    CSS.',
     '  * PERSONAL HAS NEVER BEEN REVIEWED OR TESTED. Not styling, not\n    behaviour, not on Live. Assume unknown defects, not untidy CSS. It is\n    the next section of work once the outstanding list is done.\n    Administration was brought into line with every other module on\n    20 Sep and has been tested on Live.'),
]

report, problems = [], []
planned = {}
CRLF = {}


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


b = read(BASE)
cur, n = b, 0
for old, new in EDITS:
    if new in cur:
        continue
    if cur.count(old) != 1:
        problems.append('base.html: anchor found %d time(s): %r'
                        % (cur.count(old), old[:60]))
        continue
    cur = cur.replace(old, new, 1)
    n += 1
if n:
    planned[BASE] = (b, cur)
    report.append('%-40s %d passage(s) of the standards block' % ('base.html',
                                                                  n))
else:
    report.append('%-40s already records them' % 'base.html')

if os.path.isfile(ROUNDS_FILE):
    r = read(ROUNDS_FILE)
    if "'%s'" % SUFFIX in r:
        report.append('%-40s already lists this round' % ROUNDS_FILE)
    elif r.count("    '.bak_oldrounds',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (r, r.replace(
            "    '.bak_oldrounds',\n]",
            "    '.bak_oldrounds',\n    '%s',\n]" % SUFFIX, 1))
        report.append('%-40s learns %s' % (ROUNDS_FILE, SUFFIX))
else:
    problems.append('%s missing - apply_old_rounds.py first' % ROUNDS_FILE)

GATE_NOTE = """    # base.html's standards block records the decisions of 16-22 Sep,
    # and still costs the visitor nothing. Newest, so most likely to be
    # what breaks.
    'test_standards_doc.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-40s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        if not m:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-40s + %s' % (PS1, SUITE))

# ---- SELF-CHECK: only the comment block moved, and it stays harmless -----
if BASE in planned:
    src, text = planned[BASE]
    blk = re.compile(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', re.S)
    if blk.sub('', src) != blk.sub('', text):
        problems.append('base.html: something outside the standards block '
                        'changed')
    m = blk.search(text)
    body_ = m.group(0)[len('{% comment %}'):-len('{% endcomment %}')] \
        if m else ''
    if re.search(r'<[a-zA-Z!/][^\s>]{0,24}', body_):
        problems.append('the block now holds something shaped like a tag')
    if '{' in body_ or '}' in body_:
        problems.append('the block now holds a brace')
    if ('/' + '*') in body_ or ('*' + '/') in body_:
        problems.append('the block now holds a CSS comment marker')
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', text, re.S))
    defined = set()
    for mm in re.finditer(r'([^{}]+)\{',
                          re.sub(r'/\*.*?\*/', '', css, flags=re.S)):
        defined.update(re.findall(r'\.([a-zA-Z][\w-]*)', mm.group(1)))
    for cls in re.findall(r'\.((?:alv|page|form|print)-[a-z0-9-]+)', body_):
        if cls not in defined and not cls.endswith('-'):
            problems.append('the block names .%s, which base does not '
                            'define' % cls)
    for s in set(re.findall(r'test_[a-z_]+\.py', body_)):
        if s != SUITE and not os.path.isfile(s):
            problems.append('the block cites %s, which is not in the repo'
                            % s)

print('\n' + '=' * 74)
print('THE STANDARDS BLOCK - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)
print('')
if problems:
    print('!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in sorted(set(problems)):
        print('  FAIL %s' % p)
    sys.exit(1)
if not planned:
    print('  Nothing to do - this round has already been applied.')
    sys.exit(0)
if CHECK:
    print('  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)
for path, (src, text) in sorted(planned.items()):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        CRLF[bak] = CRLF.get(path)
        write(bak, src)
    write(path, text)
print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('')
print('  Next:  python %s' % SUITE)
