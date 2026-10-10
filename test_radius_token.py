# -*- coding: utf-8 -*-
"""test_radius_token.py - Section D rounds D-12 and D-7, 9 Oct 2026.

TWO PIECES OF DRIFT, NEITHER OF WHICH CHANGES A PIXEL - WHICH IS THE
HARD PART TO PROVE.

D-12 turned 158 `border-radius: 6px` literals into
var(--alv-radius-sm). D-7 took a dead class off five spans. Both are
invisible by design, so "it still looks right" proves nothing here:
the round would look equally right if it had silently done nothing, or
if var() had resolved to nothing on a page that renders without base.

So section 5 RENDERS every affected page twice - once as this round
left it, once from the .bak_radtoken backup - and compares the
computed border-radius of every element that has one. 1942 elements
across 68 pages, and the assertion is that every single one is
unchanged.

WHAT COULD HAVE GONE WRONG, AND WHY IT DID NOT
  A standalone template renders without base, so no custom property
  resolves and var(--alv-radius-sm) would become nothing at all - a
  square corner where a round one was. B-1 learned that about colour.
  Section 3 holds the line: zero of the 158 are on a standalone page,
  and if one ever is, this fails.

  Nine of them read as "inside <script>". They are inline style
  strings in JS template literals that build markup, and several carry
  var(--alv-bad-ink) or var(--alv-surface) within a few characters of
  the radius - so var() in that position is not a hope, the app
  already does it there. Section 5 renders them anyway.

  The round is only invisible while --alv-radius-sm is 6px. Section 4
  pins that, because the day somebody retunes the token this stops
  being a no-op and starts being a change to 158 places.

NOT PROVED HERE: that 6px is the right radius, or that every one of
the 158 should share one. What is proved is that they now do, that
nothing moved when they started to, and that retuning them is one
line instead of 158.
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
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
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
if not os.path.isdir(os.path.join(ROOT, 'pages', 'templates')):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)

SUFFIX = '.bak_radtoken'
ME = 'test_radius_token.py'
PATCHER = 'apply_radius_token.py'
PS1 = 'Push-PendingChanges.ps1'

N_RADIUS = 158        # what THIS round converted
N_PRE = 13            # already tokenised before it, by the B rounds
N_TOTAL = N_RADIUS + N_PRE
N_STYLE, N_ATTR, N_SCRIPT = 156, 6, 9
N_CHIP, N_CHIP_PAGES = 5, 4

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
            for line in str(detail).split('\n')[:10]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


print(__doc__.strip().splitlines()[0])

import alv_rounds as RD                                       # noqa: E402
import alv_tree as T                                          # noqa: E402
import alv_cssrules as C                                      # noqa: E402

LIT = re.compile(r'border-radius\s*:\s*6px')
TOK = re.compile(r'border-radius\s*:\s*var\(--alv-radius-sm\)')
CHIP = 'class="alv-tag comment-author"'


def left_by(p):
    '''The file as THIS round left it - not as it is now.

    alv_rounds.as_left_by walks ROUNDS forward from this suffix and
    hands back the earliest later backup, so a round that lands after
    D-12 and edits one of these pages cannot make this suite fail for
    something it never did.
    '''
    return RD.as_left_by(p, SUFFIX, read)


# ==========================================================================
head('1. SCOPE')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
base_now = left_by(T.path_of('base.html'))
applied = 'D-12, 9 Oct 2026' in base_now
ok(applied, 'base.html carries the round note')
if not applied:
    skip('every later section', 'D-12 is not applied to this tree.')
    print('')
    print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
    sys.exit(1 if failed else 0)


# ==========================================================================
head('2. NOT ONE LITERAL LEFT, AND THE COUNT IS THE ONE MEASURED')
# ==========================================================================
# CODE, NOT PROSE. code_only_js blanks Django, HTML, CSS and JS
# comments while KEEPING THE LENGTH, so offsets still point where they
# did. Eight counts this session fired on a comment before that became
# a rule.
tok = lit = 0
dirty = []
for p in sorted(T.templates()):
    code = T.code_only_js(left_by(p))
    n_l = len(LIT.findall(code))
    tok += len(TOK.findall(code))
    lit += n_l
    if n_l:
        dirty.append('%s: %d' % (T.rel(p).replace(os.sep, '/'), n_l))
ok(lit == 0, 'no `border-radius: 6px` literal survives anywhere in code',
   '\n'.join(dirty[:10]))
# TWO NUMBERS, NOT ONE. The corpus total is not this round's count:
# thirteen declarations were already tokenised by the B rounds. Pinning
# the total as if the round had made all of it would have been a number
# that was true and attributed to the wrong cause - and the first thing
# it would hide is a later round quietly converting more.
converted = 0
for p in sorted(T.templates()):
    b = p + SUFFIX
    if os.path.isfile(b):
        converted += (len(TOK.findall(T.code_only_js(left_by(p))))
                      - len(TOK.findall(T.code_only_js(read(b)))))
ok(tok == N_TOTAL,
   '%d declaration(s) now read var(--alv-radius-sm) across the corpus'
   % tok, 'pinned at %d' % N_TOTAL)
ok(converted == N_RADIUS,
   '  of which THIS round converted %d - the other %d were already '
   'tokens before it, and measuring that against the backups is the '
   'only way to tell the two apart' % (converted, tok - converted),
   'pinned at %d' % N_RADIUS)

# CONTROL: the detector must FIND one when there is one to find.
ok(len(LIT.findall('a { border-radius: 6px; }')) == 1,
   'CONTROL: the literal detector finds a planted literal - a sweep '
   'that reports zero because its regex is broken reads exactly like a '
   'sweep that worked')
ok(len(LIT.findall('a { /* border-radius: 6px */ }')) == 1,
   '  and it is the COMMENT STRIPPING, not the regex, that keeps prose '
   'out of the count')


# ==========================================================================
head('3. WHERE THEY LIVE - AND NONE OF THEM ON A STANDALONE PAGE')
# ==========================================================================
standalone = {T.rel(x) for x in T.standalone()}
ok(len(standalone) > 0, 'alv_tree names %d standalone template(s)'
   % len(standalone))


def inside(spans, i):
    return any(a <= i < b for a, b in spans)


n_style = n_attr = n_script = n_other = 0
on_standalone = []
for p in sorted(T.templates()):
    raw = left_by(p)
    rel = T.rel(p)
    code = T.code_only_js(raw)
    sty, scr, att = (C.style_spans(raw), C.script_spans(raw),
                     C.style_attr_spans(raw))
    for m in TOK.finditer(code):
        i = m.start()
        if inside(sty, i):
            n_style += 1
        elif inside(att, i):
            n_attr += 1
        elif inside(scr, i):
            n_script += 1
        else:
            n_other += 1
        if rel in standalone:
            on_standalone.append(rel)

ok(not on_standalone,
   'NOT ONE of them is on a standalone template. This is the check that '
   'matters: a standalone page renders without base, every custom '
   'property resolves to nothing, and var() there would quietly square '
   'off a corner', sorted(set(on_standalone)))
ok(n_style == N_STYLE,
   '%d in a <style> rule (143 of them this round\'s, 13 already there)'
   % n_style, 'pinned at %d' % N_STYLE)
ok(n_attr == N_ATTR,
   '%d in a style="" attribute - alv_cssrules.VAR_SAFE already names '
   'style-attr as a place var() resolves' % n_attr,
   'pinned at %d' % N_ATTR)
ok(n_script == N_SCRIPT,
   '%d in an inline style built by script, which is a style attribute '
   'by the time a browser sees it' % n_script, 'pinned at %d' % N_SCRIPT)
ok(n_other == 0, '  and none anywhere else', n_other)


# ==========================================================================
head('4. THE ROUND IS ONLY INVISIBLE WHILE THE TOKEN IS 6PX')
# ==========================================================================
bc = T.code_only(base_now)
m = re.search(r'--alv-radius-sm\s*:\s*([^;]+);', bc)
ok(m is not None, 'base declares --alv-radius-sm')
ok(m is not None and m.group(1).strip() == '6px',
   'and it is 6px, which is what all %d of those literals said. THE DAY '
   'SOMEBODY RETUNES THIS, the round stops being a no-op and becomes a '
   'change to %d places - so this check fails on purpose and sends them '
   'to look at a render' % (N_RADIUS, N_RADIUS),
   m.group(1).strip() if m else None)


# ==========================================================================
head('5. MEASURED: EVERY RADIUS COMPUTES EXACTLY AS IT DID BEFORE')
# ==========================================================================
# A SOURCE DIFF WOULD ONLY SAY I CHANGED WHAT I SAID I WOULD CHANGE.
# The claim is about rendered pixels, so this renders: each affected
# page twice, once as the round left it and once from the backup, and
# compares every element that has a radius at all.
BOOT = 'test_fixture_bootstrap413.css'
up = False
try:
    from playwright.sync_api import sync_playwright
    import atexit
    if not os.path.isfile(BOOT):
        raise RuntimeError('%s is missing' % BOOT)
    _pw = sync_playwright().start()
    atexit.register(_pw.stop)
    _br = _pw.chromium.launch()
    up = True
except Exception as _e:
    skip('section 5', 'Chromium or the Bootstrap fixture is unavailable: %s'
         % str(_e).split('\n')[0][:70])

if up:
    boot = read(BOOT)
    bpath = T.path_of('base.html')
    base_was = read(bpath + SUFFIX) if os.path.isfile(bpath + SUFFIX) \
        else base_now

    def styles_of(t):
        return re.findall(r'<style[^>]*>(.*?)</style>', t, re.S)

    def body_markup(t):
        b = re.search(r'<body[^>]*>(.*)</body>', t, re.S)
        return b.group(1) if b else t

    def doc(base_src, t):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style>%s</head>'
                '<body class="has-sidebar"><div class="main-content '
                'with-sidebar">%s</div></body></html>'
                % (boot, '\n'.join(styles_of(base_src)),
                   ''.join('<style>%s</style>' % c for c in styles_of(t)),
                   body_markup(t)))

    JS = '''() => {
      const o = [];
      document.querySelectorAll('*').forEach(el => {
        const s = getComputedStyle(el);
        const r = [s.borderTopLeftRadius, s.borderTopRightRadius,
                   s.borderBottomRightRadius,
                   s.borderBottomLeftRadius].join(' ');
        if (r !== '0px 0px 0px 0px') { o.push(r); }
      });
      return o;
    }'''

    pages = [p for p in sorted(T.templates())
             if TOK.search(T.code_only_js(left_by(p)))
             or os.path.isfile(p + SUFFIX)]
    ctx = _br.new_context(viewport={'width': 1280, 'height': 900})
    # HERMETIC, like test_tap_target and test_control_height already are.
    # 34 templates carry a remote <link> - Font Awesome, and base pulls
    # Bootstrap from a CDN as well as the pinned 4.1.3 fixture. In a
    # sandbox with no route out those fail instantly and the two renders
    # agree. On a machine that CAN reach them they load, they race, and
    # this check failed on fsr.html with 62 elements against 60 - a
    # difference in the network, reported as a difference in the round.
    # base's own standards block says it in one line: renders are
    # hermetic.
    refused = []

    def _offline(route, request):
        refused.append(request.url)
        route.abort()

    ctx.route(re.compile(r'^https?://'), _offline)
    pg = ctx.new_page()
    moved, elems, seen = [], 0, 0
    for p in pages:
        rel = T.rel(p).replace(os.sep, '/')
        now_t = left_by(p)
        was_t = read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now_t
        pg.set_content(doc(base_now, now_t))
        a = pg.evaluate(JS)
        pg.set_content(doc(base_was, was_t))
        b = pg.evaluate(JS)
        seen += 1
        elems += len(a)
        if a != b:
            diff = [x for x in zip(a, b) if x[0] != x[1]][:2]
            moved.append('%s: %d vs %d element(s)%s'
                         % (rel, len(a), len(b),
                            (' e.g. %s' % (diff,)) if diff else ''))
    ctx.close()
    try:
        _br.close()
    except Exception:
        pass
    ok(seen > 0, 'rendered %d affected page(s) both ways' % seen)
    # A ROUTE I ADDED IS NOT A MEASUREMENT. If the pattern were wrong
    # this would be back where it started and nothing would say so.
    ok(len(refused) > 0,
       '  and the browser REFUSED %d remote request(s) - Font Awesome and '
       'the CDN copy of Bootstrap - so both renders saw the same '
       'stylesheets, which is what this comparison depends on'
       % len(refused), refused[:3])
    ok(not moved,
       'and all %d element(s) carrying a radius compute EXACTLY as they '
       'did before the round' % elems, '\n'.join(moved[:8]))
    ok(elems > 1000,
       '  %d is the whole population on those pages, not a sample' % elems,
       elems)


# ==========================================================================
head('6. D-7: THE HOOK IS GONE, AND IT REALLY WAS DEAD')
# ==========================================================================
left_chip, rule_anywhere = [], []
for p in sorted(T.templates()):
    raw = left_by(p)
    rel = T.rel(p).replace(os.sep, '/')
    if CHIP in T.code_only_js(raw):
        left_chip.append(rel)
    if re.search(r'\.comment-author\s*\{', T.code_only(raw)):
        rule_anywhere.append(rel)
ok(not left_chip, 'the dead class is off every span', left_chip)
ok(not rule_anywhere,
   'and NOTHING styles .comment-author anywhere - which is what made '
   'removing it safe. If a rule ever comes back, this fails and the '
   'class has to come back with it', rule_anywhere)

tags = 0
for p in sorted(T.templates()):
    tags += len(re.findall(r'class="alv-tag"',
                           T.code_only_js(left_by(p))))
ok(tags >= N_CHIP,
   'the %d author chip(s) still wear base\'s .alv-tag - the round took '
   'the dead half, not the live one: %d bare .alv-tag span(s) in the '
   'corpus' % (N_CHIP, tags))


# ==========================================================================
head('7. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % SUFFIX in rounds
   and rounds.index("'%s'" % SUFFIX) > rounds.index("'.bak_isscentre'"),
   '  and after HM-4, which is the ordering as_left_by needs')
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that 6px is the right radius, or that all')
print('  %d of these should share one. What IS proved is that they' % N_RADIUS)
print('  now do, that nothing moved when they started to, and that')
print('  retuning them is one line instead of %d.' % N_RADIUS)
sys.exit(1 if failed else 0)
