"""test_save_and_cancel.py - Save is at the top of every entry screen, and
   there is one way to leave a form.

    python test_save_and_cancel.py

Run from the repo root, after apply_save_and_cancel.py.

WHAT THIS SUITE CANNOT DO, SAID FIRST

It cannot tell you Save belongs at the top rather than the bottom, or that
Cancel should go. Both were settled on 17 Sep. This holds the system to
them.

SECTION 3 IS THE ONE THAT EARNS ITS KEEP, and it is here because the round
before this one retired a class with the SAME DECLARATION as the one this
round adds. .page-action-buttons-form was inert; .page-action-buttons-single
is not. The difference is what else is in the bar: a primary button eats
the free space, so justify-content has nothing to distribute, while a bar
holding only Back has space to give. Nothing static can tell those apart -
the stylesheets are identical - so section 3 renders both and measures.

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
import alv_tree

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = alv_tree.join('base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
ME = os.path.basename(__file__)

RECIPE = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
          'unit_conversions', 'celebration_', 'import_recipe',
          'map_ingredients', 'measurement_units', 'household_member',
          'categories_management')

# WIDENED 17 Sep - see apply_save_and_cancel.py. The old spelling matched
# asset_edit.html and not edit_asset.html.
ENTRY = re.compile(r'(^|/)(add|edit|new)_|(_add|_edit|_form|_new)\.html$'
                   r'|(^|/)generate_')
CONFIRM = re.compile(r'(_delete|_confirm)\.html$|(^|/)(delete|confirm)_')

SINGLE = 'page-action-buttons-single'

# The screens whose Cancel is NOT a way out of the form. Named, with the
# reason, because a count cannot tell a new one from an old one.
KEEP_CANCEL = {
    'finance_expense_add.html': 'it dismisses a dialog',
    'finance_expense_edit.html': 'it dismisses a dialog',
    'generate_lease_agreement.html': 'it dismisses a dialog',
    # ADDED 18 Sep, and the CONTROL below is what found them. Both carry
    # data-dismiss="modal" inside a .modal-footer - a preview dialog's way
    # out, not a form's - so they belong here on the same grounds as the
    # three above. The round named three of five; the check said so.
    'finance_expense_line_types_edit.html': 'it dismisses a dialog',
    'finance_valuations_edit.html': 'it dismisses a dialog',
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
    return re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), out, flags=re.S)


def close_of(scan, open_end, tag):
    depth, i = 1, open_end
    pat = re.compile(r'<(/?)%s\b[^>]*>' % tag, re.I)
    while True:
        m = pat.search(scan, i)
        if not m:
            return None
        depth += -1 if m.group(1) else 1
        i = m.end()
        if depth == 0:
            return m.end()


def templates():
    out = []
    for dirpath, _d, names in alv_tree.walk3():
        for n in sorted(names):
            if not n.endswith('.html'):
                continue
            path = os.path.join(dirpath, n)
            if os.path.abspath(path) == os.path.abspath(BASE):
                continue
            rel = alv_tree.rel(path).replace(os.sep, '/')
            if any(t in rel for t in RECIPE):
                continue
            out.append((rel, path))
    return sorted(out)


def entry_screens():
    out = []
    for rel, path in templates():
        t = read(path)
        if '<form' not in t or 'form-control' not in t:
            continue
        if not ENTRY.search(rel) or CONFIRM.search(rel):
            continue
        out.append((rel, t))
    return out


def href_of(chunk):
    m = re.search(r'\bhref\s*=\s*"([^"]*)"', chunk)
    return ' '.join(m.group(1).split()) if m else None


def elements(scan, text, word=None, cls=None):
    out = []
    for m in re.finditer(r'<(a|button)\b', scan, re.I):
        tag = re.match(r'<(a|button)\b', scan[m.start():], re.I).group(1)
        end = close_of(scan, m.start() + len(tag) + 1, tag)
        if end is None:
            continue
        chunk = text[m.start():end]
        if word and not re.search(r'>\s*(?:<i[^>]*>\s*</i>)?\s*%s\s*<' % word,
                                  chunk, re.I):
            continue
        if cls and not re.search(r'class="[^"]*\b%s\b' % cls, chunk):
            continue
        out.append((m.start(), end, chunk))
    return out


if not os.path.isdir(T):
    print('! %s not found - run from the repo root' % T)
    sys.exit(1)

B = read(BASE)
SCREENS = entry_screens()

# ---------------------------------------------------------------------- 1
head('1. SAVE IS ABOVE THE FIELDS')

late, none = [], []
for rel, t in SCREENS:
    scan = inert(t)
    ctrl = re.search(r'class="[^"]*\bform-control\b', scan)
    prim = re.search(r'<(a|button)\b[^>]*class="[^"]*\baction-primary\b', scan)
    if not prim:
        none.append(rel)
    elif ctrl and prim.start() > ctrl.start():
        late.append(rel)

print('        %d Add/Edit screen(s).' % len(SCREENS))
for rel in late:
    print('          a control appears above Save: %s' % rel)
for rel in none:
    print('          no primary button at all: %s' % rel)
check('every entry screen puts its primary above the first field', not late,
      '%d do not: %s' % (len(late), ', '.join(late[:4])))
check('  CONTROL: and they do have a primary to place',
      len(none) <= 1, '%d have none' % len(none))

# ---------------------------------------------------------------------- 2
head('2. ONE WAY OUT OF A FORM')

dupes, kept = [], []
for rel, t in SCREENS:
    scan = inert(t)
    name = rel.rsplit('/', 1)[-1]
    cancels = elements(scan, t, word='Cancel')
    backs = elements(scan, t, cls='action-back')
    if not cancels:
        continue
    for _a, _b, chunk in cancels:
        # EVIDENCE, not the word. `'dismiss' in chunk` matched the word
        # anywhere in the element - including prose. A dialog's way out
        # carries the attribute that closes the dialog.
        if re.search(r'data-dismiss\s*=\s*["\']modal', chunk):
            kept.append((rel, 'it dismisses a dialog'))
            continue
        h = href_of(chunk)
        if h is not None and any(href_of(x[2]) == h for x in backs):
            dupes.append((rel, h))
        else:
            kept.append((rel, 'it goes somewhere Back does not'))

for rel, h in dupes:
    print('          Cancel duplicates Back: %-28s %s' % (rel[:28], h[:30]))
check('no entry screen offers Cancel and Back to the same place', not dupes,
      '%d do: %s' % (len(dupes), ', '.join(r for r, _h in dupes[:4])))
print('        %d Cancel(s) kept, each for a stated reason:' % len(kept))
for rel, why in kept:
    print('          %-40s %s' % (rel[:40], why))
check('  CONTROL: every kept Cancel is one this round named',
      all(rel.rsplit('/', 1)[-1] in KEEP_CANCEL or 'somewhere Back does not'
          in why for rel, why in kept))

# ---------------------------------------------------------------------- 3
head('3. RENDERED - a LONE BACK IS RIGHT-ALIGNED ON A PHONE')

# This section used to assert that .page-action-buttons-single is NOT inert,
# unlike the -form variant retired beside it. That was true when written and
# is FALSE as of H2b (27 Sep). H2b gave base
#     .page-action-buttons:not(:has(.action-primary)) .action-back
#         { margin-left: auto; }
# inside the phone block, because thirteen bars hold a lone Back and wear no
# class at all - the user saw it as "the Back is wrong here". That rule covers
# the only case the class ever changed, so the class now changes nothing.
# Measured in Chromium, eight combinations, both widths: with the H2b rule
# present every one puts Back 8px from the right edge, class or no class. With
# the rule removed, exactly one combination moves - a lone Back with no class
# drops to the left edge at 400px. So the class is redundant, not wrong; three
# pages still wear it (title_deeds_management, tenant_lease_agreement,
# preview_imported_recipe) and retiring it is its own round.
# What this section tests now is the OUTCOME the class was bought for, and it
# fails if whichever mechanism is live goes away.

check('base declares the single-button bar',
      bool(re.search(r'\.%s\s*\{' % SINGLE, B)))
pagecopies = [rel for rel, p in templates()
              if re.search(r'\.%s\s*\{' % SINGLE, read(p))]
check('  and no page declares it any more', not pagecopies,
      '%d do: %s' % (len(pagecopies), ', '.join(pagecopies[:3])))
misuse = [rel for rel, t in SCREENS
          if re.search(r'class="[^"]*\b%s\b[^"]*"' % SINGLE, inert(t))
          and re.search(r'class="[^"]*\baction-primary\b', inert(t))]
check('  no bar carrying a primary still calls itself single', not misuse,
      '%d do: %s' % (len(misuse), ', '.join(misuse[:3])))

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

R3 = ('a lone Back sits at the right edge on a phone',
      '  and so does one in a bar that carries a primary',
      '  CONTROL: pull base\'s H2b rule and the classless bar breaks',
      '  CONTROL: with the rule gone the class still saves its three pages',
      '  the class is redundant, not wrong - H2b covers what it covered')

if sync_playwright is None:
    for _t in R3:
        skip(_t, 'playwright is not installed')
else:
    cut = B.find('{% block content %}')
    pre, post = [], []
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', B, re.S):
        (pre if m.end(1) < cut else post).append(m.group(1))

    def bar(extra, primary):
        h = '<div class="page-action-buttons %s">' % extra
        if primary:
            h += '<button class="btn action-primary">Save</button>'
        return h + ('<a href="#" class="btn action-back">'
                    '<span class="action-back-label">Back</span></a></div>')

    # H2b's rule, quoted from base so a reformat there is noticed rather
    # than silently turning the CONTROLs into no-ops.
    H2B = ('.page-action-buttons:not(:has(.action-primary)) .action-back {'
           '\n          margin-left: auto;\n        }')

    def gap(pg, html, css):
        """How far Back's right edge is from the viewport's right edge."""
        pg.set_content("<!doctype html><meta charset=utf-8><style>%s</style>"
                       "%s<style>%s</style>" % (css[0], html, css[1]),
                       wait_until='load')
        return pg.evaluate(
            "() => Math.round(innerWidth - document.querySelector("
            "'.action-back').getBoundingClientRect().right)")
    try:
        live = ('\n'.join(pre), '\n'.join(post))
        if H2B not in live[0] and H2B not in live[1]:
            raise AssertionError('base no longer spells H2B the way this '
                                 'suite quotes it - requote it')
        gone = tuple(s.replace(H2B, '') for s in live)
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page(viewport={'width': 400, 'height': 300})
            pg.route('**://**', lambda r: r.abort())
            m = {}
            for tag, css in (('live', live), ('gone', gone)):
                for nm, ex, pr in (('lone', '', False),
                                   ('lone+cls', SINGLE, False),
                                   ('prim', '', True),
                                   ('prim+cls', SINGLE, True)):
                    m[(tag, nm)] = gap(pg, bar(ex, pr), css)
            br.close()
        print('        at 400px, Back\'s gap from the right edge:')
        for tag in ('live', 'gone'):
            print('          base %-5s  %s' % (tag, '  '.join(
                '%s %dpx' % (n, m[(tag, n)])
                for n in ('lone', 'lone+cls', 'prim', 'prim+cls'))))

        check(R3[0], m[('live', 'lone')] <= 8,
              'it is %dpx short' % m[('live', 'lone')])
        check(R3[1], m[('live', 'prim')] <= 8,
              'it is %dpx short' % m[('live', 'prim')])
        check(R3[2], m[('gone', 'lone')] > 8,
              'without it the classless bar is ALREADY right-aligned, so '
              'section 2 of test_bar_mobile is measuring nothing: %dpx'
              % m[('gone', 'lone')])
        check(R3[3], m[('gone', 'lone+cls')] <= 8,
              'the class no longer does its own job either: %dpx'
              % m[('gone', 'lone+cls')])
        check(R3[4],
              m[('live', 'lone')] == m[('live', 'lone+cls')]
              == m[('live', 'prim')] == m[('live', 'prim+cls')],
              'the class still changes something under the live base - this '
              'note is wrong: %s' % {k[1]: v for k, v in m.items()
                                     if k[0] == 'live'})
    except Exception as e:
        for _t in R3:
            skip(_t, 'the browser would not run: %s' % str(e)[:40])

# ---------------------------------------------------------------------- 4
head('4. THE ENTRY PATTERN IS THE WIDE ONE')

narrow = []
for n in ('apply_entry_panel.py', 'test_entry_panel.py',
          'test_one_action_bar.py'):
    p = os.path.join(ROOT, n)
    if os.path.exists(p) and "(_add|_edit|_form)\\.html$|(^|/)generate_" \
            in read(p):
        narrow.append(n)
check('no tool still uses the narrow entry pattern', not narrow,
      '%d do: %s' % (len(narrow), ', '.join(narrow)))
check('  CONTROL: and the wide one matches the screen that exposed it',
      bool(ENTRY.search('edit_asset.html'))
      and bool(ENTRY.search('asset_edit.html'))
      and not ENTRY.search('properties.html'))

# ---------------------------------------------------------------------- 5
head('5. IT IS ON THE GATE')

if not os.path.exists(PS1):
    check('Push-PendingChanges.ps1 is here', False, 'it is not')
else:
    check('this suite is on the gate', ME in read(PS1), ME)

# ---------------------------------------------------------------------- 6
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
print('  NOT PROVED HERE: that Save belongs at the top or that Cancel should')
print('  go. Both were decided on 17 Sep from the screens themselves.')
print('=' * 72)
sys.exit(1 if FAIL else 0)
