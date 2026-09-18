"""test_admin_banner.py - the module heading is not inside anything that
   paints or lays out, and the buttons are on one bar.

    python test_admin_banner.py

Run from the repo root, after apply_admin_banner.py.

WHAT THIS SUITE CANNOT DO, SAID FIRST

It cannot tell you these screens are finished. The panel title on eleven of
them is still a bare <h2>, and the two tables on user_administration and
workspace_management have not been near the table standard. This suite is
about the header and the bar.

SECTION 2 IS THE ONE THAT EARNS ITS KEEP, and it is a POSITION check, not
a class check - because a class check is exactly what let this through.
Stage B asked "does the heading carry .page-title-h2" and eight screens
said yes while sitting inside a purple flex row that put the mode line
beside the module name, at a contrast ratio of 1.01:1.

The rule it enforces is not "the heading is inside nothing". All eight of
these sit inside a max-width layout container and so does
finance_expense_add, which renders correctly. The rule is that no container
around the heading may PAINT (a background or a gradient) or LAY OUT (a
flex or a grid) - because base styles the heading as a centred BLOCK, and a
flex row turns three stacked blocks into three items on one line.

SECTION 5 MEASURES THE DEFECT ITSELF, and its control builds the old banner
from a literal in this file, so the day the check can no longer see the
fault the control fails rather than the suite quietly passing. I FIRST
CALLED THIS AN OVERLAP. It is not one - measured, the banner lays the three
blocks side by side and they never intersect. The fault is that the mode
line sits BESIDE the module name instead of under it, at 1.01:1 against the
purple, which is what makes a screenshot look like a collision.

A SKIPPED CHECK IS COUNTED IN THE SUMMARY.
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

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
ME = os.path.basename(__file__)

ADMIN = re.compile(r'(^|/)(user_|workspace_|admin_|permission)|'
                   r'(^|/)(notification_settings|help_page|database_error)')
PERSONAL = re.compile(r'(^|/)(my_profile|personal_)')
RECIPE = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
          'unit_conversions', 'celebration_', 'import_recipe',
          'map_ingredients', 'measurement_units', 'household_member',
          'categories_management')

DEAD = ('page-header', 'header-actions')
AVATAR_SELECTORS = ('.user-avatar', '.member-avatar', '.photo-placeholder')
PURPLE = re.compile(r'#667eea|#764ba2', re.I)
BACK_RE = re.compile(r'(?<![-\w])action-back(?![-\w])')

VOID = {'input', 'br', 'img', 'hr', 'meta', 'link', 'source', 'area',
        'base', 'col', 'embed', 'param', 'track', 'wbr'}

# ONE BAR PER PAGE. my_profile was listed here with two and a reason, and
# the reason was wrong: apply_button_sweep's rule is "no page renders its
# actions twice" and the push gate rejected it as `two sets of verbs`. A
# page with two sets of verbs does not say which one commits. Its Save now
# sits in the one bar, like every other entry screen in this round.
BARS_EXPECTED = {'help_page.html': 0}

# And the reason each exception has, printed rather than assumed.
BARS_WHY = {
    'help_page.html': 'its actions live in a page-local .help-hero-actions - '
                      'the hero is its own round, not this one',
}

PASS = FAIL = SKIP = 0
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


def skip(name, why):
    global SKIP
    SKIP += 1
    print('  SKIP  %s - %s' % (name, why))


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def inert(text):
    out = re.sub(r'<(script|style)\b[^>]*>.*?</\1>',
                 lambda m: ' ' * len(m.group(0)), text, flags=re.S | re.I)
    return re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), out,
                  flags=re.S)


def nocomment(css):
    return re.sub(r'/\*.*?\*/', ' ', css, flags=re.S)


def split_rules(css):
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find('{', i)
        if j < 0:
            break
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == '{':
                depth += 1
            elif css[k] == '}':
                depth -= 1
            k += 1
        out.append((css[i:j], j, k))
        i = k
    return out


def rules_of(css):
    """(selector, declarations) for every rule, @media bodies included."""
    out = []
    for sel, b, c in split_rules(css):
        bare = ' '.join(nocomment(sel).split())
        if bare.startswith('@'):
            out.extend(rules_of(css[b + 1:c - 1]))
        else:
            out.append((bare, css[b + 1:c - 1]))
    return out


def page_css(text):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', text, re.S))


def admin_pages():
    out = []
    for dirpath, _d, names in os.walk(T):
        for n in sorted(names):
            if not n.endswith('.html') or '.bak' in n:
                continue
            rel = os.path.relpath(os.path.join(dirpath, n), T)
            rel = rel.replace(os.sep, '/')
            if ADMIN.search(rel) or PERSONAL.search(rel):
                out.append((rel, os.path.join(dirpath, n)))
    return sorted(out)


def all_pages():
    out = []
    for dirpath, _d, names in os.walk(T):
        for n in sorted(names):
            if not n.endswith('.html') or '.bak' in n:
                continue
            rel = os.path.relpath(os.path.join(dirpath, n), T)
            rel = rel.replace(os.sep, '/')
            if rel == 'base.html' or any(r in rel for r in RECIPE):
                continue
            out.append((rel, os.path.join(dirpath, n)))
    return sorted(out)


def ancestors_of_heading(text):
    """Every container the module heading sits inside, with whatever the
       page's own CSS declares for it."""
    scan = inert(text)
    c = scan.find('{% block content %}')
    h = re.search(r'<h[1-6][^>]*class="[^"]*\bpage-title-h2\b', scan)
    if c < 0 or h is None:
        return None
    css = page_css(text)
    stack = []
    for x in re.finditer(r'<(/?)(\w+)([^>]*?)(/?)>', scan[c:h.start()]):
        cl, nm, attrs, sc = x.groups()
        nm = nm.lower()
        if nm in VOID or sc or nm in ('body', 'html'):
            continue
        if cl:
            if stack:
                stack.pop()
        else:
            k = re.search(r'class="([^"]*)"', attrs)
            stack.append((nm, k.group(1).split() if k else []))
    out = []
    for nm, classes in stack:
        decls = []
        for sel, body in rules_of(css):
            for part in sel.split(','):
                if any(part.strip() == '.' + cl for cl in classes):
                    decls.append(body)
        name = ('<%s class="%s">' % (nm, ' '.join(classes))) if classes \
            else '<%s>' % nm
        out.append((name, ' '.join(' '.join(decls).split())))
    return out


