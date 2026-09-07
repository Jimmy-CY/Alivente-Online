"""apply_fsr_palette.py - the Issues module's last two screens take base's
   colours, and one figure stops shouting the same thing at every age.

    python apply_fsr_palette.py --check     dry run, writes nothing
    python apply_fsr_palette.py

Run from the repo root. Round D. Closes 4 of the Issues module's 5 screens.

TWO FILES WITH ALMOST NO COLOUR OF THEIR OWN - THEY JUST DO NOT SAY SO.

    friday_status_report.html   69 rules, 12 distinct colours, 28 uses,
                                ZERO base tokens.
    fsr_details.html            88 rules, 16 distinct colours, 46 uses,
                                TWO tokens - both added last night by the
                                Notify round.

Almost every one of those literals already has a token that means the same
thing. #f8f9fa IS --alv-surface, byte for byte. #0e7c8b IS --alv-accent.
What was missing was not a palette, it was the reference.

THE ONE REAL DEFECT: A RED THAT MEANS NOTHING.

friday_status_report.html paints three different things #FF0000 - pure red,
statically, from two rules:

    .days-open        "- 257 days open"
    .days-open        "- New Issue"          (the days_open == 0 branch)
    .resolution-time  "- Resolution: 9 days" (a CLOSED issue)

So a brand-new issue is exactly as red as one open for 257 days, and the
turnaround on a job that is finished - good news - is red too. That is the
same defect round C2 found on this module's own Analysis modal, where the
"oldest open" tile carried a verdict class in the markup and read 12d in red
exactly as loudly as 300d. A verdict that cannot change is decoration.

RENDERED BEFORE IT WAS DECIDED, and the rendering settled two things an
argument would have got wrong.

  Coloured TEXT does not work here. The figure sits inside the issue heading,
  so at the weight it needs to carry a scale it becomes louder than the issue
  title itself - and a bold green "New Issue" reads as a verdict on a problem.

  The CHIP survives paper. Printed in mono the colour is gone but the words
  "257 days open" are still there. That is base's own stated condition for a
  defensible scale - "every graded cell prints its own figure" - and today's
  #FF0000 fails it completely: printed, it is a flat grey saying nothing.

So: an .alv-age-pill on the ageing scale, full wording, on the SAME bands the
Analysis modal already uses. A resolved issue's turnaround becomes a neutral
pill - it is a fact about the past, not something ageing.

THE BANDS NOW LIVE IN TWO PLACES, and that is worth naming rather than
hiding. fsr.html's AGE_BANDS is JavaScript because the modal computes them
from a dataset; here days_open arrives from the view as a number, so the
banding is a Django {% if %} chain. Two spellings of one rule. The suite
reads the thresholds OUT of fsr.html and asserts the template chain agrees,
so the duplication cannot drift silently.

SIX RULES IN THESE TWO FILES HAVE NO USER AT ALL - checked against the
markup, the scripts, and every other template and view in the repo:

    .issue-date      fsr_details    - and this is the OTHER #FF0000, so the
                                     round's headline was nearly wrong twice
    .btn-info        fsr_details    - a filled teal Bootstrap override
    .ei-edit-btn     fsr_details    - appears nowhere in the repo
    .status-title    fsr_details    - used on the FSR, not here
    .back-button     FSR            - named only by that file's own @print

They are deleted, and the suite pins each one absent. Finding them first is
why this note does not claim four red figures were fixed: only two rules and
three markup sites were ever live.

.comment-submit WAS DRIFTING INVISIBLY, which is the subtlest thing here. The
button sweep already made it `btn action-primary`, and base wins on colour -
so a colour audit sees nothing wrong. But base does not set padding or weight
at that specificity, so the page rule still lands:

    now                        42px tall, font-weight 500
    base's .action-primary     38px tall, font-weight 400

Four pixels and a weight, on the same teal, next to a Cancel button that is
38px. Only the skin is deleted; white-space, flex-shrink and the phone
width:100% are layout and stay.

THE EMPTY STATE JOINS THE OTHER TEN. "No Issues to Display" was a 4rem green
tick on a green dashed card - four page-local rules plus two more in @print
and four on the phone. base's .alv-empty is on ten pages already. The
celebration goes: base's empty state does not congratulate you, it says there
is nothing here. #28a745 leaves the file with it.

THE TWO BADGES WERE NOT STATUSES. "Summarized Report (Max 3 comments per
issue)" was a filled teal slab; "Detailed Report (All comments)" a filled
green one. Green there does not mean good, it means detailed - colour
encoding WHICH VARIANT, which is the same mistake the Notify round removed
from the amber button last night and the tint round removed from comment
authors on 1 Sep. Both are neutral pills now: they say which report you are
holding, and neither is news.

NOT THIS ROUND, DELIBERATELY.

  The tinted issue header on fsr_details - #e8f4f8 with a 4px teal bar - takes
  --alv-accent-soft and --alv-accent so the file can honestly say it spells no
  colour by hand. WHETHER a tinted banner is right at all is the teal banner
  round's question, and it will look at all 24 instances together rather than
  set a precedent from a sample of one.

  The bare @media (max-width: 768px) on both files still reaches paper. The
  print round measured what those blocks DO - one display:none on
  .action-back-label, whose parent .header-actions the @print block already
  hides, and otherwise pure sizing - and classified them as needing a read
  rather than a fix. A later round quietly reversing that call would make the
  record unreliable, so they are left and this is the note saying why.

  #ecd9a8 on fsr_details stays. It is the Notify round's tinted border,
  chosen deliberately as page-local last night with one asker; base has twice
  declined to build on one.

HOUSE RULES: idempotent, .bak_fsrpal backups never overwritten, --check
writes nothing, SELF-CHECK BEFORE WRITING, guards PER FILE.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
FSR = os.path.join(T, 'friday_status_report.html')
FD = os.path.join(T, 'fsr_details.html')
IA = os.path.join(T, 'fsr.html')
for _p in (FSR, FD, IA):
    if not os.path.exists(_p):
        sys.exit('! %s not found - run from the repo root' % _p)


def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    return raw, ('\r\n' in raw), raw.replace('\r\n', '\n')


def sub1(t, old, new, what):
    n = t.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %r'
                 % (what, n, old[:110]))
    return t.replace(old, new, 1)


def drop_rule(text, selector, what, expect=1):
    """Delete a whole rule by brace-walking. Line-anchored, so `.badge` does
       not match `.badge-info`."""
    pat = re.compile(r'(?m)^[ \t]*' + re.escape(selector) + r'[ \t]*\{')
    hits = list(pat.finditer(text))
    if len(hits) != expect:
        sys.exit('! %s: %r matched %d rule openings, expected %d'
                 % (what, selector, len(hits), expect))
    for m in reversed(hits):
        i, depth, k = m.start(), 1, m.end()
        while depth and k < len(text):
            if text[k] == '{':
                depth += 1
            elif text[k] == '}':
                depth -= 1
            k += 1
        if depth:
            sys.exit('! %s: unbalanced braces after %r' % (what, selector))
        while k < len(text) and text[k] in '\r\n':
            k += 1
        text = text[:i] + text[k:]
    return text


# ---------------------------------------------------------------------------
# THE LITERAL SWEEP, AND WHY IT REFUSES TO ENTER A COMMENT
# ---------------------------------------------------------------------------
# A CHECK THAT READS TEXT CATCHES PROSE - twenty-two instances in this
# project. This is the same hazard one step earlier: a SWEEP that reads text
# EDITS prose. friday_status_report.html carries the comment-tint round's
# note, which says in as many words that the old wash set text to "#ff8c00 or
# #0e7c8b". A blanket replace would rewrite that sentence into a claim about
# tokens the 1 Sep round never made, and the record would quietly become
# false.
#
# So the sweep splits each <style> block on its comments and edits only the
# gaps. Comments are returned untouched, and the self-check asserts that the
# note still reads exactly as it did.
STYLE = re.compile(r'(<style[^>]*>)(.*?)(</style>)', re.S)
COMMENT = re.compile(r'/\*.*?\*/', re.S)


def sweep_css(text, mapping):
    """Replace colour literals inside <style> blocks, never inside comments.
       Returns (new text, {literal: count replaced})."""
    tally = {k: 0 for k in mapping}

    def one_block(m):
        head, body, tail = m.group(1), m.group(2), m.group(3)
        out, last = [], 0
        for c in COMMENT.finditer(body):
            out.append(('code', body[last:c.start()]))
            out.append(('note', c.group(0)))
            last = c.end()
        out.append(('code', body[last:]))
        rebuilt = []
        for kind, chunk in out:
            if kind == 'code':
                for lit, tok in mapping.items():
                    n = len(re.findall(re.escape(lit) + r'\b', chunk))
                    if n:
                        tally[lit] += n
                        chunk = re.sub(re.escape(lit) + r'\b', tok, chunk)
            rebuilt.append(chunk)
        return head + ''.join(rebuilt) + tail

    return STYLE.sub(one_block, text), tally


FAIL = []


def want(cond, msg):
    if not cond:
        FAIL.append(msg)


# ===========================================================================
# THE BANDS, READ OUT OF fsr.html RATHER THAN RETYPED
# ===========================================================================
# The Analysis modal is the definition. Retyping 30 / 90 / 180 here would
# make this file a second source of truth for the same rule, and the two
# would agree until the day somebody changed one.
_ia = load(IA)[2]
_m = re.search(r'var\s+AGE_BANDS\s*=\s*\[(.*?)\]\s*;', _ia, re.S)
if not _m:
    sys.exit('! could not read AGE_BANDS out of fsr.html')
# Parsed object by object, with min / max / cls looked up independently -
# the first draft assumed they were adjacent and matched zero bands, because
# a `c:GOOD` sits between max and cls. A scan that assumes a field ORDER is a
# guess about somebody else's formatting.
BANDS = []
for _obj in re.findall(r'\{([^{}]*)\}', _m.group(1)):
    _lo = re.search(r'\bmin\s*:\s*(\d+)', _obj)
    _hi = re.search(r'\bmax\s*:\s*([\d.e+]+)', _obj)
    _cl = re.search(r'\bcls\s*:\s*[\'"]([\w-]+)', _obj)
    if not (_lo and _hi and _cl):
        sys.exit('! an AGE_BANDS entry in fsr.html has no min/max/cls: %r'
                 % _obj[:60])
    _hv = float(_hi.group(1))
    BANDS.append((int(_lo.group(1)),
                  None if _hv >= 10 ** 8 else int(_hv),
                  _cl.group(1)))
if len(BANDS) != 4:
    sys.exit('! expected 4 ageing bands in fsr.html, got %d' % len(BANDS))


def band_chain(var):
    """The Django {% if %} chain that spells fsr.html's AGE_BANDS."""
    parts = []
    for i, (lo, hi, cls) in enumerate(BANDS):
        kw = 'if' if i == 0 else 'elif'
        if hi is None:
            parts.append('{%% else %%}%s' % cls)
        else:
            parts.append('{%% %s %s <= %d %%}%s' % (kw, var, hi, cls))
    return ''.join(parts) + '{% endif %}'


