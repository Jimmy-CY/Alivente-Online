"""Show-HeadingComponents.py - who styles the three classes the standard is
   written in, and how many ways they say the same thing.

    python Show-HeadingComponents.py

Run from the repo root. READ-ONLY: it opens files and prints. It writes
nothing, changes nothing, and exits 0 whatever it finds.

WHY

  base.html declares NONE of page-title-h2, page-subtitle-h4 or
  page-action-buttons-form, and those are the class names the standards
  block is written in. Every page that wants one has hand-written it. The
  running list calls that thirteen distinct ways; this walks the real
  corpus and says what they actually are.

  It exists because the sandbox copy of this repo is a SUBSET - about
  ninety templates of roughly two hundred - and a value chosen from a
  subset is a value chosen from the wrong corpus. That mistake has been
  made on this project twice: once measuring a stale working copy, once
  reporting the gate complete while nineteen suites were missing.

WHAT IT REPORTS

  1. Every rule touching the three, with its media context.
  2. THE CONDITIONAL. The h2's bottom margin appears to depend on whether
     a subtitle follows it, hand-derived per page. This cross-tabulates
     the two so the pattern is visible - or is contradicted.
  3. The overlap with the paper bug: rules inside a max-width query with
     no `screen` keyword fire on A4, because A4 portrait is about 718 CSS
     px wide.
  4. Colour literals, which base has tokens for.
  5. Pages using a class in markup that nothing styles.
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

import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
CLASSES = ('page-title-h2', 'page-subtitle-h4', 'page-action-buttons-form')

if not os.path.isdir(T):
    print('! %s not found - run from the repo root' % T)
    sys.exit(1)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def templates():
    out = []
    for dirpath, _d, names in os.walk(T):
        for n in names:
            if n.endswith('.html'):
                out.append(os.path.join(dirpath, n))
    return sorted(out)


def rules_of(css):
    """Every rule, with the @media it sits inside, brace-aware.

    Not a line-based scan. A line-based scan cannot tell a rule inside a
    media query from one beside it, and that difference is the whole of
    section 3 below.
    """
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    media = None
    for m in re.finditer(r'@media([^{]*)\{|([^{}]+)\{([^{}]*)\}|\}', css):
        if m.group(1) is not None:
            media = ' '.join(m.group(1).split())
        elif m.group(0) == '}':
            media = None
        else:
            yield (media, ' '.join(m.group(2).split()),
                   ' '.join(m.group(3).split()))


ROWS = []          # (rel, media, class, selector, declaration)
MARKUP = collections.defaultdict(set)
SUBTITLE = {}
CENTERED = collections.Counter()

for path in templates():
    rel = os.path.relpath(path, T).replace(os.sep, '/')
    src = read(path)
    body = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', src, flags=re.S)
    for c in CLASSES:
        if re.search(r'class="[^"]*\b%s\b' % c, body):
            MARKUP[c].add(rel)
    SUBTITLE[rel] = bool(re.search(r'class="[^"]*\bpage-subtitle-h4\b', body))
    for m in re.finditer(r'<h[24][^>]*class="[^"]*page-(?:title-h2|subtitle-h4)'
                         r'[^"]*"[^>]*>(.*?)</h[24]>', body, re.S):
        if '<center' in m.group(1):
            CENTERED[rel] += 1
    for css in re.findall(r'<style[^>]*>(.*?)</style>', src, re.S):
        for media, sel, decl in rules_of(css):
            for c in CLASSES:
                if '.' + c in sel:
                    ROWS.append((rel, media, c, sel, decl))


def head(t):
    print('\n' + '=' * 74 + '\n ' + t + '\n' + '=' * 74)


print('=' * 74)
print(' THE HEADING COMPONENTS - who styles them, and in how many ways')
print('=' * 74)
print('  %d template(s) walked, in %d director(ies)'
      % (len(templates()),
         len(set(os.path.dirname(p) for p in templates()))))

# ---------------------------------------------------------------------- 1
head('1. WHAT base WOULD TAKE OVER - the rules outside any media query')

for c in CLASSES:
    top = collections.Counter(d for _r, m, cc, _s, d in ROWS
                              if cc == c and not m)
    print('\n .%s  - used in markup on %d page(s), %d top-level rule(s)'
          % (c, len(MARKUP[c]), sum(top.values())))
    if not top:
        print('     none')
    for decl, n in top.most_common():
        print('   %3dx  %s' % (n, decl[:96]))

# ---------------------------------------------------------------------- 2
head('2. THE PHONE RULES - what each page says at narrow widths')

for c in CLASSES:
    ph = collections.Counter(d for _r, m, cc, _s, d in ROWS if cc == c and m)
    print('\n .%s  - %d rule(s) inside a media query' % (c, sum(ph.values())))
    for decl, n in ph.most_common(6):
        print('   %3dx  %s' % (n, decl[:96]))

# ---------------------------------------------------------------------- 3
head('3. THE CONDITIONAL - does the h2 bottom margin follow the subtitle?')

# The hypothesis, from a partial corpus: a page whose h2 is followed by a
# subtitle closes the gap to zero, and a page without one opens it to 1rem.
# Same rule, hand-derived per page. If that holds here, base can express it
# in ONE rule and the pages that disagree are pages that got it wrong.
cross = collections.Counter()
where = collections.defaultdict(list)
for rel, media, c, _sel, decl in ROWS:
    if c != 'page-title-h2' or media:
        continue
    g = re.search(r'margin-bottom:\s*([^;]+)', decl)
    if not g:
        continue
    key = (g.group(1).strip(), SUBTITLE.get(rel, False))
    cross[key] += 1
    where[key].append(rel)

print('\n  h2 margin-bottom    a subtitle follows    pages')
for (mb, has), n in sorted(cross.items()):
    print('  %-19s %-21s %d' % (mb, 'yes' if has else 'NO', n))
print('\n  the pages that do not fit the majority of their group:')
majority = {}
for (mb, has), n in cross.items():
    if has not in majority or n > cross[(majority[has], has)]:
        majority[has] = mb
odd = []
for (mb, has), rels in where.items():
    if majority.get(has) != mb:
        odd.extend('%-40s subtitle: %-3s  margin-bottom: %s'
                   % (r, 'yes' if has else 'NO', mb) for r in rels)
for line in sorted(odd) or ['     (none - the rule is unanimous)']:
    print('     ' + line)

# ---------------------------------------------------------------------- 4
head('4. THE PAPER BUG, WHERE IT OVERLAPS THESE THREE')

# A max-width query with no `screen` keyword applies to PAPER as well as to
# screens, and A4 portrait is about 718 CSS px - inside every 768px query.
naked, fine = collections.defaultdict(set), collections.defaultdict(set)
for rel, media, _c, _s, _d in ROWS:
    if not media:
        continue
    (fine if media.startswith('screen') else naked)[media].add(rel)
_n = set().union(*naked.values()) if naked else set()
_f = set().union(*fine.values()) if fine else set()
print('\n  %d page(s) style one of the three inside a query that FIRES ON '
      'PAPER' % len(_n))
for q, rels in sorted(naked.items(), key=lambda kv: -len(kv[1])):
    print('     %-52s %d page(s)' % (q, len(rels)))
for r in sorted(_n):
    print('       ' + r)
print('\n  %d page(s) already say screen' % len(_f))
print('\n  NOTE: a hoist DELETES the page-local copies, so every one of')
print('  those queries goes with them. The two rounds are the same edit.')

# ---------------------------------------------------------------------- 5
head('5. COLOUR LITERALS, WHERE base HAS A TOKEN')

lit = collections.Counter()
for rel, _m, c, _s, decl in ROWS:
    for g in re.finditer(r'colou?r:\s*(#[0-9a-fA-F]{3,6}|rgb[^;]+)', decl):
        lit[(c, g.group(1).strip())] += 1
if not lit:
    print('\n  none')
for (c, v), n in lit.most_common():
    print('  %3dx  .%-26s %s' % (n, c, v))

# ---------------------------------------------------------------------- 6
head('6. LOOSE ENDS')

for c in CLASSES:
    styled = set(r for r, _m, cc, _s, _d in ROWS if cc == c)
    orphan = sorted(MARKUP[c] - styled)
    print('\n  .%s: %d page(s) use it with NO rule of their own'
          % (c, len(orphan)))
    for r in orphan[:12]:
        print('     ' + r)
    if len(orphan) > 12:
        print('     ... and %d more' % (len(orphan) - 12))

print('\n  %d page(s) centre the heading with a <center> element, which the '
      'component\n  could do with text-align instead:' % len(CENTERED))
for r, n in sorted(CENTERED.items())[:10]:
    print('     %-44s %d' % (r, n))
if len(CENTERED) > 10:
    print('     ... and %d more' % (len(CENTERED) - 10))

print('\n' + '=' * 74)
print('  Read-only. Nothing was written.')
print('=' * 74)
