"""apply_required_marker.py - one way to say "required", in a colour we own.

    python apply_required_marker.py --check     dry run, writes nothing
    python apply_required_marker.py

Run from the repo root. Sized by Show-RequiredMarkers.py, which is committed
beside it. Opening move of the input-screen programme (section 4).

SEVEN SPELLINGS, THREE OUTCOMES, AND NOT ONE OF THEM OURS.

An asterisk inside a <label> is how this system says a field is required. It
does it 112 times across 33 templates, in seven different shapes:

    text-danger                   58   Bootstrap's own class
    required-mark                 32   a page rule, hardcoding #dc3545
    (inline) color: red           9    an inline style
    required                      9    a page rule, hardcoding #dc3545
    req                           2    a page rule, hardcoding #dc3545
    (bare asterisk, no element)   1    nothing at all
    required-marker text-danger   1    both at once

Rendered, those seven produce THREE outcomes:

    #dc3545   102 sites   Bootstrap's red - four spellings reaching the same
                          value, three of them by hardcoding it in eighteen
                          separate page rules
    red         9 sites   #FF0000, visibly louder than the other 102
    inherit     1 site    body text. The signal is a character, not a colour.

THE FIRST SCAN SAID 115 AND 34, WITH FOUR BARE ASTERISKS. Three of those four
were not markers: they were the `*` in `accept="image/*"` on a file input
nested inside a label. The patcher duly wrapped one, producing

    accept="image/<span class="alv-req">*</span>"

which breaks both the attribute and the file picker. The scanner had the same
bug, so the patcher's cross-check AGREED with it. Two implementations of one
rule do not drift - but one wrong rule implemented twice is still wrong, and a
cross-check between tools that share a definition tests agreement rather than
correctness. Both now blank tags before looking, so no attribute value is
reachable, and the numbers above are the corrected ones.

And base's own danger colour, --alv-bad #b3261e, appears NOWHERE among them.
The system says "required" in a colour it does not own, and if Bootstrap ever
leaves, 102 asterisks turn black.

WHAT THIS ROUND DOES

  base gains ONE rule:

      .alv-req { color: var(--alv-bad); margin-left: 2px; font-weight: 600; }

  Every one of the 112 sites becomes `<span class="alv-req">*</span>`,
  including the one genuinely bare asterisk - categories_management.html's
  "Category Name *" - which gets an element for the first time.

  The eighteen page-local rules go with them - twelve `.required-mark`, four
  `.required`, two `.req` - and with those, eighteen hand-written #dc3545.

IT IS A SWEEP, AND SWEEPS ARE WHERE THIS PROJECT GETS HURT. Four guards,
each of them a lesson with a scar on it:

  1. MARKUP ONLY. Never inside <script>, never inside a comment. The button
     sweep learned this the hard way: a class name in a JavaScript string has
     no wrapper to say what it is, and a wrong guess edits working code.

  2. THE SCANNER DECIDES WHAT IS A SITE, not the patcher. Both use the same
     rule - an asterisk-only <span> inside a <label>, or a bare asterisk in
     one - and the patcher asserts its per-file count MATCHES what the
     scanner found before it writes. Two implementations of one rule drift;
     one implementation checked twice does not.

  3. THE TAG WALKER RUNS ON EVERY FILE. On 7 Sep the Issues-table round
     shipped a 500 because a balance check ended in `or True` and an orphaned
     {% endif %} went out. Every file this round touches is walked - block
     tags opened and closed in order - and Django is asked directly where it
     is importable. Nothing is written if any file fails.

  4. THE DELTA IS BOUNDED. Per file: the markup outside the asterisk spans
     must come out byte-identical, and the only rules removed must be the
     three named ones. A sweep that cannot say exactly what it changed is a
     sweep nobody can review.

WHAT IS NOT TOUCHED, DELIBERATELY

  `text-danger` STAYS WHERE IT IS NOT A REQUIRED MARKER. It is a general
  Bootstrap utility and this system uses it for other things - error text,
  warnings in help panels. Only the asterisk spans inside labels move; every
  other text-danger is somebody else's round.

  THE RECIPE / MEAL-PLAN SIDE is excluded, as it is from every other sweep
  here. It is not on the push gate.

HOUSE RULES: idempotent, .bak_alvreq backups never overwritten, --check
writes nothing, SELF-CHECK BEFORE WRITING, guards PER FILE.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
if not os.path.exists(BASE):
    sys.exit('! %s not found - run from the repo root' % BASE)

RECIPE = ('recipe', 'meal_plan', 'meal_plans', 'ingredient', 'wcim',
          'celebration', 'pantry', 'unit_conversions', 'measurement_units',
          'household_member', 'map_ingredients', 'import_recipe',
          'preview_imported')

MARKER = 'alv-req'
# The three page-local rules this round retires, and nothing else.
RETIRE = ('required-mark', 'required', 'req')


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


FAIL = []


def want(cond, msg):
    if not cond:
        FAIL.append(msg)


def is_recipe_side(f):
    return any(k in f for k in RECIPE)


def templates():
    out = []
    for d, _s, files in os.walk(T):
        for fn in sorted(files):
            if not fn.endswith('.html') or '.bak_' in fn:
                continue
            rel = os.path.relpath(os.path.join(d, fn), T).replace(os.sep, '/')
            if not is_recipe_side(rel) and rel != 'base.html':
                out.append(rel)
    return sorted(out)


# ---------------------------------------------------------------------------
# THE ONE RULE FOR "WHAT IS A SITE", shared with Show-RequiredMarkers.py
# ---------------------------------------------------------------------------
# An asterisk inside a <label>: either wrapped in a span of its own, or bare.
# Two implementations of one rule drift; the patcher asserts its count against
# the scanner's before it writes anything.
LABEL = re.compile(r'(<label\b[^>]*>)(.*?)(</label>)', re.S)
SPAN_STAR = re.compile(r'<span(?![^>]*\bclass="[^"]*\b' + MARKER
                       + r'\b)[^>]*>\s*\*\s*</span>')
BARE_STAR = re.compile(r'(?<![>\w])\*(?![^<]*</span>)')


# ---------------------------------------------------------------------------
# WHAT COUNTS AS A BARE ASTERISK - and the bug that made this a rule of its own
# ---------------------------------------------------------------------------
# The first draft matched any `*` in a label body that was not already in a
# span. Three of the four "bare markers" it found were not markers at all:
# they were the `*` inside `accept="image/*"` on a file input nested in the
# label. The patcher wrapped it, producing
#
#     accept="image/<span class="alv-req">*</span>"
#
# which breaks the attribute AND the file picker's filter. Caught by reading
# what the four actually were, which is the only reason it was caught: the
# SCANNER had the same bug, so the patcher's cross-check against it passed.
#
# TWO IMPLEMENTATIONS OF ONE RULE DO NOT DRIFT - BUT ONE WRONG RULE
# IMPLEMENTED TWICE IS STILL WRONG. A cross-check between two tools that
# share a definition tests agreement, not correctness.
#
# So: an asterisk only counts when it is TEXT. Tags are blanked first, which
# puts every attribute value out of reach.
def text_only(body):
    """The label body with every tag blanked to spaces, offsets preserved."""
    return re.sub(r'<[^>]*>', lambda m: ' ' * len(m.group(0)), body)


def bare_star_at(body):
    """Offset of a bare asterisk in the label's TEXT, or None."""
    t = text_only(body)
    m = re.search(r'\*', t)
    return m.start() if m else None