# A value that paints nothing. `background: transparent` on a wrapper is
# not a banner, and a rule that called it one would fail on half the system.
BLANK = re.compile(r'^(none|transparent|inherit|initial|unset|0)$', re.I)


def paints_or_lays_out(decls):
    """The one rule this round is about, in one function so section 2 and
       its control cannot drift apart."""
    for m in re.finditer(r'(?<![-\w])(background(?:-color|-image)?|display)'
                         r'\s*:\s*([^;]+)', decls):
        prop, v = m.group(1), m.group(2).strip()
        if prop == 'display':
            if not re.match(r'flex|grid|inline-flex', v):
                continue
        elif BLANK.match(v):
            continue
        return '%s: %s' % (prop, v[:30])
    return None


if not os.path.isdir(T):
    print('! %s not found - run from the repo root' % T)
    sys.exit(1)

ADMIN_ALL = [(rel, read(p)) for rel, p in admin_pages()]
B = read(BASE)

# ---------------------------------------------------------------------- 1
head('1. THE PAGE-LOCAL BANNER IS GONE FROM THESE MODULES')

left = []
for rel, t in ADMIN_ALL:
    for d in DEAD:
        n = len(re.findall(r'(?<![-\w])%s(?![-\w])' % d, nocomment(t)))
        if n:
            left.append('%s: %d x %s' % (rel, n, d))
for x in left[:6]:
    print('        %s' % x)
check('no Administration or Personal screen declares its own page header',
      not left, '%d do' % len(left))
check('  CONTROL: and there are screens to have missed',
      len(ADMIN_ALL) >= 8, '%d screen(s)' % len(ADMIN_ALL))
# The word is searched OUTSIDE comments - base's own notes name retired
# classes, and "is the string still there" has found the explanation
# rather than the defect three times in this project.
check('  CONTROL: the search ignores comments',
      len(re.findall(r'(?<![-\w])page-header(?![-\w])',
                     nocomment('/* page-header */ .x{}'))) == 0)