CHAIN = band_chain('issue.days_open')
QUIET = BANDS[0][2]           # the "not ageing" step - alv-age-0

# ===========================================================================
# 1. friday_status_report.html
# ===========================================================================
S_ORIG, S_CRLF, s = load(FSR)
S_DONE = 'alv-age-pill' in s
if S_DONE:
    print('  friday_status_report.html already patched')
else:
    # ---------------------------------------------- 1a. MARKUP: the badges
    # Not statuses. They say which VARIANT of the report you are holding, and
    # a filled green slab reading "Detailed" claims a verdict it does not have.
    s = sub1(s, """                    <span class="badge badge-info">
                        <i class="fas fa-compress-alt"></i>
                        Summarized Report (Max {{ max_comments }} comment{{ max_comments|pluralize }} per issue)
                    </span>""",
             """                    <span class="alv-pill alv-pill-neutral report-type-pill">
                        <i class="fas fa-compress-alt"></i>
                        Summarized Report (Max {{ max_comments }} comment{{ max_comments|pluralize }} per issue)
                    </span>""", 'FSR: the Summarized badge')
    s = sub1(s, """                    <span class="badge badge-success">
                        <i class="fas fa-list-ul"></i>
                        Detailed Report (All comments)
                    </span>""",
             """                    <span class="alv-pill alv-pill-neutral report-type-pill">
                        <i class="fas fa-list-ul"></i>
                        Detailed Report (All comments)
                    </span>""", 'FSR: the Detailed badge')

    # ----------------------------------------- 1b. MARKUP: the empty state
    s = sub1(s, """                <div class="no-issues-container">
                    <div class="no-issues-card">
                        <div class="no-issues-icon">
                            <i class="fas fa-check-circle"></i>
                        </div>
                        <h3 class="no-issues-title">No Issues to Display</h3>
                        <p class="no-issues-message">
                            There are no issues to be displayed for this period.<br>
                            All properties are operating without any reported issues.
                        </p>
                    </div>
                </div>""",
             """                <div class="alv-empty">
                    <i class="fas fa-check-circle"></i>
                    <div class="alv-empty-title">No issues to display</div>
                    <div class="alv-empty-hint">
                        Nothing was reported for this period - every property is
                        operating without a logged issue.
                    </div>
                </div>""", 'FSR: the empty state')

    # ------------------------------------- 1c. MARKUP: the ageing figures
    s = sub1(s, """                                        {% if issue.days_to_resolve and status_group.status == 'Resolved' %}
                                            <span class="resolution-time">- Resolution: {{ issue.days_to_resolve }} day{{ issue.days_to_resolve|pluralize }}</span>
                                        {% elif issue.days_open and status_group.status != 'Resolved' %}
                                            <span class="days-open">- {{ issue.days_open }} day{{ issue.days_open|pluralize }} open</span>
                                        {% elif issue.days_open == 0 and status_group.status != 'Resolved' %}
                                            <span class="days-open">- New Issue</span>
                                        {% endif %}""",
             """                                        {% if issue.days_to_resolve and status_group.status == 'Resolved' %}
                                            <span class="alv-pill alv-pill-neutral issue-age">Resolution: {{ issue.days_to_resolve }} day{{ issue.days_to_resolve|pluralize }}</span>
                                        {% elif issue.days_open and status_group.status != 'Resolved' %}
                                            <span class="alv-age-pill issue-age @@CHAIN@@">{{ issue.days_open }} day{{ issue.days_open|pluralize }} open</span>
                                        {% elif issue.days_open == 0 and status_group.status != 'Resolved' %}
                                            <span class="alv-age-pill issue-age @@QUIET@@">New Issue</span>
                                        {% endif %}""".replace('@@CHAIN@@', CHAIN).replace('@@QUIET@@', QUIET),
             'FSR: the three ageing figures')

    # ------------------------------------------ 1d. CSS: the dead and the
    #                                                 replaced rules
    # ORDER MATTERS HERE. The phone block sets both red figures in ONE
    # grouped rule, `.days-open,\n .resolution-time {`. drop_rule is line-
    # anchored, so it would match that rule on its SECOND selector and walk
    # the braces from there - deleting the body and leaving an orphan
    # `.days-open,` line behind, which is a syntax error that reads like a
    # rule. So the grouped one goes first, by hand, and only then are the
    # counts below true.
    s = sub1(s, """        .days-open,
        .resolution-time {
            margin-left: 4px;
        }

""", '', 'FSR: the phone rule for the red pair')

    # Counts MEASURED, not assumed: several of these are declared again in
    # the phone block and twice more in @print.
    for sel, what, n in (
            ('.badge', 'FSR: the badge shell', 2),
            ('.badge-info', 'FSR: the teal slab', 1),
            ('.badge-success', 'FSR: the green slab', 1),
            ('.no-issues-container', 'FSR: empty wrapper', 1),
            ('.no-issues-card', 'FSR: empty card', 3),
            ('.no-issues-icon', 'FSR: empty icon', 3),
            ('.no-issues-title', 'FSR: empty title', 2),
            ('.no-issues-message', 'FSR: empty message', 2),
            ('.days-open', 'FSR: the red age', 1),
            ('.resolution-time', 'FSR: the red turnaround', 1)):
        s = drop_rule(s, sel, what, n)

    # .back-button is named only by this file's own @print, with nothing
    # anywhere in the repo carrying the class.
    s = sub1(s, """        .back-button,
        .header-actions {""", '        .header-actions {',
             'FSR: the dead .back-button in @print')

    # -------------------------------------------- 1e. CSS: the literals
    FSR_MAP = {
        '#2c3e50': 'var(--alv-ink)',
        '#495057': 'var(--alv-ink)',
        '#6c757d': 'var(--alv-ink-soft)',
        '#f8f9fa': 'var(--alv-surface)',
        '#ffffff': 'var(--alv-paper)',
        '#dee2e6': 'var(--alv-line)',
        '#ced4da': 'var(--alv-line)',
        '#0e7c8b': 'var(--alv-accent)',
        '#0a5e6a': 'var(--alv-accent-ink)',
    }
    s, FSR_TALLY = sweep_css(s, FSR_MAP)
    s = STYLE.sub(lambda m: m.group(1) + re.sub(
        r'\b(background(?:-color)?)\s*:\s*(?:#fff{1,2}|white)\b',
        r'\1: var(--alv-paper)', m.group(2), flags=re.I) + m.group(3), s)

    # ------------------------------------ 1f. CSS: what the chips need, and
    #                                            nothing that carries colour
    # Anchored on the DECLARATION, not the selector alone: .view-all-link is
    # declared twice, and by this point the sweep has already turned its
    # literal into a token - so the anchor has to be the post-sweep text.
    s = sub1(s, """    .view-all-link {
        color: var(--alv-accent);""",
             """    .issue-heading .issue-age {
        margin-left: 8px;
        vertical-align: 2px;
    }

    .report-type-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    .view-all-link {
        color: var(--alv-accent);""", 'FSR: the chip and pill layout rules')

