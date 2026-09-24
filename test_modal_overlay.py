# -*- coding: utf-8 -*-
"""test_modal_overlay.py - Section D, round D6: the last six pop-up
headers on the property side, and base owns the overlay two of them
sit in.

    python test_modal_overlay.py

Run from the repo root, after apply_modal_overlay.py.

  1. Base carries the overlay once, painted from the tokens.
  2. home and notifications handed their copies over - and the SCRIPT
     that builds the pop-up still builds it.
  3. RENDERED: the pop-up is what it was, and its header is now the same
     gradient as .alv-modal-head rather than a second teal.
  4. The phone: 100dvh, on both. notifications said 100vh.
  5. passport_management's three headers, rendered against the same
     bar test_modal_heads.py holds the other 51 to.
  6. notifications' override of the SHARED help modal is gone, and the
     help modal still looks exactly the same without it.
  7. Scope: nothing else on any of the four files moved. Registered in
     alv_rounds, and on the push gate.

Run it against the REVERTED tree and it must FAIL, not crash.
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
# knows, so two suites cannot collide however the gate orders them, and
# nothing is written into the working tree at all.
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

SUFFIX = '.bak_modal'
ME = 'test_modal_overlay.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')
HOME = os.path.join(T, 'home.html')
NOTIF = os.path.join(T, 'notifications.html')
PASS = os.path.join(T, 'passport_management.html')
SHELL = os.path.join(T, 'help_modal_shell.html')

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
    """The file as THIS round left it. See alv_rounds.py."""
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I)]


def css_of(t):
    return '\n'.join(styles_of(t))


def js_of(t):
    """The SCRIPTS only. Both pages build their pop-up as a string, so
    'modal-content' is a word in the markup here and a selector in the
    CSS above - counted in the wrong place, a cut that reached the script
    would be hidden by the rules it removed."""
    return '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', t, re.S))


B_NOW, B_WAS = now(BASE), was(BASE)
MARK = re.compile(r'/\* ===== ALV MODAL OVERLAY v1\b.*?'
                  r'/\* ===== /ALV MODAL OVERLAY v1 ===== \*/', re.S)

# ==========================================================================
head('1. BASE CARRIES THE OVERLAY, ONCE, AND FROM THE TOKENS')
# ==========================================================================
blocks = MARK.findall(B_NOW)
ok(len(blocks) == 1, 'base carries the ALV MODAL OVERLAY block, opened and '
   'closed, once', len(blocks))
ok(not MARK.search(B_WAS), '  CONTROL: it was not there before this round')
BLOCK = blocks[0] if blocks else ''
BODY = re.sub(r'/\*.*?\*/', '', BLOCK, flags=re.S)
for sel in ('.modal-overlay {', '.modal-overlay .modal-content {',
            '.modal-overlay .modal-header {', '.modal-overlay .modal-title {',
            '.modal-overlay .modal-close {',
            '.modal-overlay .modal-close:hover {',
            '.modal-overlay .modal-body {'):
    ok(sel in BODY, 'it defines %s' % sel[:-2])
ok(BODY.count('@media screen and (max-width: 768px)') == 1,
   'and one phone block, inside the component, where the next person '
   'will look for it')
# The literals it may keep are named in its own comment; any OTHER hex is
# a token that was not reached for.
hexes = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', BODY)))
ok(not hexes, 'no hex literal survives in the rules - the accent, the ink '
   'and the paper are tokens', hexes)
for tok in ('var(--alv-accent)', 'var(--alv-accent-ink)',
            'var(--alv-on-accent)', 'var(--alv-paper)'):
    ok(tok in BODY, '  it reads %s' % tok)
ok('100dvh' in BODY and '100vh' not in BODY,
   'the phone height is 100dvh and nowhere 100vh - an address bar counts '
   'inside 100vh and is not part of the screen')

# ==========================================================================
head('2. THE TWO PAGES HANDED THEIR COPIES OVER')
# ==========================================================================
# A rule, not a word: .modal-overlay followed by anything that is not a
# brace, up to the brace that opens its body. `.modal-overlay {` and
# `.modal-overlay .modal-content {` both count; the word in a script does
# not, and css_of is never shown a script anyway.
RULE = re.compile(r'\.modal-overlay\b[^{}]*?\{')
for label, path, n_was in (('home         ', HOME, 12),
                           ('notifications', NOTIF, 11)):
    a, b = now(path), was(path)
    left = RULE.findall(css_of(a))
    ok(not left, '%s keeps no .modal-overlay rule of its own' % label, left[:4])
    got = len(RULE.findall(css_of(b)))
    ok(got == n_was, '  CONTROL: it carried %d of them before (%d)'
       % (n_was, got))
    # A cut that reached the SCRIPT would leave a pop-up that renders
    # nothing at all, and quietly. The markup is a string, so it is
    # counted in the scripts - where removing the CSS cannot flatter it.
    for hook in ("'modal-overlay'", 'modal-content', 'modal-header',
                 'modal-title', 'modal-body'):
        ok(js_of(a).count(hook) == js_of(b).count(hook) >= 1,
           '  the script still writes %s, %d time(s)'
           % (hook, js_of(a).count(hook)),
           (js_of(b).count(hook), js_of(a).count(hook)))

# THE TWO COPIES WERE THE SAME COPY. Re-measured from the backups rather
# than taken from the round's own note - that is the fault this round is
# fixing on base's 3.9.
def decls(css):
    """{selector: the declarations, whitespace and order thrown away}."""
    out = {}
    # Comments first: the run before a selector reaches back to the last
    # brace, so home's "Lifted verbatim from notifications.html" ends up
    # INSIDE the selector and the same rule on the two pages stops
    # looking like the same rule.
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        sel = ' '.join(m.group(1).split())
        if '.modal-overlay' not in sel:
            continue
        key = sel + ('@' if '100vw' in m.group(2) or '100dvh' in m.group(2)
                     or '14px' in m.group(2) or 'font-size: 16px'
                     in m.group(2) else '')
        # ALL whitespace goes, not just the runs between words: the known
        # cosmetic difference between the two copies is the spaces inside
        # rgba(0, 0, 0, 0.5), and a diff that reports that as a difference
        # buries the one that matters.
        out[key] = sorted(''.join(d.split())
                          for d in m.group(2).split(';') if d.strip())
    return out


h_was, n_was_d = decls(css_of(was(HOME))), decls(css_of(was(NOTIF)))
if not ok(len(h_was) >= 11 and len(n_was_d) >= 11,
          'CONTROL: both backups can be read as rules (%d, %d)'
          % (len(h_was), len(n_was_d))):
    skip('the diff of the two copies', 'a backup could not be parsed')
else:
    shared = set(h_was) & set(n_was_d)
    same = [k for k in shared if h_was[k] == n_was_d[k]]
    diff = {k: (h_was[k], n_was_d[k]) for k in shared if h_was[k] != n_was_d[k]}
    ok(len(shared) == 11 and len(diff) == 1,
       'CONTROL: of the %d rules both pages wrote, %d were IDENTICAL '
       'declaration for declaration and ONE was not - they are one copy'
       % (len(shared), len(same)),
       '\n'.join('%s\n  home %s\n  notif %s' % (k, a, b)
                 for k, (a, b) in diff.items()))
    flat_h = ' '.join(sum(h_was.values(), []))
    flat_n = ' '.join(sum(n_was_d.values(), []))
    ok('100dvh' in flat_h and '100dvh' not in flat_n and '100vh' in flat_n,
       'CONTROL: and the one that MATTERED - home said 100dvh, '
       'notifications said 100vh',
       sorted(diff))
    # A headless browser has no address bar, so 100vh and 100dvh measure
    # the same here. This is said, not measured, on purpose: a check that
    # cannot tell them apart must not pretend it can.
    ok('100dvh' in BODY,
       '  base took home\'s. (NOT measurable here: a headless browser has '
       'no toolbar, so 100vh and 100dvh are equal on this machine)')

# ==========================================================================
head('3. RENDERED - THE POP-UP, AND WHAT ITS HEADER MATCHES NOW')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'

OVERLAY_MK = (
    '<div class="modal-overlay"><div class="modal-content">'
    '<div class="modal-header"><h3 class="modal-title">Arrears</h3>'
    '<button class="modal-close">&times;</button></div>'
    '<div class="modal-body">rows</div></div></div>')
HEAD_MK = (
    '<div class="modal" id="h"><div class="modal-dialog">'
    '<div class="modal-content"><div class="modal-header alv-modal-head">'
    '<h5 class="modal-title">Arrears</h5>'
    '<button class="close">&times;</button></div></div></div></div>')
OPEN_MODALS = ('<style>.modal{display:block!important;position:static'
               '!important;opacity:1!important}</style>')

LOOK = r"""() => {
  const pick = (el, props) => {
    if (!el) return null;
    const s = getComputedStyle(el);
    const o = {};
    props.forEach(p => o[p] = s[p]);
    return o;
  };
  const ov = document.querySelector('.modal-overlay');
  return {
    overlay: pick(ov, ['position', 'display', 'alignItems',
                       'justifyContent', 'zIndex', 'backgroundColor']),
    content: pick(ov && ov.querySelector('.modal-content'),
                  ['backgroundColor', 'borderTopLeftRadius', 'overflow',
                   'boxShadow', 'maxWidth', 'maxHeight', 'width', 'height']),
    header: pick(ov && ov.querySelector('.modal-header'),
                 ['backgroundColor', 'backgroundImage', 'color',
                  'paddingTop', 'paddingLeft', 'display', 'alignItems']),
    title: pick(ov && ov.querySelector('.modal-title'),
                ['fontSize', 'fontWeight', 'margin', 'color']),
    close: pick(ov && ov.querySelector('.modal-close'),
                ['color', 'width', 'height', 'fontSize',
                 'borderTopLeftRadius']),
    body: pick(ov && ov.querySelector('.modal-body'),
               ['paddingTop', 'maxHeight', 'overflowY']),
    houseHead: pick(document.querySelector('.alv-modal-head'),
                    ['backgroundImage', 'color'])
  };
}"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('sections 3 to 6', 'playwright or %s missing' % BOOT)
else:
    boot = read(BOOT)
    n = [0]

    def fixture(base_css, page_css, markup):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<title>m</title><style>%s</style><style>%s</style>%s%s'
                '</head><body class="has-sidebar"><div class="main-content '
                'with-sidebar">%s</div></body></html>'
                % (boot, base_css,
                   ''.join('<style>%s</style>' % c for c in page_css),
                   OPEN_MODALS, markup))

    def look(br, html, w=1280, js=LOOK):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_mo_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        ctx = br.new_context(viewport={'width': w, 'height': 900})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        r = pg.evaluate(js)
        ctx.close()
        return r

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        # --- the pop-up NOW: base's rules, no page CSS at all -----------
        cur = look(br, fixture(css_of(B_NOW), [], OVERLAY_MK + HEAD_MK))
        ok(cur['overlay'] is not None,
           'the pop-up draws from base alone - the pages need no CSS of '
           'their own for it')
        if cur['overlay']:
            o = cur['overlay']
            ok(o['position'] == 'fixed' and o['display'] == 'flex'
               and o['alignItems'] == 'center'
               and o['justifyContent'] == 'center' and o['zIndex'] == '1000',
               '  centred, fixed, above the page', o)
            ok(o['backgroundColor'] == 'rgba(0, 0, 0, 0.5)',
               '  and the backdrop is the half-black it always was',
               o['backgroundColor'])
        c = cur['content']
        # 90vw and 90vh arrive RESOLVED: 1152 and 810 at 1280 x 900. A
        # check written against the source text would pass on a rule that
        # never applied.
        ok(c and c['backgroundColor'] == 'rgb(255, 255, 255)'
           and c['borderTopLeftRadius'] == '12px'
           and c['overflow'] == 'hidden'
           and c['maxWidth'] == '1152px' and c['maxHeight'] == '810px',
           'the panel is paper, 12px, clipped, and 90% of the window '
           '(1152 x 810 of 1280 x 900)', c)
        hh = cur['header']
        ok(hh and hh['backgroundImage'].startswith('linear-gradient'),
           'THE HEADER IS A GRADIENT NOW, not a flat teal', hh)
        ok(hh and cur['houseHead']
           and hh['backgroundImage'] == cur['houseHead']['backgroundImage'],
           '  and it is the SAME gradient .alv-modal-head paints - one '
           'pop-up header in the house, not two',
           (hh or {}).get('backgroundImage', '')[:70] + ' vs '
           + (cur['houseHead'] or {}).get('backgroundImage', '')[:70])
        ok(hh and 'rgb(14, 124, 139)' in hh['backgroundImage'],
           '  and it starts at the accent', (hh or {}).get('backgroundImage'))
        ok(hh and hh['color'] == 'rgb(255, 255, 255)'
           and hh['paddingTop'] == '20px' and hh['paddingLeft'] == '20px',
           '  white, 20px all round', hh)
        t = cur['title']
        ok(t and t['fontSize'] == '20px' and t['fontWeight'] == '600'
           and t['margin'] == '0px' and t['color'] == 'rgb(255, 255, 255)',
           'the title is white 20px/600, no margin', t)
        cl = cur['close']
        ok(cl and cl['color'] == 'rgb(255, 255, 255)'
           and cl['width'] == '30px' and cl['height'] == '30px'
           and cl['fontSize'] == '24px'
           and cl['borderTopLeftRadius'] == '50%',
           'the close is a white 30px circle, exactly as it was. IT IS '
           'BELOW 44px, which 3.4 asks for on a phone - reported, not '
           'changed, because it is the tap-target question', cl)
        bd = cur['body']
        ok(bd and bd['paddingTop'] == '20px' and bd['maxHeight'] == '630px'
           and bd['overflowY'] == 'auto',
           'the body is 20px and scrolls past 70% of the window (630 of '
           '900)', bd)

        # --- AND IT IS WHAT IT WAS: the same pop-up, drawn from the ------
        # page's own backup CSS with NO overlay in base. Everything must
        # match except the header's paint, which is the decision.
        for label, path in (('home', HOME), ('notifications', NOTIF)):
            if not os.path.isfile(path + SUFFIX):
                skip('%s: before/after' % label, 'no %s backup' % SUFFIX)
                continue
            before = look(br, fixture(css_of(B_WAS),
                                      styles_of(was(path)), OVERLAY_MK))
            moved, kept = [], 0
            for part in ('overlay', 'content', 'title', 'close', 'body'):
                a, b = cur[part], before[part]
                if not (a and b):
                    moved.append('%s: missing' % part)
                    continue
                for k in b:
                    if a.get(k) != b[k]:
                        moved.append('%s.%s %s -> %s' % (part, k, b[k], a[k]))
                    else:
                        kept += 1
            ok(not moved and kept >= 25,
               '%-13s the pop-up is what it was - %d computed properties, '
               'all unchanged' % (label, kept), '\n'.join(moved[:8]))
            hb = before['header']
            ok(hb and hb['backgroundImage'] == 'none'
               and hb['backgroundColor'] == 'rgb(14, 124, 139)',
               '  CONTROL: its header WAS a flat teal, spelt by hand', hb)
            for k in ('color', 'paddingTop', 'paddingLeft', 'display',
                      'alignItems'):
                ok(hh[k] == hb[k],
                   '  and the header\'s %s did not move (%s)' % (k, hh[k]))

        # ==============================================================
        head('4. THE PHONE - ONE POP-UP, FULL SCREEN, ON BOTH')
        # ==============================================================
        PH = r"""() => {
          const c = document.querySelector('.modal-overlay .modal-content');
          const h = document.querySelector('.modal-overlay .modal-header');
          const t = document.querySelector('.modal-overlay .modal-title');
          const b = document.querySelector('.modal-overlay .modal-body');
          const cs = getComputedStyle(c);
          return {w: c.getBoundingClientRect().width,
                  h: c.getBoundingClientRect().height,
                  radius: cs.borderTopLeftRadius, display: cs.display,
                  dir: cs.flexDirection, box: cs.boxSizing,
                  hpad: getComputedStyle(h).paddingTop + ' '
                        + getComputedStyle(h).paddingLeft,
                  tsize: getComputedStyle(t).fontSize,
                  bpad: getComputedStyle(b).paddingTop,
                  bmax: getComputedStyle(b).maxHeight};
        }"""
        ph = look(br, fixture(css_of(B_NOW), [], OVERLAY_MK), 375, PH)
        ok(ph['w'] == 375 and ph['h'] == 900,
           'at 375 the panel fills the screen (%s x %s)' % (ph['w'], ph['h']))
        ok(ph['radius'] == '0px' and ph['display'] == 'flex'
           and ph['dir'] == 'column' and ph['box'] == 'border-box',
           '  square, a column, and the safe-area padding is inside it', ph)
        ok(ph['hpad'] == '14px 16px' and ph['tsize'] == '16px'
           and ph['bpad'] == '14px' and ph['bmax'] == 'none',
           '  the header tightens, the title drops to 16px, the body '
           'takes what is left', ph)
        # Both pages draw the same pop-up now BECAUSE neither draws it.
        for label, path in (('home', HOME), ('notifications', NOTIF)):
            same = look(br, fixture(css_of(B_NOW), styles_of(now(path)),
                                    OVERLAY_MK), 375, PH)
            ok(same == ph, '%-13s draws exactly base\'s pop-up at 375 - it '
               'has nothing of its own left to disagree with' % label,
               {k: (ph[k], same[k]) for k in ph if ph[k] != same[k]})

        # ==============================================================
        head('5. passport_management\'s THREE')
        # ==============================================================
        P_NOW, P_WAS = now(PASS), was(PASS)
        heads_now = re.findall(r'<div class="([^"]*\bmodal-header\b[^"]*)"',
                               P_NOW)
        heads_was = re.findall(r'<div class="([^"]*\bmodal-header\b[^"]*)"',
                               P_WAS)
        ok(len(heads_now) == 3, 'the page still has three pop-up headers',
           heads_now)
        ok(all('alv-modal-head' in h for h in heads_now),
           '  and every one of them wears the house class', heads_now)
        ok(sum('alv-modal-head--danger' in h for h in heads_now) == 1,
           '  exactly one is the danger variant', heads_now)
        ok('bg-danger' not in P_NOW and 'close text-white' not in P_NOW,
           '  Bootstrap\'s own red and its white close are gone')
        ok('bg-danger' in ' '.join(heads_was)
           and sum('alv-modal-head' in h for h in heads_was) == 0
           and len(heads_was) == 3,
           'CONTROL: before this round none of the three wore it, and the '
           'delete one wore Bootstrap\'s bg-danger', heads_was)
        DEL = re.search(r'id="deleteModal".*?</div>', P_NOW, re.S)
        ok(DEL is not None and 'alv-modal-head--danger' in DEL.group(0),
           '  and the danger one is the DELETE modal, not another')

        P_LOOK = r"""() => Array.from(
            document.querySelectorAll('.modal-header')).map(h => {
          const s = getComputedStyle(h);
          const t = h.querySelector('.modal-title');
          const ts = t ? getComputedStyle(t) : null;
          const c = h.querySelector('.close');
          const cs = c ? getComputedStyle(c) : null;
          return {bg: s.backgroundImage !== 'none' ? s.backgroundImage
                                                   : s.backgroundColor,
                  pad: s.paddingTop + ' ' + s.paddingLeft,
                  ink: ts ? ts.color : '', size: ts ? ts.fontSize : '',
                  weight: ts ? ts.fontWeight : '',
                  close: cs ? cs.color + ' ' + cs.opacity : 'none',
                  title: t ? t.innerText.trim().slice(0, 40) : ''};
        })"""

        def body_markup(t):
            m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock',
                          t, re.S)
            b = m.group(1) if m else t
            b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
            b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
            b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
            return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)

        got = look(br, fixture(css_of(B_NOW), styles_of(P_NOW),
                               body_markup(P_NOW)), 1280, P_LOOK)
        ok(len(got) == 3, 'rendered, the page opens three of them', len(got))
        # The same bar test_modal_heads.py holds the other 51 to.
        off = []
        for h in got:
            danger = bool(re.search(r'\bdelete\b', h['title'], re.I))
            want = 'rgb(179, 38, 30)' if danger else 'rgb(14, 124, 139)'
            if not (h['bg'].startswith('linear-gradient')
                    and want in h['bg']
                    and h['ink'] == 'rgb(255, 255, 255)'
                    and h['size'] == '20px' and h['weight'] == '600'
                    and h['close'] in ('rgb(255, 255, 255) 0.85', 'none')
                    and h['pad'] == '16px 20px'):
                off.append('%r %s' % (h['title'], h))
        ok(not off, '  teal banner, red exactly where it deletes, white '
           '20px/600 title, white close at 0.85, 16px 20px - the bar the '
           'other 51 are held to', '\n'.join(off[:3]))
        ok(len(set((h['bg'][:40], h['ink'], h['size'], h['weight'])
                   for h in got)) == 2,
           '  two looks: teal, and red where it deletes')
        if os.path.isfile(PASS + SUFFIX):
            old = look(br, fixture(css_of(B_WAS), styles_of(P_WAS),
                                   body_markup(P_WAS)), 1280, P_LOOK)
            ok(len(set((h['bg'][:40], h['ink'], h['size'], h['weight'])
                       for h in old)) == 2
               and sum(h['bg'] == 'rgba(0, 0, 0, 0)' for h in old) == 2
               and sum(h['bg'] == 'rgb(220, 53, 69)' for h in old) == 1,
               '  CONTROL: they were TWO looks before, and neither was the '
               'house - two headers with no background at all, and '
               'Bootstrap\'s own red on the third',
               [h['bg'][:28] for h in old])
            ok(not any(h['bg'].startswith('linear-gradient') for h in old),
               '  CONTROL: and not one of them was a gradient')
        else:
            skip('the three looks before', 'no %s backup' % SUFFIX)

        # ==============================================================
        head('6. THE SHARED HELP MODAL - notifications STOPS OVERRIDING IT')
        # ==============================================================
        N_NOW, N_WAS = now(NOTIF), was(NOTIF)
        ok('#notificationHelpModal .modal-header' not in N_NOW,
           'the override of the shared help modal\'s header is gone')
        ok('#notificationHelpModal .modal-header' in N_WAS,
           '  CONTROL: it was there before')
        ok('linear-gradient(135deg, #0e7c8b 0%, #0a5e6a 100%)' in N_WAS,
           '  CONTROL: and it re-spelt base\'s own gradient as two '
           'literals, with !important')
        # The STYLE block, not the first mention: the page names the modal
        # in a data-target near the top, and slicing from there would put
        # most of the page inside "what is scoped to that modal".
        _help = N_NOW[N_NOW.find('#notificationHelpModal .modal-content'):]
        ok('linear-gradient' not in _help and '#0a5e6a' not in _help
           and _help.count('#0e7c8b') == 1,
           '  the hand-spelt gradient is gone from everything still scoped '
           'to that modal - the ONE accent literal left there is the '
           'active tab\'s text, in a rule this round did not touch',
           [ln.strip()[:60] for ln in _help.split('\n')
            if 'linear-gradient' in ln or '#0a5e6a' in ln
            or '#0e7c8b' in ln][:4])
        # NOT this round's, and said rather than quietly passed over: the
        # page writes the accent by hand in seven more places, in rules
        # this round never touched. They belong to the literal sweep, not
        # to the pop-up.
        _rest = len(re.findall(r'#0e7c8b|#0a5e6a', N_NOW))
        ok(_rest == 8, '  NOTE: %d accent literal(s) remain elsewhere on '
           'the page - none of them a pop-up, none of them this round\'s'
           % _rest, _rest)
        for keep in ('#notificationHelpModal .modal-content',
                     '#notificationHelpModal .modal-body',
                     '#notificationHelpModal .nav-tabs'):
            ok(keep in N_NOW, '  %s is untouched - only the HEADER was '
               'agreed' % keep)
        ok('alv-modal-head' in read(SHELL),
           'help_modal_shell.html wears the house class, which is why the '
           'override was doing nothing the house was not')
        # And it LOOKS the same without it. Measured, not reasoned.
        SHELL_HEAD = ('<div class="modal" id="notificationHelpModal">'
                      '<div class="modal-dialog"><div class="modal-content">'
                      '<div class="modal-header alv-modal-head">'
                      '<div><h5 class="modal-title">Notifications</h5></div>'
                      '<button class="close">&times;</button></div>'
                      '</div></div></div>')
        H_LOOK = r"""() => {
          const h = document.querySelector('#notificationHelpModal '
                                           + '.modal-header');
          const s = getComputedStyle(h);
          return {bg: s.backgroundImage, ink: s.color};
        }"""
        with_over = look(br, fixture(css_of(B_WAS), styles_of(N_WAS),
                                     SHELL_HEAD), 1280, H_LOOK)
        without = look(br, fixture(css_of(B_NOW), styles_of(N_NOW),
                                   SHELL_HEAD), 1280, H_LOOK)
        ok(with_over == without,
           'the help modal\'s header is pixel-identical with the override '
           'and without it - which is what "redundant" has to mean',
           '%s\nvs\n%s' % (with_over, without))
        ok(without['bg'].startswith('linear-gradient')
           and 'rgb(14, 124, 139)' in without['bg'],
           '  and base is what paints it now', without)
        br.close()