# ---------------------------------------------------------------------- 2
head('2. NO CONTAINER AROUND A MODULE HEADING PAINTS OR LAYS OUT')

bad, checked = [], 0
for rel, path in all_pages():
    anc = ancestors_of_heading(read(path))
    if anc is None:
        continue
    checked += 1
    for name, decls in anc:
        why = paints_or_lays_out(decls)
        if why:
            bad.append('%s: %s sets %s' % (rel, name[:34], why))
for x in bad[:8]:
    print('        %s' % x)
check('no module heading sits inside a container that paints or lays out',
      not bad, '%d do' % len(bad))
check('  CONTROL: and the rule ran on the whole system, not these eight',
      checked >= 40, '%d page(s) carry a module heading' % checked)
# THE CHECK CAN SEE A BANNER, proved on literals rather than on the repo,
# so it cannot go vacuous the day the repo is clean.
check('  CONTROL: the rule catches a gradient, a flex and nothing else',
      paints_or_lays_out('background: linear-gradient(135deg,#667eea,#764ba2)')
      is not None
      and paints_or_lays_out('display: flex; gap: 8px') is not None
      and paints_or_lays_out('background-color: #667eea') is not None
      and paints_or_lays_out('max-width: 700px; margin: 0 auto;'
                             ' padding: 0 8px') is None
      and paints_or_lays_out('background: transparent') is None
      and paints_or_lays_out('display: block') is None)

# ---------------------------------------------------------------------- 3
head('3. ONE BAR, AND BACK IS ON IT')

for rel, t in ADMIN_ALL:
    if not re.search(r'class="[^"]*\bpage-title-h2\b', inert(t)):
        continue
    want = BARS_EXPECTED.get(rel, 1)
    bars = len(re.findall(r'<div\b[^>]*class="[^"]*\bpage-action-buttons\b',
                          inert(t)))
    if bars != want:
        print('        %-28s %d bar(s), expected %d' % (rel[:28], bars, want))
check('every screen here has the number of action bars it should',
      all(len(re.findall(r'<div\b[^>]*class="[^"]*\bpage-action-buttons\b',
                         inert(t))) == BARS_EXPECTED.get(rel, 1)
          for rel, t in ADMIN_ALL
          if re.search(r'class="[^"]*\bpage-title-h2\b', inert(t))))
print('        the exception is named, with its reason:')
for rel, n in sorted(BARS_EXPECTED.items()):
    print('          %-24s %d bar(s) - %s' % (rel[:24], n, BARS_WHY[rel]))
check('  every exception has a reason read off the page',
      all(rel in BARS_WHY for rel in BARS_EXPECTED))

naked = []
for rel, t in ADMIN_ALL:
    for m in re.finditer(r'<a\b[^>]*\bclass="[^"]*(?<![-\w])action-back'
                         r'(?![-\w])[^"]*"[^>]*>(.*?)</a>', inert(t), re.S):
        if 'action-back-label' not in m.group(1):
            naked.append(rel)
check('  every Back wraps its word in .action-back-label', not naked,
      '%d do not: %s' % (len(naked), ', '.join(naked[:3])))
print('        base squeezes Back to 44px below 768px and hides that span;')
print('        a bare text node has nothing to hide and overflows.')

# A SECONDARY DISAPPEARS ON A PHONE when a More menu carries the others.
# Any button left as a secondary in a bar that HAS a menu must actually be
# in that menu.
lost = []
for rel, t in ADMIN_ALL:
    s = inert(t)
    for m in re.finditer(r'<div\b[^>]*class="[^"]*\bpage-action-buttons\b'
                         r'[^"]*"[^>]*>(.*?)\n\s*</div>', s, re.S):
        bar = m.group(1)
        if 'action-more-btn' not in bar:
            continue
        menu = ''.join(re.findall(r'class="action-more-item"[^>]*>(.*?)<',
                                  bar, re.S))
        for b in re.finditer(r'class="btn action-secondary"[^>]*>(.*?)</',
                             bar, re.S):
            word = ' '.join(re.sub(r'<[^>]+>', ' ', b.group(1)).split())
            if word and word not in menu:
                lost.append('%s: %s' % (rel, word))
check('  no secondary vanishes below 768px with nothing carrying it',
      not lost, '%d would: %s' % (len(lost), '; '.join(lost[:3])))