# ===========================================================================
# 2. fsr_details.html
# ===========================================================================
D_ORIG, D_CRLF, d = load(FD)
D_DONE = '--alv-accent-soft' in d
if D_DONE:
    print('  fsr_details.html already patched')
else:
    # ------------------------------------------------- 2a. the four dead
    for sel, what, n in (('.btn-info', 'FD: the dead teal slab', 1),
                         ('.btn-info:hover', 'FD: its hover', 1),
                         ('.ei-edit-btn', 'FD: a class with no user', 2),
                         ('.issue-date', 'FD: the OTHER #FF0000', 1),
                         ('.status-title', 'FD: the FSR\'s rule, here', 1)):
        d = drop_rule(d, sel, what, n)

    # ------------------------------- 2b. .comment-submit stops out-shouting
    # base wins the colour, so this reads as harmless. It is not: base does
    # not set padding or weight at that specificity, so the page rule still
    # lands and the button comes out 42px at weight 500 beside a 38px Cancel.
    # Only the SKIN goes; white-space and flex-shrink are layout.
    d = sub1(d, """.comment-submit {
    background-color: #0e7c8b;
    color: white;
    border: 1px solid #0e7c8b;
    padding: 8px 12px;
    border-radius: 4px;
    font-weight: 500;
    white-space: nowrap;
    transition: all 0.3s ease;
    flex-shrink: 0;
}""", """.comment-submit {
    white-space: nowrap;
    flex-shrink: 0;
}""", 'FD: the Save Comment skin')
    d = drop_rule(d, '.comment-submit:hover', 'FD: its hover', 1)
    d = sub1(d, """    .comment-submit {
        width: 100%;
        padding: 10px 12px;
    }""", """    .comment-submit {
        width: 100%;
    }""", 'FD: the phone padding that made it 42px')

    # -------------------------------------------- 2c. the literals
    FD_MAP = {
        '#2c3e50': 'var(--alv-ink)',
        '#495057': 'var(--alv-ink)',
        '#6c757d': 'var(--alv-ink-soft)',
        '#f8f9fa': 'var(--alv-surface)',
        '#e9ecef': 'var(--alv-line)',
        '#ffffff': 'var(--alv-paper)',
        '#ced4da': 'var(--alv-line)',
        '#dee2e6': 'var(--alv-line)',
        '#e8f4f8': 'var(--alv-accent-soft)',
        '#0e7c8b': 'var(--alv-accent)',
        '#0a5e6a': 'var(--alv-accent-ink)',
        '#b02a37': 'var(--alv-bad)',
        '#146c43': 'var(--alv-good)',
    }
    d, FD_TALLY = sweep_css(d, FD_MAP)

    # WHITE IS TWO DIFFERENT TOKENS, AND ONLY THE DECLARATION KNOWS WHICH.
    # A literal map keyed on the colour alone gets this wrong: the edit-issue
    # modal writes #fff three times - once as the dialog's SURFACE and twice
    # as text sitting on the teal gradient header. base has a token for each
    # (--alv-paper, --alv-on-accent) and they are not interchangeable; a
    # paper-coloured heading is only correct by accident today and wrong the
    # moment either token moves. So these are swept by DECLARATION.
    def _white(text):
        text = re.sub(r'\b(background(?:-color)?)\s*:\s*(?:#fff{1,2}|white)\b',
                      r'\1: var(--alv-paper)', text, flags=re.I)
        text = re.sub(r'\bcolor\s*:\s*(?:#fff{1,2}|white)\b',
                      'color: var(--alv-on-accent)', text, flags=re.I)
        return text

    d = STYLE.sub(lambda m: m.group(1) + _white(m.group(2)) + m.group(3), d)

