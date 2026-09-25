# -*- coding: utf-8 -*-
"""test_purple.py - Section E round E2, 25 Sep 2026.

Judges the round that took the imported purple palette out of the system.

WHAT THIS SUITE IS FOR. E2's survey said, in bold, that contrast was not
the argument for the round - because it measured the PURPLES, which all
pass, and never measured #667eea, the blue half of the same palette and
the most-used member of it, which fails at 3.66 both as ink and as fill.
D9 had written that number into base.html three rounds earlier.

So this suite does not ask the source what colour anything is. It RENDERS
both sides and measures. Section 1 checks the text; section 2 is the one
that decides.
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
    print('     checks below it never ran.')


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
except Exception as e:           # a crash says less than a failure
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_purple'
ME = 'test_purple.py'
PATCHER = 'apply_purple.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')

FILES = {
    'celebration_calendar.html': 6, 'celebration_dashboard.html': 6,
    'celebration_management.html': 7, 'create_meal_plan.html': 5,
    'customer_invoice_form.html': 4, 'home.html': 4,
    'meal_plan_calendar.html': 18, 'meal_plans.html': 3,
    'measurement_units_management.html': 3, 'preview_imported_recipe.html': 2,
    'recipe_management.html': 5, 'unit_conversions_management.html': 4,
    'view_meal_plan.html': 8, 'view_recipe.html': 4,
    'finance/financial_indicators.html': 4,
}
TOTAL = sum(FILES.values())          # 83

# The two that stay, each with the reason it stays. An exception nobody
# checks is an escape hatch, so both are asserted PRESENT below.
LEAVE = {
    ('base.html', '#667eea'):
        "inside D9's comment explaining the avatar fix - a mention is "
        'not a use (lesson 34)',
    ('finance/financial_indicators.html', '#6f42c1'):
        'the valueIncrease metric colour, one of seven that tell the '
        'indicators apart; the accent is already yieldPct',
}

LITERAL = re.compile(
    r'#(?:667eea|764ba2|6f42c1|5a32a3|5e37a6|563098|7c3aed|7b1fa2|6a1b9a'
    r'|f3e5f5|f3eefb|3d2466)\b'
    r'|rgba\(\s*124,\s*58,\s*237[^)]*\)', re.I)
CSS_COMMENT = re.compile(r'/\*.*?\*/', re.S)
HTML_COMMENT = re.compile(r'<!--.*?-->', re.S)

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


def uncommented(t):
    """The text with comments removed. A block explaining what it
    replaced always contains what it replaced (lesson 34)."""
    return HTML_COMMENT.sub('', CSS_COMMENT.sub('', t))


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I)]


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    b = re.sub(r'<!--.*?-->', '', b, flags=re.S)
    b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
    b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)


# --- COLOUR ---------------------------------------------------------------
# Copied, not shared, from test_personal_heads.py - which took it from
# test_contrast.py, which took it from test_horizon_cards.py. THREE ROUNDS
# HAVE FIXED A DIFFERENT LIE IN THIS HELPER: a gradient reading as
# rgba(0,0,0,0) and scoring 21.00 (lesson 37), an unparseable colour
# scoring as black (lesson 41), and a transparent background scoring as
# black (lesson 44). A fourth copy is a fourth place for the next lie to
# live, and folding the three into one module is worth its own round.
def parse_rgb(s):
    s = s.strip().lower()
    m = re.match(r'^#([0-9a-f]{3}|[0-9a-f]{6})$', s)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = ''.join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    if s in ('white', 'black'):
        return (255, 255, 255) if s == 'white' else (0, 0, 0)
    m = re.match(r'^rgba?\(([^)]*)\)$', s)
    if m:
        v = [float(x) for x in re.findall(r'-?[\d.]+', m.group(1))[:3]]
        return tuple(v) if len(v) == 3 else None
    m = re.match(r'^color\(srgb ([^)]*)\)$', s)
    if m:
        v = [float(x) for x in re.findall(r'-?[\d.]+', m.group(1))[:3]]
        return tuple(x * 255 for x in v) if len(v) == 3 else None
    return None


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def contrast(a, b):
    ra, rb = parse_rgb(a), parse_rgb(b)
    if ra is None or rb is None:
        raise ValueError('unreadable colour: %r / %r' % (a, b))
    f = lambda v: (0.2126 * _lin(v[0]) + 0.7152 * _lin(v[1])
                   + 0.0722 * _lin(v[2]))
    x, y = f(ra) + 0.05, f(rb) + 0.05
    return max(x, y) / min(x, y)


PAPER = (255, 255, 255)


def over_paper(s):
    """A colour composited over the page behind it. An unpainted element
    is not a black one: backgroundColor reads rgba(0, 0, 0, 0)."""
    m = re.match(r'^rgba\(([^)]*)\)$', s.strip().lower())
    if not m:
        return s
    v = [float(x) for x in re.findall(r'-?[\d.]+', m.group(1))]
    if len(v) < 4 or v[3] >= 1:
        return s
    a = v[3]
    return 'rgb(%d, %d, %d)' % tuple(
        round(v[i] * a + PAPER[i] * (1 - a)) for i in range(3))


def worst_contrast(bg, ink):
    """Against the WORST stop of the paint. A gradient has no
    backgroundColor - it reads rgba(0,0,0,0) and would score 21."""
    stops = re.findall(r'rgba?\([^)]*\)|color\(srgb [^)]*\)|#[0-9a-fA-F]{6}',
                       bg)
    if not stops:
        return contrast(over_paper(bg), ink)
    return min(contrast(over_paper(s), ink) for s in stops)


def rgb_of(s):
    try:
        v = parse_rgb(over_paper(s))
    except Exception:
        return None
    return tuple(int(round(x)) for x in v) if v else None


OLD_PALETTE = {
    (102, 126, 234): '#667eea', (118, 75, 162): '#764ba2',
    (111, 66, 193): '#6f42c1', (124, 58, 237): '#7c3aed',
    (90, 50, 163): '#5a32a3', (94, 55, 166): '#5e37a6',
    (86, 48, 152): '#563098', (123, 31, 162): '#7b1fa2',
    (106, 27, 154): '#6a1b9a', (61, 36, 102): '#3d2466',
    (240, 147, 251): '#f093fb',
}


# ==========================================================================
head('1. THE SOURCE - 83 SITES GONE, 2 NAMED ONES KEPT')
# ==========================================================================
ok(as_left_by is not None, 'alv_rounds imported')
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
ok(ROUNDS and ROUNDS[-1] == SUFFIX,
   '%s is the LAST round in ROUNDS' % SUFFIX, ROUNDS[-3:] if ROUNDS else '')

left, missing_bak = [], []
for name, want in sorted(FILES.items()):
    p = os.path.join(T, name)
    if not os.path.isfile(p + SUFFIX):
        missing_bak.append(name)
    cur = uncommented(now(p))
    keep = [lit for (f, lit) in LEAVE if f == name]
    found = [m.group(0).lower() for m in LITERAL.finditer(cur)]
    stray = [x for x in found if x not in [k.lower() for k in keep]]
    if stray:
        left.append('%s: %s' % (name, ', '.join(sorted(set(stray))[:4])))

ok(not missing_bak,
   'every changed file has its %s backup - the backups ARE the delivery '
   '(lesson 32)' % SUFFIX, '\n'.join(missing_bak))
ok(not left, 'no template still paints with the imported palette',
   '\n'.join(left))

was_counts = {}
for name, want in sorted(FILES.items()):
    p = os.path.join(T, name)
    n = len(LITERAL.findall(uncommented(was(p))))
    was_counts[name] = n
grad_was = sum(len(re.findall(
    r'linear-gradient\(135deg,\s*#667eea\s*0%,\s*#764ba2\s*100%\)',
    uncommented(was(os.path.join(T, n))), re.I)) for n in FILES)
ok(grad_was == 13,
   'the round found 13 copies of the one hero gradient, as surveyed',
   'found %d' % grad_was)

for (f, lit), why in sorted(LEAVE.items()):
    p = os.path.join(T, f)
    body = now(p) if f != 'base.html' else now(BASE)
    ok(lit.lower() in body.lower(),
       'LEAVE kept: %s still has %s' % (f, lit))
    print('        %s' % why)

b_now, b_was = now(BASE), was(BASE)
ok(not os.path.isfile(BASE + SUFFIX),
   'base.html was NOT edited by this round - its only #667eea is prose')
ok('--alv-series-6' in b_now and '#4a3aa7' in b_now,
   "D5's series token --alv-series-6 is untouched")
ok('--alv-tag-plum-ink' in b_now,
   "the house's own plum tag component is untouched")

for tok in ('--alv-accent:', '--alv-accent-ink:', '--alv-accent-soft:',
            '--alv-on-accent:'):
    ok(tok in b_now, 'base defines %s, so the round wrote no dangling var'
       % tok.rstrip(':'))

pv = now(os.path.join(T, 'preview_imported_recipe.html'))
ok('{% if mode' not in pv.split('.preview-header')[1][:400]
   if '.preview-header' in pv else False,
   '.preview-header no longer paints itself by mode')
ok('background: var(--alv-accent);' in pv,
   '  and it takes the house accent, like every other header')

# ==========================================================================
head('2. RENDERED - WHAT THE PALETTE ACTUALLY MEASURED, BEFORE AND AFTER')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'
LOOK = r"""() => Array.from(document.querySelectorAll('*'))
  .map(e => {
    const s = getComputedStyle(e);
    const txt = Array.from(e.childNodes)
      .filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
    return {ink: s.color, bg: s.backgroundImage !== 'none'
                              ? s.backgroundImage : s.backgroundColor,
            size: parseFloat(s.fontSize) || 0, txt: txt.slice(0, 26)};
  })"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('section 2', 'playwright or %s missing' % BOOT)
