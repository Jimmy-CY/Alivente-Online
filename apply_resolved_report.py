"""apply_resolved_report.py - the Resolved Issues Report stops alarming you
   about good news, and starts using base's colours.

    python apply_resolved_report.py --check     dry run, writes nothing
    python apply_resolved_report.py

Run from the repo root. The third and last screen of the report family; the
other two were done by round D on 5 Sep.

THE DEFECT: AN ALARM ON THE ONE PAGE THAT ONLY EVER CARRIES GOOD NEWS.

Every issue on this report is RESOLVED - that is what the page is. And the
turnaround figure beside each one is painted like a failure:

    <span style="color: red;">Resolution: {{ issue.days_to_resolve }} day…</span>

"Resolution: 0 days" - somebody fixed it the same day - in the loudest colour
this system has. It is the third screen carrying this exact defect. Round C2
found it on the Analysis modal's oldest-open tile; round D found it on the
Friday Status Report's `.days-open` and `.resolution-time`. This is the last
one.

THREE THINGS MAKE THIS INSTANCE WORSE THAN THE OTHER TWO.

  IT IS INLINE, so no stylesheet can reach it. The other two were page rules
  a round could retire.

  IT SPELLS A KEYWORD, `red`, not a hex. Every colour audit run this week
  counted hex literals; this file reports eight of them and the red is not
  among them. It was found by a scan written specifically to look for
  keywords, after the ten-inline-styles finding.

  AND THE PAGE ALREADY HAS A RULE FOR THIS FIGURE. `.resolution-time { color:
  #0e7c8b; font-weight: bold }` is declared and used by NOTHING - the markup
  carries an inline style instead. Somebody wrote the intent, then overrode
  it in the same file. The rule is deleted with the inline style: neither was
  right, and keeping the teal one would have been a third answer to a
  question round D already settled.

WHAT THE FIGURE BECOMES: exactly what the Friday Status Report shows for the
same thing - `<span class="alv-pill alv-pill-neutral issue-age">`. A closed
issue's turnaround is a fact about the past, not something ageing and not a
verdict. The same figure on two screens should look the same.

AND THE FILE HAD NEVER BEEN TOUCHED. 42 rules, ZERO base tokens, not one
`alv-*` class in its markup, and eight colours spelled by hand:

    #2c3e50  3   -> --alv-ink          #dee2e6  1   -> --alv-line
    #6c757d  3   -> --alv-ink-soft     #eee     1   -> --alv-line
    #495057  1   -> --alv-ink          #0e7c8b  2   -> --alv-accent
    #ffffff  1   -> --alv-paper        #f0f0f0  1   -> dies with .comment-user
    white    1   -> --alv-paper

TWO DEAD RULES GO. `.resolution-time`, above, and `.comment-user` - a chip
for a comment's author that no markup carries. Checked against the markup,
the script and the rest of the repo before deleting, which is the habit round
D's six dead rules bought.

ONE THING WORTH KNOWING RATHER THAN QUIETLY DELETING. `.comment-user` is a
CHIP rule - background, padding, radius - and the other three screens in this
module DO show a comment's author as a quiet `.alv-tag` chip, put there by the
comment-tint round on 1 Sep. This page shows it as plain text inside the date:
`2026-07-30 (SS):`. So the dead rule is the trace of an intention that was
never wired up, and deleting it removes the last sign of it. Whether this
page's authors should become chips like the other three is a SHAPE question,
not a colour one, and it is left open deliberately rather than folded in.

NOT THIS ROUND. The bare `@media (max-width: 768px)` stays bare. The print
round measured what these blocks do and classified this one as needing a read
rather than a fix, and a later round quietly reversing that call would make
the record unreliable - the same decision round D took on the other two
report screens.

HOUSE RULES: idempotent, .bak_rir backups never overwritten, --check writes
nothing, SELF-CHECK BEFORE WRITING, guards PER FILE.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
RIR = os.path.join(T, 'resolved_issues_report.html')
FSR = os.path.join(T, 'friday_status_report.html')
BASE = os.path.join(T, 'base.html')
for _p in (RIR, BASE):
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


def drop_rule(text, selector, what, expect):
    pat = re.compile(r'(?m)^[ \t]*' + re.escape(selector) + r'[ \t]*\{')
    hits = list(pat.finditer(text))
    if len(hits) != expect:
        sys.exit('! %s: %r matched %d openings, expected %d'
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


# THE SWEEP REFUSES TO ENTER A COMMENT. A sweep that reads text edits prose -
# the mirror of the twenty-three times a check that reads text has caught it.
STYLE = re.compile(r'(<style[^>]*>)(.*?)(</style>)', re.S)
COMMENT = re.compile(r'/\*.*?\*/', re.S)


def sweep_css(text, mapping):
    tally = {k: 0 for k in mapping}

    def one(m):
        head, body, tail = m.group(1), m.group(2), m.group(3)
        out, last = [], 0
        for c in COMMENT.finditer(body):
            out.append(('code', body[last:c.start()]))
            out.append(('note', c.group(0)))
            last = c.end()
        out.append(('code', body[last:]))
        parts = []
        for kind, chunk in out:
            if kind == 'code':
                for lit, tok in mapping.items():
                    n = len(re.findall(re.escape(lit) + r'\b', chunk))
                    if n:
                        tally[lit] += n
                        chunk = re.sub(re.escape(lit) + r'\b', tok, chunk)
            parts.append(chunk)
        return head + ''.join(parts) + tail

    return STYLE.sub(one, text), tally


def tag_fault(src):
    OPEN = {'if': 'endif', 'for': 'endfor', 'block': 'endblock',
            'with': 'endwith', 'comment': 'endcomment',
            'spaceless': 'endspaceless', 'autoescape': 'endautoescape'}
    CLOSE = {v: k for k, v in OPEN.items()}
    stack = []
    for m in re.finditer(r'\{%\s*(\w+)', src):
        t = m.group(1)
        ln = src.count('\n', 0, m.start()) + 1
        if t in OPEN:
            stack.append((t, ln))
        elif t in CLOSE:
            if not stack:
                return 'line %d: %s with nothing open' % (ln, t)
            top, at = stack.pop()
            if OPEN[top] != t:
                return ('line %d: %s closes {%% %s %%} from line %d'
                        % (ln, t, top, at))
    return 'unclosed {%% %s %%} from %d' % stack[-1] if stack else None


FAIL = []


def want(cond, msg):
    if not cond:
        FAIL.append(msg)


F_ORIG, F_CRLF, f = load(RIR)
DONE = 'alv-pill-neutral' in f
if DONE:
    print('  resolved_issues_report.html already patched')
else:
    # ------------------------------------------------- 1. the wrong verdict
    # Byte-identical to what friday_status_report.html shows for the same
    # figure. The same thing on two screens should look the same.
    f = sub1(f,
             """<span style="color: red;">Resolution: {{ issue.days_to_resolve }} day{{ issue.days_to_resolve|pluralize }}</span>""",
             """<span class="alv-pill alv-pill-neutral issue-age">Resolution: {{ issue.days_to_resolve }} day{{ issue.days_to_resolve|pluralize }}</span>""",
             'RIR: the red turnaround')

    # ------------------------------------- 1b. the dash left holding nothing
    # `({{ description }}) -` was a separator between two runs of TEXT, and it
    # read correctly while the figure was text. It is not one any more: the
    # figure is an object with its own edge, and the dash now dangles in front
    # of it - visible in the render, invisible to every check above. The
    # Friday report closes the bracket and puts the pill next to it, so this
    # does too. This is residue from the line above, not a second decision.
    f = sub1(f, """({{ issue.description }}) -\n""",
             """({{ issue.description }})\n""", 'RIR: the dangling dash')

    # ------------------------------------------------------ 2. the two dead
    # `.resolution-time` is a rule for the very figure above, overridden by
    # the inline style it sat beside. `.comment-user` is a chip nothing wears.
    f = drop_rule(f, '.resolution-time', 'RIR: the unused teal rule', 1)
    f = drop_rule(f, '.comment-user', 'RIR: a chip with no wearer', 2)

    # ------------------------------------------------------ 3. the literals
    RIR_MAP = {
        '#2c3e50': 'var(--alv-ink)',
        '#495057': 'var(--alv-ink)',
        '#6c757d': 'var(--alv-ink-soft)',
        '#ffffff': 'var(--alv-paper)',
        '#dee2e6': 'var(--alv-line)',
        '#eee': 'var(--alv-line)',
        '#0e7c8b': 'var(--alv-accent)',
    }
    f, TALLY = sweep_css(f, RIR_MAP)
    f = STYLE.sub(lambda m: m.group(1) + re.sub(
        r'\b(background(?:-color)?)\s*:\s*white\b',
        r'\1: var(--alv-paper)', m.group(2), flags=re.I) + m.group(3), f)

    # ------------------------------ 4. the chip needs the spacing the Friday
    #                                   report gives it, and nothing else
    # ONE selector, not two. The Friday report spells this
    # `.issue-heading .issue-age` because that is where its pill sits; here
    # the pill sits inside `.issue-description`. Copying BOTH halves across
    # would have shipped a selector that matches nothing on this page - a
    # brand-new dead rule, in the round that deletes two of them.
    #
    # Anchored on the DECLARATION: .issue-description is declared twice,
    # once here and once in the phone block. The sweep has already run, so
    # this anchor has to be text the sweep does not touch - a font-size.
    f = sub1(f, """    .issue-description {
        font-size: 1rem;""",
             """    .issue-description .issue-age {
        margin-left: 8px;
        vertical-align: 2px;
    }

    .issue-description {
        font-size: 1rem;""", 'RIR: the chip spacing')

    # ------------------------------------------- 5. the note, AFTER the sweep
    f = sub1(f, """    .issue-description .issue-age {""",
             """    /* THE TURNAROUND STOPPED BEING AN ALARM - 7 Sep.

       Every issue on this report is RESOLVED - that is what the page is -
       and the turnaround beside each one was painted `red` from an INLINE
       style. "Resolution: 0 days", a same-day fix, in the loudest colour
       the system has. Third screen with this defect: C2 found it on the
       Analysis modal, round D on the Friday report, this is the last.

       Being inline, no stylesheet could reach it. Being a KEYWORD rather
       than a hex, no colour audit this week could see it either - this file
       reports eight hex literals and the red was not among them.

       AND THE PAGE ALREADY HAD A RULE FOR THIS FIGURE. `.resolution-time`
       was declared teal and worn by nothing, because the markup carried the
       inline style instead. Both are gone: the figure is now the same
       neutral pill the Friday report shows, because the same figure on two
       screens should look the same. The `-` that used to separate the
       description from the figure went with it: it separated two runs of
       text, and there are no longer two runs of text to separate. */
    .issue-description .issue-age {""", 'RIR: say why the red went')

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
_nc = COMMENT.sub('', re.sub(r'<!--.*?-->', '', f, flags=re.S))
_css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', _nc, re.S))
_mk = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', _nc, flags=re.S)

want('color: red' not in _mk, 'RIR: the inline red survives')
want('style="' not in _mk,
     'RIR: an inline style survives - there was only ever one')
want('alv-pill alv-pill-neutral issue-age' in _mk,
     'RIR: the figure is not the Friday report\'s pill')

want(') -' not in _mk, 'RIR: the dangling dash survives')

# THE NEW RULE MUST MATCH SOMETHING. A selector added in the round that
# deletes two dead rules had better not be a third. Checked against the
# markup, not against what the Friday report happens to spell.
_desc = re.search(r'<span class="issue-description">(.*?)</span>\s*</span>',
                  _mk, re.S)
want(_desc is not None and 'issue-age' in _desc.group(1),
     'RIR: .issue-description .issue-age matches nothing on this page')
want('.issue-heading .issue-age' not in _css,
     'RIR: the Friday report\'s selector was copied across and is dead here')

for sel in ('.resolution-time', '.comment-user'):
    want(not re.search(r'(?m)^\s*' + re.escape(sel) + r'\s*[,{]', _css),
         'RIR: the dead rule %s survives' % sel)
    want(sel[1:] not in _mk, 'RIR: %s appears in the markup after all' % sel)

_hex = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', _css)))
want(not _hex, 'RIR: colours still spelled by hand: %s' % _hex)
want(not re.search(r':\s*white\b', _css, re.I),
     'RIR: a bare `white` keyword survives')
want(len(set(re.findall(r'--alv-[a-z0-9-]+', _css))) >= 5,
     'RIR: it does not reference base')

# Every token must EXIST in base, or the colour falls back to nothing.
_b = load(BASE)[2]
_bcss = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', _b, re.S))
_missing = [t for t in set(re.findall(r'var\(\s*(--alv-[a-z0-9-]+)', _css))
            if (t + ':') not in _bcss]
want(not _missing, 'RIR: base does not declare %s' % _missing)
for need in ('.alv-pill', '.alv-pill-neutral'):
    want(need in _bcss, 'base does not define %s' % need)

# THE SAME FIGURE ON TWO SCREENS. If the Friday report is there, the class
# list must match it exactly rather than approximately.
if os.path.exists(FSR):
    _fsr = load(FSR)[2]
    _m = re.search(r'<span class="([^"]*)">Resolution:', _fsr)
    want(_m is not None and ('<span class="%s">Resolution:' % _m.group(1))
         in _mk,
         'RIR: the pill does not match the Friday report\'s exactly (%s)'
         % (_m.group(1) if _m else 'not found there either'))

# THE DELTA, against the backup when there is one.
_before = F_ORIG.replace('\r\n', '\n')
_bak = RIR + '.bak_rir'
if os.path.exists(_bak):
    _before = load(_bak)[2]
_wascss = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>',
                               COMMENT.sub('', _before), re.S))
want(len(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', _wascss))) >= 7,
     'RIR: the backup does not look like the pre-round file')

_f = tag_fault(f)
want(_f is None, 'RIR: the template will not parse - %s' % _f)
for blk in re.findall(r'<style[^>]*>(.*?)</style>', f, re.S):
    want(blk.count('{') == blk.count('}'), 'RIR: unbalanced braces')
for _m2 in COMMENT.finditer(f):
    want(not re.search(r'</?(?:script|style)\b', _m2.group(0)),
         'RIR: a CSS comment spells a script or style tag')

# NOT THIS ROUND, asserted so it reads as a decision.
want(re.search(r'@media\s*\(\s*max-width', f) is not None,
     'RIR: the bare phone query was changed - that is the print round\'s call')

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)


def save(p, orig, crlf, new, done):
    if done:
        return
    out = new.replace('\n', '\r\n') if crlf else new
    print('  %-32s %d -> %d bytes'
          % (os.path.basename(p), len(orig.encode('utf-8')),
             len(out.encode('utf-8'))))
    if CHECK:
        return
    bak = p + '.bak_rir'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(orig)
        print('    backup -> %s' % os.path.basename(bak))
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)


save(RIR, F_ORIG, F_CRLF, f, DONE)
print('\n  --check: nothing written.' if CHECK else '\n  done.')
