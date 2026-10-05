# -*- coding: utf-8 -*-
"""test_pd3.py - Section PD round PD-3, 5 Oct 2026.

property_detail.html stops carrying its own palette, and stops scrolling
sideways on every phone.

THE SEVEN PIXELS ARE THE PART THIS SUITE EXISTS FOR. They cannot be seen
by reading the file: the wrapper's 8px padding is in one rule, Bootstrap's
-15px row margin is in another file entirely, and the subtraction happens
in the browser. Section 1 paints the page as PD-3 found it and as PD-3
left it, at four widths, and compares scrollWidth against clientWidth.
A text check would have passed on the broken page at every width.

WHAT IT DELIBERATELY DOES NOT CLAIM. That the other 25 !important flags
are dead. I dropped each of the 39 and repainted: 19 changed nothing. But
the fixture flattens the page's {% for %} loops and draws a fraction of
the real rows, so that measurement can prove a flag MATTERS and cannot
prove one does not. Only the 15 rules that are provably dead ON PAPER
were removed - Bootstrap 4.1.3 already ships .text-left/.text-center/
.text-right with the same property, the same value and the same flag, and
all 22 <th> on this page carry the utility class. Section 4 proves that
rather than asserting it, and section 5 asserts the other 25 are STILL
THERE, so a later round cannot quietly take them on this one's authority.

THE AMBER. #ffc107 became var(--alv-warn), which is #8e6207 and reads as
olive rather than amber. Shown to Demetri rendered, beside the red and
green stripes, and kept: var(--alv-warn) was already the left stripe in
four other places in the tree, so this is the house answer and not a
choice invented here. Section 3 records the count so the eight #ffc107
stripes still on OTHER pages stay visible as the drift they are.
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

SUFFIX = '.bak_pd3'
ME = 'test_pd3.py'
PATCHER = 'apply_pd3.py'
PS1 = 'Push-PendingChanges.ps1'

PAGE = alv_tree.path_of('property_detail.html')
BASE = alv_tree.path_of('base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

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


# FONT AWESOME IS A CDN AWAY FROM THIS SANDBOX. Its glyphs never arrive,
# so an <i> would collapse to zero width and every icon control would
# measure narrow - which is one of the things being measured. A 1em
# square keeps the GEOMETRY honest even though the picture is not.
FA_STUB = ('i[class*="fa-"], span[class*="fa-"]{display:inline-block;'
           'width:1em;height:1em;vertical-align:-0.125em;background:#bbb;}')

RAW, OLDRAW = now(PAGE), (was(PAGE) if os.path.exists(PAGE + SUFFIX) else '')
BRAW = now(BASE)
SRC = alv_tree.code_only(RAW)
CSS = css_of(RAW)


def page_html(raw, basesrc, extra=''):
    body = re.sub(r'<style[^>]*>.*?</style>', '', raw, flags=re.S | re.I)
    body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.S | re.I)
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<style>%s</style><style>%s</style><style>%s</style>'
            '<style>%s</style><style>%s</style></head>'
            '<body style="margin:0">%s</body></html>'
            % (read(BOOT), css_of(alv_tree.code_only(basesrc)), FA_STUB,
               css_of(raw), extra, detag(body)))


try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

PROBE = """() => {
  const doc = document.documentElement;
  const ctrl = {};
  for (const e of document.querySelectorAll('select, input, button, textarea')) {
    if (e.type === 'hidden') continue;
    const r = e.getBoundingClientRect();
    if (!r.height) continue;
    const k = e.tagName.toLowerCase() + '.' + (e.className || '-');
    ctrl[k] = Math.round(r.height * 10) / 10;
  }
  return {W: doc.clientWidth, scrollW: doc.scrollWidth, ctrl,
          n: document.getElementsByTagName('*').length};
}"""


def paint(raw, basesrc, width, extra=''):
    with sync_playwright() as pw:
        exe = '/opt/pw-browsers/chromium'
        b = pw.chromium.launch(**({'executable_path': exe}
                                  if os.path.exists(exe) else {}))
        pg = b.new_page(viewport={'width': width, 'height': 1400})
        pg.set_content(page_html(raw, basesrc, extra))
        pg.wait_for_timeout(320)
        r = pg.evaluate(PROBE)
        b.close()
    return r


print(__doc__.strip().splitlines()[0])

WIDTHS = (320, 390, 768, 1180)
shots = {}

# ==========================================================================
head('1. the seven pixels')

if sync_playwright is None or not OLDRAW:
    for _ in WIDTHS:
        print('  --    the overflow  (playwright or backup missing)')
else:
    for w in WIDTHS:
        a = paint(OLDRAW, BRAW, w)
        b = paint(RAW, BRAW, w)
        shots[w] = (a, b)
        over_was = a['scrollW'] - a['W']
        over_now = b['scrollW'] - b['W']
        if w < 992:
            ok(over_was > 0 and over_now == 0,
               '%4dpx  the page scrolled sideways by %d and now does not'
               % (w, over_was),
               'was %+d, now %+d - if was is 0 the defect was not there'
               % (over_was, over_now))
        else:
            ok(over_was == 0 and over_now == 0,
               '%4dpx  desktop was clean and stays clean' % w,
               'was %+d, now %+d' % (over_was, over_now))
    # THE CAUSE, not just the symptom. 15 - 8 = 7, and the round's claim
    # is that the rows now match the wrapper rather than Bootstrap.
    mob = re.search(r'@media screen and \(max-width: 768px\)', CSS)
    ok(mob is not None, '  the mobile block is still where the rule lives')
    ok(re.search(r'\.property-detail-page\.container-fluid\s*>\s*\.row\s*\{'
                 r'[^{}]*margin-left:\s*-8px', CSS) is not None,
       '  and the rows are pulled in to -8px to meet its 8px padding',
       'the compensating rule is not there')
    ok(re.search(r'>\s*\.row\s*>\s*\[class\*="col-"\]\s*\{'
                 r'[^{}]*padding-left:\s*8px', CSS) is not None,
       '  with the columns at 8px rather than Bootstrap\'s 15px')
    # SCOPED TO DIRECT CHILDREN. A bare .row rule would also move the rows
    # inside cards and tables, which never overflowed.
    ok(not re.search(r'(^|[,}])\s*\.row\s*\{', CSS, re.M),
       '  and no bare .row rule was added, so nested rows are untouched')

# ==========================================================================
head('2. forty-four pixels to tap')

if shots:
    a, b = shots[390]
    small_was = {k: v for k, v in a['ctrl'].items() if v < 43.5}
    small_now = {k: v for k, v in b['ctrl'].items() if v < 43.5}
    ok(bool(small_was),
       'at 390px the page really did have a control under 44px',
       'it did not - then this half of the round is aimed at nothing')
    for k, v in sorted(small_was.items()):
        print('      was  %-52s %.1f' % (k[:52], v))
    ok(not small_now, 'and now it does not',
       '\n'.join('%s %.1f' % (k[:52], v) for k, v in sorted(small_now.items())))
    ok(re.search(r'min-height:\s*44px', CSS) is not None,
       '  set as min-height, so a long option cannot clip it')

# ==========================================================================
head('3. the page stops carrying its own palette')

live = alv_tree.code_only(RAW)          # comments out, all four kinds
old_live = alv_tree.code_only(OLDRAW) if OLDRAW else ''

hex_now = re.findall(r'#[0-9a-fA-F]{3,8}\b', live)
hex_was = re.findall(r'#[0-9a-fA-F]{3,8}\b', old_live)
ok(len(hex_was) > 50,
   'the page really did carry %d hex literals in live code' % len(hex_was),
   'far fewer than expected - has the census stopped finding them?')
ok(not hex_now, 'and now carries none at all',
   'still there: %s' % ', '.join(sorted(set(h.lower() for h in hex_now))[:8]))

# THE EIGHT IN THE FILE ARE ALL IN PROSE. DB-7 and PD-2 describe what
# THEY removed, in the past tense. A literal in a comment paints nothing,
# and deleting another round's record of its own finding would be worse
# than leaving it.
in_file = re.findall(r'#[0-9a-fA-F]{3,8}\b', RAW)
ok(len(in_file) > 0 and not hex_now,
   '  the %d still in the file are every one of them inside a comment'
   % len(in_file))

tokens = set(re.findall(r'var\((--alv-[\w-]+)\)', CSS))
declared = set(re.findall(r'(--alv-[\w-]+)\s*:', css_of(BRAW)))
unknown = sorted(t for t in tokens if t not in declared)
ok(not unknown, '  and every token it names is one base declares',
   'base does not declare: %s' % ', '.join(unknown))
print('      %d var(--alv-*) uses over %d distinct tokens'
      % (len(re.findall(r'var\(--alv-', CSS)), len(tokens)))

# THE AMBER, AND THE DRIFT IT LEAVES BEHIND. var(--alv-warn) is the house
# left stripe - four other places in the tree already use it - so this
# page taking it is a page catching up, not a page inventing. The count
# of pages that have NOT caught up is printed so it stays visible.
stray = 0
for p in alv_tree.templates():
    if p == PAGE:
        continue
    c = css_of(alv_tree.code_only(read(p)))
    stray += len(re.findall(r'border-left\s*:[^;]*#ffc107', c))
print('      %d #ffc107 left stripe(s) remain on OTHER pages - drift for a '
      'later round, named here so it is not forgotten' % stray)

# ==========================================================================
head('4. fifteen rules Bootstrap already said')

boot = read(BOOT)
for word in ('left', 'center', 'right'):
    ok(re.search(r'\.text-%s\s*\{\s*text-align:\s*%s\s*!important\s*\}'
                 % (word, word), boot) is not None,
       'Bootstrap ships .text-%s with !important and the same value' % word,
       'if it does not, the removal argument collapses')

# THE QUESTION IS NOT WHETHER EVERY <th> CARRIES A text-* CLASS. Six of
# the 28 do not, and that is fine: the removed rules were spelt
# `.issues-table th.text-left`, so a <th> WITHOUT the utility class was
# never matched by them in the first place. The claim is narrower and
# exactly checkable - every <th> the removed rules COULD have reached
# still carries the Bootstrap class that now does the work, and the
# round removed CSS, not markup.
util = re.compile(r'\btext-(?:left|center|right)\b')
ths_was = [c for c in re.findall(r'<th[^>]*class="([^"]*)"', old_live)
           if util.search(c)]
ths_now = [c for c in re.findall(r'<th[^>]*class="([^"]*)"', SRC)
           if util.search(c)]
ok(len(ths_was) > 0 and ths_now == ths_was,
   'and all %d <th> the removed rules could reach still carry the '
   'Bootstrap class that now does the work' % len(ths_now),
   'was %d, now %d - the round touched markup, which it must not have'
   % (len(ths_was), len(ths_now)))
print('      %d of the page\'s %d <th> carry a text-* utility; the other '
      '%d were never matched' % (len(ths_now),
                                 len(re.findall(r'<th[^>]*class="', SRC)),
                                 len(re.findall(r'<th[^>]*class="', SRC))
                                 - len(ths_now)))

DEAD = re.compile(r'\.[\w-]+-table\s+th\.text-(?:left|center|right)\s*\{')
ok(len(DEAD.findall(css_of(old_live))) == 15,
   '  the page really did restate them 15 times',
   '%d found' % len(DEAD.findall(css_of(old_live))))
ok(not DEAD.findall(css_of(live)), '  and restates them no more')

# ==========================================================================
head('5. the twenty-five that were NOT proved dead')

imp_was = len(re.findall(r'!important', css_of(old_live)))
imp_now = len(re.findall(r'!important', css_of(live)))
ok(imp_was == 39, 'the page carried 39 !important flags', imp_was)
ok(imp_now == 25,
   'and carries 25 - the 14 that went were on the 15 dead rules',
   '%d now, expected 25' % imp_now)
print('      The other 25 are NOT a claim. Dropping each one and '
      'repainting')
print('      showed 19 changing nothing, but the fixture flattens this '
      'page\'s')
print('      {% for %} loops and draws a fraction of its rows - which can '
      'prove')
print('      a flag matters and cannot prove one does not. They stay.')

# ==========================================================================
head('6. the control - a live hex the census must catch')

if sync_playwright is None or not OLDRAW:
    print('  --    the control  (playwright missing)')
else:
    # Plant a literal in LIVE code - not in a comment, which is the whole
    # distinction section 3 turns on. The check must FAIL, not crash.
    planted = RAW.replace('.action-btn i { margin-right: 4px; }',
                          '.action-btn i { margin-right: 4px; color: #ff00ff; }',
                          1)
    ok(planted != RAW, 'the control could be planted')
    caught = re.findall(r'#[0-9a-fA-F]{3,8}\b', alv_tree.code_only(planted))
    ok(bool(caught), 'and the census catches a literal in live code',
       'it did not - then section 3 proves nothing')
    # AND THE COMMENT CASE, the other way round: a literal added to a
    # COMMENT must NOT be caught, or section 3 would fail on prose.
    inprose = RAW.replace('/* THE COLUMN COUNT IS ALL THAT IS LEFT TO SAY',
                          '/* a note mentioning #ff00ff\n   THE COLUMN COUNT '
                          'IS ALL THAT IS LEFT TO SAY', 1)
    ok(inprose != RAW, '  and a literal could be planted in a comment too')
    ok('#ff00ff' not in alv_tree.code_only(inprose),
       '  which the census correctly does NOT count',
       'it counted a comment - section 3 would fail on another round\'s '
       'record of its own finding')
    ok(not re.findall(r'#[0-9a-fA-F]{3,8}\b', alv_tree.code_only(RAW)),
       '  and the page itself is clean again')

# ==========================================================================
head('7. registration')

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
print('  NOT PROVED HERE: that the 25 surviving !important flags are')
print('  needed. Nineteen of them changed nothing when dropped, but a')
print('  fixture with a fraction of the rows cannot prove a negative.')
print('  They are a question for a round that can render the real page.')
