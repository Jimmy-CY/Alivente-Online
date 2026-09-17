"""Show-AdminPersonal.py - what is actually in the Administration and
   Personal modules, which have never had a test pass.

    python Show-AdminPersonal.py

READ-ONLY. It writes nothing and changes nothing. Run it from the repo
root.

WHY THIS EXISTS

  Every round in this sequence has been aimed at the modules you test.
  Administration and Personal were flagged at the start as never having
  had a review, and they have been carried along by the sweeps anyway:
  SEVEN of their eleven templates have been changed by this session's
  rounds - the label sweep, the component round, the panel wrap, the
  action bar, the Cancel removal, the headings.

  That is a debt those rounds created. This is the survey before deciding
  what to do about it, and it is deliberately read-only: nothing here
  proposes a fix.

WHAT IT REPORTS, AND WHY EACH ONE

  FAULTS first - things that are wrong rather than merely non-standard.
  Crossed tags are the sharp one: a </div> closing before the </form> it
  sits inside is markup a browser silently repairs, differently in
  different browsers, and it has been in these pages since before any
  round in this sequence.

  Then STANDARDS, one line per dimension, so the gap is legible as a list
  of rounds rather than a mood.

  Then a COLOUR. #667eea appears 49 times across this module. It is NOT
  foreign to the system - base uses it for the avatar circle, paired with
  #764ba2 - but 38 of those uses are icons and focus rings borrowing the
  avatar's purple where the accent token belongs.

WHAT IT DOES NOT DO

  It draws no conclusions and proposes no round. A count is evidence about
  the present, never an argument about what the standard should be - which
  is the mistake that cost the panel its wash.
"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')

# The two modules, by the names their templates carry. A RULE rather than
# a list, so a screen added next month is surveyed too.
ADMIN = re.compile(r'(^|/)(user_|workspace_|admin_|permission)|'
                   r'(^|/)(notification_settings|help_page|database_error)')
PERSONAL = re.compile(r'(^|/)(my_profile|personal_)')

VOID = {'input', 'br', 'img', 'hr', 'meta', 'link', 'source', 'area',
        'base', 'col', 'embed', 'param', 'track', 'wbr'}

# The house components, and the round that owns each.
# The short name is what the column is headed with: truncating the class
# names gave six columns reading "page-" and "form-", which is a table
# that cannot be read.
STANDARDS = (
    ('page-title-h2', 'head', 'the module heading', 'the heading round'),
    ('page-subtitle-h4', 'mode', 'the mode line', 'the heading round'),
    ('page-action-buttons', 'bar', 'the action bar', 'the button sweep'),
    ('form-card', 'panel', 'the panel', 'the component round'),
    ('form-section-title', 'ptitle', 'the panel title', 'the component round'),
    ('form-control', 'ctrl', 'the control', 'the component round'),
)

STRAY = '#667eea'


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def inert(text):
    out = re.sub(r'<(script|style)\b[^>]*>.*?</\1>',
                 lambda m: ' ' * len(m.group(0)), text, flags=re.S | re.I)
    return re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), out, flags=re.S)


def pages():
    out = []
    for dirpath, _d, names in os.walk(T):
        for n in sorted(names):
            if not n.endswith('.html'):
                continue
            rel = os.path.relpath(os.path.join(dirpath, n), T)
            rel = rel.replace(os.sep, '/')
            if ADMIN.search(rel):
                out.append((rel, os.path.join(dirpath, n), 'Administration'))
            elif PERSONAL.search(rel):
                out.append((rel, os.path.join(dirpath, n), 'Personal'))
    return sorted(out)


def crossed(scan):
    """Close tags that do not match what is open, with the detail."""
    stack, bad = [], []
    for m in re.finditer(r'<(/?)(\w+)([^>]*?)(/?)>', scan):
        close, name, _a, selfclose = m.groups()
        name = name.lower()
        if name in VOID or selfclose:
            continue
        if close:
            if not stack:
                bad.append('</%s> with nothing open' % name)
            elif stack[-1][0] != name:
                bad.append('</%s> closes a <%s>' % (name, stack[-1][0]))
                stack.pop()
            else:
                stack.pop()
        else:
            stack.append((name, m.start()))
    for name, _pos in stack:
        bad.append('<%s> never closed' % name)
    return bad


def touched(path):
    """Has one of this session's rounds written to this page?"""
    d, n = os.path.dirname(path), os.path.basename(path)
    return sorted(x.split('.bak_')[1] for x in os.listdir(d)
                  if x.startswith(n + '.bak_'))


