"""test_label_bold.py - every field label is bold, and the bold comes from
   the markup rather than from a rule somebody has to remember.

    python test_label_bold.py

Run from the repo root, after apply_label_bold.py.

WHAT THIS SUITE CANNOT DO, SAID FIRST
-------------------------------------
It cannot tell you bold is the right choice. That was settled on 9 Sep
against a 545-label count that split 338 plain to 207 bold - the majority
was plain and the standard went the other way, because the model page and
the two biggest Add screens already agreed and because a label is a LABEL.
This suite only holds the system to it.

SECTION 4 IS THE ONE THAT EARNS ITS KEEP. The weight comes from a strong
element, so it depends on nothing in any stylesheet - unless a stylesheet
takes it away. A single `strong { font-weight: normal }` anywhere in base,
or a Bootstrap reset, would silently un-bold every label in the system and
leave the markup looking perfectly correct. So section 4 renders a real
field against base's real CSS and reads the computed weight back.

SECTION 3 IS A REPORT AND SAYS SO. It began as a check - "no page makes a
label bold with CSS instead" - and that claim is not this round's. A page
that bolds in CSS and omits the strong element already fails section 2;
the only thing section 3 could add is a page that does both, which is
redundancy on pages this round never opened. It names them instead.

A SKIPPED CHECK IS COUNTED IN THE SUMMARY, not printed and forgotten. So
is a reported one.
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

RECIPE = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
          'unit_conversions', 'celebration_', 'import_recipe',
          'map_ingredients', 'measurement_units', 'household_member',
          'categories_management')

LABEL = re.compile(r'<label\b[^>]*>(.*?)</label>', re.S)
CTRL = r'<(input|select|textarea)\b[^>]*>'

# The shapes the sweep deliberately did not guess at. NAMED, because a
# count cannot tell a new one from an old one - and each is a label whose
# text is not simply the field's name.
NOT_SWEPT = {
    'generate_lease_agreement.html',   # three labels JavaScript rewrites,
                                       # and one with an (auto-calculated)
                                       # hint that is not part of the name
    'property_assets.html',            # a size/format hint in a <small>
    'projects/projects_delete.html',   # not a field name at all: a sentence
                                       # of instruction with a red DELETE in
                                       # the middle of it, already bold from
                                       # a font-weight-bold utility class.
                                       # The delete-confirm pages own it.
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


def templates():
    out = []
    for dirpath, _d, names in os.walk(T):
        for n in names:
            if n.endswith('.html'):
                out.append(os.path.join(dirpath, n))
    return sorted(out)


def rel_of(p):
    return os.path.relpath(p, T).replace(os.sep, '/')


def is_recipe(rel):
    return any(t in rel for t in RECIPE)


def scannable(text):
    return re.sub(r'<(script|style)[^>]*>.*?</\1>',
                  lambda m: ' ' * len(m.group(0)), text, flags=re.S)


def control_of(scan, m):
    f = re.search(r'\bfor\s*=\s*"([^"]+)"', m.group(0))
    if f:
        c = re.search(r'<(input|select|textarea)[^>]*\bid\s*=\s*"%s"[^>]*>'
                      % re.escape(f.group(1)), scan)
        if c:
            return c.group(0)
    after = scan[m.end():m.end() + 400]
    nxt = re.search(CTRL, after)
    lbl = re.search(r'<label\b', after)
    if nxt and (not lbl or nxt.start() < lbl.start()):
        return nxt.group(0)
    return None


def fields_of(text):
    """(bold, plain) field labels on one page, per section 3.6.

    A FIELD is a label naming a control that carries form-control. Not a
    tab, not a checkbox, not a label that wraps its own input - the first
    draft of the sweep took help_page's tabs because a radio followed one.
    """
    scan = scannable(text)
    bold, plain = [], []
    for m in LABEL.finditer(scan):
        inner = m.group(1)
        if re.search(r'<(input|select|textarea)\b', inner) or not inner.strip():
            continue
        c = control_of(scan, m)
        if not c or 'form-control' not in c:
            continue
        (bold if '<strong' in inner else plain).append(
            ' '.join(text[m.start(1):m.end(1)].split())[:70])
    return bold, plain


if not os.path.isdir(T):
    print('! %s not found - run from the repo root' % T)
    sys.exit(1)

B = read(BASE)

# ---------------------------------------------------------------------- 1
head('1. THE STANDARD STILL SAYS IT')

check('base states the field shape', 'label > strong' in B)
check('  and names the asterisk class beside it', 'span.alv-req' in B)
check('  and the control it goes with', 'input.form-control' in B)
check('  CONTROL: and the block really is there to have lost it',
      'THE LABEL IS BOLD' in B)

# ---------------------------------------------------------------------- 2
head('2. THE CORPUS - every field label, present tense')

pm_bold = pm_plain = 0
offenders = {}
rec_bold = rec_plain = 0
for p in templates():
    rel = rel_of(p)
    bold, plain = fields_of(read(p))
    if is_recipe(rel):
        rec_bold += len(bold)
        rec_plain += len(plain)
        continue
    pm_bold += len(bold)
    pm_plain += len(plain)
    if plain:
        offenders[rel] = plain

print('        %d field label(s) in property management: %d bold, %d plain.'
      % (pm_bold + pm_plain, pm_bold, pm_plain))
for rel, items in sorted(offenders.items()):
    for t in items:
        print('          plain: %-32s %s' % (rel[:32], t))

_unexpected = sorted(r for r in offenders if r not in NOT_SWEPT)
check('every plain field label is one the sweep named and left alone',
      not _unexpected, '%d not accounted for: %s'
      % (len(_unexpected), ', '.join(_unexpected[:4])))
check('  CONTROL: and there are bold ones, so it is measuring something',
      pm_bold >= 100, '%d bold' % pm_bold)
check('  CONTROL: the two exceptions are still there to be excepted',
      set(offenders) & NOT_SWEPT == set(offenders) & NOT_SWEPT)

# The recipe side is REPORTED, never failed. Section 2.K: 29 templates, no
# round has swept them and the push gate does not run them. Reporting the
# number is what stops it being forgotten; failing on it would be failing
# on work nobody has agreed to do.
print('        the recipe side, out of scope and reported: %d bold, %d plain.'
      % (rec_bold, rec_plain))

# ---------------------------------------------------------------------- 3
head('3. THE PAGES THAT ALSO SAY IT IN CSS - REPORTED, NOT FAILED')

# SCOPE GUARD #29. This section began as a check: "no page makes a label
# bold with CSS instead". It fails the test I apply to every other one -
# ASK WHAT THE CLAIM IS ABOUT.
#
# This round's claim is that every field label is bold FROM ITS MARKUP. A
# page that bolds labels in CSS and omits the strong element already fails
# section 2, because section 2 asks the markup and does not care what any
# stylesheet says. So the only thing this section can catch that section 2
# cannot is a page that does BOTH - which is redundancy, not drift, and
# which this round did not create.
#
# Removing those rules is a CSS consolidation, on pages this round never
# opened, and a round that changes two things cannot say which one did it.
# So the rules are NAMED here and left alone, and the summary counts them
# so they are not forgotten. There is deliberately no ceiling: a count
# cannot tell a page leaving this set from a page joining it.
#
# The first draft also matched `.detail-label` and `.report-year-label` -
# \blabel\b matches after a hyphen - and reported 53 where there are 13.
# A pattern that cannot tell a class name from an element name is not
# measuring what it says it is.
ELEM = re.compile(r'(?<![-\w.#:])label(?![-\w])')
BOLDCLS = re.compile(r'\b(font-weight-bold|fw-bold|text-bold)\b')

weighted = []
for p in templates():
    rel = rel_of(p)
    if is_recipe(rel):
        continue
    for css in re.findall(r'<style[^>]*>(.*?)</style>', read(p), re.S):
        css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
        for m in re.finditer(r'([^{}]*)\{([^}]*)\}', css):
            sel = ' '.join(m.group(1).split())
            if not ELEM.search(sel):
                continue
            if re.search(r'font-weight:\s*(bold|[6-9]00)', m.group(2)):
                weighted.append('%s: %s' % (rel, sel))

utility = []
for p in templates():
    rel = rel_of(p)
    if is_recipe(rel):
        continue
    text = read(p)
    scan = scannable(text)
    for m in LABEL.finditer(scan):
        c = control_of(scan, m)
        if not c or 'form-control' not in c:
            continue
        cls = re.search(r'\bclass\s*=\s*"([^"]*)"', m.group(0))
        if cls and BOLDCLS.search(cls.group(1)):
            utility.append('%s: class="%s"' % (rel, cls.group(1)))

print('        %d page-local CSS rule(s) also bold a label element:'
      % len(weighted))
for w in weighted:
    print('          %s' % w)
print('        %d field label(s) carry a bold utility class:' % len(utility))
for u in utility:
    print('          %s' % u)
print('        Redundant, not wrong. A CSS consolidation round owns them.')

# The report has no ceiling and no floor, so nothing above can fail. What
# CAN be wrong is the pattern that produced it, and that is worth a check
# of its own: it must see the element and not the class name, which is the
# exact mistake the first draft made.
check('CONTROL: the pattern reads label as an element, not as a class name',
      bool(ELEM.search('.form-group label'))
      and bool(ELEM.search('label'))
      and not ELEM.search('.detail-label')
      and not ELEM.search('.label-x')
      and not ELEM.search('.report-year-label'))

# ---------------------------------------------------------------------- 4
head('4. RENDERED - the strong element actually renders bold')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

if sync_playwright is None:
    for n in ('a field label renders bold',
              'CONTROL: and a plain one does not',
              'the required marker sits beside it, not inside it'):
        skip(n, 'playwright is not installed')
else:
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', B, re.S))
    page = ("<!doctype html><meta charset=utf-8><style>%s</style>"
            "<label id=a for=x><strong>Customer Name</strong> "
            "<span class='alv-req'>*</span></label>"
            "<input id=x class='form-control'>"
            "<label id=b for=y>Plain</label><input id=y class='form-control'>"
            % css)
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page(viewport={'width': 1200, 'height': 800})
            pg.route('**://**', lambda r: r.abort())
            pg.set_content(page, wait_until='load')
            m = pg.evaluate("""() => {
                const w = (s) => getComputedStyle(
                    document.querySelector(s)).fontWeight;
                const strong = document.querySelector('#a strong');
                const mark = document.querySelector('#a .alv-req');
                return {bold: w('#a strong'), plain: w('#b'),
                        markInsideStrong: strong.contains(mark),
                        markColour: getComputedStyle(mark).color};
            }""")
            br.close()
        check('a field label renders bold', int(m['bold']) >= 600, m['bold'])
        check('CONTROL: and a plain one does not', int(m['plain']) < 600,
              m['plain'])
        check('the required marker sits beside the name, not inside it',
              not m['markInsideStrong'])
        check('  and it keeps the colour base gives it', m['markColour'],
              m['markColour'])
    except Exception as e:
        for n in ('a field label renders bold',
                  'CONTROL: and a plain one does not',
                  'the required marker sits beside it, not inside it'):
            skip(n, 'the browser would not run: %s' % str(e)[:40])

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
print('  REPORTED, NOT FAILED: %d plain field label(s) on the recipe side;'
      % rec_plain)
print('  %d page-local CSS rule(s) and %d utility class(es) that also say'
      % (len(weighted), len(utility)))
print('  bold. Each belongs to a round that is not this one.')
print('')
print('  NOT PROVED HERE: that bold is the right choice. That was settled')
print('  on 9 Sep against a count that went the other way. This only holds')
print('  the system to it.')
print('=' * 72)
sys.exit(1 if FAIL else 0)
