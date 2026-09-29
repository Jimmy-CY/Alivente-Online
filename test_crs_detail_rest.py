# -*- coding: utf-8 -*-
"""test_crs_detail_rest.py - Section X round X10, 29 Sep 2026.

X8 took this page's colour, X9 its sections, form and tables. X10 takes
the lifecycle timeline, the Excel panel and the XML modal - and with
them the CRS module is finished.

SECTION 1 is the three clusters, on tokens.

SECTION 2 is THE THREE COLOURS THAT NEEDED A DECISION rather than a
lookup, and the reasoning is asserted, not just recorded.

SECTION 3 is the alias, deleted - the eighth and last copy.

SECTION 4 is TWO COLOUR KEYWORDS X5 COULD NOT SEE on the CRS hub. That
round cleared its three hexes and stopped; a hex search does not find a
word. This round's module-wide audit found them.

SECTION 5 is the module, whole: eight pages, zero hexes, zero colour
keywords, no local palette - and crs_outstanding() empty for the first
time.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import os
import re
import sys

import alv_tree

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_crsdetr'
ME = 'test_crs_detail_rest.py'
PATCHER = 'apply_crs_detail_rest.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = os.path.join(ROOT, 'crs', 'templates', 'crs', 'submission_detail.html')
BASE = os.path.join(T, 'base.html')
HOUSE = os.path.join(T, 'suppliers.html')   # the control: a house list page
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')
MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)


def bare(s):
    """Lesson 21 - strip CSS comments before ANY selector comparison."""
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def nocmt(s):
    """The same, for a body or a whole file. X1's own patcher failed its
    first hex gate on the explanatory comment it had just written."""
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


def sels(css):
    return [bare(m.group(1)) for m in RULE.finditer(css)]


def markup(t):
    return re.sub(r'<(script|style)\b.*?</\1>', '', t, flags=re.S | re.I)


def has_class(mk, name):
    """A whole class token, not a substring. `action-icon` is inside
    `mobile-action-icon`, and the patcher's first gate fell for it."""
    return bool(re.search(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', mk))


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)), flags=re.S)
            for m in STYLE.finditer(t)]


def one_branch(t):
    while True:
        stack = []
        for m in TAG.finditer(t):
            k = m.group(1)
            if k == 'if':
                stack.append([m.start(), m.end(), None])
            elif k in ('elif', 'else'):
                if stack and stack[-1][2] is None:
                    stack[-1][2] = m.start()
            elif k == 'endif':
                if not stack:
                    return t
                s, fe, cut = stack.pop()
                if cut is not None:
                    t = t[:s] + t[fe:cut] + t[m.end():]
                    break
        else:
            return t


def body_of(t):
    t = one_branch(t)
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
        b = re.sub(rx, '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'AT', b, flags=re.S)


pn, pw_ = now(PAGE), was(PAGE)
cn = '\n'.join(STYLE.findall(pn))
cw = '\n'.join(STYLE.findall(pw_))
mn, mw = markup(pn), markup(pw_)
HUB = os.path.join(ROOT, 'crs', 'templates', 'crs', 'index.html')


def rule(css, sel):
    return [m.group(2) for m in RULE.finditer(css) if bare(m.group(1)) == sel]


def css_of(t):
    return '\n'.join(STYLE.findall(t))


def hexes(c):
    return sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(c))))


def keywords(c):
    return [bare(m.group(1)) for m in RULE.finditer(c)
            if re.search(r'(?:^|[;{])\s*(?:colou?r|background(?:-color)?|'
                         r'border(?:-\w+)?-colou?r)\s*:\s*'
                         r'(?:white|black|red|green|blue|grey|gray)\b',
                         m.group(2), re.I)]


