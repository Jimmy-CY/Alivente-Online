# -*- coding: utf-8 -*-
"""test_label_weight.py - round LB-1, 10 Oct 2026.

ONE WEIGHT FOR A FIELD LABEL, AND ONE MECHANISM THAT CARRIES IT.

    python test_label_weight.py

Run from the repo root, after apply_label_weight.py.

WHAT THIS SUITE DOES NOT CLAIM, SAID FIRST
------------------------------------------
It does not claim bold is right. That was settled on 9 Sep and
test_label_bold.py holds the system to it. This suite is about the
WEIGHT and the MECHANISM: that there is one of each, and that no page
can quietly acquire a second.

THE BUG IT EXISTS TO PREVENT IS A RELATIVE ONE. `<strong>` carries the
browser default `font-weight: bolder`, measured from whatever the label
says - 400 gives 700, 600 gives 900. Eighteen pages set 600 on the label
and pushed their own labels two steps past the house without asking.
base now pins the value absolutely, and section 4 proves it in a browser
rather than by reading the stylesheet, because a rule that is present
and overridden reads exactly like a rule that works.

SECTION 5 IS THE ONE THAT PROTECTS SOMEBODY ELSE'S WORK. 67 labels in
the corpus bold only their NAME and keep a hint beside it in normal
weight - `<strong>Email CC</strong> (optional)`. The obvious version of
this round would have put the weight on the label and flattened all 67.
The guard is on the strong FOR THAT REASON, and section 5 measures that
the contrast survived.
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
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
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

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import alv_rounds                                               # noqa: E402
import alv_tree                                                 # noqa: E402

SUFFIX = '.bak_lblwt'
PATCHER = 'apply_label_weight.py'
HELD = 'test_label_bold.py'
ME = os.path.basename(__file__)
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')

# Pinned by measurement, 10 Oct 2026.
N_CRS = 24                 # plain CRS field labels this round wrapped
N_CRS_PAGES = 4
N_PART = 2                 # of those, the ones with a hint after the name
N_RULES = 22               # whole .form-group label rules removed
N_HINT = 69                # labels that bold only part of themselves
N_HINT_WAS = 67            # ... 67 before this round added two

CRS_PAGES = ('crs/country_form.html', 'crs/fi_form.html',
             'crs/submission_detail.html', 'crs/submission_start.html')

WEIGHTED = (
    'create_meal_plan.html', 'customer_form.html',
    'customer_invoice_form.html', 'finance_expense_add.html',
    'finance_expense_edit.html', 'finance_expense_line_types_add.html',
    'finance_expense_line_types_edit.html', 'finance_expense_types_add.html',
    'finance_expense_types_edit.html', 'finance_revenue_add.html',
    'finance_revenue_edit.html', 'finance_revenue_line_types_add.html',
    'finance_revenue_line_types_edit.html', 'finance_revenue_types_add.html',
    'finance_revenue_types_edit.html', 'my_profile.html',
    'notification_settings.html', 'personal_notification_settings.html',
    'user_add.html', 'user_edit.html', 'workspace_add.html',
    'workspace_edit.html',
)

PASS = FAIL = SKIP = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  ok   %s' % name)
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL %s%s' % (name, ('  [%s]' % extra) if extra else ''))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def css_of(text):
    import alv_cssrules
    out = []
    for a, b in alv_cssrules.style_spans(text):
        out.append(re.sub(r'/\*.*?\*/', '', text[a:b], flags=re.S))
    return '\n'.join(out)


print(__doc__.strip().split('\n')[0])

BASE = alv_tree.path_of('base.html')

# ---------------------------------------------------------------------- 1
head('1. SCOPE')

check('%s is on disk' % PATCHER, os.path.isfile(os.path.join(ROOT, PATCHER)))
check('  and base.html is where alv_tree says', os.path.isfile(BASE))
check('  and %s, the suite this round released, is still here' % HELD,
      os.path.isfile(os.path.join(ROOT, HELD)))

# ---------------------------------------------------------------------- 2
head('2. BASE PINS THE BOLD, AND PINS IT ON THE RIGHT ELEMENT')

b = read(BASE)
bcss = css_of(b)
guard = re.search(r'\.form-group label strong,\s*\.form-group label b\s*\{'
                  r'([^}]*)\}', bcss)
check('base declares the guard on strong AND b inside a field label',
      guard is not None)
if guard:
    body = ' '.join(guard.group(1).split())
    check('  and the value is an absolute 700, not bolder',
          re.search(r'font-weight:\s*700\s*;?', body) is not None, body[:40])
    check('  CONTROL: and it is not the word bolder, which is the bug',
          'bolder' not in body, body[:40])

lab = re.search(r'(?<![-\w])\.form-group label\s*\{([^}]*)\}', bcss)
check('  base still sets NO weight on the label itself', lab is not None
      and 'font-weight' not in lab.group(1),
      '' if lab is None else ' '.join(lab.group(1).split())[:50])
print('        Deliberate. 67 labels bold only their NAME and keep a hint')
print('        beside it; a weight on the label would flatten every one.')

# A gate reads the file AS THIS ROUND LEFT IT.
# BEFORE is the backup, not as_left_by. as_left_by(p, SUFFIX) answers
# "the file as THIS round left it", and for the newest round that is the
# file as it is now - which would have made the control below pass by
# reading the very text it is supposed to prove was absent.
def before(p):
    # A SUITE RUN BEFORE ITS ROUND SHOULD SAY SO. Without this the
    # first thing anyone sees is a FileNotFoundError traceback, which
    # blocks a push exactly as hard as a failure and says far less.
    b = p + SUFFIX
    if not os.path.exists(b):
        print('')
        print('  !! %s has no %s backup.' % (os.path.basename(p), SUFFIX))
        print('     This suite judges the round against what it replaced,')
        print('     so it cannot run until apply_label_weight.py has.')
        sys.exit(1)
    return read(b)


check('  CONTROL: and the backup proves base did not already say it',
      '.form-group label strong' not in before(BASE))

# ---------------------------------------------------------------------- 3
head('3. THE CRS FORMS - 24 LABELS THAT WERE PLAIN')

LABEL = re.compile(r'<label\b[^>]*>(.*?)</label>', re.S)
wrapped = 0
part = 0
bad = []
for rel in CRS_PAGES:
    p = alv_tree.path_of(rel)
    t = read(p)
    was = before(p)
    n_before = len([1 for m in LABEL.finditer(was) if '<strong' in m.group(1)])
    n_after = len([1 for m in LABEL.finditer(t) if '<strong' in m.group(1)])
    wrapped += n_after - n_before
    for m in LABEL.finditer(t):
        i = m.group(1)
        if '<strong' not in i:
            continue
        # base's shape: the NAME in the strong, the asterisk outside it.
        if 'alv-req' in i and 'alv-req' in re.sub(
                r'<strong\b.*?</strong>', '', i, flags=re.S):
            continue
        if 'alv-req' in i:
            bad.append('%s: %s' % (rel, ' '.join(i.split())[:50]))
    after_strong = [re.sub(r'<strong\b.*?</strong>', '', m.group(1),
                           flags=re.S).strip()
                    for m in LABEL.finditer(t) if '<strong' in m.group(1)]
    part += len([x for x in after_strong
                 if x and not re.fullmatch(r'(<span[^>]*>\*</span>)', x)])

check('%d field label(s) gained a strong across the %d CRS form page(s)'
      % (wrapped, N_CRS_PAGES), wrapped == N_CRS, '%d' % wrapped)
check('  and every asterisk stayed OUTSIDE the strong, as base specifies',
      not bad, '; '.join(bad[:2]))
print('        base: label > strong is the field name, span.alv-req the star.')
print('        145 labels in the corpus already write it that way.')

for rel in CRS_PAGES:
    t = read(alv_tree.path_of(rel))
    plain = []
    for m in LABEL.finditer(t):
        i = m.group(1)
        if '<strong' in i or not i.strip():
            continue
        if re.search(r'<(input|select|textarea)\b', i) \
                or re.search(r'\{\{\s*form\.\w+\s*\}\}', i):
            continue
        # A LABEL OVER NOTHING IS NOT A FIELD LABEL. submission_detail
        # writes Transmitting Country over a rendered VALUE, not over a
        # control, and bolding it would be a different decision on a
        # different component.
        after = t[m.end():m.end() + 400]
        c = re.search(r'<(input|select|textarea)\b[^>]*>', after)
        d = re.search(r'\{\{\s*form\.\w+\s*\}\}', after)
        l2 = re.search(r'<label\b', after)
        first = min([x.start() for x in (c, d) if x] or [10 ** 6])
        if first == 10 ** 6 or (l2 and l2.start() < first):
            continue
        plain.append(' '.join(i.split())[:46])
    check('  %s has no plain field label left' % rel, not plain,
          '; '.join(plain[:2]))

# ---------------------------------------------------------------------- 4
head('4. NO PAGE DECLARES A LABEL WEIGHT ANY MORE')

RULE = re.compile(r'(?<![-\w])\.form-group\s+label\s*\{([^}]*)\}')
left = []
for p in alv_tree.templates():
    rel = alv_tree.rel(p)
    if rel == 'base.html':
        continue
    for m in RULE.finditer(css_of(read(p))):
        if 'font-weight' in m.group(1):
            left.append(rel)
check('not one page still writes a weight onto .form-group label',
      not left, '%d left: %s' % (len(left), ', '.join(left[:3])))

removed = 0
for rel in WEIGHTED:
    p = alv_tree.path_of(rel)
    was = before(p)
    if [m for m in RULE.finditer(css_of(was)) if 'font-weight' in m.group(1)]:
        removed += 1
check('  CONTROL: and the backups prove %d page(s) really did carry one'
      % N_RULES, removed == N_RULES, '%d' % removed)
print('        Every one of the 22 held a font-weight AND NOTHING ELSE, so')
print('        what came out is the whole rule, not a line from inside one.')

# ---------------------------------------------------------------------- 5
head('5. MEASURED IN A BROWSER - ONE WEIGHT, AND THE HINTS SURVIVED')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    SKIP += 1
    print('  skip playwright is not installed here')
    sync_playwright = None

if sync_playwright is not None:
    import alv_cssrules
    boot = read(os.path.join(ROOT, 'test_fixture_bootstrap413.css'))
    basecss = re.sub(r'\{%.*?%\}', '', bcss, flags=re.S)

    # The four weights this round found, each written the way its pages
    # wrote it, plus a hint label and a REMOTE STYLESHEET that must be
    # refused - a render that can reach a CDN is not a measurement.
    CASES = (
        ('was 400 - a plain name', '', '<strong>Country Code</strong>'),
        ('was 600 - plain under a page rule',
         '.c1 .form-group label{font-weight:600}',
         '<strong>Workspace</strong>'),
        ('was 700 - the house majority', '',
         '<strong>Property Name</strong>'),
        ('was 900 - strong under a page rule',
         '.c3 .form-group label{font-weight:600}',
         '<strong>Expense Type</strong>'),
    )
    HINT = '<strong>Email CC</strong> (optional)'
    cols = ''.join(
        '<div class="form-group c%d"><label>%s</label></div>' % (i, m)
        for i, (_n, _c, m) in enumerate(CASES))
    cols += '<div class="form-group hint"><label>%s</label></div>' % HINT
    doc = ('<!doctype html><html><head><meta charset="utf-8">'
           '<link rel="stylesheet" href="https://example.invalid/x.css">'
           '<style>%s</style><style>%s</style><style>%s</style>'
           '</head><body>%s</body></html>'
           % (boot, basecss, '\n'.join(c for _n, c, _m in CASES), cols))
    fx = os.path.join(SCRATCH, 'lblwt.html')
    with open(fx, 'w', encoding='utf-8') as f:
        f.write(doc)

    refused = []
    pw = sync_playwright().start()
    try:
        br = pw.chromium.launch()
        ctx = br.new_context(viewport={'width': 1100, 'height': 400})

        def _abort(route):
            refused.append(route.request.url)
            route.abort()

        ctx.route(re.compile(r'^https?://'), _abort)
        pg = ctx.new_page()
        _goto(pg, fx)
        pg.wait_for_timeout(120)
        weights = pg.eval_on_selector_all(
            '.form-group label strong',
            'ls => ls.map(l => getComputedStyle(l).fontWeight)')
        hint_lab = pg.eval_on_selector(
            '.hint label', 'e => getComputedStyle(e).fontWeight')
        hint_str = pg.eval_on_selector(
            '.hint label strong', 'e => getComputedStyle(e).fontWeight')
        ctx.close()
        br.close()
    finally:
        pw.stop()

    check('CONTROL: the fixture asked for a remote stylesheet and the '
          'browser REFUSED it', len(refused) == 1,
          '%d refused' % len(refused))
    print('        A render that can reach a CDN measures whatever the CDN')
    print('        served today. That is what broke D-12 push one.')
    names = [n for n, _c, _m in CASES]
    check('all %d case(s) now render at one weight' % len(CASES),
          len(set(weights)) == 1, '%s' % list(zip(names, weights)))
    check('  and that weight is 700', set(weights) == {'700'},
          '%s' % sorted(set(weights)))
    check('  CONTROL: the 600 rules really are still on the fixture, so '
          'this is a pin and not an empty page',
          '.c3 .form-group label{font-weight:600}' in doc)
    check('a hint label still reads its name bold and its hint plain',
          hint_lab != hint_str and hint_str == '700',
          'label %s, strong %s' % (hint_lab, hint_str))

# ---------------------------------------------------------------------- 6
head('6. THE 67 HINT LABELS AND THE RECIPE SIDE, BOTH LEFT ALONE')

STRONG = re.compile(r'<(strong|b)\b[^>]*>(.*?)</\1>', re.S | re.I)


def flat(h):
    h = re.sub(r'<[^>]+>', '', h)
    h = re.sub(r'\{%.*?%\}', '', h, flags=re.S)
    return ' '.join(h.replace('&nbsp;', ' ').split())


def part_wrapped(text):
    n = 0
    for m in LABEL.finditer(alv_tree.code_only(text)):
        inner = m.group(1)
        ss = STRONG.findall(inner)
        if not ss:
            continue
        rest = flat(inner)
        for s in ss:
            rest = rest.replace(flat(s[1]), '', 1)
        if rest.replace('*', '').strip():
            n += 1
    return n


hint = sum(part_wrapped(read(p)) for p in alv_tree.templates())
hint_was = sum(part_wrapped(read(p + SUFFIX) if os.path.exists(p + SUFFIX)
                            else read(p)) for p in alv_tree.templates())
check('%d label(s) bold only part of themselves' % hint,
      hint == N_HINT, '%d' % hint)
check('  and %d did before this round, which added the other two'
      % N_HINT_WAS, hint_was == N_HINT_WAS, '%d' % hint_was)
print('        A ROUND THAT ADDS ANYTHING OWNS EVERY NUMBER THAT COUNTS')
print('        IT. Submission notes (optional) and Acknowledgement notes')
print('        (optional) are two of the 67 shape, so they are two more.')
print('        Email CC (optional) - the contrast IS the information, and')
print('        it survives only because base pinned the strong, not the')
print('        label. This number moving means somebody flattened them.')

RECIPE = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
          'unit_conversions', 'celebration_', 'import_recipe',
          'map_ingredients', 'measurement_units', 'household_member',
          'categories_management')
def recipe_plain(text):
    n = 0
    for m in LABEL.finditer(text):
        i = m.group(1)
        if '<strong' in i or not i.strip():
            continue
        if re.search(r'<(input|select|textarea)\b', i):
            continue
        after = text[m.end():m.end() + 400]
        c = re.search(r'<(input|select|textarea)\b[^>]*>', after)
        l2 = re.search(r'<label\b', after)
        if c and (not l2 or c.start() < l2.start()) \
                and 'form-control' in c.group(0):
            n += 1
    return n


rec = rec_was = 0
for p in alv_tree.templates():
    if not any(x in alv_tree.rel(p) for x in RECIPE):
        continue
    rec += recipe_plain(read(p))
    rec_was += recipe_plain(read(p + SUFFIX) if os.path.exists(p + SUFFIX)
                            else read(p))
# THE CLAIM IS THAT IT DID NOT MOVE, not that it is any one number. A
# count pinned as a literal is a claim that can only be true until the
# next round legitimately changes it - which is how test_passport_holder
# came to assert that 0097 was the latest migration.
check('the recipe side still carries every plain field label it had',
      rec == rec_was, '%d now, %d before' % (rec, rec_was))
check('  CONTROL: and there are some, so that is not an empty comparison',
      rec >= 40, '%d' % rec)
print('        %d plain field label(s) on the recipe side.' % rec)
print('        Section 2.K: reported, never failed. No round has swept the')
print('        recipe templates and failing on them would be failing on')
print('        work nobody has agreed to do. LB-1 did not change that.')

# ---------------------------------------------------------------------- 7
head('7. THE SUITE THIS ROUND RELEASED')

held = read(os.path.join(ROOT, HELD))
check('%s walks every root now, not pages/templates alone' % HELD,
      'alv_tree.walk3()' in held and 'os.walk(T)' not in held)
check('  and it can see a Django-rendered control', 'widget_class' in held)
check('  and it is off alv_tree.WAITING',
      HELD not in alv_tree.WAITING)
check('  and on CONVERTED instead', HELD in alv_tree.CONVERTED)
check('  CONTROL: WAITING is not simply empty - others are still held',
      len(alv_tree.WAITING) > 0, '%d held' % len(alv_tree.WAITING))

# ---------------------------------------------------------------------- 8
head('8. REGISTERED, ON THE GATE')

ps = read(PS1)
check('%s is in the $suites list' % ME, "'%s'" % ME in ps)
check('  and this round is on alv_rounds.ROUNDS', SUFFIX in alv_rounds.ROUNDS)
check('  and this suite is on alv_tree.CONVERTED', ME in alv_tree.CONVERTED)

# ----------------------------------------------------------------------
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (PASS, FAIL, SKIP))
print('=' * 74)
if FAILED:
    print('')
    for f in FAILED:
        print('  FAILED  %s' % f)
print('')
print('  NOT PROVED HERE: that bold is the right choice for a')
print('  field label. That was settled on 9 Sep and test_label_bold')
print('  holds the system to it. This suite proves there is ONE')
print('  weight and ONE mechanism, and that neither can drift back.')
sys.exit(1 if FAIL else 0)
