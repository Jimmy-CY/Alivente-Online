# -*- coding: utf-8 -*-
"""test_named_bars.py - Section E round E3b, 25 Sep 2026.

Judges the round that took the last four action bars off names of their
own: two page bars onto .page-action-buttons, two mobile row grids onto
.mobile-action-bar.

THE SURVEY FOR THIS ROUND WAS WRONG TWICE, AND BOTH WERE MEASUREMENT
ERRORS, SO THIS SUITE MEASURES.

  1. It read the icon contrast against the HOVER tile instead of the
     resting one, and reported two failures that were not the two real
     ones.
  2. It said base defines no .icon-color-* rules. base defines twelve.

Section 2 renders the pages and reads the boxes and the colours out of the
browser.
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
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_namedbars'
ME = 'test_named_bars.py'
PATCHER = 'apply_named_bars.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')

BARS = ('preview-action-bar', 'recipe-action-bar',
        'contact-action-bar-mobile', 'event-action-bar-mobile')
TOKEN = re.compile(r'(?<![\w-])\.(%s)(?![\w-])' % '|'.join(BARS))
FILES = {
    'preview_imported_recipe.html': (6, 0, 1),
    'view_recipe.html': (9, 0, 1),
    'celebration_management.html': (19, 1, 2),
}
PAGE_BARS = ('preview_imported_recipe.html', 'view_recipe.html')
GRIDS = 'celebration_management.html'
KEEP_SEL = ('.contact-card.compact-view:not(.expanded) .mobile-action-bar')
ICON_BAR = 3.0          # icons are non-text: the bar is 3:1, not 4.5:1
TAP = 44
PHONE = 390

CSS_COMMENT = re.compile(r'/\*.*?\*/', re.S)
HTML_COMMENT = re.compile(r'<!--.*?-->', re.S)
CLASSATTR = re.compile(r'class="([^"]*)"')

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
    return HTML_COMMENT.sub('', CSS_COMMENT.sub('', t))


def wears(t, name):
    """By EXACT class token. base's standards block records what a
    substring count costs: 26 where the answer was seven."""
    return sum(1 for m in CLASSATTR.finditer(t) if name in m.group(1).split())


# THE MODAL CONDITIONAL. view_recipe hides its whole top button group with
#     {% if request.GET.modal %}
#     .recipe-detail-container > div:first-of-type { display: none !important; }
#     {% endif %}
# Stripping a conditional's TAGS but keeping its BODY applies that rule
# always, and the first render of this page came back empty - one step
# from "the recipe action bar is invisible on phones", which is false.
# STRIPPING A CONDITIONAL IS NOT EVALUATING IT FALSE. The body goes too.
MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I)]


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    b = re.sub(r'<!--.*?-->', '', b, flags=re.S)
    b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
    b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)


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
    """An unpainted element is not a black one (lesson 44)."""
    m = re.match(r'^rgba\(([^)]*)\)$', s.strip().lower())
    if not m:
        return s
    v = [float(x) for x in re.findall(r'-?[\d.]+', m.group(1))]
    if len(v) < 4 or v[3] >= 1:
        return s
    a = v[3]
    return 'rgb(%d, %d, %d)' % tuple(
        round(v[i] * a + PAPER[i] * (1 - a)) for i in range(3))


# ==========================================================================
head('1. THE SOURCE - FOUR NAMES GONE, ONE RULE KEPT, ONE LINE OF BASE')
# ==========================================================================
ok(as_left_by is not None, 'alv_rounds imported')
ok(SUFFIX in ROUNDS and '.bak_actionbar' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_actionbar'),
   'alv_rounds lists %s after .bak_actionbar' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else '')

# ASKED OF THE WHOLE FILE, NOT OF THE STYLESHEET.
# The first version of this check tested `wears(cur, bar) or
# TOKEN.search(cur)` - and TOKEN.search ignores `bar`, so it reported the
# first name in the list whatever it found. That bug is the only reason
# this round did not ship broken: it fired on celebration_management,
# where two `card.querySelector('.contact-action-bar-mobile')` calls were
# still live because the patcher rewrote CSS and markup and never touched
# <script>. A class name lives in THREE places. Ask about all three.
missing, leftovers = [], []
for name in sorted(FILES):
    p = os.path.join(T, name)
    if not os.path.isfile(p + SUFFIX):
        missing.append(name)
    cur = uncommented(now(p))
    for bar in BARS:
        if bar in cur:
            where = []
            if wears(cur, bar):
                where.append('a class attribute')
            if re.search(r'(?<![\w-])\.%s(?![\w-])' % bar, cur):
                where.append('a selector')
            scripts = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>',
                                            cur, re.S | re.I))
            if bar in scripts:
                where.append('a SCRIPT')
            leftovers.append('%s: %s (in %s)'
                             % (name, bar, ', '.join(where) or 'prose'))
ok(not missing, 'every changed file has its %s backup - the backups ARE '
   'the delivery (lesson 32)' % SUFFIX, '\n'.join(missing))
ok(not leftovers, 'not one of the four local bar names survives anywhere '
   'in these files - selector, class attribute OR script',
   '\n'.join(leftovers))

# The whole tree, so a name cannot come back somewhere else.
loose = []
for d, _x, fs in os.walk(T):
    for f in sorted(fs):
        if not f.endswith('.html') or '.bak' in f:
            continue
        rel = os.path.relpath(os.path.join(d, f), T).replace('\\', '/')
        t = uncommented(now(os.path.join(d, f)))
        for bar in BARS:
            if bar in t:
                loose.append('%s: %s' % (rel, bar))
ok(not loose, 'and no template anywhere else carries one either',
   '\n'.join(loose))

pv = now(os.path.join(T, 'preview_imported_recipe.html'))
ok("{% if mode != 'edit' %} page-action-buttons-single" in pv,
   "the preview bar's conditional is INVERTED - -single is the "
   'NO-primary case, as its two existing users show')
ok('has-primary' not in pv, '  and has-primary is gone')

cm = now(os.path.join(T, GRIDS))
ok(wears(cm, 'mobile-action-bar') == 2,
   'both celebration grids wear the house grid')
ok('mobile-action-bar cols-2' in cm,
   '  and the two-column one takes base\'s .cols-2 rather than its own '
   'grid-template')
ok("card.querySelector('[data-actions=\"contact\"]')" in cm,
   'the script identifies the contact grid by DATA ATTRIBUTE - both grids '
   'are .mobile-action-bar now, and the first one in the card is the '
   'EVENT grid, so the old query would have hidden the wrong element')
# COUNTED IN THE MARKUP, NOT IN THE FILE. `data-actions=` appears four
# times - twice on the grids and twice inside the script that queries
# them - so counting the string counts the question and the answer. The
# scripts come out first. (This is the same mistake as the substring
# count base warns about, one layer down: a token means different things
# in different contexts, so say which context you mean.)
cm_markup = re.sub(r'<script[^>]*>.*?</script>', '', cm, flags=re.S | re.I)
ok(cm_markup.count('data-actions=') == 2,
   '  and both grids carry the hook, so the pair is self-describing',
   cm_markup.count('data-actions='))
ok(KEEP_SEL in ' '.join(cm.split()),
   'the one KEPT rule is re-scoped, not deleted')
print('        a collapsed card hides its actions - this page\'s '
      'behaviour, not the grid\'s')

b_now, b_was = now(BASE), was(BASE)
ok(os.path.isfile(BASE + SUFFIX), 'base.html has its backup')
ok('.icon-color-add' in b_now and '.icon-color-add' not in b_was,
   'base gained .icon-color-add - the member its own family was missing')
# SPLIT AND INDEX [1] CRASHES WHEN THE THING IS ABSENT, and the thing is
# absent in exactly the run that matters - the revert test. A crash blocks
# a push as hard as a failure and says far less about why, so a check that
# asks "is X right" must survive X not being there at all.
_add = re.search(r'\.icon-color-add\s*\{([^{}]*)\}', b_now)
ok(bool(_add) and 'var(--alv-good)' in _add.group(1),
   '  valued like its sibling .icon-color-approve',
   _add.group(1)[:50] if _add else 'no .icon-color-add rule at all')
# ONE line, and the suite proves it is the only one.
diff = [l for l in b_now.split('\n') if l not in b_was.split('\n')]
ok(len([l for l in diff if l.strip() and not l.strip().startswith(('/*', '*', '-add.', 'with it;'))]) <= 1,
   'base changed by ONE rule and nothing else - E3 changed none, and a '
   'round that touches base must show exactly what it touched',
   '\n'.join(diff[:6]))
for other in ('.icon-color-edit', '.icon-color-delete', '.mobile-action-bar',
              '.page-action-buttons-single'):
    ok(other in b_now, '  base still defines %s' % other)

# ==========================================================================
head('2. RENDERED - THE ICONS AND THE CONTROLS, BEFORE AND AFTER')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'
LOOK = r"""(sel) => {
  const out = [], seen = new Set();
  document.querySelectorAll(sel).forEach(bar => {
    if (getComputedStyle(bar).display === 'none') return;
    bar.querySelectorAll('a, button, .btn, .mobile-action-btn').forEach(el => {
      if (seen.has(el)) return; seen.add(el);
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) return;
      const ic = el.querySelector('.mobile-action-icon');
      out.push({h: Math.round(r.height),
                bg: getComputedStyle(el).backgroundColor,
                ink: ic ? getComputedStyle(ic).color : '',
                off: el.classList.contains('mobile-action-disabled'),
                cls: ic ? ic.className.slice(0, 40) : el.className.slice(0, 30),
                t: (el.innerText || '').trim().slice(0, 18)});
    });
  });
  return out;
}"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('section 2', 'playwright or %s missing' % BOOT)
else:
    boot = read(BOOT)
    n = [0]

    def look(br, base_css, page_css, markup, sel):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_nb_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write('<!doctype html><html><head><meta charset="utf-8">'
                    '<title>p</title><style>%s</style><style>%s</style>%s'
                    '</head><body class="has-sidebar"><div class="main-content'
                    ' with-sidebar">%s</div></body></html>'
                    % (boot, base_css,
                       ''.join('<style>%s</style>' % c for c in page_css),
                       markup))
        ctx = br.new_context(viewport={'width': PHONE, 'height': 900})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        r = pg.evaluate(LOOK, sel)
        ctx.close()
        return r

    WAS_SEL = {
        'preview_imported_recipe.html': '.preview-action-bar',
        'view_recipe.html': '.recipe-action-bar',
        GRIDS: '.contact-action-bar-mobile, .event-action-bar-mobile',
    }
    NOW_SEL = {
        'preview_imported_recipe.html': '.page-action-buttons',
        'view_recipe.html': '.page-action-buttons',
        GRIDS: '.mobile-action-bar',
    }
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        B_NOW = '\n'.join(styles_of(now(BASE)))
        B_WAS = '\n'.join(styles_of(was(BASE)))
        icon_bad_b, icon_bad_a = [], []
        off_b, off_a = [], []

        def c_off(e):
            try:
                return contrast(over_paper(e['bg']), e['ink'])
            except ValueError:
                return 0.0

        tap_bad_b, tap_bad_a = [], []
        seen_b = seen_a = icons_b = icons_a = 0
        unread = []
        for name in sorted(FILES):
            p = os.path.join(T, name)
            rows_a = look(br, B_NOW, styles_of(now(p)), body_markup(now(p)),
                          NOW_SEL[name])
            rows_b = look(br, B_WAS, styles_of(was(p)), body_markup(was(p)),
                          WAS_SEL[name])
            for rows, tapbad, iconbad, which in (
                    (rows_b, tap_bad_b, icon_bad_b, 'before'),
                    (rows_a, tap_bad_a, icon_bad_a, 'after')):
                for e in rows:
                    if which == 'before':
                        seen_b += 1
                    else:
                        seen_a += 1
                    if e['h'] < TAP:
                        tapbad.append('%-30s %-18s %dpx'
                                      % (name[:30], e['t'] or '(icon)',
                                         e['h']))
                    if not e['ink']:
                        continue
                    # A DISABLED CONTROL IS EXEMPT. WCAG 1.4.3 and 1.4.11
                    # both exclude inactive components, and the house has
                    # a token for exactly this - --alv-ink-faint - whose
                    # whole job is to look unavailable. Counting them made
                    # five "failures" that all measured an identical 2.85,
                    # which is what gave the miscount away: a real spread
                    # of colours does not land on one number.
                    if e['off']:
                        if which == 'before':
                            off_b.append(c_off(e))
                        else:
                            off_a.append(c_off(e))
                        continue
                    if which == 'before':
                        icons_b += 1
                    else:
                        icons_a += 1
                    try:
                        c = contrast(over_paper(e['bg']), e['ink'])
                    except ValueError as err:
                        unread.append(str(err))
                        continue
                    if c < ICON_BAR:
                        iconbad.append('%-28s %-26s %.2f'
                                       % (name[:28], e['cls'][:26], c))
        br.close()

    ok(not unread, 'every colour measured was one the parser understands '
       '(lesson 41)', '\n'.join(unread[:4]))
    print('')
    print('      BEFORE  %d control(s), %d under %dpx; %d icon(s), %d '
          'below %.1f:1' % (seen_b, len(tap_bad_b), TAP, icons_b,
                            len(icon_bad_b), ICON_BAR))
    for x in icon_bad_b[:5]:
        print('         %s' % x)
    for x in tap_bad_b[:4]:
        print('         %s' % x)
    print('      AFTER   %d control(s), %d under %dpx; %d icon(s), %d '
          'below %.1f:1' % (seen_a, len(tap_bad_a), TAP, icons_a,
                            len(icon_bad_a), ICON_BAR))
    for x in icon_bad_a[:5]:
        print('         %s' % x)
    for x in tap_bad_a[:4]:
        print('         %s' % x)
    print('')
    ok(seen_b > 0, 'the before-render found controls - a measurement of '
       'nothing passes for free, and this page produced exactly that once')
    ok(seen_a > 0, 'the after-render found controls')
    ok(icons_b > 0 and icons_a > 0, 'and it found the grid icons on both '
       'sides', 'before %d, after %d' % (icons_b, icons_a))
    ok(len(icon_bad_b) > 0, 'the round had icon contrast to fix: %d below '
       '%.1f:1 before it' % (len(icon_bad_b), ICON_BAR))
    ok(not icon_bad_a, 'NO icon is below %.1f:1 any more' % ICON_BAR,
       '\n'.join(icon_bad_a))
    if off_b and off_a:
        print('      DISABLED icons, exempt but reported: %.2f before -> '
              '%.2f after (the house --alv-ink-faint)'
              % (min(off_b), min(off_a)))
    ok(min(off_a) >= min(off_b) if (off_a and off_b) else True,
       'and the disabled icons, though exempt, did not get fainter')
    ok(len(tap_bad_a) <= len(tap_bad_b),
       'and the round did not make any tap target smaller',
       'before %d, after %d' % (len(tap_bad_b), len(tap_bad_a)))