# ---------------------------------------------------------------------- 4
head('4. THE PURPLE IS THE AVATAR, AND THE TEST IS THE SELECTOR')

borrowed, kept = [], []
for rel, t in ADMIN_ALL:
    for sel, body in rules_of(page_css(t)):
        n = len(PURPLE.findall(body))
        if not n:
            continue
        if any(s in sel for s in AVATAR_SELECTORS):
            kept.append('%s %s x%d' % (rel, sel[:22], n))
        else:
            borrowed.append('%s: %s' % (rel, sel[:40]))
    body = re.sub(r'<style[^>]*>.*?</style>', ' ', t, flags=re.S)
    if PURPLE.search(body):
        borrowed.append('%s: in the markup' % rel)
for x in borrowed[:6]:
    print('        %s' % x)
check('purple survives only where the selector says avatar', not borrowed,
      '%d elsewhere' % len(borrowed))
for x in kept:
    print('        kept: %s' % x)
check('  CONTROL: and the avatars were not swept away with the banner',
      len(kept) >= 3, '%d rule(s)' % len(kept))
# STAGE A JUDGED THIS BY PROXIMITY - a #667eea within 90 characters of a
# #764ba2 was "the avatar" - and the banner gradient is that pair written
# out, so all sixteen banner values were spared. The selector is the test.
check('  CONTROL: proximity would have called the banner an avatar',
      PURPLE.search('linear-gradient(135deg, #667eea 0%, #764ba2 100%)')
      is not None)

# ---------------------------------------------------------------------- 5
head('5. RENDERED - the mode line is UNDER the module line, and legible')

# I FIRST CALLED THIS AN OVERLAP AND IT IS NOT ONE. Measured, the banner
# puts the three blocks SIDE BY SIDE - h2 at x 625-911, h4 at x 995-1118 -
# so they never intersect. What makes it look like a collision in a
# screenshot is the second fault: --alv-ink-soft on the purple is
# 1.01:1 against AA's 4.5, so the mode line and Back are all but invisible
# and read as smears over the module name. This section checks the two
# things that are true: the lines STACK, and every one of them is legible.

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


def luminance(rgb):
    c = [v / 255.0 for v in rgb]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
         for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(fg, bg):
    a, b_ = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (a + 0.05) / (b_ + 0.05)


def rgb(s):
    n = [int(x) for x in re.findall(r'\d+', s)[:3]]
    return n if len(n) == 3 else [0, 0, 0]


BANNER = ("<div class='user-form-container'>"
          "<div style='background:linear-gradient(135deg,#667eea 0%,"
          "#764ba2 100%);color:#fff;padding:20px 25px;border-radius:10px;"
          "display:flex;justify-content:space-between;align-items:center'>"
          "<h2 class='page-title-h2' id=h2>USER ADMINISTRATION</h2>"
          "<h4 class='page-subtitle-h4' id=h4>ADD NEW USER</h4>"
          "<a class='btn action-back' id=bk>Back</a></div></div>")

HOUSE = ("<div class='user-form-container'>"
         "<h2 class='page-title-h2' id=h2>USER ADMINISTRATION</h2>"
         "<h4 class='page-subtitle-h4' id=h4>ADD NEW USER</h4><br/>"
         "<div class='page-action-buttons'>"
         "<button class='btn action-primary'>Create User</button>"
         "<a class='btn action-back' id=bk>"
         "<span class='action-back-label'>Back</span></a></div></div>")

WRAP = '.user-form-container{max-width:700px;margin:0 auto}'

if sync_playwright is None:
    skip('the mode line sits under the module line', 'playwright not installed')
    skip('every line in the header is legible where it sits', 'ditto')