else:
    boot = read(BOOT)
    n = [0]

    def look(br, base_css, page_css, markup):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_pu_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write('<!doctype html><html><head><meta charset="utf-8">'
                    '<title>p</title><style>%s</style><style>%s</style>%s'
                    '</head><body class="has-sidebar"><div class="main-content'
                    ' with-sidebar">%s</div></body></html>'
                    % (boot, base_css,
                       ''.join('<style>%s</style>' % c for c in page_css),
                       markup))
        ctx = br.new_context(viewport={'width': 1280, 'height': 900})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        r = pg.evaluate(LOOK)
        ctx.close()
        return r

    def judge(rows, palette_only):
        """Every element drawing TEXT on a paint this round is about."""
        out, unreadable = [], []
        for e in rows:
            if not e['txt'] or not e['ink']:
                continue
            inks, bgs = rgb_of(e['ink']), rgb_of(e['bg'])
            touched = (inks in palette_only) or (bgs in palette_only)
            if not touched:
                continue
            try:
                c = worst_contrast(e['bg'], e['ink'])
            except ValueError as err:
                unreadable.append(str(err))
                continue
            bar = 3.0 if e['size'] >= 24 else 4.5
            out.append((c, bar, e['txt']))
        return out, unreadable

    NEW_PALETTE = {(14, 124, 139), (10, 94, 106), (228, 243, 245)}
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        B_NOW = '\n'.join(styles_of(now(BASE)))
        B_WAS = '\n'.join(styles_of(was(BASE)))
        bad_before, bad_after, unread = [], [], []
        seen_before = seen_after = 0
        for name in sorted(FILES):
            p = os.path.join(T, name)
            a = look(br, B_NOW, styles_of(now(p)), body_markup(now(p)))
            b = look(br, B_WAS, styles_of(was(p)), body_markup(was(p)))
            rb, u1 = judge(b, set(OLD_PALETTE))
            ra, u2 = judge(a, NEW_PALETTE)
            unread += u1 + u2
            seen_before += len(rb)
            seen_after += len(ra)
            for c, bar, txt in rb:
                if c < bar:
                    bad_before.append('%s %r %.2f' % (name, txt, c))
            for c, bar, txt in ra:
                if c < bar:
                    bad_after.append('%s %r %.2f' % (name, txt, c))
        br.close()

    ok(not unread, 'every colour measured was one the parser understands '
       '(lesson 41 - a helper that cannot read a colour must raise)',
       '\n'.join(unread[:5]))
    print('')
    print('      BEFORE  %d element(s) drew text on the imported palette; '
          '%d failed' % (seen_before, len(bad_before)))
    for lineitem in bad_before[:6]:
        print('         %s' % lineitem)
    print('      AFTER   %d element(s) draw text on the house palette;  '
          '%d fail' % (seen_after, len(bad_after)))
    for lineitem in bad_after[:6]:
        print('         %s' % lineitem)
    print('')
    ok(seen_before > 0,
       'the before-render actually found the old palette - a measurement '
       'of nothing passes for free')
    ok(seen_after > 0, 'the after-render actually found the house palette')
    ok(len(bad_before) > 0,
       'the round had something to fix: %d rendered failure(s) before it'
       % len(bad_before))
    ok(not bad_after, 'NOTHING drawn on the house palette fails its bar',
       '\n'.join(bad_after))

