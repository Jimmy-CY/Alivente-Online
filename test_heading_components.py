"""test_heading_components.py - base owns the three classes the standard is
   written in, and no page restates them.

    python test_heading_components.py

Run from the repo root, after apply_heading_components.py.

WHAT THIS SUITE CANNOT DO, SAID FIRST
-------------------------------------
It cannot tell you the spacing is RIGHT. Whether 1rem under a heading looks
better than 0.75rem is a judgement, and the only instrument for it is eyes
on a screen. What it can tell you is that there is now ONE answer instead
of thirty-four, that the answer is the one that was agreed, and that the
conditional half of it actually fires.

SECTION 3 IS THE ONE THAT EARNS ITS KEEP, because the conditional is the
part that can silently not work. base says

    .page-title-h2:has(+ .page-subtitle-h4) { margin-bottom: 0; }

and a browser that does not support :has() ignores that line completely and
leaves every heading with the 1rem gap - no error, no warning, a layout
that is slightly wrong everywhere and looks deliberate. Reading the
stylesheet cannot distinguish that from working. So section 3 renders both
shapes in Chromium and MEASURES the gap.

A SKIPPED CHECK IS REPORTED, NOT SWALLOWED. Eleven suites on this gate
print a SKIP line when Playwright is absent and then report "0 failed" and
exit 0, which is how a fresh clone goes green having proved a third less
than it looks. The summary here counts skips beside passes and failures.
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

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
ME = os.path.basename(__file__)
MARK = 'ALV PAGE HEADING v1'
# SCOPE GUARD #30. This was three classes. .page-action-buttons-form
# has been retired: it declared justify-content: flex-end and lost every
# time to the auto margin base puts on .action-back, which is on every
# entry screen. The heading round's claim was that BASE OWNS THE CLASSES
# THE STANDARD IS WRITTEN IN - not that there are three of them. Asserting
# base still defines a class nobody should use would hold the system to a
# mistake. What replaces it is stronger: the class must be gone from base
# AND from every template. See test_one_action_bar.py.
CLASSES = ('page-title-h2', 'page-subtitle-h4')
RETIRED = 'page-action-buttons-form'

PASS = FAIL = SKIP = 0
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


def skip(name, why):
    """A check that did not run. COUNTED, and named in the summary.

    The alternative - printing a line and moving on - is what lets a suite
    report zero failures having proved a third less than it looks.
    """
    global SKIP
    SKIP += 1
    print('  SKIP  %s - %s' % (name, why))


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


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


def rel_of(p):
    return os.path.relpath(p, T).replace(os.sep, '/')


def stylesheets(text):
    return [m.group(1) for m in
            re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S)]


def rules(text):
    """(media, selector, declaration) for every rule, brace-aware.

    Comments blanked to spaces of the same length first. A brace inside a
    comment desynchronises a brace-counting walk, which is how the patcher
    for this round deleted a media block that was not empty - caught by a
    check, not by reading.
    """
    out = []
    for css in stylesheets(text):
        scan = re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), css,
                      flags=re.S)
        media = None
        for m in re.finditer(r'@media([^{]*)\{|([^{}]+)\{([^{}]*)\}|\}', scan):
            if m.group(1) is not None:
                media = ' '.join(m.group(1).split())
            elif m.group(0) == '}':
                media = None
            else:
                # READ THE SELECTOR WITH ITS COMMENTS GONE. The walk uses
                # the blanked copy, but the text comes from the original,
                # and the original span starts after the previous rule's
                # brace - so a comment sitting above a rule lands INSIDE
                # its selector. The first draft reported base's selector as
                # `/* ===== ALV PAGE HEADING v1 ===== */ .page-title-h2`
                # and then could not find the rule it had just read.
                a, b = m.span(2)
                sel = re.sub(r'/\*.*?\*/', ' ', css[a:b], flags=re.S)
                out.append((media, ' '.join(sel.split()),
                            ' '.join(css[m.start(3):m.end(3)].split())))
    return out


if not os.path.isdir(T):
    print('! %s not found - run from the repo root' % T)
    sys.exit(1)

B = read(BASE)
BR = rules(B)

# ---------------------------------------------------------------------- 1
head('1. base DECLARES THEM, ONCE EACH')

check('base carries the block', MARK in B)
check('  exactly once', B.count(MARK) == 1, str(B.count(MARK)))

for c in CLASSES:
    own = [r for r in BR if r[1] == '.' + c and not r[0]]
    check('base defines .%s' % c, len(own) == 1,
          '%d rule(s): %s' % (len(own), own[0][2][:56] if own else ''))

_h2 = [r for r in BR if r[1] == '.page-title-h2' and not r[0]]
check('  the heading centres itself, so no page needs a center element',
      bool(_h2) and 'text-align: center' in _h2[0][2])
check('  and opens a gap below it by default',
      bool(_h2) and 'margin-bottom: 1rem' in _h2[0][2], _h2[0][2] if _h2 else '')

_cond = [r for r in BR if ':has(+ .page-subtitle-h4)' in r[1]]
check('THE CONDITIONAL IS STATED ONCE', len(_cond) == 1, str(len(_cond)))
check('  and it closes the gap', bool(_cond)
      and 'margin-bottom: 0' in _cond[0][2],
      _cond[0][2] if _cond else '')

_h4 = [r for r in BR if r[1] == '.page-subtitle-h4' and not r[0]]
check('the subtitle takes a base token, not a literal',
      bool(_h4) and 'var(--alv-ink-soft)' in _h4[0][2])
check('  CONTROL: and --alv-ink-soft is declared',
      re.search(r'--alv-ink-soft\s*:', B) is not None)
check('  no #6c757d survives on it, which is Bootstrap\'s grey',
      not [r for r in BR if 'page-subtitle' in r[1] and '#6c757d' in r[2]])

# The retired class, checked here as well as in its own suite, because
# this is the suite that used to REQUIRE it. A claim that changes sides
# should be visible in the place it used to live.
#
# A CLASS TOKEN OR A RULE, NEVER THE BARE STRING. base's own note NAMES the
# class it retired - that is what the note is for - and the first spelling
# of this check searched for the string and reported base.html as still
# carrying it. Third time this week a check has been pointed at a substring
# instead of at the thing it names.
_RET_USE = re.compile(r'class="[^"]*(?<![-\w])' + RETIRED + r'(?![-\w])')
_RET_RULE = re.compile(r'\.' + RETIRED + r'\b[^{}\n]*\{')
_ret = []
for _d, _s, _ns in os.walk(T):
    for _n in sorted(_ns):
        if not _n.endswith('.html'):
            continue
        _t = read(os.path.join(_d, _n))
        if _RET_USE.search(_t) or _RET_RULE.search(_t):
            _ret.append(os.path.relpath(os.path.join(_d, _n), T)
                        .replace(os.sep, '/'))
check('the retired form-bar variant is gone from base and every page',
      not _ret, '%d still carry it: %s' % (len(_ret), ', '.join(sorted(_ret)[:4])))
check('  CONTROL: and the check can see a class token when there is one',
      bool(_RET_USE.search('class="a ' + RETIRED + ' b"'))
      and not _RET_USE.search('class="' + RETIRED + '-x"')
      and bool(_RET_RULE.search('.' + RETIRED + ' { a: b; }')))

# ---------------------------------------------------------------------- 2
head('2. NO PAGE RESTATES THEM - and none fires on paper')

restate, bare = [], []
for p in templates():
    if os.path.abspath(p) == os.path.abspath(BASE):
        continue
    for media, sel, _d in rules(read(p)):
        if any('.' + c in sel for c in CLASSES):
            restate.append('%s: %s' % (rel_of(p), sel[:40]))
            if media and not media.startswith('screen'):
                bare.append(rel_of(p))

check('no page styles one of the three any more', not restate,
      '%d: %s' % (len(restate), '; '.join(restate[:3])))
check('  so none of them can fire on paper', not bare,
      '%d: %s' % (len(bare), ', '.join(sorted(set(bare))[:4])))

_bm = [r for r in BR if r[0] and any('.' + c in r[1] for c in CLASSES)]
check('base\'s own phone rules say screen', bool(_bm)
      and all(r[0].startswith('screen') for r in _bm),
      '%d rule(s): %s' % (len(_bm), _bm[0][0] if _bm else ''))
check('  CONTROL: and there are phone rules to have got wrong',
      len(_bm) >= 2, '%d' % len(_bm))

users = [rel_of(p) for p in templates()
         if re.search(r'class="[^"]*\bpage-title-h2\b', read(p))]
check('  the pages still USE the class base now styles', len(users) >= 30,
      '%d page(s)' % len(users))

centred = []
for p in templates():
    for m in re.finditer(r'<h[24][^>]*class="[^"]*\bpage-(?:title-h2|'
                         r'subtitle-h4)\b[^"]*"[^>]*>(.*?)</h[24]>',
                         read(p), re.S):
        if '<center' in m.group(1).lower():
            centred.append(rel_of(p))
check('no heading wraps itself in a center element', not centred,
      '%d: %s' % (len(centred), ', '.join(sorted(set(centred))[:4])))

# ---------------------------------------------------------------------- 3
head('3. RENDERED - the conditional actually fires')

# :has() is the part that can silently not work. A browser without it drops
# the rule and every heading keeps the default gap: no error, no warning,
# a layout that is slightly wrong everywhere and looks intentional.
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

if sync_playwright is None:
    for n in ('the gap closes when a subtitle follows',
              'the gap opens when nothing follows',
              'CONTROL: the two differ, so the rule is doing something',
              'the subtitle is the quieter of the two'):
        skip(n, 'playwright is not installed')
else:
    css = '\n'.join(stylesheets(B))
    page_html = ("<!doctype html><meta charset=utf-8><style>%s</style>"
                 "<div id=a><h2 class='page-title-h2'>MODULE</h2>"
                 "<h4 class='page-subtitle-h4'>MODE</h4></div>"
                 "<div id=b><h2 class='page-title-h2'>MODULE</h2>"
                 "<p id=after>body</p></div>" % css)
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page(viewport={'width': 1200, 'height': 900})
            # NOTHING LEAVES THIS MACHINE. base pulls fonts and icons from
            # CDNs; a suite that lets those through is measuring somebody
            # else's network.
            pg.route('**://**', lambda r: r.abort())
            pg.set_content(page_html, wait_until='load')
            m = pg.evaluate("""() => {
                const g = (s) => document.querySelector(s)
                    .getBoundingClientRect();
                const h2a = g('#a .page-title-h2');
                const h4  = g('#a .page-subtitle-h4');
                const h2b = g('#b .page-title-h2');
                const aft = g('#after');
                const cs  = getComputedStyle(
                    document.querySelector('#a .page-subtitle-h4'));
                const ch2 = getComputedStyle(
                    document.querySelector('#a .page-title-h2'));
                return {withSub: h4.top - h2a.bottom,
                        without: aft.top - h2b.bottom,
                        subColour: cs.color, align: ch2.textAlign};
            }""")
            br.close()
        check('the gap closes when a subtitle follows', m['withSub'] < 6,
              '%.1fpx' % m['withSub'])
        check('the gap opens when nothing follows', m['without'] > 10,
              '%.1fpx' % m['without'])
        check('CONTROL: the two differ, so :has() is doing something',
              m['without'] - m['withSub'] > 8,
              '%.1f vs %.1f' % (m['without'], m['withSub']))
        check('the heading centres itself without a center element',
              m['align'] == 'center', m['align'])
        check('the subtitle is the quieter of the two',
              m['subColour'] not in ('rgb(0, 0, 0)', ''), m['subColour'])
    except Exception as e:
        for n in ('the gap closes when a subtitle follows',
                  'the gap opens when nothing follows',
                  'CONTROL: the two differ, so the rule is doing something',
                  'the subtitle is the quieter of the two'):
            skip(n, 'the browser would not run: %s' % str(e)[:44])

# ---------------------------------------------------------------------- 4
head('4. IT IS ON THE GATE')

if not os.path.exists(PS1):
    check('Push-PendingChanges.ps1 is here', False, 'it is not')
else:
    check('this suite is on the gate', ME in read(PS1), ME)

# ---------------------------------------------------------------------- 5
print('\n' + '=' * 72)
print('  %d passed, %d failed, %d skipped' % (PASS, FAIL, SKIP))
if FAILED:
    print('')
    for f in FAILED:
        print('  - %s' % f)
if SKIP:
    print('')
    print('  %d check(s) DID NOT RUN. That is not the same as passing, and')
    print('  a summary that hides it is why a fresh clone can go green')
    print('  having proved a third less than it looks.' % ())
print('')
print('  NOT PROVED HERE: that the spacing is the RIGHT spacing. One answer')
print('  instead of thirty-four is what this measures; whether that answer')
print('  is handsome wants eyes on a screen.')
print('=' * 72)
sys.exit(1 if FAIL else 0)