# ===========================================================================
# THE PROSE GOES LAST - after the sweep, never before it
# ===========================================================================
# ORDER OF OPERATIONS, learned the hard way two rounds ago: an explanatory
# comment names the literals it explains, so writing it BEFORE the sweep lets
# the sweep rewrite the explanation into a claim nobody made.
if not S_DONE:
    s = sub1(s, """    .issue-heading .issue-age {""",
             """    /* THE RED WAS NOT A SCALE - 5 Sep.

       .days-open and .resolution-time were both #FF0000, flat, from the
       markup. So "New Issue" (the days_open == 0 branch) was exactly as red
       as "257 days open", and the turnaround on a CLOSED issue - good news -
       was red as well. A verdict that cannot change is decoration, which is
       what round C2 said about the Analysis modal's oldest-open tile.

       The figure is an .alv-age-pill on the SAME bands fsr.html computes, and
       the suite reads those bands out of fsr.html rather than trusting this
       file. A resolved issue's turnaround is a neutral pill: a fact about the
       past, not something ageing.

       WHY A CHIP AND NOT COLOURED TEXT. Rendered both ways first. The figure
       sits inside the issue heading, and at the weight a scale needs it ends
       up louder than the issue title. The chip also survives paper: printed
       in mono the colour goes but "257 days open" is still there, which is
       base's own condition for a defensible scale. #FF0000 printed grey and
       said nothing. */
    .issue-heading .issue-age {""", 'FSR: say why the red went')