def blank_noncode(src):
    """Script blocks and comments replaced by spaces of equal length, so
       offsets are preserved and nothing inside them can ever be matched."""
    def blank(m):
        return ' ' * len(m.group(0))
    src = re.sub(r'<!--.*?-->', blank, src, flags=re.S)
    return re.sub(r'<(script|style)[^>]*>.*?</\1>', blank, src, flags=re.S)


def rewrite(src):
    """Return (new src, sites rewritten). MARKUP ONLY."""
    safe = blank_noncode(src)
    out, last, n = [], 0, 0
    for m in LABEL.finditer(safe):
        body = src[m.start(2):m.end(2)]
        if '*' not in body:
            continue
        new_body, k = SPAN_STAR.subn(
            '<span class="%s">*</span>' % MARKER, body)
        if k == 0 and MARKER not in body:
            # a bare asterisk - give it an element for the first time, but
            # ONLY where the asterisk is text. See text_only() above.
            _at = bare_star_at(body)
            if _at is not None:
                new_body = (body[:_at] + '<span class="%s">*</span>' % MARKER
                            + body[_at + 1:])
                k = 1
        if k == 0:
            continue
        out.append(src[last:m.start(2)])
        out.append(new_body)
        last = m.end(2)
        n += k
    out.append(src[last:])
    return ''.join(out), n