# ==========================================================================
head('3. THE LATER EDIT - E1 SAID FIFTEEN WHERE IT MEASURED ELEVEN')
# ==========================================================================
for name in ('test_modal_heads.py', 'apply_personal_heads.py'):
    p = os.path.join(ROOT, name)
    if not os.path.isfile(p):
        skip(name, 'not on disk')
        continue
    t = read(p)
    ok(os.path.isfile(p + SUFFIX),
       '%s has its %s backup' % (name, SUFFIX))
    if name == 'test_modal_heads.py':
        ok('eleven of which were' in t,
           '%s now says eleven' % name)
        ok('fifteen of which were' not in t,
           '  and no longer says fifteen')
    else:
        ok('eleven contrast failures' in t, '%s now says eleven' % name)
        ok('fifteen contrast failures' not in t,
           '  and no longer says fifteen')
        ok('RENDERED it is' in t,
           "  the patcher's own 15-vs-11 explanation is left intact - it "
           'was right all along')

av = os.path.join(ROOT, 'test_avatar.py')
if os.path.isfile(av):
    t = read(av)
    ok(os.path.isfile(av + SUFFIX), 'test_avatar.py has its backup')
    ok('ok(others == 0,' in t,
       "D9's deferral to 2.K is spent - test_avatar now requires that NO "
       'purple rule remains')
    ok('others >= 40' not in t, '  and no longer requires that forty do')

