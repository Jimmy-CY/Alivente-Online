# -*- coding: utf-8 -*-
"""test_walk_help.py - Section W round W2, 28 Sep 2026.

Reported by Demetri: "Help Buttons are not as per standard."

They were not. help_page.html had no .page-action-buttons at all - it
wrote its own component under its own four names, eleven rules and 1,761
characters, for something base has owned since the action-bar round.

SECTION 3 IS RENDERED AND IT IS THE POINT. The old bar was
`justify-content: center`, so the primary sat mid-screen with Back beside
it. Measured at 1280px: primary at 617-817, Back at 827-903. The house
bar puts the primary at the left and Back flush right - 260-450 and
1185-1260 - which is what every other page in the system does.

SECTION 5 RECORDS WHAT THIS ROUND KEPT AND WHY. `.help-hero h2` still
overrides the title's colour and weight, and deleting it would change a
title nobody complained about. The reason it CAN differ is a gap in
base: .page-title-h2 sets alignment and two margins and nothing else -
no colour, no weight, no size - so eighty-eight pages inherit whatever
they happen to inherit. That is a question about the heading standard,
not about this page.
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

SUFFIX = '.bak_walk2'
ME = 'test_walk_help.py'
PATCHER = 'apply_walk_help.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'
PAGE = os.path.join(T, 'help_page.html')

OLD_NAMES = ['help-hero-actions', 'btn-generate-manual', 'btn-help-back',
             'help-back-label']
DEAD = ['.help-hero-actions', '.btn-generate-manual',
        '.btn-generate-manual:hover', '.btn-help-back',
        '.btn-help-back:hover', '.btn-help-back .help-back-label',
        '.help-hero p']
KEPT = ['.help-hero', '.help-hero h2']

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
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')
MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)


def bare(s):
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def css_of(t):
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return '\n'.join(STYLE.findall(raw))


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)), flags=re.S)
            for m in STYLE.finditer(t)]


def has_rule(css, sel):
    return any(bare(m.group(1)) == sel for m in RULE.finditer(css))


def markup(t):
    return re.sub(r'<(script|style)\b.*?</\1>', '', t, flags=re.S | re.I)


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
    return re.sub(r'\{\{.*?\}\}', '42', b, flags=re.S)


tn, tw = now(PAGE), was(PAGE)
cn, cw = css_of(tn), css_of(tw)

print('=' * 74)
print('%s - W2, THE HELP PAGE' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE PAGE WROTE ITS OWN COMPONENT, AND HAS STOPPED')
# ==========================================================================
for n in OLD_NAMES:
    ok(n not in tn, '%-22s is gone from the page entirely' % n)
    ok(n in tw, '  CONTROL: it was there before')
for d in DEAD:
    ok(not has_rule(cn, d), '%-34s no longer declared' % d)
    ok(has_rule(cw, d), '  CONTROL: it was declared before')
ok(len(tn) < len(tw),
   '  %d characters left the page' % (len(tw) - len(tn)),
   '%d -> %d' % (len(tw), len(tn)))

# ==========================================================================
head('2. IT WEARS base\'s NAMES NOW')
# ==========================================================================
mk = markup(tn)
ok('page-action-buttons' in mk, 'the bar is .page-action-buttons')
i = mk.index('<div class="page-action-buttons">')
bar = mk[i:mk.index('</div>', mk.index('action-back', i))]
ok('action-primary' in bar, '  the primary is .action-primary')
ok('action-back' in bar, '  Back is .action-back')
ok('action-back-label' in bar,
   "  and its label is .action-back-label, which base hides on a phone")
ok(bar.index('action-primary') < bar.index('action-back'),
   '  primary first, Back last')
ok('class="page-note"' in mk,
   'the description wears .page-note - the component G3b-1 made for it')
ok(has_rule(css_of(read(BASE)), '.page-note'),
   '  and base declares it')
ok('page-title-h2' in mk, 'the title was ALREADY correct - only the bar '
   'below it was hand-rolled')

# ==========================================================================
head('3. RENDERED - THE LAYOUT IS WHY IT LOOKED WRONG')
# ==========================================================================
try:
    import playwright  # noqa: F401
    HAVE = True
except Exception:
    HAVE = False

boot = read(BOOT) if os.path.isfile(BOOT) else ''
bcss = '\n'.join(styles_of(read(BASE)))


def fixture(page_text):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>%s</head>'
            '<body class="has-sidebar"><div class="main-content '
            'with-sidebar">%s</div></body></html>'
            % (boot, bcss,
               ''.join('<style>%s</style>' % c for c in styles_of(page_text)),
               body_of(page_text)))


PROBE = """() => {
  const bar = document.querySelector('.page-action-buttons, .help-hero-actions');
  if (!bar) return null;
  const kids = Array.from(bar.children).map(e => {
    const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    return {cls: e.className.replace('btn ', ''), w: Math.round(r.width),
            left: Math.round(r.left), right: Math.round(r.right),
            grad: s.backgroundImage !== 'none',
            bg: s.backgroundColor};
  });
  const p = document.querySelector('.page-note, .help-hero p');
  const ps = p ? getComputedStyle(p) : null;
  return {kids: kids,
          note: ps ? {size: ps.fontSize, color: ps.color} : null};
}"""


def shoot(text, width):
    from playwright.sync_api import sync_playwright
    fx = os.path.join(SCRATCH, 'w2_%d.html' % width)
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write(fixture(text))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': width, 'height': 800})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        out = pg.evaluate(PROBE)
        br.close()
    return out


if not HAVE:
    skip('the rendered probe', 'playwright is not installed')
else:
    for width in (1280, 390):
        a, b = shoot(tn, width), shoot(tw, width)
        ok(len(a['kids']) == 2,
           'at %4dpx the bar holds the primary and Back' % width, a['kids'])
        prim, back = a['kids'][0], a['kids'][1]
        ok(prim['left'] < width / 3,
           '  the primary is on the LEFT (%d)' % prim['left'])
        ok(back['right'] >= width - 30,
           '  and Back is flush right (%d of %d)' % (back['right'], width))
        bp, bb = b['kids'][0], b['kids'][1]
        if width == 1280:
            ok(bp['left'] > width / 3,
               '  CONTROL: before, the primary sat mid-screen at %d'
               % bp['left'])
            ok(bb['right'] < width - 300,
               '  and Back sat beside it at %d, not at the end'
               % bb['right'])
        ok(back['right'] <= width, '  nothing runs off the end')
        ok(back['left'] >= prim['right'],
           '  and they do not overlap')

    a, b = shoot(tn, 1280), shoot(tw, 1280)
    ok(b['kids'][0]['grad'] and not a['kids'][0]['grad'],
       'the primary was a GRADIENT and is now a flat house fill',
       '%s -> %s' % (b['kids'][0]['bg'], a['kids'][0]['bg']))
    ok(a['kids'][0]['bg'] == 'rgb(14, 124, 139)',
       '  which is --alv-accent', a['kids'][0]['bg'])
    ok(a['note']['size'] == '12px' and b['note']['size'] == '16px',
       'the description is base\'s 12px note, not a 16px paragraph',
       '%s -> %s' % (b['note']['size'], a['note']['size']))
    ok(a['note']['color'] == 'rgb(91, 107, 115)',
       '  in --alv-ink-soft, not #6c757d', a['note']['color'])

    p = shoot(tn, 390)
    ok(p['kids'][1]['w'] == 44,
       'on a phone Back is 44px - the house tap target', p['kids'][1]['w'])
    q = shoot(tw, 390)
    ok(q['kids'][1]['w'] == 50,
       '  CONTROL: it was 50px, set by hand', q['kids'][1]['w'])

# ==========================================================================
head('4. WHAT THIS ROUND KEPT, DELIBERATELY')
# ==========================================================================
for k in KEPT:
    ok(has_rule(cn, k), '%-16s is KEPT' % k)
ok('#2c3e50' in cn,
   '  .help-hero h2 still sets its own colour - deleting it would change '
   'a title nobody reported')
bcss_only = css_of(read(BASE))
m = [x.group(2) for x in RULE.finditer(bcss_only)
     if bare(x.group(1)) == '.page-title-h2']
ok(m and not re.search(r'(?:^|[;{])\s*(?:color|font-weight|font-size)\s*:',
                       m[0]),
   '  and the reason it CAN differ is base: .page-title-h2 sets no '
   'colour, weight or size at all', ' '.join(m[0].split()) if m else '')

# ==========================================================================
head('5. CONTROLS, AND THE GATE')
# ==========================================================================
ok(bare('/* Hero action row */ .help-hero-actions') == '.help-hero-actions',
   'the selector reader strips a comment banner (lesson 21)')
ok(has_rule('a{x:1}.help-hero{y:2}', '.help-hero')
   and not has_rule('a{x:1}.help-hero-actions{y:2}', '.help-hero'),
   '  and matches a whole selector, not a prefix of a longer one')
ok('btn-generate-manual' in was(PAGE),
   'reverting the page puts its own component back, so section 1 would '
   'FAIL')

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and SUFFIX in ROUNDS and '.bak_walk1' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_walk1'),
       '  and after the round before it (lesson 54)', ROUNDS[-3:])
ps1 = read(PS1) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  FOUND HERE, NOT FIXED HERE: base\'s .page-title-h2 sets text-align')
print('  and two margins and NOTHING else - no colour, no weight, no size.')
print('  So eighty-eight pages\' titles are whatever they inherit, and any')
print('  page may override without contradicting the standard. This page')
print('  does, at weight 700 and #2c3e50 against the usual 500 and #212529.')
print('  That is a gap in the heading standard and deserves its own round.')
print('=' * 74)
sys.exit(1 if failed else 0)
