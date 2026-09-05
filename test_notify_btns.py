"""test_notify_btns.py - the Edit / Notify Now row joins the standard.

    python test_notify_btns.py

Run from the repo root, after apply_notify_btns.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 2 RENDERS the row. The round's claim is that Notify Now stops
    being a SLAB and becomes a quiet button carrying warn INK - and "not a
    slab" is a computed background, not a class name. The CONTROL renders
    the same three from .bak_notify, where Notify must BE a slab and the
    badge must be button-shaped; without it, "the background is paper" would
    pass on a probe that found nothing.

  * IT ALSO CHECKS THE TWO BUTTONS ARE THE SAME SHAPE AND DIFFERENT INK.
    That is the whole design: they are peers, told apart by consequence, not
    by one of them shouting.

  * SECTION 3 guards the JS HOOKS. The class names survive with no
    appearance attached, purely so the script can find its elements - and
    the script's three lookups are asserted by name, because losing one
    would leave a button that renders correctly and does nothing.
"""
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
FD = os.path.join(T, 'fsr_details.html')
FBAK = FD + '.bak_notify'

PASS = FAIL = 0
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


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def nocomment(t):
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{#[^\n]*?#\}', '', t)
    return re.sub(r'/\*.*?\*/', '', t, flags=re.S)


for p in (BASE, FD):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the repo root' % p)
BS, F = read(BASE), read(FD)
if 'notify-urgent-btn status-btn' not in F:
    print('\n! not patched - run apply_notify_btns.py first.')
    sys.exit(1)
BC, FC = nocomment(BS), nocomment(F)

# ===========================================================================
head('1. three controls, none of them styled inline any more')
# ===========================================================================
check("CONTROL: the round's prose still names #ffc107", '#ffc107' in F)
check('CONTROL: .. and it is gone once stripped', '#ffc107' not in FC)

for el in ('notify-urgent-btn', 'notified-badge', 'comment-edit-btn'):
    check('%-20s carries no style attribute' % el,
          not re.search(r'class="[^"]*%s[^"]*"[^>]*style=' % el, FC))
check('the badgeStyle variable is gone', 'badgeStyle' not in FC)

check('Edit is base\'s inline button', 'comment-edit-btn status-btn' in FC)
check('Notify Now is too', 'notify-urgent-btn status-btn' in FC)
check('the badge is a PILL, not a button',
      FC.count('notified-badge alv-pill alv-pill-neutral') == 3,
      '%d of 3' % FC.count('notified-badge alv-pill alv-pill-neutral'))
check('  which is the template plus both script rebuilds',
      FC.count('alv-pill-neutral">Notified') == 3)

check('the bell is Font Awesome, not an emoji',
      'fas fa-bell' in FC and '\U0001f514' not in FC)

check('the warn tone is written in TOKENS',
      'var(--alv-warn)' in F and 'var(--alv-warn-soft)' in F)
check('  and is page-local, since base has one asker',
      '.status-btn-warn' not in FC and '.notify-urgent-btn.status-btn' in F)

# ===========================================================================
head('2. rendered: a quiet button with warn ink, not an amber slab')
# ===========================================================================
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('  SKIP  playwright not installed')
    sync_playwright = None

BOOT = None
for _c in (os.path.join(ROOT, 'test_fixture_bootstrap413.css'),
           '/tmp/bootstrap.min.css'):
    if os.path.exists(_c):
        BOOT = open(_c, encoding='utf-8').read()
        break
if BOOT is None:
    print('  !! test_fixture_bootstrap413.css missing - browser checks skipped')
    sync_playwright = None

if sync_playwright is not None:
    def css_of(s):
        return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', s, re.S))

    AFTER = ('<button class="comment-edit-btn status-btn" id="e">Edit</button>'
             '<button class="notify-urgent-btn status-btn" id="n">Notify Now</button>'
             '<span class="notified-badge alv-pill alv-pill-neutral" id="b">'
             'Notified 4 min ago</span>')
    BEFORE = ('<button class="comment-edit-btn" id="e">Edit</button>'
              '<button class="notify-urgent-btn" id="n" style="background-color:'
              '#ffc107;border:1px solid #ffc107;color:#212529;padding:4px 10px;'
              'border-radius:3px;font-size:12px;">Notify Now</button>'
              '<span class="notified-badge" id="b" style="background-color:'
              '#6c757d;color:white;padding:4px 10px;border-radius:3px;'
              'font-size:12px;">Notified 4 min ago</span>')

    FIX = ('<!doctype html><meta charset=utf-8><style>%s</style><style>%s</style>'
           '<style>%s</style><style>body{margin:0;padding:20px;background:#fff}'
           '#loud{font-size:33px;font-weight:800}</style>%s'
           '<div id="loud">c</div>')

    PROBE = """() => {
      const g = s => { const c = getComputedStyle(document.getElementById(s));
        const r = document.getElementById(s).getBoundingClientRect();
        return {bg: c.backgroundColor, fg: c.color, bd: c.borderTopColor,
                bw: c.borderTopWidth, rad: c.borderTopLeftRadius,
                h: Math.round(r.height)}; };
      return {e: g('e'), n: g('n'), b: g('b'),
              loud: getComputedStyle(document.getElementById('loud')).fontSize};
    }"""

    def render(br, bs, fs, markup):
        f = os.path.join(tempfile.gettempdir(), 'nbt.html')
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(FIX % (BOOT, css_of(bs), css_of(fs), markup))
        pg = br.new_page(viewport={'width': 800, 'height': 300})
        pg.goto('file://' + f)
        r = pg.evaluate(PROBE)
        pg.close()
        return r

    with sync_playwright() as p:
        br = p.chromium.launch()
        NOW = render(br, BS, F, AFTER)
        WAS = render(br, BS, read(FBAK), BEFORE) if os.path.exists(FBAK) else None
        br.close()

    check('CONTROL: the probe reads a deliberately sized element',
          NOW['loud'] == '33px', NOW['loud'])

    # THE CLAIM.
    check('Notify Now is NOT a filled slab any more',
          NOW['n']['bg'] in ('rgb(255, 255, 255)', 'rgba(0, 0, 0, 0)'),
          NOW['n']['bg'])
    check('  it carries warn INK instead',
          NOW['n']['fg'] != NOW['e']['fg'],
          'notify %s vs edit %s' % (NOW['n']['fg'], NOW['e']['fg']))
    check('  and a tinted border, not the accent one',
          NOW['n']['bd'] != NOW['e']['bd'],
          '%s vs %s' % (NOW['n']['bd'], NOW['e']['bd']))
    check('the two buttons are the SAME SHAPE - peers, not a loud and a quiet',
          NOW['n']['h'] == NOW['e']['h']
          and NOW['n']['rad'] == NOW['e']['rad']
          and NOW['n']['bw'] == NOW['e']['bw'],
          '%dpx / %s / %s vs %dpx / %s / %s'
          % (NOW['e']['h'], NOW['e']['rad'], NOW['e']['bw'],
             NOW['n']['h'], NOW['n']['rad'], NOW['n']['bw']))
    check('the badge is a tinted pill, not a grey block',
          NOW['b']['bg'] != 'rgb(108, 117, 125)'
          and NOW['b']['fg'] != 'rgb(255, 255, 255)',
          '%s on %s' % (NOW['b']['fg'], NOW['b']['bg']))
    check('  and it is rounder than the buttons - a state, not an action',
          NOW['b']['rad'] != NOW['e']['rad'],
          '%s vs %s' % (NOW['b']['rad'], NOW['e']['rad']))

    if WAS:
        check('CONTROL: before, Notify Now WAS an amber slab',
              WAS['n']['bg'] == 'rgb(255, 193, 7)', WAS['n']['bg'])
        check('CONTROL: .. and the badge WAS a grey block',
              WAS['b']['bg'] == 'rgb(108, 117, 125)', WAS['b']['bg'])
        check('CONTROL: .. and the two buttons did NOT match',
              WAS['n']['bg'] != WAS['e']['bg'],
              '%s vs %s' % (WAS['n']['bg'], WAS['e']['bg']))

    # The amber must be BASE's warn, not the Bootstrap one it replaced.
    _warn = re.search(r'--alv-warn:\s*(#[0-9a-fA-F]{6})', BS)
    if _warn:
        def hexof(rgb):
            m = re.findall(r'\d+', rgb)
            return '#%02x%02x%02x' % tuple(int(x) for x in m[:3])
        check('  the ink is base\'s --alv-warn, not Bootstrap\'s #ffc107',
              hexof(NOW['n']['fg']).lower() == _warn.group(1).lower(),
              '%s vs %s' % (hexof(NOW['n']['fg']), _warn.group(1)))

# ===========================================================================
head('3. the class names survive as JS hooks')
# ===========================================================================
check('the script still binds .notify-urgent-btn',
      "querySelectorAll('.notify-urgent-btn')" in FC)
check('  still finds the cell to replace',
      "closest('.notify-urgent-cell')" in FC)
check('  and still removes Edit by data-comment-id',
      ".comment-edit-btn[data-comment-id=" in FC)
check('the hook classes carry no appearance of their own',
      not re.search(r'(?m)^\.comment-edit-btn\s*\{', FC)
      and not re.search(r'(?m)^\.notified-badge\s*\{', FC))
check('  except the one TONE, which is the point',
      '.notify-urgent-btn.status-btn {' in FC)

check('base is untouched by this round',
      '.status-btn {' in BC and '.alv-pill-neutral' in BC)

# ONE check, not one per comment. Twenty identical PASS lines tell a reader
# nothing they could not get from a single line naming the offender.
_bad = [m.group(0)[:60] for m in re.finditer(r'/\*.*?\*/', F, re.S)
        if re.search(r'</?(?:script|style)\b', m.group(0))]
check('no CSS comment spells a script or style tag (%d scanned)'
      % len(re.findall(r'/\*.*?\*/', F, re.S)), not _bad,
      _bad[0] if _bad else '')
for blk in re.findall(r'<style[^>]*>(.*?)</style>', F, re.S):
    check('braces balance in a style block', blk.count('{') == blk.count('}'))

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for x in FAILED:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