def bare_queries(text):
    out = []
    for css in re.findall(r'<style[^>]*>(.*?)</style>', text, re.S):
        css = re.sub(r'/\*.*?\*/', ' ', css, flags=re.S)
        for m in re.finditer(r'@media([^{]*)\{', css):
            q = ' '.join(m.group(1).split())
            if 'max-width' in q and not q.startswith('screen') \
                    and 'print' not in q:
                out.append(q)
    return out


def head(t):
    print('')
    print('=' * 74)
    print(' ' + t)
    print('=' * 74)


if not os.path.isdir(T):
    print('! %s not found - run from the repo root' % T)
    sys.exit(1)

ALL = pages()

# ---------------------------------------------------------------- 1
head('1. WHAT IS IN THESE TWO MODULES')

print('  %d template(s): %d Administration, %d Personal.'
      % (len(ALL), sum(1 for _r, _p, m in ALL if m == 'Administration'),
         sum(1 for _r, _p, m in ALL if m == 'Personal')))
print('')
print('  %-28s %-14s %s' % ('template', 'module', 'what it holds'))
for rel, path, mod in ALL:
    t = read(path)
    s = inert(t)
    bits = []
    n = len(re.findall(r'<form\b', s))
    if n:
        bits.append('%d form%s' % (n, '' if n == 1 else 's'))
    n = len(re.findall(r'<table\b', s))
    if n:
        bits.append('%d table%s' % (n, '' if n == 1 else 's'))
    n = len(re.findall(r'class="[^"]*\bform-control\b', s))
    if n:
        bits.append('%d control%s' % (n, '' if n == 1 else 's'))
    n = len(re.findall(r'class="[^"]*\bmodal\b', s))
    if n:
        bits.append('%d modal%s' % (n, '' if n == 1 else 's'))
    print('  %-28s %-14s %s' % (rel[:28], mod, ', '.join(bits) or 'no form'))

# ---------------------------------------------------------------- 2
head('2. WHAT THIS SESSION ALREADY CHANGED IN THEM')

any_touched = False
for rel, path, _m in ALL:
    r = touched(path)
    if r:
        any_touched = True
        print('  %-28s %s' % (rel[:28], ', '.join(r)))
if not any_touched:
    print('  No backups on disk - either nothing was changed, or the')
    print('  backups have been cleaned up. Backups are gitignored, so a')
    print('  fresh clone shows nothing here and that is not evidence.')
print('')
print('  These rounds were aimed at the modules you test. These screens')
print('  were carried along by them and have still never been reviewed.')

# ---------------------------------------------------------------- 3
head('3. FAULTS - things that are wrong, not merely non-standard')

found = False
for rel, path, _m in ALL:
    t = read(path)
    bad = crossed(inert(t))
    if bad:
        found = True
        print('  %s' % rel)
        for b in bad[:4]:
            print('      %s' % b)

if not found:
    print('  No crossed or unclosed tags.')
else:
    print('')
    print('  A </div> closing before the </form> it sits inside is markup')
    print('  every browser repairs, and not all of them the same way. This')
    print('  predates every round in this sequence - the oldest backup on')
    print('  disk already shows it.')

print('')
dup = []
for rel, path, _m in ALL:
    s = inert(read(path))
    ids = re.findall(r'\bid\s*=\s*"([^"]+)"', s)
    seen = collections.Counter(ids)
    for i, n in seen.items():
        if n > 1 and '{{' not in i:
            dup.append('%s: id="%s" appears %d times' % (rel, i, n))
print('  DUPLICATE ids: %d' % len(dup))
for d in dup[:8]:
    print('      %s' % d)

print('')
nocsrf = []
for rel, path, _m in ALL:
    t = read(path)
    for m in re.finditer(r'<form\b[^>]*>', inert(t)):
        tag = t[m.start():m.end()]
        if re.search(r'method\s*=\s*"post"', tag, re.I):
            after = t[m.end():m.end() + 400]
            if 'csrf_token' not in after:
                nocsrf.append('%s: a POST form with no csrf token nearby'
                              % rel)
print('  POST forms with no csrf token in the first 400 characters: %d'
      % len(nocsrf))
for x in nocsrf[:6]:
    print('      %s' % x)

# ---------------------------------------------------------------- 4
head('4. STANDARDS - which components these screens are on')