print('=' * 74)
print('%s - X10, THE LAST OF THE CRS MODULE' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE THREE CLUSTERS, ON TOKENS')
# ==========================================================================
_src = read(os.path.join(ROOT, PATCHER))
# THE CLOSING BRACKET IS THE ONE AT THE START OF A LINE, not the first
# one after `SCOPE = [`. X10's scope contains
# `.excel-upload-row input[type="file"]`, so a search for the first `]`
# stops INSIDE a selector and the list comes back seven items long
# instead of thirty-six. X9's copy of this parse survived only because
# none of its selectors happened to contain a bracket.
_i = _src.index('SCOPE = [')
SCOPE = re.findall(r"'([^']+)'", _src[_src.index('[', _i):
                                      _src.index('\n]', _i)])
ok(len(SCOPE) >= 30, 'this round owns %d named rules' % len(SCOPE))
for group, lead in (('lifecycle', '.lifecycle-event'),
                    ('Excel', '.excel-current, .xml-current'),
                    ('XML modal', '.xml-modal-header')):
    ok(lead in SCOPE, '  the %s cluster is in scope (%s)' % (group, lead))
dirty = []
for sel in SCOPE:
    b = rule(cn, sel)
    if not b:
        dirty.append((sel, 'VANISHED'))
        continue
    h = re.findall(r'#[0-9a-fA-F]{3,8}\b', b[0])
    k = re.findall(r'(?:^|[;{])\s*(?:colou?r|background(?:-color)?|'
                   r'border(?:-\w+)?-colou?r)\s*:\s*'
                   r'(white|black|red|green)\b', b[0], re.I)
    if h or k or 'var(--crs-' in b[0]:
        dirty.append((sel, h + k))
ok(not dirty, '  and every one is clean - no hex, no keyword, no alias',
   dirty)
ok(rule(cn, '.lifecycle-notes-content')
   and 'transparent' in rule(cn, '.lifecycle-notes-content')[0],
   '  `transparent` is LEFT - it is the absence of a colour rather than '
   'one, and nothing about it is invisible to an audit')

# ==========================================================================
head('2. THE THREE THAT NEEDED A DECISION, NOT A LOOKUP')
# ==========================================================================
was_excel = rule(cw, '.excel-current > i.fa-file-excel')
now_excel = rule(cn, '.excel-current > i.fa-file-excel')
ok(was_excel and '#1d6f42' in was_excel[0],
   'CONTROL: the Excel file icon was a green hex', was_excel)
ok(now_excel and 'var(--alv-tag-moss-ink)' in now_excel[0],
   '  and takes a TAG ink, not --alv-good. Green on that icon does not '
   'mean healthy, it means Excel - a FILE TYPE, which is categorical, '
   'and the house has inks for exactly that', now_excel)
ok(now_excel and 'alv-good' not in now_excel[0],
   '  NOT --alv-good, which on this page already means acknowledged - a '
   'colour must not mean two things at once')

was_xml = rule(cw, '.xml-current > i.fa-file-code')
now_xml = rule(cn, '.xml-current > i.fa-file-code')
ok(was_xml and '#17a2b8' in was_xml[0],
   'CONTROL: the XML file icon was #17a2b8', was_xml)
ok(now_xml and 'var(--alv-accent)' in now_xml[0],
   '  and is the house accent - the hex test_deeper_teal.py has been '
   'waiting on', now_xml)
gone_17 = len(re.findall(r'#17a2b8', nocmt(pw_))) - \
    len(re.findall(r'#17a2b8', nocmt(pn)))
ok(gone_17 >= 1, '  %d occurrence(s) of it leave the page' % gone_17)

was_stripe = rule(cw, '.lifecycle-notes')
now_stripe = rule(cn, '.lifecycle-notes')
ok(was_stripe and '#ffc107' in was_stripe[0],
   'CONTROL: the notes stripe was Bootstrap amber', was_stripe)
ok(now_stripe and 'var(--alv-warn)' in now_stripe[0],
   '  and is full-strength --alv-warn, 188 of 765 away - the largest '
   'single move in the X section, and made on purpose', now_stripe)
neighbour = rule(cn, '.lifecycle-event')
ok(neighbour and 'border-left: 3px solid var(--alv-accent)' in
   ' '.join(neighbour[0].split()),
   '  because the stripe BESIDE it is a full-strength accent, not a line '
   'tint - taking --alv-warn-line to keep the pixel closer would have '
   'made two stripes doing the same job answer to different kinds of '
   'token', neighbour)

# ==========================================================================
head('3. THE ALIAS, DELETED - THE EIGHTH AND LAST COPY')
# ==========================================================================
ok('--crs-dark' in nocmt(pw_),
   'CONTROL: the page still held the alias when this round started')
ok(rule(cw, ':root'), '  in a :root block of its own', rule(cw, ':root'))
ok('--crs-' not in nocmt(pn), 'nothing on the page declares or reads it',
   re.findall(r'--crs-\w+', nocmt(pn))[:4])
ok(':root' not in sels(cn), '  and the block is gone')
ok(len(re.findall(r'var\(--crs-', pw_)) >= 4,
   '  CONTROL: X8 left %d reader(s) standing on purpose, because they '
   'lived in the clusters X9 and X10 owned'
   % len(re.findall(r'var\(--crs-', pw_)))

# ==========================================================================
head('4. TWO COLOUR KEYWORDS X5 COULD NOT SEE')
# ==========================================================================
hub_now = css_of(read(HUB))
hub_was = css_of(read(HUB + SUFFIX)) if os.path.isfile(HUB + SUFFIX) \
    else hub_now
ok(len(keywords(hub_was)) == 2,
   'CONTROL: the CRS hub painted 2 rules with the keyword white',
   keywords(hub_was))
ok(not hexes(hub_was),
   '  and carried NO hex at all - X5 cleared all three and stopped, '
   'which is exactly why the keywords survived: a hex search does not '
   'find a word', hexes(hub_was))
ok(not keywords(hub_now), '  both are gone now', keywords(hub_now))
ok('var(--alv-on-accent)' in hub_now,
   '  on --alv-on-accent, the token base owns for text on the accent',
   'alv-on-accent' in hub_now)

# ==========================================================================
head('5. THE MODULE, WHOLE')
# ==========================================================================
tot_h = tot_k = tot_a = 0
for n in alv_tree.crs_pages():
    c = css_of(read(os.path.join(ROOT, 'crs', 'templates', n)))
    h, k = hexes(c), keywords(c)
    a = 1 if '--crs-' in nocmt(c) else 0
    tot_h += len(h)
    tot_k += len(k)
    tot_a += a
    ok(not h and not k and not a,
       '  %-28s hex %-2d keyword %-2d alias %d' % (n, len(h), len(k), a),
       {'hex': h, 'keyword': k})
ok(tot_h == 0 and tot_k == 0 and tot_a == 0,
   'ACROSS ALL %d CRS PAGES: zero hexes, zero colour keywords, no local '
   'palette' % len(alv_tree.crs_pages()), [tot_h, tot_k, tot_a])
ok(alv_tree.crs_outstanding() == [],
   'and crs_outstanding() is EMPTY for the first time',
   alv_tree.crs_outstanding())
ok(len(alv_tree.CRS_HOUSE) == len(alv_tree.crs_pages()),
   '  every page in the module is in CRS_HOUSE',
   [len(alv_tree.CRS_HOUSE), len(alv_tree.crs_pages())])

# THE THING THAT STARTED IT.
ok(len(alv_tree.roots()) == 2,
   'CONTROL: and the module is still in the second root, which is where '
   'no gate could see it eleven rounds ago',
   [os.path.basename(os.path.dirname(r)) + '/' + os.path.basename(r)
    for r in alv_tree.roots()])

# ==========================================================================
head('6. CONTROLS, AND THE GATE')
# ==========================================================================
ok(bare('/* banner */ .lifecycle-event') == '.lifecycle-event',
   'the selector reader strips a comment banner (lesson 21)')
broken = [' '.join(c.split())[:60] for c in re.findall(r'/\*.*?\*/', cn, re.S)
          if '{' in c or '}' in c]
ok(not broken, '  and no CSS comment carries a brace', broken)
ok('#ffc107' in nocmt(cw),
   'reverting the page brings the Bootstrap amber back, so section 2 '
   'would FAIL - a revert is caught')
ok(os.path.isfile(HUB + SUFFIX),
   'the hub has a %s backup too - this round changed TWO files' % SUFFIX)

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and SUFFIX in ROUNDS and '.bak_crsdets' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_crsdets'),
       '  and after X9, which it depends on (lesson 54)', ROUNDS[-3:])
ps1 = read(os.path.join(ROOT, PS1)) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  THE CRS MODULE IS HOUSE. Eight pages, ten rounds. What began as')
print('  a green nothing could see - because the module lives in a second')
print('  Django app no census in this programme had ever walked - is now')
print('  zero hexes and zero colour keywords across all eight.')
print('')
print('  NEXT: the WAITING register in alv_tree.py holds 27 suites that')
print('  were kept on the narrow root because CRS failed their standard.')
print('  Most of those standards are now met. The next round runs them')
print('  against the wide tree and takes off every one that passes.')
print('=' * 74)
sys.exit(1 if failed else 0)
