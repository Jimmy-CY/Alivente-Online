# -*- coding: utf-8 -*-
"""apply_horizon_cards.py - Section D, round D8: a time horizon is not a
status, and the zoom-guard note stops inventing pages.

    python apply_horizon_cards.py --check     dry run, nothing written
    python apply_horizon_cards.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

Decided 25 Sep, from claude/outstanding_plan_25_sep.md.

PART ONE - cashflow_forecast's three summary cards.

D5 left these alone on purpose and wrote down why: "those are applied, and
they are a question for their own round". This is that round, and the
question had three answers nobody had measured.

  FAULT ONE - TWO OF THE THREE FAIL CONTRAST, on production, today.
  White text on each header, measured:

      Current Month   #dc3545   4.53   passes, just
      Next 3 Months   #fd7e14   2.57   FAILS even for large text
      Next 12 Months  #28a745   3.13   large text only, and the h6 is 13px

  FAULT TWO - THE HEADER FIGHTS THE FIGURE UNDERNEATH IT. Each card's
  body already carries status colour where it means something:

      .cf-net.cf-pos .cf-val { color: var(--alv-accent); }
      .cf-net.cf-neg .cf-val { color: var(--alv-bad); }

  So a card HEADED RED showing a POSITIVE Net in teal says two opposite
  things at once, and the one place colour is meaningful on that card is
  drowned by a header that means nothing.

  FAULT THREE - IT IS A SEQUENCE WEARING STATUS COLOURS. Current Month /
  Next 3 / Next 12 is an ordered horizon. Nothing about the current month
  is bad and nothing about twelve months out is good. 3.1 says colour
  means something and is not decoration; this is the opposite.

  DECIDED: all three take the house accent, like every other card header
  in the system. The icon, the label and the date range in .cf-range
  already say which horizon it is - colour was adding nothing but noise
  and two contrast failures. White on --alv-accent measures 4.91.

  A sequential ramp was offered and declined. For the record it was
  workable: accent-ink / accent / accent-soft at 7.44 / 4.91 / 11.37 with
  the light end in ink, lightness monotonic 0.443 -> 0.538 -> 0.642. A
  three-step ramp keeping WHITE on all three is not available - three
  steps dark enough for 4.5:1 sit inside 0.1 of lightness and cannot be
  told apart.

  Six literals go. `.summary-card { background: white }` STAYS: it is the
  card's paper, not the header's paint, and swapping it is a different
  round's sweep.

PART TWO - test_zoom_guards.py's closing note was wrong on all four pages.

It has been printing, on every gate run:

  "4 page(s) shrink a text control below 16px and carry NO guard at all -
   on a phone those controls may be under 16px today: fsr_details.html,
   invoices.html, physical_invoice_list.html, suppliers.html"

RENDERED at 375, all four have ZERO controls under 16px:

    fsr_details              7 controls visible, 0 under 16px
    invoices                 2 controls visible, 0 under 16px
    physical_invoice_list    5 controls visible, 0 under 16px
    suppliers                2 controls visible, 0 under 16px

Why each was wrong:

  fsr_details            has a guard - `font-size: 16px !important;
                         /* iOS zoom guard */` in its own phone query
  physical_invoice_list  has a guard - `font-size: 16px` in its phone
                         query
  suppliers              .filter-title is an <h5>. iOS zooms a focused
                         FORM FIELD, not a heading
  invoices               .btn-outline-secondary is a BUTTON. Same

Two of those are the detector's fault and they are the same bug:
`guards()` recognises a control with

    (?<![-\\w])(input|select|textarea)(?![-\\w])

and every class on those pages is `.numbering-input`,
`.comment-input-full` - the word is preceded by a HYPHEN, so the
lookbehind rejects it and the guard is not counted. The other two are the
note trusting a selector that merely looks control-ish.

THE FIX IS NOT A BETTER REGEX. The suite already renders; the note is
rebuilt from the RENDER, at 375, on the same pages - so it can only ever
name a page whose controls really do measure small. A selector cannot be
guessed wrong if it is never consulted.
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
T = os.path.join('pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
SUFFIX = '.bak_horizon'
SUITE = 'test_horizon_cards.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS_FILE = 'alv_rounds.py'
CFF = os.path.join(T, 'finance', 'cashflow_forecast.html')
ZG = 'test_zoom_guards.py'

CRLF = {}
planned = {}
report = []
problems = []
swept = []


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


# ==========================================================================
# PART ONE - the three cards
# ==========================================================================
HEAD_OLD = """.summary-card .card-header {
    padding: 12px 20px;
    margin: 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}
