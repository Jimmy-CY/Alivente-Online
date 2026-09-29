# -*- coding: utf-8 -*-
"""test_crs_detail_colour.py - Section X round X8, 29 Sep 2026.

The last CRS page, and much the biggest. Demetri chose to split it
colour-first, so THIS ROUND CHANGES EVERYTHING YOU CAN SEE AND NOTHING
STRUCTURAL. X9 takes the form cluster and the four tables; X10 the
lifecycle timeline, the Excel panel and the XML modal.

SECTION 1 is the shell and the alias - and :root is RETONED here rather
than deleted, which is the opposite of what X1 to X7 did, for a reason
this suite asserts rather than asks you to believe.

SECTION 2 is the twenty-three buttons, toned BY CONSEQUENCE.

SECTION 3 is the badges and the banners.

SECTION 4 is what the round deliberately did NOT do, and the suite fails
if it did more.

SECTION 1 IS THE GREEN, GONE. Measured in a browser, before and after,
at 1280 and 390.

SECTION 2 IS THE HELP BUTTON, and the reason it was the only green
control in a bar where Back carried the same Bootstrap class.

SECTION 3 IS THE TABLE - the house component, with a phone card layout
that comes from base rather than from five hand-numbered nth-child rules.

SECTION 4 IS THE MODAL.

SECTION 5 IS WHAT THE ROUND LEFT ALONE, AND WHY. A round that cannot say
what it did not do is a round that will be blamed for it later.
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

SUFFIX = '.bak_crsdetc'
ME = 'test_crs_detail_colour.py'
PATCHER = 'apply_crs_detail_colour.py'
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
BTN = re.compile(r'<(?:button|a)\b[^>]*class="[^"]*\bbtn\b[^"]*"[^>]*>')


def rule(css, sel):
    return [m.group(2) for m in RULE.finditer(css) if bare(m.group(1)) == sel]


def classes(t):
    return [' '.join(re.search(r'class="([^"]*)"', m.group(0)).group(1).split())
            for m in BTN.finditer(markup(t))]


print('=' * 74)
print('%s - X8, SUBMISSION DETAIL: THE COLOUR' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE SHELL, AND THE ALIAS THAT IS RETONED RATHER THAN DELETED')
# ==========================================================================
ok('.crs-panel' in sels(cw), 'CONTROL: the page sat in the green panel')
ok('.crs-panel' not in sels(cn) and not has_class(mn, 'crs-panel'),
   '  and it is deleted, as on every other CRS list and form screen')
ok('ALIVENTE ONLINE -' in mw and 'ALIVENTE ONLINE -' not in mn,
   'the title drops the brand prefix')
for h6 in re.findall(r'<h[1-6]\b[^>]*>.*?</h[1-6]>', mn, re.S):
    ok('<center>' not in h6, '  and no heading wraps itself in <center>',
       ' '.join(h6.split())[:60])
ok(mn.count('page-subtitle-h4') == 1,
   '  and it gains the subtitle every house screen carries')
ok('action-icon' in mw and not has_class(mn, 'action-icon'),
   'Help comes off `action-icon`, the class base has never owned')

# THE OPPOSITE OF X1 TO X7, AND WHY.
root_w = rule(cw, ':root')
root_n = rule(cn, ':root')
ok(root_w and '#28a745' in root_w[0],
   'CONTROL: the --crs-* alias held the Bootstrap green', root_w)
ok(root_n, ':root SURVIVES this round - X1 to X7 deleted it, and here '
   'that would be wrong', root_n)
ok(root_n and not re.findall(r'#[0-9a-fA-F]{3,8}\b', root_n[0]),
   '  but it holds no hex any more')
ok(root_n and 'var(--alv-accent)' in root_n[0],
   '  it points at the house accent, the way personal.html points '
   '--personal-dark at it', root_n)
readers = len(re.findall(r'var\(--crs-', pn))
ok(readers >= 8,
   '  and %d rules still READ it - in the validation, XML and lifecycle '
   'clusters, which are X9 and X10. Deleting the block now would leave '
   'every one of them with no value at all; retoning it turns all of '
   'them teal in a single line, which is what a colour round is for'
   % readers, readers)

# ==========================================================================
head('2. TWENTY-THREE BUTTONS, TONED BY CONSEQUENCE')
# ==========================================================================
cw_btns, cn_btns = classes(pw_), classes(pn)
ok(len(cw_btns) == 23 and len(cn_btns) == 23,
   'the page has 23 btn controls, before and after',
   [len(cw_btns), len(cn_btns)])
boot_w = sorted({c for cs in cw_btns for c in cs.split()
                 if re.match(r'btn-(?:outline-)?(?:success|warning|info|'
                             r'primary|danger|secondary)$', c)})
ok(len(boot_w) >= 6,
   'CONTROL: they used %d different Bootstrap colour families'
   % len(boot_w), boot_w)
left = sorted(set(re.findall(
    r'btn-(?:outline-)?(?:success|warning|info|primary|danger|secondary)\b',
    mn)))
ok(not left, '  and NONE survives anywhere on the page', left)


def n_of(cls, cs):
    return sum(1 for c in cs if cls in c.split())


ok(n_of('action-primary', cn_btns) == 5,
   '.action-primary x5 - the affirmative act of the thing you are looking '
   'at: Generate XML, Generate Nil XML, Save Header Changes, Upload, and '
   'Apply on a corrected cell', n_of('action-primary', cn_btns))
ok(n_of('action-danger', cn_btns) == 5,
   '.action-danger x5 - the irreversible: Delete Submission, its confirm, '
   'Remove Excel, Close Submission and ITS confirm',
   n_of('action-danger', cn_btns))
ok(n_of('action-secondary', cn_btns) == 12,
   '.action-secondary x12 - everything that reads, fetches or records',
   n_of('action-secondary', cn_btns))
ok(n_of('action-back', cn_btns) == 1, '.action-back x1 - Back')
ok(n_of('action-primary', cn_btns) + n_of('action-danger', cn_btns)
   + n_of('action-secondary', cn_btns) + n_of('action-back', cn_btns) == 23,
   '  and all 23 are accounted for, with none in two families')

# THE TWO ARGUABLE ONES, MADE EXECUTABLE.
i_close = [i for i, c in enumerate(cw_btns) if c == 'btn btn-warning']
ok(len(i_close) == 2,
   'CONTROL: Close Submission and its confirm were AMBER', i_close)
ok(all('action-danger' in cn_btns[i] for i in i_close),
   '  and are now danger. Amber reads as "careful"; closing a submission '
   'is not careful, it is FINAL. Leaving it amber would have used a '
   'semantic token to paint a button - the thing standard 3.1 names last '
   '- and left the only irreversible control looking gentler than Delete',
   [cn_btns[i] for i in i_close])

marks = [i for i, c in enumerate(cw_btns)
         if c in ('btn btn-primary btn-sm', 'btn btn-success btn-sm',
                  'btn btn-danger btn-sm')]
ok(len(set(cw_btns[i] for i in marks)) >= 3,
   'CONTROL: the three Mark as buttons were blue, green and red',
   sorted({cw_btns[i] for i in marks}))
ok(all('action-secondary' in cn_btns[i] for i in (15, 16, 17)),
   '  and all three are now secondary. They are peers that RECORD an '
   'outcome, not cause one - and the outcome\'s colour is already '
   'carried, correctly, by the status badge. Painting the buttons too '
   'would say it twice, and say it where red means "this destroys '
   'something" everywhere else on the page',
   [cn_btns[i] for i in (15, 16, 17)])
ok('fix-btn' in cn_btns[6] and 'xml-view-btn' in cn_btns[7],
   '  and the two buttons with a SIZE class of their own keep it - the '
   'round changed the tone, not the geometry',
   [cn_btns[6], cn_btns[7]])

# ==========================================================================
head('3. THE BADGES AND THE BANNERS')
# ==========================================================================
ok('.status-badge' in sels(cw) and '.status-badge' not in sels(cn),
   'the badge gives up its own geometry to .alv-pill')
ok(mn.count('class="alv-pill status-') == 1,
   '  and the markup builds it as .alv-pill plus a status name')
TONES = {
    '.status-draft': 'var(--alv-neutral-soft)',
    '.status-closed': 'var(--alv-info-soft)',
    '.status-submitted_externally': 'var(--alv-warn-soft)',
    '.status-acknowledged': 'var(--alv-good-soft)',
    '.status-rejected': 'var(--alv-bad-soft)',
    '.banner-success': 'var(--alv-good-soft)',
    '.banner-warning': 'var(--alv-warn-soft)',
    '.banner-error': 'var(--alv-bad-soft)',
}
for sel, tok in sorted(TONES.items()):
    b, a = rule(cw, sel), rule(cn, sel)
    ok(b and re.findall(r'#[0-9a-fA-F]{3,8}\b', b[0]),
       'CONTROL: %-30s was a hex' % sel, b)
    ok(a and tok in a[0], '  %-30s -> %s' % (sel, tok), a)
ok(len({v for k, v in TONES.items() if k.startswith('.status')}) == 5,
   '  the five statuses take five DIFFERENT tokens')

ok('style="background:#fff3cd' in mw,
   'CONTROL: a SECOND badge painted itself amber with an inline style= - '
   'written by hand into the markup where no stylesheet can see it and '
   'no hex audit can find it')
ok('style="background:#fff3cd' not in mn,
   '  it is gone')
ok(mn.count('alv-pill alv-pill-info') == 1,
   '  and Nil Return takes the INFORMATIONAL pill, because a nil return '
   'is a fact about the submission and not a warning')

# ==========================================================================
head('4. WHAT THIS ROUND DID NOT DO - AND THE SUITE FAILS IF IT DID')
# ==========================================================================
rest = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(cn))))
was = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(cw))))
ok(len(rest) < len(was),
   'distinct hexes fell from %d to %d' % (len(was), len(rest)))
ok(len(rest) > 0,
   '  and are NOT zero. X8 is the colour round only; the form cluster, '
   'the four tables, the timeline, the Excel panel and the XML modal '
   'keep theirs for X9 and X10. If this ever reads zero, a round did '
   'more than it says it does', rest)
for keep in ('.detail-section-title', '.validation-table',
             '.lifecycle-event', '.excel-current, .xml-current',
             '.xml-modal-header'):
    ok(keep in sels(cn), '  KEPT for X9/X10: %s' % keep)
ok(len(re.findall(r'\sstyle="', mn)) >= 15,
   '  and the remaining inline style= attributes are untouched - they '
   'carry LAYOUT, not colour, and belong to the inline-style sweep',
   len(re.findall(r'\sstyle="', mn)))

# ==========================================================================
head('5. CONTROLS, AND THE GATE')
# ==========================================================================
ok(bare('/* banner */ .status-draft') == '.status-draft',
   'the selector reader strips a comment banner (lesson 21)')
broken = [' '.join(c.split())[:60] for c in re.findall(r'/\*.*?\*/', cn, re.S)
          if '{' in c or '}' in c]
ok(not broken,
   '  and no CSS comment on the page contains a brace, which would split '
   'a rule in the wrong place - X6 learned that one the hard way', broken)
ok(has_class('class="mobile-action-icon"', 'mobile-action-icon')
   and not has_class('class="mobile-action-icon"', 'action-icon'),
   '  and a class test does not fire on a longer name containing it')
ok('#28a745' in nocmt(cw),
   'reverting the page brings the Bootstrap green back, so section 1 '
   'would FAIL - a revert is caught')

# THE REGISTER, AND THE ONE PAGE THAT IS NOW BETWEEN STATES.
#
# Every other CRS suite asserted "the pages not in CRS_HOUSE are exactly
# the ones still carrying the module green". After X8 that test can no
# longer tell this page apart: submission_detail is GREEN-FREE but it is
# NOT finished - X9 owns its form and tables, X10 its timeline, Excel
# panel and XML modal. So the register stays honest by saying both
# things out loud rather than by collapsing them into one count.
green = [n for n in alv_tree.crs_pages()
         if re.search(r'#(?:28a745|d4edda|218838)\b',
                      nocmt(read(os.path.join(ROOT, 'crs', 'templates', n))),
                      re.I)]
ok(not green,
   'NO CRS page carries the module green any longer - not one of the '
   'eight', green)
# NOT AN ASSERTION ABOUT THE REGISTER. The first draft required this
# page to be the one outstanding entry - true when X8 was written, false
# the moment X10 finished the page and emptied the list. A suite asserts
# what ITS OWN round guarantees; the register belongs to whichever round
# is last. `now()` reads the page as X8 left it, so this stays true.
ok(len(rest) > 0,
   'X8 left this page unfinished on purpose: %d hexes remain in its '
   'form, tables, timeline, Excel panel and XML modal, which are X9 and '
   'X10' % len(rest))

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and SUFFIX in ROUNDS and '.bak_crsstart' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_crsstart'),
       '  and after the round before it (lesson 54)', ROUNDS[-3:])
ps1 = read(os.path.join(ROOT, PS1)) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NEXT: X9 - the form cluster and the four tables on this page.')
print('  Then X10 - the lifecycle timeline, the Excel panel and the XML')
print('  modal, and the round that deletes the --crs-* alias for good.')
print('=' * 74)
sys.exit(1 if failed else 0)
