# -*- coding: utf-8 -*-
"""test_card_wrap.py - Section CW round CW-1, 5 Oct 2026.

Found while rendering RA-3, not reported by anyone: the Ingredient
Shopping Units page pushed itself sideways at every phone width.

    320px  scrollWidth 448  over +128
    390px  scrollWidth 448  over  +58
    414px  scrollWidth 448  over  +34
    768px  scrollWidth 768  over   +0

What stuck out was the Conversion cell's badges - `Missing` and `N/A` at
384..448 on a 390px screen, outside their own <td>, which ended at 353.

THOSE FOUR NUMBERS ARE ONE BROWSER'S TEXT METRICS, and this suite's first
build asserted one of them. Chromium measures the same badges 11px
narrower with the fonts a Windows laptop has installed, so the overflow
there was +47, and at [272/274] the round was refused by its own suite
over a number that was never the claim. The claim is that a cell with no
room for its value pushes the page sideways, and that one declaration in
base stops it. Direction travels between machines; a relation between two
renders in the same browser travels; an absolute text width does not.
Section 3 now measures and PRINTS the overflow and asserts only its
sign - and does it against a base that differs from the shipped one by
nothing but the declaration itself.

THE CAUSE WAS IN BASE. Its card pattern lays every cell out as a flex row
with the label on the left and the value on the right, and the label is
explicitly flex-shrink: 0. Flex does not wrap unless told to, so a cell
whose VALUE is wider than the room the label leaves has nowhere to go.
That is true of every card table in the app; Ingredients was simply the
first with a value wide enough to prove it.

SECTION 2 IS WHY THIS SUITE EXISTS. One declaration in base reflows every
table in the app, so the question is not "did it fix Ingredients" - it is
"what ELSE moved". It paints eight card tables before and after and
requires that six of them do not move at all, by a single pixel, in
height or in overflow. A fix in base that quietly reflowed the tree would
be worth knowing about before it shipped.
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
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_cardwrap'
ME = 'test_card_wrap.py'
PATCHER = 'apply_card_wrap.py'
PS1 = 'Push-PendingChanges.ps1'
BOOTF = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BASE = alv_tree.path_of('base.html')

VICTIM = 'ingredient_base_units_management.html'
# The seven others painted. Six must not move; property_detail may, and
# section 2 says which it was rather than allowing any of them to.
OTHERS = ['property_detail.html', 'tenant.html', 'properties.html',
          'measurement_units_management.html', 'physical_invoice_list.html',
          'passport_management.html', 'title_deeds_management.html']
MAY_MOVE = {'property_detail.html'}

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


def detag(s):
    s = re.sub(r'\{%\s*(block|endblock|extends|load|csrf_token)[^%]*%\}', '', s)
    s = re.sub(r'\{%\s*(else|endif|endfor|empty)\s*%\}', '', s)
    s = re.sub(r'\{%[^%]*%\}', '', s)
    s = re.sub(r'\{\{[^}]*\}\}', 'Sample', s)
    return re.sub(r'\{#.*?#\}', '', s, flags=re.S)


FA = ('i[class*="fa-"]{display:inline-block;width:1em;height:1em;'
      'vertical-align:-0.125em;background:#bbb;}')


def path_of(rel):
    hits = [q for q in alv_tree.templates()
            if alv_tree.rel(q).replace(os.sep, '/') == rel]
    return hits[0] if hits else None


def page_html(raw, basesrc):
    body = re.sub(r'<style[^>]*>.*?</style>', '', raw, flags=re.S | re.I)
    body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.S | re.I)
    return ('<!doctype html><html><head><meta charset="utf-8"><style>%s</style>'
            '<style>%s</style><style>%s</style><style>%s</style></head>'
            '<body style="margin:0">%s</body></html>'
            % (read(BOOTF), css_of(alv_tree.code_only(basesrc)), FA,
               css_of(raw), detag(body)))


PROBE = """() => {
  const d = document.documentElement;
  const cells = [...document.querySelectorAll('.alv-table td')];
  return {over: d.scrollWidth - d.clientWidth, cells: cells.length,
          h: cells.reduce((a, c) =>
               a + Math.round(c.getBoundingClientRect().height), 0)};
}"""

print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. the rule, and what it was missing')

b_now, b_was = now(BASE), was(BASE)
# THE CARD RULE, NOT THE FIRST .alv-table td RULE. base declares that
# selector several times - the desktop one, the print one, the card one -
# and the first build of this section matched the desktop rule and failed
# on a round that had worked. The card rule is the one carrying
# min-height: 28px.
CARD = re.compile(r'\.alv-table\s+td\s*\{([^{}]*min-height:\s*28px[^{}]*)\}')
card = CARD.search(css_of(b_was))
ok(card is not None, 'base lays a card cell out as a flex row')
if card:
    body = ' '.join(card.group(1).split())
    ok('display: flex' in body, '  with display: flex', body[:90])
    ok('flex-wrap' not in body,
       '  and no flex-wrap, which is why a wide value had nowhere to go',
       'it already wrapped - then the overflow had another cause')
lab = re.search(r'\.alv-table\s+td::before\s*\{([^{}]*)\}', css_of(b_was))
ok(lab is not None and 'flex-shrink: 0' in ' '.join(lab.group(1).split()),
   '  and the label beside it refuses to shrink',
   'without that the label would give way and nothing would overflow')

card2 = CARD.search(css_of(b_now))
ok(card2 is not None and 'flex-wrap: wrap' in ' '.join(card2.group(1).split()),
   'and now it wraps')

# ==========================================================================
head('2. eight card tables painted - what else moved')

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if sync_playwright is None:
    print('  --    the renders  (playwright missing)')
else:
    exe = '/opt/pw-browsers/chromium'
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))

        def paint(raw, basesrc, width=390):
            pg = br.new_page(viewport={'width': width, 'height': 1000})
            pg.set_content(page_html(raw, basesrc))
            pg.wait_for_timeout(250)
            r = pg.evaluate(PROBE)
            pg.close()
            return r

        v = path_of(VICTIM)
        for w in (320, 390, 414, 768):
            a = paint(now(v), b_was, w)
            c = paint(now(v), b_now, w)
            if w < 768:
                ok(a['over'] > 0 and c['over'] == 0,
                   '%-5s Ingredients pushed the page %+d and now does not'
                   % ('%dpx' % w, a['over']),
                   'was %+d, now %+d' % (a['over'], c['over']))
            else:
                ok(a['over'] == 0 and c['over'] == 0,
                   '%-5s was clean and stays clean' % ('%dpx' % w))

        still = 0
        for name in OTHERS:
            p = path_of(name)
            if not p:
                continue
            a, c = paint(now(p), b_was), paint(now(p), b_now)
            moved = (a['h'] != c['h']) or (a['over'] != c['over'])
            if name in MAY_MOVE:
                print('      %-38s %d cells, height %d -> %d  (allowed)'
                      % (name, a['cells'], a['h'], c['h']))
                continue
            if not moved:
                still += 1
            ok(not moved,
               '%-38s %d cells, not one pixel moved' % (name, a['cells']),
               'height %d -> %d, overflow %+d -> %+d'
               % (a['h'], c['h'], a['over'], c['over']))
        ok(still >= 6,
           '  %d of the painted tables are untouched by a change in base'
           % still, '%d - a base change that reflows the tree is worth '
                    'knowing about' % still)

        # ==================================================================
        head('3. the control - a declaration that must be caught')

        # THE CONTROL IS SURGICAL, AND IT CLAIMS NO PIXEL COUNT.
        #
        # Section 2 already compares base as CW-1 found it with base as
        # CW-1 left it, so repeating that here would prove nothing twice.
        # Those two files differ by a declaration AND a five-line comment,
        # and a comparison across both cannot say which did the work. So
        # the control builds a third base: the shipped one with the single
        # flex-wrap taken back out and everything else, comment included,
        # left exactly where it is. If the overflow returns, it returned
        # for that one declaration.
        #
        # And it asserts the SIGN, never the size. The first build required
        # exactly 58 at 390 - what this sandbox's Chromium measures. The
        # laptop measured 47, the same defect through different font
        # metrics, and the suite refused a round that was correct. The
        # number is printed as evidence and is not a condition.
        mm = re.search(r'\.alv-table\s+td\s*\{[^{}]*min-height:\s*28px[^{}]*\}',
                       b_now)
        rule = mm.group(0) if mm else ''
        stripped, n = re.subn(r'[ \t]*flex-wrap:\s*wrap;[ \t]*\r?\n', '', rule)
        ok(mm is not None and n == 1,
           'the control is base as CW-1 left it, less the one declaration',
           'the card rule gave up %d flex-wrap line(s), expected 1' % n)
        b_cut = b_now[:mm.start()] + stripped + b_now[mm.end():] if mm else b_was
        a = paint(now(v), b_cut, 390)
        c = paint(now(v), b_now, 390)
        ok(a['over'] > 0,
           '  without it Ingredients overflows again, by %+d at 390'
           % a['over'],
           'it fits without the declaration - then the page was fixed by '
           'something else and this round is taking the credit')
        ok(c['over'] == 0, '  and with it, by nothing')
        ok(a['h'] < c['h'],
           '  the card is %dpx taller, which is the line the value moved to'
           % (c['h'] - a['h']),
           'it is not taller - then nothing wrapped and the fix is elsewhere')
        br.close()

# ==========================================================================
head('4. and base still says it only once')

ok(len(re.findall(r'flex-wrap:\s*wrap', css_of(b_now)))
   - len(re.findall(r'flex-wrap:\s*wrap', css_of(b_was))) == 1,
   'exactly one flex-wrap was added to base',
   'base gained %d - this round claims one'
   % (len(re.findall(r'flex-wrap:\s*wrap', css_of(b_now)))
      - len(re.findall(r'flex-wrap:\s*wrap', css_of(b_was)))))
ok(len(b_now) - len(b_was) < 700,
   '  and the file grew by %d bytes, comment included'
   % (len(b_now) - len(b_was)))

# ==========================================================================
head('5. registration')

ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s is in the push suites' % ME)

# ==========================================================================
print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that no OTHER card table in the app reflows.')
print('  Eight were painted and six did not move, which is evidence and')
print('  not proof - the tree holds over a hundred. A value that was')
print('  already fitting cannot start wrapping, which is the argument;')
print('  the eight are what was measured.')