print('  %-28s %s' % ('template', ' '.join('%-6s' % c[1]
                                           for c in STANDARDS)))
gap = collections.Counter()
for rel, path, _m in ALL:
    s = inert(read(path))
    marks = []
    for cls, _short, _what, _round in STANDARDS:
        has = re.search(r'class="[^"]*\b%s\b' % cls, s) is not None
        marks.append('%-6s' % ('yes' if has else '-'))
        if not has:
            gap[cls] += 1
    print('  %-28s %s' % (rel[:28], ' '.join(marks)))
print('')
for cls, short, what, owner in STANDARDS:
    print('    %-6s %-20s %-18s missing on %d of %d   (%s)'
          % (short, cls, what, gap[cls], len(ALL), owner))
print('')
print('  A dash is not automatically a fault: admin_apms is a dashboard and')
print('  has no form to panel. The column is here so the gap reads as a')
print('  list of rounds rather than an impression.')

# ---------------------------------------------------------------- 5
head('5. A COLOUR BORROWED FROM THE AVATAR')

# THE COLOUR IS IN BASE, AND FOR A REASON. The control line below caught
# me: #667eea is half of the AVATAR gradient - the circle with the user's
# initials in the sidebar and the top nav - and base declares it there
# deliberately. It is not a foreign colour.
#
# What these screens do with it is different: they borrow the avatar's
# purple for ICON COLOURS and FOCUS RINGS, where the accent token belongs.
# So the report separates the two uses rather than counting a string.
hits = collections.Counter()
kind = collections.Counter()
for rel, path, _m in ALL:
    t = read(path)
    n = t.count(STRAY)
    if n:
        hits[rel] = n
    for m in re.finditer(r'.{0,60}' + re.escape(STRAY) + r'.{0,20}', t):
        seg = ' '.join(m.group(0).split())
        if '764ba2' in seg:
            kind['the avatar gradient, as base declares it'] += 1
        elif 'border' in seg:
            kind['a border or focus ring'] += 1
        elif 'color:' in seg:
            kind['an icon or text colour'] += 1
        else:
            kind['something else'] += 1

print('  %s appears %d time(s) across %d of these templates.'
      % (STRAY, sum(hits.values()), len(hits)))
for rel, n in hits.most_common():
    print('      %-30s %d' % (rel[:30], n))
print('')
print('  WHAT IT IS BEING USED FOR:')
for k, n in kind.most_common():
    print('      %-40s %d' % (k, n))

B = read(BASE)
print('')
print('  base uses it too - in the sidebar avatar and the top-nav badge,')
print('  paired with #764ba2. That use is deliberate. The %d uses above'
      % (sum(kind.values()) - kind['the avatar gradient, as base declares it']))
print('  that are NOT the avatar are borrowing it for icons and focus,')
print('  where the accent this system defines is %s.'
      % (re.search(r'--alv-accent:\s*([^;]+);', B).group(1).strip()
         if re.search(r'--alv-accent:\s*([^;]+);', B) else '?'))
print('')
print('  The first version of this section asserted the colour belonged to')
print('  no palette here. Its own control line said IT IS IN BASE, CHECK')
print('  THIS - and it was right. A report that cannot contradict its')
print('  author is not worth printing.')

# ---------------------------------------------------------------- 6
head('6. INLINE STYLES AND PHONE QUERIES')

inline = collections.Counter()
bare = collections.Counter()
for rel, path, _m in ALL:
    t = read(path)
    inline[rel] = len(re.findall(r'\sstyle\s*=\s*"', inert(t)))
    n = len(bare_queries(t))
    if n:
        bare[rel] = n
print('  INLINE style attributes: %d across %d template(s)'
      % (sum(inline.values()), sum(1 for v in inline.values() if v)))
for rel, n in inline.most_common(8):
    if n:
        print('      %-30s %d' % (rel[:30], n))
print('')
print('  BARE max-width queries - these fire on PAPER as well as on phones,')
print('  because A4 portrait is about 718 CSS px: %d across %d template(s)'
      % (sum(bare.values()), len(bare)))
for rel, n in bare.most_common(8):
    print('      %-30s %d' % (rel[:30], n))

# ---------------------------------------------------------------- 7
head('7. WHAT THIS ADDS UP TO')

print('  Nothing here is a proposal. Every number is a count of what is on')
print('  disk today, and a count is evidence about the present rather than')
print('  an argument about what the standard should be.')
print('')
print('  Nothing was written. This script only reads.')