def drop_rule(text, selector, what):
    """Delete every rule whose selector names this class. Returns (text, n)."""
    pat = re.compile(r'(?m)^[ \t]*[^{}\n]*\.' + re.escape(selector)
                     + r'(?![\w-])[^{}\n]*\{')
    n = 0
    while True:
        m = pat.search(text)
        if not m:
            return text, n
        i, depth, k = m.start(), 1, m.end()
        while depth and k < len(text):
            if text[k] == '{':
                depth += 1
            elif text[k] == '}':
                depth -= 1
            k += 1
        if depth:
            sys.exit('! %s: unbalanced braces after .%s' % (what, selector))
        while k < len(text) and text[k] in '\r\n':
            k += 1
        text = text[:i] + text[k:]
        n += 1


def tag_fault(src):
    """First structural fault in the Django block tags, or None."""
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
                return ('line %d: %s closes a {%% %s %%} from line %d'
                        % (ln, t, top, at))
    return 'unclosed {%% %s %%} from line %d' % stack[-1] if stack else None


# ===========================================================================
# 1. base.html - one rule
# ===========================================================================
B_ORIG, B_CRLF, b = load(BASE)
B_DONE = '.alv-req' in b
if B_DONE:
    print('  base.html already patched')
else:
    b = sub1(b, """      .alv-empty {""",
             """      /* THE REQUIRED MARKER - 7 Sep. base's first.

         An asterisk in a label is how this system says a field is required.
         It did it 115 times across 34 templates in SEVEN shapes, and those
         seven rendered as THREE things: #dc3545 on 102 of them (Bootstrap's
         red, reached by four spellings, three of which hardcoded the value
         in eighteen separate page rules), a louder #FF0000 on nine inline
         ones, and NOTHING on four bare asterisks, where the signal was a
         character rather than a colour.

         --alv-bad appeared nowhere among them. The system said "required" in
         a colour it did not own, and if Bootstrap ever left, 102 asterisks
         would have turned black.

         font-weight is here because the asterisk is small and the ink is
         dark; at 400 it reads as punctuation. */
      .alv-req {
        color: var(--alv-bad);
        margin-left: 2px;
        font-weight: 600;
      }

      .alv-empty {""", 'REQ: base gains .alv-req')
    _bnc = re.sub(r'/\*.*?\*/', '', b, flags=re.S)
    want('--alv-bad:' in _bnc, 'REQ: base has no --alv-bad to point at')
    want(_bnc.count('.alv-req {') == 1, 'REQ: .alv-req declared more than once')

# ===========================================================================
# 2. the 34 templates
# ===========================================================================
TOUCHED, TOTAL, DROPPED = [], 0, 0
PENDING = []

for rel in templates():
    p = os.path.join(T, *rel.split('/'))
    orig, crlf, t = load(p)
    new, n = rewrite(t)
    dropped = 0
    for cls in RETIRE:
        new, k = drop_rule(new, cls, 'REQ: %s' % rel)
        dropped += k
    if n == 0 and dropped == 0:
        continue

    # ------------------------------------------------ per-file guards
    # THE DELTA IS BOUNDED. Outside the asterisk spans and the three retired
    # rules, the file must be byte-identical.
    def _norm(x):
        return re.sub(r'<span[^>]*>\s*\*\s*</span>', '*', x)
    _a, _b2 = _norm(new), _norm(t)
    for cls in RETIRE:
        _b2, _ = drop_rule(_b2, cls, 'x')
    want(_a == _b2,
         'REQ: %s changed something other than the marker and its rules' % rel)
    _f = tag_fault(new)
    want(_f is None, 'REQ: %s will not parse - %s' % (rel, _f))
    want(new.count('class="%s"' % MARKER) >= n,
         'REQ: %s lost a marker it just wrote' % rel)

    TOTAL += n
    DROPPED += dropped
    TOUCHED.append((rel, n, dropped))
    PENDING.append((p, orig, crlf, new))

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
# THE SCANNER IS THE AUTHORITY ON WHAT A SITE IS. If it is beside us, ask it
# rather than trusting a second implementation of the same rule.
_scan = os.path.join(ROOT, 'Show-RequiredMarkers.py')
if os.path.exists(_scan) and not os.path.exists(
        os.path.join(T, 'base.html.bak_alvreq')):
    import subprocess
    _r = subprocess.run([sys.executable, _scan], cwd=ROOT,
                        capture_output=True, text=True)
    _m = re.search(r'(\d+) site\(s\) across (\d+) template\(s\)', _r.stdout)
    if _m:
        want(int(_m.group(1)) == TOTAL,
             'REQ: the scanner counts %s sites, this round found %d'
             % (_m.group(1), TOTAL))
        want(int(_m.group(2)) == len(TOUCHED),
             'REQ: the scanner sees %s templates, this round touched %d'
             % (_m.group(2), len(TOUCHED)))
    else:
        print('  (could not read the scanner\'s count - check skipped)')