if not D_DONE:
    d = sub1(d, """.comment-submit {
    white-space: nowrap;""",
             """/* THE SKIN CAME OFF THIS ONE, NOT THE CLASS - 5 Sep.

   The button sweep already made it `btn action-primary`, and base wins on
   colour, so nothing looked wrong. But base does not set padding or weight at
   that specificity: the page rule still landed and the button came out 42px
   tall at weight 500 next to a 38px Cancel. Same teal, wrong size - which is
   why a colour audit found nothing for a week.

   white-space and flex-shrink are layout in a flex row and stay. */
.comment-submit {
    white-space: nowrap;""", 'FD: say why the skin went')

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
_snc = COMMENT.sub('', re.sub(r'<!--.*?-->', '', s, flags=re.S), )
_dnc = COMMENT.sub('', re.sub(r'<!--.*?-->', '', d, flags=re.S), )

# --- the round's own claims, per file -------------------------------------
want('#FF0000' not in _snc, 'FSR: a #FF0000 survives outside a comment')
want('#FF0000' not in _dnc, 'FD: a #FF0000 survives outside a comment')
want('#28a745' not in _snc, 'FSR: the Bootstrap green survives')
for lit in ('#2c3e50', '#6c757d', '#f8f9fa', '#dee2e6', '#ced4da',
            '#0e7c8b', '#0a5e6a', '#495057'):
    want(lit not in _snc, 'FSR: the literal %s survives' % lit)
    want(lit not in _dnc, 'FD: the literal %s survives' % lit)