else:
    cut = B.find('{% block content %}')
    pre, post = [], []
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', B, re.S):
        (pre if m.end(1) < cut else post).append(m.group(1))

    def probe(body):
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page(viewport={'width': 1900, 'height': 500})
            pg.route('**://**', lambda r: r.abort())
            pg.set_content(
                "<!doctype html><meta charset=utf-8><style>%s</style>"
                "<style>%s</style>%s<style>%s\n*{transition:none!important}"
                "</style>" % ('\n'.join(pre), WRAP, body, '\n'.join(post)),
                wait_until='load')
            out = pg.evaluate("""() => ['h2','h4','bk'].map(i => {
                const e = document.getElementById(i);
                const r = e.getBoundingClientRect();
                const s = getComputedStyle(e);
                let n = e, bg = 'rgba(0, 0, 0, 0)';
                while (n && n !== document.documentElement) {
                    const c = getComputedStyle(n);
                    const v = c.backgroundImage !== 'none'
                            ? c.backgroundImage : c.backgroundColor;
                    if (v && v !== 'rgba(0, 0, 0, 0)') { bg = v; break; }
                    n = n.parentElement;
                }
                return {top: r.top, bottom: r.bottom, left: r.left,
                        right: r.right, color: s.color, bg: bg};
            })""")
            br.close()
        return out

    def stacked(p):
        return p[1]['top'] >= p[0]['bottom'] - 1

    try:
        house, banner = probe(HOUSE), probe(BANNER)

        check('the mode line sits UNDER the module line, not beside it',
              stacked(house),
              'module ends y=%.0f, mode starts y=%.0f'
              % (house[0]['bottom'], house[1]['top']))
        # THE CONTROL IS THE OLD BANNER, BUILT FROM A LITERAL ABOVE. If it
        # ever passes, this check can no longer see what it exists for.
        check('  CONTROL: and the banner really did put them side by side',
              not stacked(banner),
              'module x %.0f-%.0f, mode x %.0f-%.0f'
              % (banner[0]['left'], banner[0]['right'],
                 banner[1]['left'], banner[1]['right']))

        # LEGIBILITY. A gradient background reports as an image, not a
        # colour, so it is read from the declared stops instead of guessed.
        def ratio(el):
            bg = el['bg']
            if 'gradient' in bg:
                stops = re.findall(r'rgba?\([^)]*\)', bg)
                if not stops:
                    return None
                vals = [contrast(rgb(el['color']), rgb(s)) for s in stops]
                return min(vals)
            if 'rgba(0, 0, 0, 0)' in bg:
                bg = 'rgb(255,255,255)'
            return contrast(rgb(el['color']), rgb(bg))

        dim = []
        for name, el in zip(('module', 'mode', 'Back'), house):
            r = ratio(el)
            if r is not None and r < 4.5:
                dim.append('%s %.2f:1' % (name, r))
        check('  every line in the header meets AA against what is behind it',
              not dim, '; '.join(dim) if dim else 'all >= 4.5:1')
        was = ['%s %.2f:1' % (n, ratio(e))
               for n, e in zip(('module', 'mode', 'Back'), banner)
               if ratio(e) is not None]
        print('        on the old banner it was: %s' % ', '.join(was))
        check('  CONTROL: and the banner really was illegible',
              any(ratio(e) is not None and ratio(e) < 4.5 for e in banner[1:]))
    except Exception as e:
        skip('the mode line sits under the module line',
             'the browser would not run: %s' % str(e)[:44])

# ---------------------------------------------------------------------- 6
head('6. RENDERED - the bar fits a 390px phone, and Back is an icon')

# THE CHECK WHOSE ABSENCE LET A BROKEN ROUND SHIP. Moving Back into
# .page-action-buttons put it under each page's OWN phone rules, and six of
# these pages carry `.page-action-buttons .btn { width: 100% }` in a phone
# block. It was harmless while the bar held one submit button. With Back in
# there it made Back 404px wide on a 390px screen and the page scrolled
# sideways - on six screens at once, and nothing in this suite looked.
#
# base LOSES that fight rather than winning it: base declares the bar at
# line 1703, BEFORE {% block content %} at line 2203, so a page-local copy
# at equal specificity comes later in the document and wins. That is the
# opposite way round from the form components, which base declares after
# the block - and it is exactly the kind of thing only a render can tell
# you.

if sync_playwright is None:
    skip('every bar fits a 390px phone', 'playwright is not installed')