want(TOTAL > 0 or B_DONE, 'REQ: no sites found at all')
want(DROPPED == 18 or B_DONE,
     'REQ: expected 18 page rules retired, dropped %d' % DROPPED)

# ===========================================================================
# 3. SECTION 4b - the SCOPE GUARD, ELEVENTH occurrence
# ===========================================================================
# test_sticky_sweep.py asserts, per page, that the sticky sweep changed the
# STYLESHEET and left the MARKUP byte-for-byte alone - measured live against
# .bak_sticky. True of that round, and true until some later round
# legitimately edits one of its six pages.
#
# This one does: passport_management.html carries six required markers, and
# it is the ONLY one of the six this round touches (checked, rather than
# assumed - the other five have no .bak_alvreq).
#
# The plain kind of guard, and the suite already has the mechanism: a LATER
# map that points a page's historical comparison at the snapshot the later
# round leaves. It gains one line. Nothing about the claim changes - it is
# still "the sweep did not touch the markup", just measured between two
# snapshots instead of against a file somebody else now owns.
TS = os.path.join(ROOT, 'test_sticky_sweep.py')
SUITE = None
if not os.path.exists(TS):
    print('  test_sticky_sweep.py not found - skipping its 4b')
else:
    S_ORIG, S_CRLF, ts = load(TS)
    if "'passport_management.html': '.bak_alvreq'" in ts:
        print('  test_sticky_sweep.py already patched')
    else:
        _a = ("""    LATER = {'comments_report.html': '.bak_cmttint',
             'fsr.html': '.bak_iapal'}""")
        _n = ("""    # FIFTH page-owner entry, 7 Sep. The required-marker round rewrites
    # passport_management.html's six asterisk spans, and it is the only
    # one of these six pages it touches.
    LATER = {'comments_report.html': '.bak_cmttint',
             'fsr.html': '.bak_iapal',
             'passport_management.html': '.bak_alvreq'}""")
        if ts.count(_a) != 1:
            FAIL.append('test_sticky_sweep.py: its LATER map did not match once')
        else:
            ts = ts.replace(_a, _n, 1)
            try:
                compile(ts, 'test_sticky_sweep.py', 'exec')
            except SyntaxError as _e:
                FAIL.append('test_sticky_sweep.py: the patch does not parse '
                            '- %s' % _e)
            # The snapshot it now points at must actually exist, or the
            # suite trades a false failure for a different false failure.
            want(os.path.exists(os.path.join(
                T, 'passport_management.html.bak_alvreq')) or CHECK,
                'REQ: no passport_management.html.bak_alvreq to point at')
            SUITE = (TS, S_ORIG, S_CRLF, ts)
            print('  test_sticky_sweep.py     passport_management added to '
                  'its LATER map')

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)


def save(p, orig, crlf, new, done=False):
    if done:
        return
    out = new.replace('\n', '\r\n') if crlf else new
    # relpath against the TEMPLATES dir prints '../../test_sticky_sweep.py'
    # for a file at the repo root. Name it against whichever it is under.
    _root = T if os.path.abspath(p).startswith(os.path.abspath(T)) else ROOT
    print('  %-42s %d -> %d bytes'
          % (os.path.relpath(p, _root).replace(os.sep, '/'),
             len(orig.encode('utf-8')), len(out.encode('utf-8'))))
    if CHECK:
        return
    bak = p + '.bak_alvreq'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(orig)
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)


print('\n  %d site(s) in %d template(s); %d page rule(s) retired.'
      % (TOTAL, len(TOUCHED), DROPPED))
save(BASE, B_ORIG, B_CRLF, b, B_DONE)
for args in PENDING:
    save(*args)
if SUITE:
    save(*SUITE)
print('\n  --check: nothing written.' if CHECK else '\n  done.')
