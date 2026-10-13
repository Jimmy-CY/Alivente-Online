# -*- coding: utf-8 -*-
"""test_surface_border.py - F2b, A BORDER IS NAMED BY THE BORDER TOKEN

F2a split every use of --alv-surface-deep into buckets and fixed the
backgrounds. It left the borders and said why: the change is below what
an eye can read, so it is a decision about naming rather than about
looking. Demetri took it on 13 Oct.

    --alv-surface-deep   #e9ecef    the far stop of the panel wash
    --alv-line           #e3e8ea    the border token
    15 RGB units apart in total, 6 on the widest channel

SECTION 5 IS THE POINT. A round whose whole claim is "nothing moves"
has to render both and show it, and show it over the WHOLE computed
style rather than the one property it expects to change - E15 learned
that the hard way, three widenings and three reversals. Every element
that carries a border is dumped before and after, and the only
difference permitted anywhere is a border colour going from the one
token to the other.

SECTION 6 IS WHY THE SUITE IS NOT RELEASED. I expected F2b to free
test_surface_deep and said so when the decision was put. It does not,
and the round found out by trying rather than by arguing. The numbers
are there so the next person does not have to rediscover them.

WHAT IS NOT PROVED HERE: that --alv-line is the right value for a
border, only that it is the right NAME. If the house ever retunes it,
these 78 follow - which is the whole of what this round buys.
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
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

SUFFIX = '.bak_surfborder'
ME = 'test_surface_border.py'
PATCHER = 'apply_surface_border.py'
PS1 = 'Push-PendingChanges.ps1'
SD = 'test_surface_deep.py'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

OLD, NEW = 'var(--alv-surface-deep)', 'var(--alv-line)'
SD_HEX, LINE_HEX = '#e9ecef', '#e3e8ea'
BORDER = re.compile(r'border[\w-]*\s*:\s*[^;}]*' + re.escape(OLD) + r'[^;}]*;')
NEWB = re.compile(r'border[\w-]*\s*:\s*[^;}]*' + re.escape(NEW) + r'[^;}]*;')
FALLBACK = 'var(--alv-disabled-bg, ' + OLD + ')'
N_CONVERT, N_PAGES, N_FALLBACK, N_OTHER = 78, 43, 3, 96

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
            for line in str(detail).split('\n')[:6]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    """The page as F2b found it - and SCOPED, because most pages have no
    backup of this round and never needed one."""
    b = p + SUFFIX
    return read(b) if os.path.isfile(b) else read(p)


def touched():
    return [p for p in alv_tree.templates() if os.path.isfile(p + SUFFIX)]


def srgb(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def lum(h):
    h = h.lstrip('#')
    r, g, b = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return 0.2126 * srgb(r) + 0.7152 * srgb(g) + 0.0722 * srgb(b)


def cr(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


print('=' * 74)
print('%s - F2b, A BORDER IS NAMED BY THE BORDER TOKEN' % ME)
print('=' * 74)

# ==========================================================================
head('1. REGISTERED')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(SUFFIX in ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in alv_tree.CONVERTED, '%s is on alv_tree.CONVERTED' % ME)

# ==========================================================================
head('2. SEVENTY-EIGHT BORDERS, FORTY-THREE PAGES, AND NOT base')
# ==========================================================================
pages = touched()
ok(len(pages) == N_PAGES, '%d page(s) were converted' % N_PAGES, len(pages))
before = sum(len([m for m in BORDER.finditer(was(p))
                  if FALLBACK not in m.group(0)]) for p in pages)
ok(before == N_CONVERT,
   '  carrying %d plain border declaration(s) on the panel-wash token'
   % N_CONVERT, before)
left = []
for p in alv_tree.templates():
    for m in BORDER.finditer(read(p)):
        if FALLBACK not in m.group(0):
            left.append('%s: %s' % (alv_tree.rel(p),
                                    ' '.join(m.group(0).split())[:50]))
ok(not left, 'not one plain border draws on it now', left[:4])
gained = sum(len(NEWB.findall(read(p))) - len(NEWB.findall(was(p)))
             for p in pages)
ok(gained == N_CONVERT,
   '  and exactly %d gained the border token' % N_CONVERT, gained)

b = alv_tree.join('base.html')
ok(not os.path.isfile(b + SUFFIX), 'base.html was NOT touched')
ok(len(BORDER.findall(read(b))) == N_FALLBACK,
   '  its %d border uses are all the var() fallback' % N_FALLBACK,
   len(BORDER.findall(read(b))))

# ==========================================================================
head('3. THE SHAPE IT REFUSES - WHERE THE EDGE IS MEANT TO BE THE FILL')
# ==========================================================================
fb = []
for p in alv_tree.templates():
    for m in BORDER.finditer(read(p)):
        if FALLBACK in m.group(0):
            fb.append(alv_tree.rel(p))
ok(len(fb) == N_FALLBACK,
   '%d var() fallback(s) survive, all in base' % N_FALLBACK, fb)
ok(set(fb) == {'base.html'}, '  and nowhere else', sorted(set(fb)))
src = read(b)
for sel in ('.btn.action-secondary[disabled]',
            '.btn.action-primary[aria-disabled="true"]',
            '.btn.action-danger[aria-disabled="true"]'):
    i = src.find(sel)
    blk = src[i:i + 400] if i >= 0 else ''
    ok(blk.count(FALLBACK) == 2,
       '%-44s writes it for BOTH fill and edge' % sel, blk.count(FALLBACK))
print('        E-10 switched-off recipe: a disabled control is one flat')
print('        block. Converting the edge would give it a rim a different')
print('        colour from its fill - visible, and a different decision.')
ok('FALLBACK in d' in read(os.path.join(ROOT, PATCHER)),
   'the patcher refuses it BY SHAPE, not by page name')
print('        An exclusion list of page names would stop working the day')
print('        that recipe moved. The shape would not.')

# ==========================================================================
head('4. THE NON-BORDER USES ARE NOT THIS ROUND')
# ==========================================================================
other = 0
for p in alv_tree.templates():
    t = read(p)
    other += t.count(OLD) - sum(m.group(0).count(OLD)
                                for m in BORDER.finditer(t))
ok(other == N_OTHER,
   '%d non-border use(s) of the panel-wash token are untouched' % N_OTHER,
   other)
print('        Backgrounds, gradient stops and custom properties. F2a')
print('        settled those; a round that re-opened them would be doing')
print('        F2a job again, badly.')

# ==========================================================================
head('5. RENDERED - THE WHOLE COMPUTED STYLE, AND ONE PROPERTY MOVES')
# ==========================================================================
print('  declared, before any browser:')
for ground, name in (('#ffffff', 'paper  '), ('#f8f9fa', 'surface')):
    print('     against %s   %s %.3f:1  ->  %s %.3f:1   (delta %.3f)'
          % (name, SD_HEX, cr(SD_HEX, ground), LINE_HEX,
             cr(LINE_HEX, ground), abs(cr(SD_HEX, ground)
                                       - cr(LINE_HEX, ground))))
d = sum(abs(int(SD_HEX.lstrip('#')[i:i + 2], 16)
            - int(LINE_HEX.lstrip('#')[i:i + 2], 16)) for i in (0, 2, 4))
ok(d <= 20, 'the two tokens are %d RGB units apart in total' % d, d)

try:
    import playwright  # noqa: F401
    HAVE = True
except Exception:
    HAVE = False

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)), flags=re.S)
            for m in STYLE.finditer(t)]


def one_branch(t):
    while True:
        st = []
        for m in TAG.finditer(t):
            k = m.group(1)
            if k == 'if':
                st.append([m.start(), m.end(), None])
            elif k in ('elif', 'else'):
                if st and st[-1][2] is None:
                    st[-1][2] = m.start()
            elif k == 'endif':
                if not st:
                    return t
                s_, fe, cut = st.pop()
                if cut is not None:
                    t = t[:s_] + t[fe:cut] + t[m.end():]
                    break
        else:
            return t


def body_of(t):
    t = one_branch(t)
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    bd = m.group(1) if m else t
    bd = re.sub(r'<(script|style)\b.*?</\1>', '', bd, flags=re.S | re.I)
    for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
        bd = re.sub(rx, '', bd, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', '42', bd, flags=re.S)


boot = read(BOOT) if os.path.isfile(BOOT) else ''
bcss = '\n'.join(styles_of(read(alv_tree.join('base.html'))))

# EVERY PROPERTY, SORTED. Not a list I chose - E15 found out four times
# over that every list is a subset of something, and that the browser's
# own enumeration order is not stable when a rule changes.
DUMP = """() => {
  const out = [];
  document.querySelectorAll('*').forEach((e, i) => {
    const s = getComputedStyle(e);
    if (s.borderTopWidth === '0px' && s.borderBottomWidth === '0px' &&
        s.borderLeftWidth === '0px' && s.borderRightWidth === '0px') return;
    const props = [];
    for (const k of s) { props.push(k + '=' + s.getPropertyValue(k)); }
    props.sort();
    out.push(i + '\\u0000' + props.join('\\n'));
  });
  return out;
}"""

if not HAVE:
    skip('section 5', 'playwright is not installed')
else:
    from playwright.sync_api import sync_playwright
    # The six pages carrying the most conversions - enough shapes to be
    # worth rendering, few enough to run on every push.
    rank = sorted(pages, key=lambda p: -len(
        [m for m in BORDER.finditer(was(p)) if FALLBACK not in m.group(0)]))
    sample = rank[:6]
    moved, seen, elements = [], 0, 0
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        for p in sample:
            rel = alv_tree.rel(p)
            shots = {}
            for tag, text in (('before', was(p)), ('after', read(p))):
                fx = os.path.join(SCRATCH, '%s_%s.html'
                                  % (rel.replace('/', '_'), tag))
                with open(fx, 'w', encoding='utf-8') as fh:
                    fh.write('<!doctype html><html><head>'
                             '<meta charset="utf-8">'
                             '<style>%s</style><style>%s</style>%s</head>'
                             '<body><div class="main-content">%s</div>'
                             '</body></html>'
                             % (boot, bcss,
                                ''.join('<style>%s</style>' % c
                                        for c in styles_of(text)),
                                body_of(text)))
                ctx = br.new_context(viewport={'width': 1280, 'height': 900})
                # HERMETIC - a gate that passes only when a CDN is up is
                # not a gate.
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                _goto(pg, fx)
                shots[tag] = pg.evaluate(DUMP)
                pg.close()
                ctx.close()
            elements += len(shots['after'])
            diffs = []
            for a, bq in zip(shots['before'], shots['after']):
                if a == bq:
                    continue
                da = dict(l.split('=', 1) for l in a.split('\u0000')[1]
                          .split('\n') if '=' in l)
                db = dict(l.split('=', 1) for l in bq.split('\u0000')[1]
                          .split('\n') if '=' in l)
                for k in sorted(set(da) | set(db)):
                    if da.get(k) != db.get(k):
                        diffs.append((k, da.get(k), db.get(k)))
            seen += len(diffs)
            bad = [d for d in diffs
                   if 'border' not in d[0] or 'color' not in d[0]
                   or 'rgb(233, 236, 239)' not in str(d[1])
                   or 'rgb(227, 232, 234)' not in str(d[2])]
            ok(not bad,
               '%-40s %d element(s) with a border; the only change is a '
               'border COLOUR, %s -> %s'
               % (rel[:40], len(shots['after']), SD_HEX, LINE_HEX),
               '; '.join('%s %s -> %s' % x for x in bad[:3]))
            if bad:
                moved.append(rel)
        br.close()
    ok(not moved, 'not one of the %d pages rendered moved anything else'
       % len(sample), moved)
    ok(seen > 0,
       'CONTROL: and the probe DID see the border colours change - %d '
       'computed differences across %d element(s)' % (seen, elements),
       '%d / %d' % (seen, elements))
    print('        Without that control, "nothing else moved" is a')
    print('        sentence a probe comparing nothing prints just as')
    print('        happily.')

# ==========================================================================
head('6. WHY %s IS NOT RELEASED' % SD)
# ==========================================================================
ok(SD in alv_tree.WAITING, '%s is still on WAITING' % SD)
why = alv_tree.WAITING.get(SD, '')
ok('F2b took the 78 border uses' in why,
   '  with a reason that has been RE-MEASURED, not carried forward')
ok('wait on F2b' not in why,
   '  the stale half is gone - the decision was taken on 13 Oct')
for n in ('93 to 56', 'LEFT_CUSTOM 3 to 1', 'second-root'):
    ok(n in why, '  and it names %r, so the next round starts measured' % n)
ok('CRS' not in why,
   '  and it says second root, NOT CRS - X11 asserts no held reason blames '
   'CRS, because ten CRS rounds landed and a register pointing there sends '
   'the next reader to the wrong module')
print('        My first wording named CRS, truthfully, and X11 check fired')
print('        on it. The check is right; my words were the cheaper thing')
print('        to change. A round that rewrites someone else control to')
print('        accommodate its own prose has removed a control.')
ok(not os.path.isfile(os.path.join(ROOT, SD) + SUFFIX),
   '  CONTROL: and F2b took no backup of the suite - it rewrote a reason '
   'in alv_tree, not the suite')
print('        I expected F2b to free it and said so when the decision')
print('        was put. Widened, its reader hands it CRS backups F2a')
print('        never had a claim on - 6 phantom backgrounds and 15')
print('        phantom borders - and BL-2 scoped reader fixes those but')
print('        moves both its pins. The round found that out by trying.')
print('        FOURTH occurrence of the as_left_by lesson.')

# ==========================================================================
head('7. ON THE GATE')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok('no page draws a plain border on the panel-wash token' in ps,
   '  and a sentinel refuses one coming back')
blk = ps[ps.index('$sentinels = @('):]
blk = blk[:blk.index('\n)\n')]
rows = [l.rstrip() for l in blk.split('\n')
        if l.strip() and not l.strip().startswith('#')]
ok(not rows[-1].endswith(','),
   '  and $sentinels does not end in a comma', rows[-1][-40:])

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
if skipped:
    print('')
    print('  %d check(s) DID NOT RUN. That is not the same as passing.'
          % skipped)
print('')
print('  NOT PROVED HERE: that --alv-line is the right VALUE for a border,')
print('  only that it is the right NAME. Nor that the six pages rendered')
print('  stand for all 43 - they are the six carrying the most')
print('  conversions, which is a sample and says so.')
sys.exit(1 if failed else 0)