else:
    def bar_of(text):
        s = inert(text)
        m = re.search(r'<div\b[^>]*class="[^"]*\bpage-action-buttons\b'
                      r'[^"]*"[^>]*>', s)
        if not m:
            return None
        d, j = 1, m.end()
        for x in re.finditer(r'<(/?)div\b[^>]*>', s[m.end():]):
            d += -1 if x.group(1) else 1
            if d == 0:
                j = m.end() + x.end()
                break
        return re.sub(r'\{%[^%]*%\}', '#', text[m.start():j])

    def phone(bar, own):
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page(viewport={'width': 390, 'height': 600})
            pg.route('**://**', lambda r: r.abort())
            pg.set_content(
                "<!doctype html><meta charset=utf-8><style>%s</style>"
                "<style>%s</style>%s<style>%s\n*{transition:none!important}"
                "</style>" % ('\n'.join(pre), own, bar, '\n'.join(post)),
                wait_until='load')
            out = pg.evaluate(
                "() => {"
                " const b = document.querySelector('.page-action-buttons');"
                " const vis = Array.from(b.children).filter("
                "   e => getComputedStyle(e).display !== 'none');"
                " const back = vis.find("
                "   e => e.classList.contains('action-back'));"
                " return {over: document.documentElement.scrollWidth > 390,"
                "   backW: back ? Math.round("
                "     back.getBoundingClientRect().width) : null,"
                "   wrap: getComputedStyle(b).flexWrap};"
                "}")
            br.close()
        return out

    wide, wrapped, done = [], [], 0
    for _rel, _t in ADMIN_ALL:
        _bar = bar_of(_t)
        if _bar is None:
            continue
        try:
            _o = phone(_bar, page_css(_t))
        except Exception as _e:
            skip('%s fits a 390px phone' % _rel, str(_e)[:40])
            continue
        done += 1
        if _o['over']:
            wide.append('%s scrolls sideways' % _rel)
        if _o['backW'] is not None and _o['backW'] > 48:
            wide.append('%s Back is %dpx' % (_rel, _o['backW']))
        if _o['wrap'] != 'nowrap':
            wrapped.append(_rel)
    for _x in wide[:6]:
        print('        %s' % _x)
    check('no action bar overflows a 390px phone, and Back stays an icon',
          not wide, '%d problem(s)' % len(wide))
    check('  the bar is told not to wrap', not wrapped,
          '%d wrap: %s' % (len(wrapped), ', '.join(wrapped[:3])))
    check('  CONTROL: and there were bars to measure', done >= 8,
          '%d bar(s) rendered' % done)

    # THE CONTROL THAT MATTERS: put the offending rule back, and the check
    # must fail. Without it this would go on passing the day it stopped
    # looking - which is the whole reason it exists.
    try:
        _probe = None
        for _r, _x in ADMIN_ALL:
            if _r == 'user_add.html':
                _probe = bar_of(_x)
        if _probe is None:
            skip('CONTROL: the page-local width rule is caught',
                 'user_add.html has no bar to probe')
        else:
            _hurt = phone(_probe,
                          '@media screen and (max-width: 768px){'
                          '.page-action-buttons .btn{width:100%}}')
            check('  CONTROL: a page-local width:100% on the bar IS caught',
                  _hurt['over'] or (_hurt['backW'] or 0) > 48,
                  'Back %spx, overflow %s' % (_hurt['backW'], _hurt['over']))
    except Exception as _e:
        skip('CONTROL: the page-local width rule is caught', str(_e)[:44])

# ---------------------------------------------------------------------- 7
head('7. IT IS ON THE GATE')

if not os.path.exists(PS1):
    check('Push-PendingChanges.ps1 is here', False, 'it is not')
else:
    check('this suite is on the gate', ME in read(PS1), ME)

# ---------------------------------------------------------------------- 8
print('\n' + '=' * 72)
print('  %d passed, %d failed, %d skipped' % (PASS, FAIL, SKIP))
if FAILED:
    print('')
    for f in FAILED:
        print('  - %s' % f)
if SKIP:
    print('')
    print('  %d check(s) DID NOT RUN. That is not the same as passing.' % SKIP)
print('')
print('  NOTED, NOT FIXED: workspace_management spells its Help button\'s')
print('  label .action-back-label. base only hides that span inside an')
print('  .action-back, so it is inert - a wrong name, not a wrong render.')
print('')
print('  STILL TO COME in these modules: the panel title on 11 screens,')
print('  and the two tables on user_administration and workspace_management.')
print('=' * 72)
sys.exit(1 if FAIL else 0)