# ==========================================================================
head('7. SCOPE, THEN REGISTERED AND ON THE GATE')
# ==========================================================================
for label, path in (('base.html               ', BASE),
                    ('home.html               ', HOME),
                    ('notifications.html      ', NOTIF),
                    ('passport_management.html', PASS)):
    if not os.path.isfile(path + SUFFIX):
        skip('scope on %s' % label.strip(), 'no %s backup' % SUFFIX)
        continue
    a, b = now(path), was(path)
    ok(a.count('{') == a.count('}'), '%s braces balanced' % label,
       (a.count('{'), a.count('}')))
    ok(sorted(re.findall(r'\bid="([^"]+)"', a))
       == sorted(re.findall(r'\bid="([^"]+)"', b)),
       '  every id is still there')
    ok(a.count('{%') == b.count('{%') and a.count('{{') == b.count('{{'),
       '  every Django tag is still there')
    ok(re.findall(r'<(?:input|select|textarea)\b[^>]*?(?:name|id)="([^"]+)"',
                  a)
       == re.findall(r'<(?:input|select|textarea)\b[^>]*?(?:name|id)="([^"]+)"',
                     b),
       '  every control is still there, in order')
    if path in (HOME, NOTIF):
        # Outside <style>, these two pages are byte-for-byte what they
        # were apart from the two comments that described the cut rules.
        def nostyle(t):
            return re.sub(r'<style[^>]*>.*?</style>', '', t, flags=re.S | re.I)
        da = nostyle(a)
        db = nostyle(b)
        if path == NOTIF:
            db = db.replace(
                "<!-- Scoped CSS overrides so the Bootstrap help modal isn't"
                " affected by the page's custom modal-overlay styles -->", '')
            da = re.sub(r'<!-- Scoped CSS overrides for the shared help '
                        r'modal\..*?-->', '', da, flags=re.S)
        ok(da == db, '  and outside <style> the page did not move',
           'lengths %d vs %d' % (len(da), len(db)))

ok(SUFFIX in ROUNDS and '.bak_series' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_series'),
   'alv_rounds lists %s after .bak_series' % SUFFIX)
ps = read(PS1) if os.path.isfile(PS1) else ''
_s = ps[ps.find('$suites = @('):]
_m = re.search(r'\n\)\s*?\n', _s)
ok(_m is not None and "'%s'" % ME in _s[:_m.end()],
   '%s is on the push gate' % ME)

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
