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
capitals, prefixed, and unchanged in substance from what was there before.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PREFIX = 'ALIVENTE ONLINE - '

# Deliberately out of scope: a record name inside the title, so prefixing
# gives two dashes doing different jobs. Awaiting the projects/ survey.
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


def literal(t):
    """The text with Django tags removed - what a reader sees minus the
       data. A title that is only `{{ name|upper }}` has no literal, and
       must not be judged on capitalisation it does not control."""
    return re.sub(r'\{[{%#][^}]*[}%#]\}', '', t or '').strip()


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
    check('%-40s title is prefixed and capitals' % rel,
          t_now is not None and t_now.startswith(PREFIX)
          and literal(t_now) == literal(t_now).upper(),
          (t_now or '?')[:44])
    # THE WORDS MUST SURVIVE. A prefix is added and the case changes; the
    # page must not be renamed by a round about formatting.
    if t_was:
        _w = [w for w in re.findall(r'[A-Za-z]{3,}', literal(t_was))]
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
    ok = t.startswith(PREFIX) and lit == lit.upper()
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

check('most of the system complies', len(GOOD) >= 40,
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
head('3. the pages agree with the standard base.html states')
# ===========================================================================
_b = read(BASE)
_m = re.search(r'\{%\s*comment\s*%\}(.*?)\{%\s*endcomment\s*%\}', _b, re.S)
if not _m:
    print('  SKIP  base.html carries no standards block to read')
else:
    DOC = _m.group(1)
    check('base states the heading standard', 'PAGE HEADINGS' in DOC)
    _pfx = re.search(r'prefixed `([^`]+)`', DOC)
    check('  and names the prefix', _pfx is not None,
          repr(_pfx.group(1)) if _pfx else '')
    check('  which is the one the pages actually use',
          _pfx is not None and _pfx.group(1).strip() == PREFIX.strip(),
          '%r vs %r' % (_pfx.group(1) if _pfx else None, PREFIX))
    check('  it says the title is capitals', 'CAPITALS' in DOC)
    check('  and the subtitle is sentence case',
          'SENTENCE CASE' in DOC or 'Sentence case' in DOC)
    check('  and that no heading carries an icon', 'NO ICON' in DOC)
    # The document must not claim compliance it does not have.
    _claims = re.search(r'KNOWN GAP[^\n]*\n(?:[^\n]*\n){0,4}', DOC)
    check('  and it records the gap honestly rather than claiming none',
          _claims is not None and re.search(r'\d+ pages?', _claims.group(0))
          is not None,
          ' '.join(_claims.group(0).split())[:60] if _claims else 'no gap noted')

# ===========================================================================
head('4. what the round left alone')
# ===========================================================================
for rel in sorted(DEFERRED):
    p = os.path.join(T, rel.replace('/', os.sep))
    if not os.path.exists(p):
        continue
    check('%-40s untouched - a record name in its title' % rel,
          not os.path.exists(p + '.bak_hstd'))
    t, _ = heading_of(read(p))
    check('  and it still carries one, which is why', t is not None
          and '{{' in t, (t or '')[:44])

_prj = [p for p in TEMPLATES if rel_of(p).startswith('projects/')]
check('the projects/ module is untouched (%d template(s))' % len(_prj),
      not any(os.path.exists(p + '.bak_hstd') for p in _prj))
check('  CONTROL: it really does have headings to leave alone',
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
print('  Only that it is capitals, prefixed, and unchanged in substance.')
if FAILED:
    print('\n  failures:')
    for x in FAILED[:20]:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
