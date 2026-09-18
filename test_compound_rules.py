"""test_compound_rules.py - no page rule outranks base any more, and the
   screens that were overridden now render the standard.

    python test_compound_rules.py

Run from the repo root, after apply_compound_rules.py.

WHAT THIS SUITE CANNOT DO, SAID FIRST

It cannot tell you the standard is the right standard. It can tell you the
last screens are now on it.

SECTION 3 IS THE ONE THAT EARNS ITS KEEP, AND IT IS DIFFERENT FROM THE
EARLIER COMPONENT SUITES. Those could claim their deletions changed
nothing, because base already beat what they removed on document order.
A COMPOUND RULE IS NOT EQUAL: two classes beat one whatever the order, so
every deletion in this round DID change a page. Section 3 renders each
migrated screen's own stylesheet under base and reads the control back -
including the FOCUS state, which is the whole reason the red ring was
found in the first place and which no static read of the file can see.

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

import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
ME = os.path.basename(__file__)

RECIPE = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
          'unit_conversions', 'celebration_', 'import_recipe',
          'map_ingredients', 'measurement_units', 'household_member',
          'categories_management')

OWNED = {
    '.form-card': {'background', 'border', 'border-radius', 'padding',
                   'margin-bottom', 'box-shadow'},
    '.form-section-title': {'color', 'font-weight', 'margin',
                            'margin-top', 'margin-bottom'},
    '.form-group': {'margin-bottom'},
    '.form-group label': {'display', 'color', 'font-size', 'margin-bottom'},
    '.form-control': {'width', 'background', 'background-color', 'border',
                      'border-radius', 'padding', 'font-size', 'transition'},
    '.form-control:focus': {'border-color', 'box-shadow', 'outline'},
    '.form-text': {'font-size', 'color', 'margin-top'},
}

# The compound rules deliberately kept, each with its reason. NAMED,
# because a count cannot tell a new one from an old one.
KEEP = {
    '.vat-input-wrap .form-control':
        'it makes room for the VAT suffix, which base never claimed',
    '.prorata-panel .form-section-title':
        'the prorata warning panel titles itself in its own dark red',
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


def blank_comments(css):
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), css, flags=re.S)


def style_spans(text):
    return [(m.start(1), m.end(1))
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S)]


def rules_in(css, base=0):
    blanked = blank_comments(css)
    out = []

    def walk(lo, hi, media):
        i = lo
        while i < hi:
            at = blanked.find('@', i)
            brace = blanked.find('{', i)
            if brace < 0 or brace >= hi:
                return
            if 0 <= at < brace:
                depth, j = 1, brace + 1
                while j < hi and depth:
                    if blanked[j] == '{':
                        depth += 1
                    elif blanked[j] == '}':
                        depth -= 1
                    j += 1
                if blanked[at:brace].lstrip().startswith('@media'):
                    walk(brace + 1, j - 1, (base + at, base + j))
                i = j
                continue
            close = blanked.find('}', brace)
            if close < 0 or close >= hi:
                return
            k = i
            while k < brace and blanked[k] in ' \t\r\n':
                k += 1
            out.append((base + k, base + brace, base + brace + 1,
                        base + close, media))
            i = close + 1

    walk(0, len(css), None)
    return out


def sel_list(text, a, b):
    raw = re.sub(r'/\*.*?\*/', ' ', text[a:b], flags=re.S)
    return [' '.join(p.split()) for p in raw.split(',') if p.strip()]


def props_of(text, a, b):
    return {d.split(':', 1)[0].strip().lower()
            for d in text[a:b].split(';') if ':' in d}


def target_of(sel):
    parts = sel.split()
    if not parts:
        return None
    last = parts[-1]
    for k in ('.form-control:focus', '.form-control', '.form-card',
              '.form-section-title', '.form-group', '.form-text'):
        if last == k:
            return k
    if last == 'label' and len(parts) > 1 and parts[-2] == '.form-group':
        return '.form-group label'
    return None


def templates():
    out = []
    for dirpath, _d, names in os.walk(T):
        for n in sorted(names):
            if not n.endswith('.html'):
                continue
            path = os.path.join(dirpath, n)
            if os.path.abspath(path) == os.path.abspath(BASE):
                continue
            rel = os.path.relpath(path, T).replace(os.sep, '/')
            if any(t in rel for t in RECIPE):
                continue
            out.append((rel, path))
    return sorted(out)


if not os.path.isdir(T):
    print('! %s not found - run from the repo root' % T)
    sys.exit(1)

B = read(BASE)

# ---------------------------------------------------------------------- 1
head('1. ONE NAME FOR THE FIELD WRAPPER')

third = [rel for rel, p in templates()
         if re.search(r'(?<![-\w])form-field(?![-\w])', read(p))]
check('no page still wraps its fields in a third name', not third,
      '%d do: %s' % (len(third), ', '.join(third[:4])))
check('  CONTROL: and .form-group is genuinely in use',
      sum(1 for _r, p in templates()
          if 'form-group' in read(p)) >= 20)
check('base still declares the wrapper', '.form-group {' in B
      or re.search(r'\.form-group\s*\{', B) is not None)

# ---------------------------------------------------------------------- 2
head('2. NO PAGE RULE OUTRANKS BASE ANY MORE')

over, kept, foreign = [], [], []
for rel, path in templates():
    text = read(path)
    for a, b in style_spans(text):
        for (sa, sb, da, db, media) in rules_in(text[a:b], a):
            if media is not None:
                continue
            sels = sel_list(text, sa, sb)
            # ONLY RULES THAT TOUCH THESE COMPONENTS. Without this the
            # section reported 651 "rules targeting something base does not
            # own", which is simply every compound selector in the repo -
            # .page-header h1, .filter-label i, and so on. A report whose
            # number is that large is not a report about anything.
            if not any(re.search(r'(?<![-\w])\.(form-control|form-group'
                                 r'|form-card|form-text|form-section-title)'
                                 r'(?![-\w])', s) for s in sels):
                continue
            comp = [s for s in sels if len(s.split()) > 1 and s not in OWNED]
            if not comp or len(comp) != len(sels):
                continue
            if any(s in KEEP for s in sels):
                kept.append((rel, ', '.join(sels)))
                continue
            targets = [target_of(s) for s in sels]
            if any(t is None for t in targets):
                foreign.append((rel, ', '.join(sels)))
                continue
            allowed = set()
            for t in targets:
                allowed |= OWNED[t]
            if not (props_of(text, da, db) - allowed):
                over.append((rel, ', '.join(sels)))

for rel, sel in over:
    print('        still outranks base: %-28s %s' % (rel[:28], sel[:34]))
check('no compound rule duplicates what base declares', not over,
      '%d do: %s' % (len(over), '; '.join(s for _r, s in over[:3])))

# A RULE, NOT A LIST. A compound rule survives only because it sets
# something base never claims, or because it is one of the two named
# exceptions with a reason. Both are checkable on a page written next
# month.
print('        %d compound rule(s) kept, each named:' % len(kept))
for rel, sel in kept:
    print('          %-28s %-32s %s'
          % (rel[:28], sel[:32], KEEP.get(sel, '')[:34]))
check('  CONTROL: every kept rule has a reason on the record',
      all(any(s in KEEP for s in sel.split(', ')) for _r, sel in kept))

agg = collections.Counter(sel for _rel, sel in foreign)
print('        %d rule(s) target something base does not own - reported:'
      % len(foreign))
for sel, n in agg.most_common(6):
    print('          %-44s %d page(s)' % (sel[:44], n))

# ---------------------------------------------------------------------- 3
head('3. RENDERED - the migrated screens show the standard, focus included')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

WANT = {'border': '2px', 'radius': '8px', 'pad': '9px', 'font': '14px'}

if sync_playwright is None:
    skip('every entry screen renders base\'s control', 'playwright missing')
    skip('  and focuses in the accent, never in the bad colour',
         'playwright missing')
else:
    cut = B.find('{% block content %}')
    pre, post = [], []
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', B, re.S):
        (pre if m.end(1) < cut else post).append(m.group(1))
    accent = re.search(r'--alv-accent:\s*([^;]+);', B)
    bad = re.search(r'--alv-bad:\s*([^;]+);', B)
    MK = ("<div class='form-card'><div class='form-group'>"
          "<label for='x'><strong>Amount</strong></label>"
          "<input id='x' class='form-control' value='1'></div></div>")
    off, red, unfocusable = [], [], []
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page(viewport={'width': 1100, 'height': 500})
            pg.route('**://**', lambda r: r.abort())
            # TRANSITIONS OFF IN THE FIXTURE, and this is the whole reason
            # the first version of this check could not fail. base gives the
            # control `transition: border-color 0.15s ease`, so the computed
            # colour read immediately after focus is still the RESTING one -
            # the animation has barely started. I read it at 0ms and
            # concluded the focus ring was dead system-wide; an injected
            # !important rule at ID specificity "lost" for the same reason,
            # which should have been the clue. Measured across time it goes
            # #e3e8ea -> #68aab3 at 50ms -> #0e7c8b by 150ms. Nothing was
            # wrong with the CSS. A rendered check has to stop the clock or
            # wait for it.
            #
            # THE RESTING COLOUR AND THE FOCUSED ONE, BOTH MEASURED.
            # The first version of this check read the computed style after
            # calling focus() and compared it against nothing, so it could
            # not fail: it silently read the RESTING border on every page
            # and passed whatever the focus rule said. The red-ring
            # sabotage proved it - section 2 caught that rule and section 3
            # did not notice. Reading both, and requiring them to DIFFER,
            # is what makes the focus measurement real.
            for rel, path in templates():
                t_ = read(path)
                if 'form-control' not in t_ or '<form' not in t_:
                    continue
                own = '\n'.join(t_[a:b] for a, b in style_spans(t_))
                pg.set_content(
                    "<!doctype html><meta charset=utf-8><style>%s</style>"
                    "<style>%s</style>%s<style>%s</style>"
                    # AS CSS, not as another style element - the first
                    # attempt appended a <style> tag INSIDE the style
                    # element and produced invalid CSS that did nothing.
                    % ('\n'.join(pre), own, MK, '\n'.join(post)
                       + '\n*{transition:none!important}'),
                    wait_until='load')
                resting = pg.evaluate(
                    "() => getComputedStyle("
                    "document.querySelector('.form-control')).borderTopColor")
                pg.focus('.form-control')
                m = pg.evaluate("""() => {
                    const e = document.querySelector('.form-control');
                    const c = getComputedStyle(e);
                    return {border: c.borderTopWidth,
                            radius: c.borderTopLeftRadius,
                            pad: c.paddingTop, font: c.fontSize,
                            ring: c.borderTopColor,
                            focused: document.activeElement === e};
                }""")
                if not m['focused'] or m['ring'] == resting:
                    unfocusable.append(rel)
                bad_keys = [k for k, v in WANT.items() if m[k] != v]
                if bad_keys:
                    off.append((rel, bad_keys))
                r = [int(x) for x in re.findall(r'\d+', m['ring'])[:3]]
                if r and r[0] > 150 and r[1] < 90 and r[2] < 90:
                    red.append((rel, m['ring']))
            br.close()
        for rel, ks in off:
            print('        not on base\'s control: %-28s %s'
                  % (rel[:28], ', '.join(ks)))
        check('every entry screen renders base\'s control', not off,
              '%d do not: %s' % (len(off), ', '.join(r for r, _k in off[:4])))
        for rel, ring in red:
            print('        RED FOCUS RING: %-28s %s' % (rel[:28], ring))
        check('  and none of them focuses in a red ring', not red,
              '%d do: %s' % (len(red), ', '.join(r for r, _x in red[:4])))

        check('  CONTROL: focusing really changes the border, so this is '
              'measuring the focus state', not unfocusable,
              '%d screen(s) showed no change on focus: %s'
              % (len(unfocusable), ', '.join(unfocusable[:3])))
        check('  CONTROL: the accent and bad tokens are different colours',
              bool(accent) and bool(bad)
              and accent.group(1).strip() != bad.group(1).strip(),
              '%s vs %s' % (accent.group(1).strip() if accent else '?',
                            bad.group(1).strip() if bad else '?'))
    except Exception as e:
        skip('every entry screen renders base\'s control',
             'the browser would not run: %s' % str(e)[:40])
        skip('  and focuses in the accent, never in the bad colour',
             'the browser would not run: %s' % str(e)[:40])

# ---------------------------------------------------------------------- 4
head('4. IT IS ON THE GATE')

if not os.path.exists(PS1):
    check('Push-PendingChanges.ps1 is here', False, 'it is not')
else:
    check('this suite is on the gate', ME in read(PS1), ME)

# ---------------------------------------------------------------------- 5
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
print('  REPORTED, NOT FAILED: the rules targeting things base does not own')
print('  - an h2 inside the panel on six pages, a Bootstrap card body on')
print('  one. Two ways to title a panel is a round of its own.')
print('=' * 72)
sys.exit(1 if FAIL else 0)