"""
HEAD_NEW = """.summary-card .card-header {
    /* ONE HEADER FOR ALL THREE HORIZONS. [D8, 25 Sep]
       These wore #dc3545 / #fd7e14 / #28a745 - a time horizon painted in
       status colours. Two failed contrast with their own white text
       (2.57 and 3.13 against the 4.5 the text needs), and the red one
       sat above a POSITIVE Net drawn in teal by .cf-net.cf-pos, so the
       card said two opposite things at once. Current Month / Next 3 /
       Next 12 is a sequence, not a state: the icon, the label and the
       date range say which one it is. White on the accent is 4.91. */
    background: var(--alv-accent);
    padding: 12px 20px;
    margin: 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}
"""
H6_OLD = """.summary-card .card-header h6 {
    margin: 0;
    font-size: 13px;
    font-weight: 600;
    color: white;
"""
H6_NEW = """.summary-card .card-header h6 {
    margin: 0;
    font-size: 13px;
    font-weight: 600;
    color: var(--alv-on-accent);
"""
# The three that go. Matched whole, with their literals, so a page that
# has already been edited cannot be half-cut.
VARIANTS = """.summary-card.current-month .card-header {
    background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
}
.summary-card.short-term .card-header {
    background: linear-gradient(135deg, #fd7e14 0%, #e8630a 100%);
}
.summary-card.long-term .card-header {
    background: linear-gradient(135deg, #28a745 0%, #218838 100%);
}

"""

# ==========================================================================
# PART TWO - the zoom-guard note, rebuilt from the render
# ==========================================================================
NOTE_OLD = """    if guards(css_of(read(p))) == 0:
        unguarded.append(rel)
if unguarded:
    notes.append('%d page(s) shrink a text control below 16px and carry NO '
                 'guard at all - on a phone those controls may be under 16px '
                 'today: %s. Not this round\\'s to fix; measured and reported.'
                 % (len(unguarded), ', '.join(unguarded)))
"""
NOTE_NEW = """    if guards(css_of(read(p))) == 0:
        unguarded.append(rel)
# LATER - Section D round D8, 25 Sep. THIS NOTE USED TO BE PRINTED HERE,
# from `unguarded`, and it was wrong on all four pages it named:
#
#   fsr_details            HAS a guard - `font-size: 16px !important;
#                          /* iOS zoom guard */` in its own phone query
#   physical_invoice_list  HAS a guard - `font-size: 16px` in its phone
#                          query
#   suppliers              .filter-title is an <h5>; iOS zooms a focused
#                          FORM FIELD, not a heading
#   invoices               .btn-outline-secondary is a BUTTON. Same
#
# The first two are one bug in guards(): its control pattern is
# `(?<![-\\w])(input|select|textarea)(?![-\\w])`, and those pages spell
# their classes .numbering-input and .comment-input-full - the word is
# preceded by a HYPHEN, the lookbehind rejects it, and a real 16px guard
# goes uncounted. The other two are the note trusting a selector that
# merely looks control-ish.
#
# Rather than a better regex, the note is now built from the RENDER, at
# 375, in the browser section below - where a page can only be named if
# its controls really do measure small. `unguarded` is kept as the list
# of pages to LOOK at, which is all a selector can honestly give.
"""
RENDER_ANCHOR = """                             % (rel, x[1].lower(), x[3][:24], x[4], y[4]))
        br.close()
"""
RENDER_NEW = """                             % (rel, x[1].lower(), x[3][:24], x[4], y[4]))

        # ---- the note, MEASURED ----------------------------------- D8 --
        # Every page the selectors call unguarded, rendered at 375. Only a
        # control that really measures under 16px is reported, and when
        # none does the suite says so with the count it checked - a note
        # that can only ever shrink is how the last one stayed wrong.
        really, looked = [], 0
        for rel in unguarded:
            p = os.path.join(ROOT, rel)
            if not os.path.isfile(p):
                continue
            t = read(p)
            rows = render(br, page_html(boot, base_now, styles_of(t),
                                        body_markup(t)), 375)
            looked += len(rows)
            really += ['%s %s.%s %s' % (rel, c[1].lower(), c[3][:20], c[4])
                       for c in rows if float(c[4][:-2]) < 16]
        if really:
            notes.append('%d control(s) on the %d page(s) with no guard in '
                         'their own CSS really do measure below 16px at 375: '
                         '%s' % (len(really), len(unguarded),
                                 '; '.join(really[:6])))
        else:
            notes.append('%d page(s) have no 16px guard their CSS can be '
                         'read as carrying - and RENDERED at 375, %d control'
                         '(s) across them measure under 16px. The selector '
                         'says look; the render says there is nothing there. '
                         'Pages looked at: %s'
                         % (len(unguarded), len(really), ', '.join(unguarded)))
        br.close()
"""

# ==========================================================================
# LATER - the suite whose finding this round answers
# ==========================================================================
LATER = {}
# NO LATER EDIT IS NEEDED, AND THE FIRST DRAFT MADE ONE ANYWAY.
#
# test_series_scale.py checks `.summary-card.current-month .card-header`
# is still there and says those headers "are a question for their own
# round". That looked like a claim D8 would falsify, so this round
# re-pointed it - and BROKE it, because the check reads the file through
# alv_rounds.as_left_by at D5's suffix. What it is asking about is
# cashflow_forecast AS D5 LEFT IT, which is a backup on disk that D8
# cannot reach and must not. The claim was never in danger; the edit was.
#
# The rule is the one the scope guards already encode: before re-pointing
# an older suite, check whether it is asking about the file NOW or about
# the file as ITS round left it. Only the first kind can be broken by a
# later round. RUN IT FIRST - the sweep found this in one line.


# ==========================================================================
# WORK
# ==========================================================================
if not os.path.isfile(CFF):
    problems.append('%s not found' % CFF)
else:
    src = read(CFF)
    cur = src
    for label, old, new in (('the shared header', HEAD_OLD, HEAD_NEW),
                            ('its title', H6_OLD, H6_NEW),
                            ('the three variants', VARIANTS, '')):
        if new and new in cur:
            continue
        if not new and old not in cur:
            continue
        if cur.count(old) != 1:
            problems.append('cashflow_forecast: %s matched %d time(s)'
                            % (label, cur.count(old)))
            continue
        if not new:
            for ln in old.split('\n'):
                if 'linear-gradient' in ln:
                    swept.append(' '.join(ln.split())[:70])
        cur = cur.replace(old, new, 1)
    if cur != src:
        planned[CFF] = (src, cur)
        report.append('%-40s three horizons, one accent header'
                      % 'finance/cashflow_forecast.html')
    else:
        report.append('%-40s already done' % 'finance/cashflow_forecast.html')

if not os.path.isfile(ZG):
    problems.append('%s not found' % ZG)
else:
    src = read(ZG)
    cur, n = src, 0
    for old, new in ((NOTE_OLD, NOTE_NEW), (RENDER_ANCHOR, RENDER_NEW)):
        if new in cur:
            continue
        if old not in cur:
            continue
        if cur.count(old) != 1:
            problems.append('%s: an anchor matched %d time(s)'
                            % (ZG, cur.count(old)))
            continue
        cur = cur.replace(old, new, 1)
        n += 1
    if n:
        try:
            compile(cur, ZG, 'exec')
        except SyntaxError as e:
            problems.append('%s would not compile: line %s' % (ZG, e.lineno))
        planned[ZG] = (src, cur)
        report.append('%-40s the note is measured, not guessed (%d edit(s))'
                      % (ZG, n))
    else:
        report.append('%-40s already done' % ZG)

for sv, edits in sorted(LATER.items()):
    if not os.path.isfile(sv):
        problems.append('%s not found' % sv)
        continue
    src_ = read(sv)
    cur_, n_, done_ = src_, 0, 0
    for old_, new_ in edits:
        if new_ and new_ in cur_:
            done_ += 1
            continue
        if old_ not in cur_:
            done_ += 1
            continue
        if cur_.count(old_) != 1:
            problems.append('%s: anchor found %d time(s)'
                            % (sv, cur_.count(old_)))
            continue
        cur_ = cur_.replace(old_, new_, 1)
        n_ += 1
    if n_:
        try:
            compile(cur_, sv, 'exec')
        except SyntaxError as e:
            problems.append('%s would not compile: line %s' % (sv, e.lineno))
        planned[sv] = (src_, cur_)
        report.append('%-40s LATER: %d edit(s)' % (sv, n_))
    elif done_ == len(edits):
        report.append('%-40s LATER: already done' % sv)

# ==========================================================================
# SELF-CHECKS
# ==========================================================================
for path, (src, cur) in list(planned.items()):
    if path.endswith('.py'):
        continue
    name = os.path.basename(path)
    if cur.count('{') != cur.count('}'):
        problems.append('%s: braces are unbalanced' % name)
    if sorted(re.findall(r'\bid="([^"]+)"', cur)) \
            != sorted(re.findall(r'\bid="([^"]+)"', src)):
        problems.append('%s: an id changed' % name)
    if cur.count('{%') != src.count('{%') or cur.count('{{') != src.count('{{'):
        problems.append('%s: a Django tag changed' % name)
    if re.sub(r'<style[^>]*>.*?</style>', '', cur, flags=re.S | re.I) \
            != re.sub(r'<style[^>]*>.*?</style>', '', src, flags=re.S | re.I):
        problems.append('%s: the markup moved - this round cuts CSS only'
                        % name)
    if path == CFF:
        # The three CLASSES stay on the cards. They are what the script
        # targets by id and what a later round would need to tell them
        # apart; only their PAINT went.
        for cls in ('current-month', 'short-term', 'long-term'):
            if cur.count('summary-card %s' % cls) != src.count(
                    'summary-card %s' % cls):
                problems.append('%s: the %s card lost its class'
                                % (name, cls))
        # Comment-stripped, so the paragraph that records what they WERE
        # is not read as the rules surviving (lesson 34).
        body = re.sub(r'/\*.*?\*/', '', cur, flags=re.S)
        for sel in ('.summary-card.current-month .card-header',
                    '.summary-card.short-term .card-header',
                    '.summary-card.long-term .card-header'):
            if sel in body:
                problems.append('%s: %s survived' % (name, sel))
        # THE LITERALS THIS ROUND OWNS ARE THE ONES IN A GRADIENT. A first
        # draft asked whether #dc3545 appeared anywhere and failed on
        # `.alert-danger { border-color: #dc3545 }` - a danger alert, which
        # is red for the reason red exists. Scoped to the paint this round
        # removed; the alert's literal belongs to the literal sweep.
        for lit in ('#dc3545', '#fd7e14', '#28a745', '#c82333', '#e8630a',
                    '#218838'):
            for m in re.finditer(r'linear-gradient\([^)]*\)', body):
                if lit in m.group(0):
                    problems.append('%s: %s survived in a gradient'
                                    % (name, lit))
        if 'background: var(--alv-accent);' not in body:
            problems.append('%s: the accent did not land' % name)

# ==========================================================================
# REGISTERED, AND ON THE GATE
# ==========================================================================
if os.path.isfile(ROUNDS_FILE):
    r = read(ROUNDS_FILE)
    if "'%s'" % SUFFIX in r:
        report.append('%-40s already lists this round' % ROUNDS_FILE)
    elif r.count("    '.bak_backlabel',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS (.bak_backlabel) '
                        '- apply_back_label.py first' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (r, r.replace(
            "    '.bak_backlabel',\n]",
            "    '.bak_backlabel',\n    '%s',\n]" % SUFFIX, 1))
        report.append('%-40s learns %s' % (ROUNDS_FILE, SUFFIX))
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # Section D round D8: a time horizon is not a status - the three
    # cashflow summary cards take one accent header, two of which had been
    # failing contrast - and the zoom-guard note is measured, not guessed,
    'test_horizon_cards.py'"""
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
else:
    problems.append('%s missing' % PS1)

# ==========================================================================
print('\n' + '=' * 78)
print('SECTION D, ROUND D8 - A HORIZON IS NOT A STATUS - %s'
      % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 78)
for line in report:
    print('  ' + line)
if swept:
    print('\n  THE THREE HEADERS THIS ROUND REMOVED:')
    for s in swept:
        print('    %s' % s)
    print('    white text on them measured 4.53, 2.57 and 3.13;'
          ' the accent is 4.91')
print('')
if problems:
    print('!' * 78)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 78)
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