fh = os.path.join(ROOT, 'test_finance_headings.py')
if os.path.isfile(fh):
    t = read(fh)
    ok(os.path.isfile(fh + SUFFIX),
       'test_finance_headings.py has its backup')
    ok('_EXPECT_BANNERS' in t,
       'the gradient banners left over are NAMED, not counted by a floor')
    ok('len(_left) >= 8' not in t, '  and the old floor of eight is gone')
    for name in ('household_member_management.html',
                 'unit_conversions_wizard.html'):
        ok(name in t, '  %s is named among them' % name)

# ==========================================================================
head('4. CONTROLS - checks that would catch a vacuous suite')
# ==========================================================================
ok(TOTAL == 83, 'the survey total is 83 sites', TOTAL)
ok(len(FILES) == 15, '15 files, and base.html is not one of them',
   len(FILES))
ok('base.html' not in FILES, '  base.html really is absent from the list')
ok(sum(was_counts.values()) >= TOTAL,
   'the backups between them hold at least 83 palette literals',
   sum(was_counts.values()))
ok(LITERAL.search('#667eea') is not None,
   'the literal pattern matches a colour it should')
ok(LITERAL.search('#0e7c8b') is None,
   '  and does not match the house accent')
ok(uncommented('a/* #667eea */b') == 'ab',
   'the comment stripper really removes a CSS comment')
ok(round(contrast('#667eea', '#ffffff'), 2) == 3.66,
   '#667eea measures 3.66 on white - the number D9 wrote into base',
   round(contrast('#667eea', '#ffffff'), 2))
ok(round(contrast('#0e7c8b', '#ffffff'), 2) == 4.91,
   'the house accent measures 4.91 on white',
   round(contrast('#0e7c8b', '#ffffff'), 2))
try:
    contrast('not-a-colour', '#fff')
    ok(False, 'contrast() raises on a colour it cannot read')
except ValueError:
    ok(True, 'contrast() raises on a colour it cannot read (lesson 41)')

p1 = os.path.join(ROOT, PS1)
if os.path.isfile(p1):
    ok(ME in read(p1), '%s is on the push gate' % ME)
else:
    skip(PS1, 'not on disk')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