for lit in ('#e8f4f8', '#e9ecef', '#b02a37', '#146c43'):
    want(lit not in _dnc, 'FD: the literal %s survives' % lit)
# #ecd9a8 STAYS. It is the Notify round's page-local warn tint, decided last
# night with one asker, and a check wider than its round reports the rest of
# the file as a defect - fourth time this week.
want('#ecd9a8' in _dnc, 'FD: the Notify round\'s tint was swept by mistake')

# --- the six dead rules, each pinned absent -------------------------------
for sel in ('.issue-date', '.btn-info', '.ei-edit-btn', '.status-title'):
    want(not re.search(r'(?m)^\s*' + re.escape(sel) + r'\s*[,{]', _dnc),
         'FD: the dead rule %s is still declared' % sel)
want('.back-button' not in _snc, 'FSR: the dead .back-button is still named')
for sel in ('.badge-info', '.badge-success', '.no-issues-card',
            '.days-open', '.resolution-time'):
    want(sel not in _snc, 'FSR: %s survives' % sel)

# --- the ageing chain agrees with fsr.html --------------------------------
want(CHAIN in _snc, 'FSR: the band chain does not match fsr.html\'s AGE_BANDS')
want(_snc.count('alv-age-pill') == 2,
     'FSR: expected two age chips, got %d' % _snc.count('alv-age-pill'))
