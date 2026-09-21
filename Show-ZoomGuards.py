# -*- coding: utf-8 -*-
"""Show-ZoomGuards.py - which page-local iOS zoom guards base has made
redundant, and which it has not.

    python Show-ZoomGuards.py
    python Show-ZoomGuards.py --verbose     every guard, with its verdict

Run from the repo root. READ-ONLY - nothing is written.

WHY IT EXISTS

  iOS Safari zooms the page whenever a focused input is under 16px, and
  .form-control is 14px. base now sets 16px on .form-control below 768px,
  and says so in its own comment:

      "62 pages had each written this rule locally before base did. Those
       locals are now redundant; removing them is a round of its own."

  THAT SENTENCE IS OPTIMISTIC, and this tool is the measurement of by how
  much. base guards ONE selector at ONE width. A page-local guard can reach
  things base does not:

    * a control with NO .form-control class - a bare <select>, a number
      input in a hand-built modal. base never touches it, so its local
      guard is the only thing stopping the zoom.
    * the DESKTOP, where a guard has no media query at all.
    * other properties, bundled into the same rule - a padding, a width.

  And a local guard written !important can be quietly holding off a smaller
  font-size elsewhere on the same page, which base's plain declaration will
  lose to once the local one is gone.

  Controls built by SCRIPT are counted as well as markup. A guard can exist
  for a modal row added on click, and stripping <script> before looking
  would call that guard redundant when it is the only one protecting it.
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
from collections import Counter, defaultdict

ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

VERBOSE = '--verbose' in sys.argv

# Not in scope, each with its reason. Named, so the survey can say so.
OUT_OF_SCOPE = {
    'create_recipe (OLD DO NOT USE).html':
        'no view renders it - a dead file',
    'edit_recipe (OLD DO NOT USE).html':
        'no view renders it - a dead file',
    'error_pages/connectivity_error.html':
        'does not extend base, so base\'s guard never reaches it',
}


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def css_of(t):
    """Every <style> block, Django tags and CSS COMMENTS removed.

    SEVENTH TIME. The first run of this tool printed base's guard twice, the
    first with a paragraph of prose as its media condition - because base
    has a comment that says `@media (max-width: 768px)` in so many words,
    and the parser looked for `@media` before it removed comments. The
    selector-level strip below was not enough: a comment has to be gone
    before anything reads the text for structure at all."""
    css = '\n'.join(re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
                    for m in re.finditer(r'<style[^>]*>(.*?)</style>',
                                         t, re.S))
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)


def rules(css, media=''):
    """(media, [selectors], body) - nesting-aware, comments removed from the
    selector text before it is split. A comment is not a selector: this
    project has learned that six times."""
    out, i, n = [], 0, len(css)
    while i < n:
        at = re.compile(r'@media([^{]*)\{').search(css, i)
        r = re.compile(r'([^{}@]+)\{([^{}]*)\}').search(css, i)
        if at and (not r or at.start() < r.start()):
            d, j = 1, at.end()
            while j < n and d:
                d += 1 if css[j] == '{' else (-1 if css[j] == '}' else 0)
                j += 1
            out += rules(css[at.end():j - 1], ' '.join(at.group(1).split()))
            i = j
            continue
        if not r:
            break
        sel = re.sub(r'/\*.*?\*/', '', r.group(1), flags=re.S)
        sels = [' '.join(s.split()) for s in sel.split(',') if s.strip()]
        body = re.sub(r'/\*.*?\*/', '', r.group(2), flags=re.S)
        out.append((media, sels, ' '.join(body.split())))
        i = r.end()
    return out


def declarations(body):
    out = {}
    for part in body.split(';'):
        if ':' in part:
            k, v = part.split(':', 1)
            out[k.strip().lower()] = v.strip()
    return out


# --- what base promises -----------------------------------------------------
BASE_CSS = css_of(read(os.path.join(ROOT, 'base.html')))
BASE_GUARD = [(m, s, b) for m, s, b in rules(BASE_CSS)
              if declarations(b).get('font-size', '').startswith('16px')
              and any('form-control' in x for x in s)]


# --- the controls on a page, INCLUDING ones a script builds ----------------
CONTROL = re.compile(r'<(input|select|textarea)\b([^>]*)>', re.I)
SKIP_TYPES = {'submit', 'button', 'reset', 'hidden', 'checkbox', 'radio',
              'file', 'image', 'range', 'color'}


def controls(text):
    """Every text-entry control, from markup AND from script strings.

    A guard can exist for a control a script builds - a modal row added on
    click - and stripping <script> before looking would call that guard
    redundant when it is the only thing protecting that control."""
    out = []
    for m in CONTROL.finditer(text):
        tag, attrs = m.group(1).lower(), m.group(2)
        ty = 'text'
        t = re.search(r'type\s*=\s*["\']?([a-zA-Z-]+)', attrs)
        if tag == 'input' and t:
            ty = t.group(1).lower()
        if tag == 'input' and ty in SKIP_TYPES:
            continue
        cls = re.search(r'class\s*=\s*["\']([^"\']*)', attrs)
        classes = set((cls.group(1) if cls else '').split())
        out.append({'tag': tag, 'type': ty if tag == 'input' else tag,
                    'classes': classes})
    return out


def subject(selector):
    """The compound a selector actually styles - its last one - reduced to
    (tag, classes, type). `.form-group input[type="text"]` styles an input
    of type text wherever it sits; ancestors are ignored, which can only
    OVER-match, which can only err towards keeping a guard."""
    last = re.split(r'\s+|>|\+|~', selector.strip())[-1]
    last = re.sub(r':[\w-]+(\([^)]*\))?', '', last)
    tag = re.match(r'^([a-zA-Z]+)', last)
    ty = re.search(r'\[type\s*=\s*["\']?([a-zA-Z-]+)', last)
    return (tag.group(1).lower() if tag else None,
            set(re.findall(r'\.([\w-]+)', last)),
            ty.group(1).lower() if ty else None)


def matches(ctl, subj):
    tag, classes, ty = subj
    if tag and tag != ctl['tag']:
        return False
    if classes and not classes <= ctl['classes']:
        return False
    if ty and ty != ctl['type']:
        return False
    return bool(tag or classes or ty)


# --- the guards ---------------------------------------------------------------
GUARD_SUBJECT = re.compile(r'form-control|(?<![-\w])(input|select|textarea)'
                           r'(?![-\w])|filter-select|search-input')

found = []          # one entry per guard rule
for dp, _d, ns in os.walk(ROOT):
    for n in sorted(ns):
        if not n.endswith('.html'):
            continue
        rel = os.path.relpath(os.path.join(dp, n), ROOT).replace(os.sep, '/')
        if rel == 'base.html':
            continue
        text = read(os.path.join(dp, n))
        ctls = controls(text)
        for media, sels, body in rules(css_of(text)):
            decl = declarations(body)
            if not decl.get('font-size', '').startswith('16px'):
                continue
            if not any(GUARD_SUBJECT.search(s) for s in sels):
                continue
            # which controls does this guard reach that base does NOT?
            orphans = Counter()
            for s in sels:
                subj = subject(s)
                for c in ctls:
                    if matches(c, subj) and 'form-control' not in c['classes']:
                        orphans['%s[%s]' % (c['tag'], c['type'])] += 1
            found.append({
                'rel': rel, 'media': media, 'sels': sels, 'body': body,
                'extra': sorted(k for k in decl if k != 'font-size'),
                'important': '!important' in decl.get('font-size', ''),
                'orphans': orphans,
            })


def verdict(g):
    if g['rel'] in OUT_OF_SCOPE:
        return 'OUT'
    if not g['media']:
        return 'EVERY-WIDTH'
    if not re.search(r'max-width\s*:\s*7(6[0-9]|[0-5]\d)px', g['media']) \
            and '768' not in g['media']:
        return 'OTHER-WIDTH'
    if g['orphans']:
        return 'ORPHANS'
    if g['extra']:
        return 'MIXED'
    return 'REDUNDANT'


for g in found:
    g['verdict'] = verdict(g)

# ============================================================================
# !important - the risk the headline count cannot see
#
# base's guard is NOT !important. A page that removes its own !important
# guard is safe only if nothing else on that page, below 768px, sets a
# control's font-size to something smaller - because then the smaller
# number would win against base's plain declaration.
# ============================================================================
shrinkers = defaultdict(list)
for dp, _d, ns in os.walk(ROOT):
    for n in sorted(ns):
        if not n.endswith('.html'):
            continue
        rel = os.path.relpath(os.path.join(dp, n), ROOT).replace(os.sep, '/')
        if rel == 'base.html':
            continue
        text = read(os.path.join(dp, n))
        ctls = controls(text)
        for media, sels, body in rules(css_of(text)):
            fs = declarations(body).get('font-size', '')
            m = re.match(r'([\d.]+)(px|rem|em)', fs)
            if not m:
                continue
            px = float(m.group(1)) * (16 if m.group(2) in ('rem', 'em') else 1)
            if px >= 16:
                continue
            # WHAT THE SELECTOR MATCHES, NOT WHAT IT SAYS. `.line-input`
            # names no control and every element it matches is an input;
            # the first version of this survey, and of the patcher, missed
            # it for that reason, and the rendered suite caught the patcher
            # removing a guard that was holding those inputs at 16px.
            hit = [x for x in sels if any(matches(c, subject(x))
                                          for c in ctls)]
            if hit:
                shrinkers[rel].append('%s -> %s (%s)'
                                      % (', '.join(hit)[:46], fs,
                                         media or 'every width'))

# ============================================================================
print('\n' + '=' * 74)
print('THE iOS ZOOM GUARDS - read-only survey')
print('=' * 74)
print("""
  base's guard, verbatim:
""")
for m, s, b in BASE_GUARD:
    print('      @media %s  { %s { %s } }' % (m, ', '.join(s), b))
print("""
  That is ONE selector at ONE width. A page-local guard is redundant only
  where it reaches nothing that base does not - same width, only font-size,
  and no control it covers is missing the .form-control class.
""")

by = defaultdict(list)
for g in found:
    by[g['verdict']].append(g)

ORDER = [
    ('REDUNDANT', 'base covers it exactly - these can simply go'),
    ('MIXED', 'the 16px is redundant, but the rule also sets something '
              'else - only the font-size can go'),
    ('ORPHANS', 'it guards a control with NO .form-control class, which base '
                'never reaches - removing it brings the zoom back'),
    ('EVERY-WIDTH', 'no media query - it sets 16px on the DESKTOP too, which '
                    'base does not'),
    ('OTHER-WIDTH', 'a different breakpoint from base\'s 768px'),
    ('OUT', 'out of scope, with a reason'),
]
print('%d guard rule(s) on %d page(s):\n'
      % (len(found), len({g['rel'] for g in found})))
removable = [g for g in found if g['verdict'] in ('REDUNDANT', 'MIXED')
             and g['rel'] not in shrinkers]
for key, why in ORDER:
    gs = by.get(key, [])
    print('  %-12s %3d rule(s) on %3d page(s)   %s'
          % (key, len(gs), len({g['rel'] for g in gs}), why))

print('\n  After the page rule below: %d rule(s) on %d page(s) can go.'
      % (len(removable), len({g['rel'] for g in removable})))

print('\n' + '-' * 74)
print('ORPHANS - the controls base never reaches')
print('-' * 74)
orph = Counter()
pages = defaultdict(Counter)
for g in by.get('ORPHANS', []):
    for k, v in g['orphans'].items():
        pages[g['rel']][k] = max(pages[g['rel']][k], v)
for rel in sorted(pages):
    print('  %-44s %s' % (rel, ', '.join('%d %s' % (v, k)
                                         for k, v in sorted(pages[rel].items()))))
    for k, v in pages[rel].items():
        orph[k] += v
print('\n  in total: %s' % ', '.join('%d %s' % (v, k)
                                     for k, v in orph.most_common()))

print('\n' + '-' * 74)
print('EVERY-WIDTH and OTHER-WIDTH')
print('-' * 74)
for key in ('EVERY-WIDTH', 'OTHER-WIDTH'):
    for g in by.get(key, []):
        print('  %-12s %-36s %-26s %s'
              % (key, g['rel'], (g['media'] or '(none)')[:26],
                 ', '.join(g['sels'])[:40]))

print('\n' + '-' * 74)
print('MIXED - what else those rules set')
print('-' * 74)
print('  %s' % ', '.join('%s x%d' % (k, v) for k, v in Counter(
    p for g in by.get('MIXED', []) for p in g['extra']).most_common()))

print('\n' + '-' * 74)
print('!important, and what could beat base once it goes')
print('-' * 74)
rem = [g for g in found if g['verdict'] in ('REDUNDANT', 'MIXED')]
risky = sorted({g['rel'] for g in rem if g['rel'] in shrinkers})
print('  A page that sets a text control below 16px anywhere keeps EVERY')
print('  guard: base\'s plain 16px can lose to that smaller number, whether')
print('  the local guard was !important or simply later in the cascade.')
print('  %d page(s) with a removable guard are caught by that rule:'
      % len(risky))
for rel in risky:
    print('      %s' % rel)
    for s in shrinkers[rel][:3]:
        print('          %s' % s)

bare = [g for g in found if g['verdict'] in ('REDUNDANT', 'MIXED')
        and g['media'] and 'screen' not in g['media']]
print('\n' + '-' * 74)
print('THE PRINT-LEAK OVERLAP')
print('-' * 74)
print('  %d removable guard(s) sit in a bare (max-width) block. If removing'
      % len(bare))
print('  one empties its block, the block goes - and test_print_leaks.py')
print('  promises every query survives. Stage E needed a LATER entry for')
print('  exactly this; this round would need one per emptied block.')

print('\n' + '-' * 74)
print('OUT OF SCOPE')
print('-' * 74)
for rel, why in sorted(OUT_OF_SCOPE.items()):
    print('  %-40s %s' % (rel, why))

if VERBOSE:
    print('\n' + '=' * 74)
    print('EVERY GUARD')
    print('=' * 74)
    for g in sorted(found, key=lambda x: (x['verdict'], x['rel'])):
        print('  %-11s %-40s %-30s %s'
              % (g['verdict'], g['rel'], (g['media'] or '-')[:30],
                 ', '.join(g['sels'])[:50]))

print('\n' + '=' * 74)
print('Nothing was written. This tool only reads.')
print('=' * 74)