# ==========================================================================
head('3. CONTROLS - checks that would catch a vacuous suite')
# ==========================================================================
ok(sum(v[0] for v in FILES.values()) == 34,
   'the survey total is 34 deleted rules',
   sum(v[0] for v in FILES.values()))
ok(len(FILES) == 3, 'three templates, plus one line of base')
ok(TOKEN.search('.recipe-action-bar .btn') is not None,
   'the selector pattern matches a real local bar')
ok(TOKEN.search('.page-action-buttons .btn') is None,
   '  and does not match the house container')
ok(wears('<div class="mobile-action-bar cols-2">', 'mobile-action-bar') == 1,
   'the token counter reads the house grid')
ok(wears('<div class="contact-action-bar-mobile">', 'mobile-action-bar') == 0,
   '  and is not fooled by a name that merely contains it')
ok(MODAL_IF.sub('', '{% if request.GET.modal %}X{% endif %}Y') == 'Y',
   'the modal conditional is dropped BODY AND ALL - stripping only its '
   'tags is what hid the recipe bar in every render')
ok(round(contrast('#ffc107', '#f8f9fa'), 2) == 1.55,
   'the amber icon really did measure 1.55 on the resting tile',
   round(contrast('#ffc107', '#f8f9fa'), 2))
ok(round(contrast('#dc3545', '#f8f9fa'), 2) == 4.30,
   '  and the red one was never failing - the survey said it was',
   round(contrast('#dc3545', '#f8f9fa'), 2))

tt = os.path.join(ROOT, 'test_tap_target.py')
if os.path.isfile(tt):
    ttx = read(tt)
    ok(os.path.isfile(tt + SUFFIX), 'test_tap_target.py has its backup')
    ok('DONE_OWN_ROUND' in ttx,
       'test_tap_target no longer holds celebration_management "untouched '
       'until its own round" - this was that round')
    ok('56px' in ttx,
       '  and it records WHY the page stopped declaring 44px: base gives '
       '56, which is larger than what the local rules declared')

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