want(_snc.count('alv-pill alv-pill-neutral') == 3,
     'FSR: expected 3 neutral pills (2 badges + the turnaround), got %d'
     % _snc.count('alv-pill alv-pill-neutral'))
want('alv-empty-title' in _snc and 'alv-empty-hint' in _snc,
     'FSR: the empty state did not migrate to base')

# --- THE DELTA, measured against the BACKUP when there is one -------------
# On a second run the ORIG is already the patched file, so a delta against it
# is zero and the check reports a correct file as broken.
def _before(path, orig):
    b = path + '.bak_fsrpal'
    return load(b)[2] if os.path.exists(b) else orig.replace('\r\n', '\n')


for _tag, _path, _orig, _now in (('FSR', FSR, S_ORIG, _snc),
                                 ('FD', FD, D_ORIG, _dnc)):
    _was = COMMENT.sub('', _before(_path, _orig))
    _w = len(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', _was)))
    _n = len(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', _now)))
    want(_n < _w, '%s: no literal left the file (%d -> %d distinct)'
         % (_tag, _w, _n))
want(len(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', _snc))) == 0,
     'FSR: %s still spelled by hand'
     % sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', _snc))))
want(sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', _dnc))) == ['#ecd9a8'],
     'FD: expected only the Notify tint left, got %s'
     % sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', _dnc))))
# No bare `white` keyword either, in either file - it is the same literal
# wearing a different spelling, and a claim of "no colour by hand" that only
# counts hexes is a claim about notation.
for _tag, _t2 in (('FSR', _snc), ('FD', _dnc)):
    want(not re.search(r':\s*white\b', _t2, re.I),
         '%s: a bare `white` keyword survives' % _tag)
# The gradient header takes --alv-on-accent for its TEXT, not --alv-paper.
want('linear-gradient' not in _dnc or 'var(--alv-on-accent)' in _dnc,
     'FD: the gradient header lost its on-accent ink')

# --- the comment-tint round's note must read exactly as it did ------------
# The sweep refuses to enter a comment; this is the check that says so.
_NOTE = 'author and body all set to #ff8c00 or #0e7c8b at weight 600'
for _tag, _t in (('FSR', s), ('FD', d)):
    want(_NOTE in _t,
         '%s: the sweep rewrote the comment-tint round\'s note' % _tag)

# --- structure -------------------------------------------------------------
for _tag, _t in (('FSR', s), ('FD', d)):
    for blk in re.findall(r'<style[^>]*>(.*?)</style>', _t, re.S):
        want(blk.count('{') == blk.count('}'),
             '%s: unbalanced braces in a style block' % _tag)
    # PROSE THAT CONTAINS MARKUP IS MARKUP.
    for _m2 in COMMENT.finditer(_t):
        want(not re.search(r'</?(?:script|style)\b', _m2.group(0)),
             '%s: a CSS comment spells a script or style tag' % _tag)
    want(len(re.findall(r'<style[^>]*>', _t))
         == len(re.findall(r'</style>', _t)), '%s: a style tag is unbalanced'
         % _tag)
# The Django tags in the chain have to balance, or the page 500s.
want(_snc.count('{% if') + _snc.count('{% elif') + _snc.count('{% else')
     >= _snc.count('{% endif %}'), 'FSR: an if/endif is unbalanced')

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)


def save(p, orig, crlf, new, done):
    if done:
        return
    out = new.replace('\n', '\r\n') if crlf else new
    # BYTES, NOT CHARACTERS. len() of a str counts characters, and these two
    # files carry '\u2264' and '\u2014' in their comments - three bytes each,
    # one character each. The printed figure was eight short of what wc -c
    # sees, and a push body that quotes it is quoting the wrong unit.
    print('  %-30s %d -> %d bytes'
          % (os.path.basename(p), len(orig.encode('utf-8')),
             len(out.encode('utf-8'))))
    if CHECK:
        return
    bak = p + '.bak_fsrpal'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(orig)
        print('    backup -> %s' % os.path.basename(bak))
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)


save(FSR, S_ORIG, S_CRLF, s, S_DONE)
save(FD, D_ORIG, D_CRLF, d, D_DONE)
print('\n  --check: nothing written.' if CHECK else '\n  done.')
