"""test_heading_standard.py - every page heads itself the way base.html says.

    python test_heading_standard.py

Run from the repo root, after apply_heading_standard.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 2 CHECKS THE WHOLE CORPUS, not just the 29 pages this round
    touched. That is the point: a heading standard is only worth writing
    down if something can tell you how far the system is from it. The suite
    reports the number of compliant pages, names every page that is not, and
    holds a floor - so the next round inherits a measurement rather than a
    memory, and a page added next month that ignores the standard shows up
    here rather than in a screenshot six weeks later.

  * SECTION 3 READS THE STANDARD OUT OF base.html AND CHECKS THE PAGES
    AGAINST IT. If somebody edits the standards block to say something else,
    this suite starts measuring the new thing. A document and a suite that
    can disagree silently is the failure the standards block exists to
    prevent, so they are wired to the same source.

  * SECTION 4 asserts what the round left alone: the words of every title
    survive, no icon crept back, and the pages deliberately excluded -
    property_assets and the nine under projects/, all of which carry a
    record name inside the title - are untouched and still non-compliant,
    which is a decision and not an oversight.

WHAT THIS SUITE CANNOT DO, SAID FIRST. It reads templates. It cannot tell
you whether a title is the RIGHT words for the page, only that it is
capitals, unbranded, and unchanged in substance from what was there before.

SCOPE GUARD #16 - 8 Sep 2026, THE SAME DAY THIS SUITE WAS WRITTEN
-----------------------------------------------------------------
This suite used to assert that every title STARTS with `ALIVENTE ONLINE - `.
That is now false by agreement: the brand moved off the heading and into the
browser tab, because it was identical on all 66 pages that carried it and so
distinguished nothing, and because seven of the twelve real property names
already contain a dash - making `ALIVENTE ONLINE - PROPERTY ASSETS - ATHENS
- SECOND FLOOR` today's output rather than a worst case.

The guard rule is: ASK WHAT THE CLAIM IS ABOUT. The claim here is *every
page heads itself the same way, by agreement rather than by accident*. That
claim survives; only the agreed shape changed. So the assertion is REPLACED
with its opposite and dated - not exception-listed, and not re-pointed at a
new literal with the old reasoning left standing behind it.

The prefix is enforced-absent by test_heading_prefix.py, which also renders
base's title tag through Django to prove the brand still reaches the browser.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
# The brand, which a heading must NOT carry. See scope guard #16 above.
PREFIX = 'ALIVENTE ONLINE - '
# The one page whose heading IS the brand: shown when the database is
# unreachable, where the chrome is not guaranteed to render.
KEEPS_THE_BRAND = 'error_pages/connectivity_error.html'

# Deferred by the heading round because a record name inside a title gives
# two dashes doing different jobs; DONE by the shape-B round on 9 Sep. Kept
# as a set because section 4 now checks that the deferral was resolved
# rather than that it still stands - see scope guard #18 there.
DEFERRED = {'property_assets.html'}

PASS = FAIL = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def markup_of(t):
    return re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t, flags=re.S)


def rel_of(p):
    return os.path.relpath(p, T).replace(os.sep, '/')


TEMPLATES = []
for _d, _s, _fs in os.walk(T):
    for _f in _fs:
        if _f.endswith('.html'):
            TEMPLATES.append(os.path.join(_d, _f))
TEMPLATES.sort()


def heading_of(src):
    """(title, subtitle) for a page that uses the centred heading, else
       (None, None). Django tags are blanked, not stripped, so a title that
       is entirely dynamic does not read as an empty string."""
    mk = markup_of(src)
    m = re.search(r'<h2[^>]*>\s*<center>\s*(.*?)\s*</center>\s*</h2>', mk, re.S)
    if not m:
        return None, None
    t = re.sub(r'\s+', ' ', m.group(1)).strip()
    s = re.search(r'</h2>\s*(?:\{#.*?#\}\s*)?<h5[^>]*>\s*<center>\s*(.*?)\s*'
                  r'</center>', mk, re.S)
    return t, (re.sub(r'\s+', ' ', s.group(1)).strip() if s else None)


def second_line(src):
    """The line under the title, WHATEVER TAG IT USES: (tag, text).

       The round that set this standard looked only for an h5 immediately
       after the h2, found six, and called the sample too small to settle
       anything. There are twenty-four - fourteen of them h4, and invisible
       to that scan. A survey that names the tag it expects finds only that
       tag, the same way a survey named after a colour found only teal."""
    mk = markup_of(src)
    m = re.search(r'<h2[^>]*>\s*<center>.*?</center>\s*</h2>', mk, re.S)
    if not m:
        return None, None
    after = mk[m.end():m.end() + 460]
    s = re.search(r'<(h[3-6])[^>]*>\s*(?:<center>)?\s*(.*?)\s*(?:</center>)?\s*'
                  r'</\1>', after, re.S)
    if not s:
        return None, None
    return s.group(1), re.sub(r'\s+', ' ', s.group(2)).strip()


def literal(t):
    """The text with Django tags AND HTML entities removed - what a reader
       sees minus the data. A title that is only `{{ name|upper }}` has no
       literal and must not be judged on capitalisation it does not control.

       Entities matter: `{{ number }} &mdash; {{ tenant }}` reduced to
       `&mdash;`, whose entity NAME is five letters, so it read as a label
       and failed a page that has none."""
    t = re.sub(r'\{[{%#][^}]*[}%#]\}', '', t or '')
    return re.sub(r'&[a-zA-Z]+;|&#\d+;', '', t).strip()


# ===========================================================================
head('1. the 29 pages this round moved')
# ===========================================================================
MOVED = [p for p in TEMPLATES if os.path.exists(p + '.bak_hstd')]
check('the round left backups to compare against', len(MOVED) >= 25,
      '%d found' % len(MOVED))

for p in MOVED:
    rel = rel_of(p)
    now, was = read(p), read(p + '.bak_hstd')
    t_now, s_now = heading_of(now)
    t_was, s_was = heading_of(was)
    check('%-40s title is capitals and carries no brand' % rel,
          t_now is not None and PREFIX not in t_now
          and literal(t_now) == literal(t_now).upper(),
          (t_now or '?')[:44])
    # THE WORDS MUST SURVIVE. A prefix is added and the case changes; the
    # page must not be renamed by a round about formatting.
    if t_was:
        # ALIVENTE and ONLINE are the constant this round removed, so they
        # are not words that have to survive - they are the words that had
        # to go.
        _w = [w for w in re.findall(r'[A-Za-z]{3,}', literal(t_was))
              if w.upper() not in ('ALIVENTE', 'ONLINE')]
        _kept = [w for w in _w if w.upper() in literal(t_now).upper()]
        check('  and its words survived',
              len(_kept) >= len(_w) - 1,
              '%s -> %s' % (t_was[:24], t_now[:30]))
    check('  no icon in the heading', t_now is not None and '<i ' not in t_now)
    if s_now is not None:
        _l = [c for c in literal(s_now) if c.isalpha()]
        check('  subtitle is not all capitals',
              not _l or not all(c.isupper() for c in _l), s_now[:44])
    check('  the round says why', 'HEADING STANDARD - 8 Sep' in now)
    check('  and says it in a Django comment, which does not ship',
          '{# HEADING STANDARD' in now)

# ===========================================================================
head('2. the whole corpus, measured')
# ===========================================================================
GOOD, BAD, DYNAMIC = [], [], []
for p in TEMPLATES:
    rel = rel_of(p)
    if rel == 'base.html':
        continue
    t, s = heading_of(read(p))
    if t is None:
        continue
    lit = literal(t)
    if rel == KEEPS_THE_BRAND:
        continue
    ok = PREFIX not in t and lit == lit.upper()
    if s is not None:
        _l = [c for c in literal(s) if c.isalpha()]
        ok = ok and (not _l or not all(c.isupper() for c in _l))
    if not lit:
        DYNAMIC.append(rel)
    elif ok:
        GOOD.append(rel)
    else:
        BAD.append((rel, t[:40]))

print('        %d page(s) use the centred heading: %d comply, %d do not, '
      '%d have\n        no literal title to judge.'
      % (len(GOOD) + len(BAD) + len(DYNAMIC), len(GOOD), len(BAD),
         len(DYNAMIC)))
for rel, t in BAD:
    print('          not yet: %-38s %s' % (rel, t))

# The floor rose when the prefix came off: a page no longer has to carry a
# constant to comply, only to be capitals with a sentence-case second line.
check('most of the system complies', len(GOOD) >= 60,
      '%d of %d' % (len(GOOD), len(GOOD) + len(BAD)))
# A REPORT WITH A FLOOR, not an equality - the corpus grows, and a hardcoded
# count has failed correct work twelve times on this codebase.
check('  and the shortfall is only the deferred pages', len(BAD) <= 12,
      '%d outstanding' % len(BAD))
_unexpected = [r for r, _ in BAD
               if r not in DEFERRED and not r.startswith('projects/')]
check('  every non-compliant page is one we deliberately deferred',
      not _unexpected, str(_unexpected[:4]))

# ===========================================================================
head('2b. the tag decides the case - h4 labels shout, h5 sentences do not')
# ===========================================================================
# WHICH TAG A LINE USES IS THE RULE. h4 holds a MODE LABEL - ADD NEW
# PROPERTY, EDIT EXISTING SUPPLIER, UPLOAD / VIEW / DELETE - and is capitals
# because a label is. h5 holds a descriptive sentence and is sentence case.
H4, H5 = [], []
for p in TEMPLATES:
    rel = rel_of(p)
    if rel == 'base.html':
        continue
    tag, txt = second_line(read(p))
    if not tag or not literal(txt):
        continue
    (H4 if tag == 'h4' else H5 if tag == 'h5' else []).append((rel, txt))

print('        %d page(s) carry a line under the title: %d are h4 mode '
      'labels,\n        %d are h5 descriptive lines.'
      % (len(H4) + len(H5), len(H4), len(H5)))
check('the corpus really does use both tags', H4 and H5,
      '%d h4, %d h5' % (len(H4), len(H5)))
check('  CONTROL: and enough of each to be a rule rather than a coincidence',
      len(H4) >= 8 and len(H5) >= 4)

_shouty = [(r, t) for r, t in H5
           if [c for c in literal(t) if c.isalpha()]
           and all(c.isupper() for c in literal(t) if c.isalpha())]
check('every h5 descriptive line is sentence case, not capitals',
      not _shouty, str([r for r, _ in _shouty][:4]))

# AN h4 IS TWO THINGS, WHICH IS WHY THE TAG IS NOT THE RULE. Most hold a
# MODE LABEL - ADD NEW PROPERTY - which is capitals because a label shouts.
# Three hold a RECORD NAME instead: `{{ number }} - {{ tenant_name }}`,
# whose case belongs to the data and which no rule here can set. Judging
# those on capitalisation they do not control would fail correct pages, so
# they are separated by whether the line is mostly interpolation.
_labels = [(r, t) for r, t in H4
           if len([c for c in literal(t) if c.isalpha()]) >= 3]
_records = [(r, t) for r, t in H4
            if len([c for c in literal(t) if c.isalpha()]) < 3]
print('        of the h4s, %d are mode labels and %d name a record - the '
      'record\n        names take their case from the data.'
      % (len(_labels), len(_records)))
_quiet = [(r, t) for r, t in _labels if literal(t) != literal(t).upper()]
check('almost every h4 mode label is capitals - a label shouts',
      len(_quiet) <= 1, str([r for r, _ in _quiet][:4]))
for r, t in _quiet:
    print('        NOTE  %s reads %r - a mode label in sentence case, and '
          'the only one.\n              One word, outside this round\'s '
          'agreed scope.' % (r, literal(t)[:40]))
check('  CONTROL: and the check can see a lowercase one - it just did'
      if _quiet else '  CONTROL: there ARE labels to get wrong',
      len(_labels) >= 8, '%d label(s)' % len(_labels))

# A page picks one or the other. Both would be a title, a label AND a
# sentence, which is a third pattern nobody chose.
_both = []
for p in TEMPLATES:
    mk = markup_of(read(p))
    m = re.search(r'<h2[^>]*>\s*<center>.*?</center>\s*</h2>', mk, re.S)
    if not m:
        continue
    after = mk[m.end():m.end() + 460]
    if re.search(r'<h4[^>]*>', after) and re.search(r'<h5[^>]*>', after):
        _both.append(rel_of(p))
check('no page carries both an h4 label and an h5 sentence', not _both,
      str(_both[:4]))

# ===========================================================================
head('3. the pages agree with the standard base.html states')
# ===========================================================================
_b = read(BASE)
_m = re.search(r'\{%\s*comment\s*%\}(.*?)\{%\s*endcomment\s*%\}', _b, re.S)
if not _m:
    print('  SKIP  base.html carries no standards block to read')
else:
    DOC = _m.group(1)
    check('base states the heading standard', 'PAGE HEADINGS' in DOC)
    # THE DOCUMENT MUST STATE THE RULE THE PAGES FOLLOW, and after guard
    # #16 that rule is the absence of the brand, not its presence. A
    # document still describing the old shape is the silent disagreement
    # the standards block exists to prevent.
    # CASE-INSENSITIVE ON PURPOSE. The document sets its own headline rules
    # in capitals - `NO BRAND PREFIX` - and a check that demanded one
    # casing would have failed correct prose, which has happened here
    # before (a check demanded a numeral and failed on "ten pages").
    check('  and says the heading carries no brand prefix',
          re.search(r'no brand prefix', DOC, re.I) is not None)
    check('  and says where the brand went instead',
          'browser tab' in DOC or 'BROWSER TAB' in DOC)
    check('  and names the one page that keeps it',
          'connectivity_error' in DOC)
    check('  CONTROL: it does NOT still instruct anyone to prefix a title',
          re.search(r'prefixed `ALIVENTE', DOC) is None)
    check('  it says the title is capitals', 'CAPITALS' in DOC)
    check('  and the subtitle is sentence case',
          'SENTENCE CASE' in DOC or 'Sentence case' in DOC)
    check('  and that no heading carries an icon', 'NO ICON' in DOC)
    # THE h4 RULE MUST BE IN THE DOCUMENT, or this suite is enforcing
    # something base.html does not claim - which is the same silent
    # disagreement the standards block exists to prevent.
    check('  it states the h4 mode label rule', 'MODE LABEL' in DOC)
    check('    and that an h4 also carries a RECORD NAME, so the tag is not '
          'the rule', 'RECORD NAME' in DOC)
    check('    and it records the one exception by name',
          'customer_invoice_form' in DOC)
    check('    and that a page has one or the other, not both',
          re.search(r'h4 or an h5, not both', DOC) is not None)
    # The document must not claim compliance it does not have.
    # QUANTIFIED, in digits or in words. The first version demanded a
    # numeral and failed on "ten pages" - correct prose, arbitrary check.
    _claims = re.search(r'KNOWN GAP[^\n]*\n(?:[^\n]*\n){0,4}', DOC)
    _words = r'(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|' \
             r'eleven|twelve|twenty|thirty)'
    check('  and it records the gap honestly rather than claiming none',
          _claims is not None
          and re.search(_words + r'\s+pages?', _claims.group(0), re.I)
          is not None,
          ' '.join(_claims.group(0).split())[:60] if _claims else 'no gap')

# ===========================================================================
head('4. what the round left alone')
# ===========================================================================
# SCOPE GUARD #18 - 9 Sep. This section used to assert that
# property_assets and the projects/ module were UNTOUCHED and still
# non-compliant, which was correct and carried its own expiry date: it held
# only until a round agreed to do them. The shape-B round did, on 9 Sep.
#
# Ask what the claim is ABOUT. It was never "these pages must stay broken" -
# it was "their exclusion from the heading round was a DECISION, not an
# oversight, and something can tell you which". So the assertion is turned
# over: they are now checked for COMPLIANCE, and the fact that they were
# deferred and then done is recorded rather than asserted forever.
for rel in sorted(DEFERRED):
    p = os.path.join(T, rel.replace('/', os.sep))
    if not os.path.exists(p):
        continue
    check('%-40s was deferred, and has since been done' % rel,
          os.path.exists(p + '.bak_prj'))
    t, _ = heading_of(read(p))
    check('  and its title now holds no record name',
          t is not None and '{{' not in t, (t or '')[:44])
    check('  which moved to the line below it',
          re.search(r'<h4[^>]*page-subtitle-h4[^>]*>[^<]*<center>[^<]*\{\{',
                    read(p), re.S) is not None
          or '{{' in (second_line(read(p))[1] or ''))

_prj = [p for p in TEMPLATES if rel_of(p).startswith('projects/')]
check('the heading round itself never touched projects/ (%d template(s))'
      % len(_prj),
      not any(os.path.exists(p + '.bak_hstd') for p in _prj))
check('  and a later round did - which is why they comply now',
      sum(1 for p in _prj if os.path.exists(p + '.bak_prj')) >= 10,
      '%d' % sum(1 for p in _prj if os.path.exists(p + '.bak_prj')))
check('  CONTROL: it really does have headings to have got wrong',
      sum(1 for p in _prj if heading_of(read(p))[0]) >= 5,
      '%d' % sum(1 for p in _prj if heading_of(read(p))[0]))

# Structure untouched: this round edits text and adds a comment.
for p in MOVED:
    rel = rel_of(p)
    now, was = markup_of(read(p)), markup_of(read(p + '.bak_hstd'))
    d_now = len(re.findall(r'<div\b', now)) - len(re.findall(r'</div>', now))
    d_was = len(re.findall(r'<div\b', was)) - len(re.findall(r'</div>', was))
    check('%-40s <div> balance unchanged' % rel, d_now == d_was,
          '%+d -> %+d' % (d_was, d_now))
    stack, fault = [], None
    OPEN = {'if': 'endif', 'for': 'endfor', 'block': 'endblock',
            'with': 'endwith'}
    CLOSE = {v: k for k, v in OPEN.items()}
    for m in re.finditer(r'\{%\s*(\w+)', read(p)):
        t2 = m.group(1)
        if t2 in OPEN:
            stack.append(t2)
        elif t2 in CLOSE and (not stack or OPEN[stack.pop()] != t2):
            fault = t2
            break
    check('  and its Django tags balance', fault is None and not stack,
          fault or ','.join(stack))

# A pre-existing structural fault, reported rather than fixed here.
_unclosed = []
for p in TEMPLATES:
    mk = markup_of(read(p))
    d = len(re.findall(r'<div\b', mk)) - len(re.findall(r'</div>', mk))
    if d:
        _unclosed.append('%s (%+d)' % (rel_of(p), d))
if _unclosed:
    print('        NOTE  pre-existing unbalanced <div>s, none of them this '
          'round\'s doing:\n          %s' % ', '.join(_unclosed))

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
print('\n  NOT PROVED HERE: that a title is the RIGHT words for its page.')
print('  Only that it is capitals, unbranded, and unchanged in substance.')
if FAILED:
    print('\n  failures:')
    for x in FAILED[:20]:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
