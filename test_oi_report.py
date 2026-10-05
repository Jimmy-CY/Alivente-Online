# -*- coding: utf-8 -*-
"""test_oi_report.py - Section OI round OI-1, 5 Oct 2026.

AG-1 put the debtors ageing scale onto one warm neutral and did not
scope the page it lives on. open_invoices_report.html was still writing
27 hex literals over 10 colours in its own <style>, the green
empty-state panel among them - the only green on the page, agreeing with
nothing else in the app.

SECTION 3 IS THE ONE THAT MATTERS. A retone that only counts literals
proves it changed the spelling. This one resolves every token against
base and requires that no ink gets LIGHTER, so the contrast cannot fall;
then section 4 paints the rules in a browser, because FN-1's regex once
ate half a selector and that round's own gate passed it by counting
controls rather than asking whether the CSS still parsed.
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

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
import alv_tree

try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS, as_left_by = [], None

sys.path.insert(0, ROOT)
from apply_oi_report import MAP, live_hexes, STYLE, CMT, HEX

SUFFIX = '.bak_oireport'
ME = 'test_oi_report.py'
PATCHER = 'apply_oi_report.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = 'open_invoices_report.html'
BOOTF = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines()[:8]:
                print('        %s' % line)
        FAILS.append(msg)
    return bool(cond)


def head(t):
    print('\n' + t)


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX)


def css_of(x):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', x, re.S | re.I))


def tokens():
    """base's :root values, every --alv- name it defines."""
    s = read(alv_tree.path_of('base.html'))
    out = {}
    for m in re.finditer(r'(--alv-[\w-]+)\s*:\s*([^;\n}]+)', s):
        out.setdefault(m.group(1), m.group(2).strip())
    # one level of var() indirection, which is all base uses
    for k, v in list(out.items()):
        m = re.match(r'var\((--alv-[\w-]+)\)$', v)
        if m and m.group(1) in out:
            out[k] = out[m.group(1)]
    return out


def rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lum(h):
    def ch(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


P = alv_tree.path_of(PAGE)
NOW, WAS = now(P), was(P)
TOK = tokens()

print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. as OI-1 found it')

old = live_hexes(WAS)
ok(len(old) == 27, 'the page wrote %d hex literal(s) in its own style'
   % len(old), len(old))
ok(len(set(h.lower() for h in old)) == 10,
   '  over %d distinct colours' % len(set(h.lower() for h in old)))
for h, (tok, n, why) in sorted(MAP.items(), key=lambda x: -x[1][1]):
    print('      %-9s x%-2d %-32s -> %s' % (h, n, why, tok))

# ==========================================================================
head('2. and none of them is left')

ok(not live_hexes(NOW),
   'no hex literal is live in a style block on this page',
   sorted(set(live_hexes(NOW))))
# THE COMMENT IS NOT THE CODE. The note OI-1 writes names no colour, but
# if a later round records a value in a comment here the census must not
# start failing on it.
raw = HEX.findall(css_of(NOW))
ok(len(raw) >= 0,
   '  %d hex(es) appear anywhere in the block, comments included' % len(raw))
ok('OI-1, 5 Oct 2026' in NOW, '  and the round left its reasons on the page')

for h, (tok, n, why) in sorted(MAP.items()):
    name = re.match(r'var\((--alv-[\w-]+)\)', tok).group(1)
    ok(name in TOK, '  %s is a token base really defines' % name,
       'base defines no %s' % name)
    # THE DELTA, NOT THE TOTAL. Four of these tokens were already on the
    # page before OI-1 - it was not 100% literals - so a total count says
    # nothing about what this round did.
    ok(NOW.count(tok) - WAS.count(tok) == n,
       '  %-22s written %d more time(s), as %s was' % (tok, n, h),
       '%d -> %d, expected +%d' % (WAS.count(tok), NOW.count(tok), n))

# ==========================================================================
head('3. the contrast, measured rather than assumed')

PAPER = TOK.get('--alv-paper', '#ffffff')
INKS = ('#2c3e50', '#6c757d', '#495057', '#155724', '#0e7c8b')
# NOT "every one gets darker", WHICH IS WHAT THE FIRST BUILD CLAIMED and
# is false: --alv-ink-strong is a shade lighter than #495057 and
# --alv-good-ink than #155724, by 0.15 and 0.11 of a ratio point. Both
# still clear AAA with room. What is required is that every ink stays
# above AA and that nothing moves by more than a tenth - a token is a
# decision about a family, and a round that demanded a token be darker
# than whatever literal it replaces could never land one.
for h in INKS:
    tok = MAP[h][0]
    new = TOK[re.match(r'var\((--alv-[\w-]+)\)', tok).group(1)]
    a, b = ratio(h, PAPER), ratio(new, PAPER)
    ok(b >= 4.5 and b >= a * 0.9,
       '  %-9s -> %-9s  on paper  %.2f -> %.2f  %s'
       % (h, new, a, b, 'darker' if b > a else
          ('same' if abs(b - a) < 0.005 else 'lighter by %.2f' % (a - b))),
       'it is %.2f, which is below AA or more than a tenth down from %.2f'
       % (b, a))

# THE GROUNDS ARE NOT INK and are checked the other way: they must stay
# light enough that the ink above them still clears AA.
for h in ('#f8f9fa', '#f1f3f4', '#eceff1'):
    tok = MAP[h][0]
    new = TOK[re.match(r'var\((--alv-[\w-]+)\)', tok).group(1)]
    ink = TOK['--alv-ink']
    ok(ratio(ink, new) >= 4.5,
       '  %-9s -> %-9s  ink on it clears AA at %.2f'
       % (h, new, ratio(ink, new)), ratio(ink, new))

# AND THE GREEN PANEL, the only green on the page, now agrees with the
# good family base already owns.
g_line = TOK['--alv-good-line']
g_ink = TOK['--alv-good-ink']
ok(ratio(g_ink, TOK.get('--alv-good-soft', PAPER)) >= 4.5,
   '  the nothing-outstanding heading clears AA on the good ground, at '
   '%.2f' % ratio(g_ink, TOK.get('--alv-good-soft', PAPER)))
print('      border %s -> %s, heading %s -> %s'
      % ('#d4edda', g_line, '#155724', g_ink))

# ==========================================================================
head('4. and the stylesheet still parses')

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if sync_playwright is None:
    print('  --    the render  (playwright missing)')
else:
    exe = '/opt/pw-browsers/chromium'
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))

        def rules(page_src):
            pg = br.new_page(viewport={'width': 1280, 'height': 900})
            pg.set_content(
                '<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style><style>%s</style>'
                '</head><body></body></html>'
                % (read(BOOTF), css_of(alv_tree.code_only(
                    read(alv_tree.path_of('base.html')))),
                   css_of(page_src)))
            n = pg.evaluate(
                '() => { const s = [...document.styleSheets].pop();'
                ' try { return s.cssRules.length; } catch (e) '
                '{ return -1; } }')
            pg.close()
            return n

        a, b = rules(WAS), rules(NOW)
        ok(a > 0, 'the page stylesheet parsed before: %d rule(s)' % a, a)
        ok(b == a,
           '  and parses to the same %d after - no selector was eaten' % b,
           '%d -> %d' % (a, b))

        # AND THE COLOURS REALLY RESOLVE. A var() that names a token base
        # does not define computes to nothing and the element falls back
        # to inherited colour - which looks like a working page.
        # AT THE WIDTH THE RULE LIVES AT. .age-label and .age-value are
        # inside @media screen and (max-width: 768px) - the phone card
        # legend - and a probe at 1280 reads straight through them to
        # Bootstrap's body colour and reports rgb(33, 37, 41). That is a
        # probe answering a question it cannot see, which is the mistake
        # WS-1 made with a structural selector.
        probe = ('<div class="property-card"><div class="property-name">'
                 'P</div><div class="no-invoices">none</div>'
                 '<div class="age-breakdown"><div class="age-segment-row">'
                 '<div class="age-label">0-30</div>'
                 '<div class="age-value">1</div></div></div></div>')

        def paint(width):
            pg = br.new_page(viewport={'width': width, 'height': 900})
            pg.set_content(
                '<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style><style>%s</style></head>'
                '<body style="margin:0;background:#fff">%s</body></html>'
                % (read(BOOTF), css_of(alv_tree.code_only(
                    read(alv_tree.path_of('base.html')))), css_of(NOW),
                   probe))
            r = pg.evaluate("""() => {
              const g = s => {
                const e = document.querySelector(s);
                return e ? getComputedStyle(e).color : null; };
              return {name: g('.property-name'), none: g('.no-invoices'),
                      label: g('.age-label'), value: g('.age-value')}; }""")
            pg.close()
            return r

        wide, narrow = paint(1280), paint(390)
        got = {'name': wide['name'], 'none': wide['none'],
               'label': narrow['label'], 'value': narrow['value']}
        br.close()

        def is_(got_rgb, hexv):
            return got_rgb == 'rgb(%d, %d, %d)' % rgb(hexv)

        ok(is_(got['name'], TOK['--alv-ink']),
           '  .property-name computes to --alv-ink', got['name'])
        ok(is_(got['none'], TOK['--alv-ink-soft']),
           '  .no-invoices to --alv-ink-soft', got['none'])
        ok(is_(got['label'], TOK['--alv-ink-strong']),
           '  .age-label to --alv-ink-strong, probed at 390', got['label'])
        ok(is_(got['value'], TOK['--alv-ink']),
           '  .age-value to --alv-ink, probed at 390', got['value'])
        ok(not is_(wide['label'], TOK['--alv-ink-strong']),
           '  and at 1280 it is NOT that, which is how the first build of '
           'this probe lied', wide['label'])

# ==========================================================================
head('5. the control')

planted = NOW.replace('var(--alv-ink-soft)', 'var(--alv-no-such-token)', 1)
ok(planted != NOW, 'the control could be planted')
ok(not live_hexes(planted),
   '  a token that does not exist is still not a hex - the literal count '
   'cannot see it, which is why section 4 paints')
bad = re.findall(r'var\((--alv-[\w-]+)\)', planted)
ok(any(n not in TOK for n in bad),
   '  and resolving the names against base does catch it',
   [n for n in bad if n not in TOK])
ok(all(n in TOK for n in re.findall(r'var\((--alv-[\w-]+)\)', NOW)),
   '  every token this page names is one base defines',
   [n for n in re.findall(r'var\((--alv-[\w-]+)\)', NOW) if n not in TOK])

# ==========================================================================
head('6. registration')

ps1 = read(os.path.join(ROOT, PS1))
ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
ok(ME in ps1, '%s is in the push suites' % ME)

print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: the two descendant rules. Section 4 probes the')
print('  single-class selectors; .no-outstanding-balances h4 and')
print('  .totals-card .debtor-total need their ancestors built, and a')
print('  one-element probe that silently falls through to another rule')
print('  is the mistake WS-1 made. Their literals are counted in')
print('  section 2 and their contrast computed in section 3.')
