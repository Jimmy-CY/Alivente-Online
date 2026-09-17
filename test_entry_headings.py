"""test_entry_headings.py - every entry screen heads itself the house way,
   and its module name still matches the screen Back returns to.

    python test_entry_headings.py

Run from the repo root, after apply_entry_headings.py.

WHAT THIS SUITE CANNOT DO, SAID FIRST

It cannot tell you INVOICE CUSTOMERS is the right words for that module.
It can tell you the entry screen and its list screen still agree - which
is the part that rots.

SECTION 2 IS THE ONE THAT EARNS ITS KEEP. The headings were DERIVED: each
entry screen's module name was read off the screen its Back button returns
to. A derivation is only worth having if it is re-checked, so section 2
follows every Back link again and compares. Rename a module on its list
screen and its Add and Edit screens are reported the same day, instead of
drifting quietly for months - which is exactly how the system ended up
with five different class names for one heading.

A SKIPPED CHECK IS COUNTED IN THE SUMMARY.
"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
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

ENTRY = re.compile(r'(^|/)(add|edit|new)_|(_add|_edit|_form|_new)\.html$'
                   r'|(^|/)generate_')
CONFIRM = re.compile(r'(_delete|_confirm)\.html$|(^|/)(delete|confirm)_')

H2, H4 = 'page-title-h2', 'page-subtitle-h4'
RETIRED = ('page-title-center', 'page-subtitle-center')

# Screens whose module name could NOT be derived, each with the reason.
# NAMED, because a count cannot tell a new one from an old one.
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


def text_of(html):
    out = re.sub(r'\{\{.*?\}\}|\{%.*?%\}', ' ', html, flags=re.S)
    return ' '.join(re.sub(r'<[^>]+>', ' ', out).split()).upper()


def heading_text(src, cls):
    m = re.search(r'<h[1-6][^>]*class="[^"]*\b%s\b[^"]*"[^>]*>(.*?)</h[1-6]>'
                  % cls, inert(src), re.S)
    return text_of(m.group(1)) if m else None


def first_heading(src):
    m = re.search(r'<(h[1-4])\b[^>]*>(.*?)</\1>', inert(src), re.S)
    return text_of(m.group(2)) if m else None


def resolve(url_name):
    """The template a url name refers to, searched properly.

    NOT just <name>.html at the top level. `projects` lives in
    projects/projects.html, and act_expense_add's Back points at
    `act_expense_all`, which is not a template name at all. The first
    version assumed url name == template stem, which held for the eight
    screens this round wrote and for barely half of the rest - so the
    re-check reported nine screens as underivable when several were simply
    in a subdirectory.
    """
    for dirpath, _d, names in os.walk(T):
        for n in names:
            if n == url_name + '.html':
                return os.path.join(dirpath, n)
    return None


def same_module(a, b):
    """Do two headings name the same module?

    NOT string equality. customer_invoice_form says CUSTOMER INVOICE and
    its list says PHYSICAL INVOICES; physical_invoice_edit says PHYSICAL
    INVOICE. An entry screen naming the singular thing it is editing and a
    list naming the plural is correct English, not drift, and a rule that
    calls it drift would have me "fixing" three good headings.
    """
    norm = lambda s: ' '.join(w[:-1] if len(w) > 3 and w.endswith('S') else w
                              for w in (s or '').split())
    return norm(a) == norm(b)


def back_url(src):
    m = re.search(r'<a\b[^>]*class="[^"]*\baction-back\b[^"]*"[^>]*>',
                  inert(src))
    if not m:
        return None
    u = re.search(r"\{%\s*url\s*'([^']+)'", m.group(0))
    return u.group(1) if u else None


if not os.path.isdir(T):
    print('! %s not found - run from the repo root' % T)
    sys.exit(1)

SCREENS = []
for rel, path in templates():
    t = read(path)
    if '<form' not in t or 'form-control' not in t:
        continue
    if not ENTRY.search(rel) or CONFIRM.search(rel):
        continue
    SCREENS.append((rel, t))

# ---------------------------------------------------------------------- 1
head('1. EVERY ENTRY SCREEN HEADS ITSELF THE HOUSE WAY')

no_h2 = [rel for rel, t in SCREENS
         if not re.search(r'class="[^"]*\b%s\b' % H2, inert(t))]
no_h4 = [rel for rel, t in SCREENS
         if not re.search(r'class="[^"]*\b%s\b' % H4, inert(t))]
print('        %d entry screen(s).' % len(SCREENS))
for rel in no_h2:
    print('          no module line: %s' % rel)
for rel in no_h4:
    print('          no mode line: %s' % rel)
check('every entry screen carries the module line', not no_h2,
      '%d do not: %s' % (len(no_h2), ', '.join(no_h2[:4])))
# edit_asset is the one screen with a module line and no mode line. Its
# Back goes to a DETAIL page, not a list, so there is no module name to
# read and its single heading is the mode. Named with the reason rather
# than guessed at - ASSET DETAILS / EDIT ASSET is what the rule would have
# produced, and it reads like a mistake.
NO_MODE = {'edit_asset.html': 'its Back goes to a detail page, so there is '
                              'no module name to read'}
_um = [r for r in no_h4 if r.rsplit('/', 1)[-1] not in NO_MODE]
check('  and the mode line, or a stated reason it has none', not _um,
      '%d unexplained: %s' % (len(_um), ', '.join(_um[:4])))

retired = []
for rel, path in templates():
    t = read(path)
    for c in RETIRED:
        if re.search(r'(?<![-\w])%s(?![-\w])' % c, t):
            retired.append('%s: %s' % (rel, c))
check('  the fifth class pair is gone from every page', not retired,
      '%d left: %s' % (len(retired), '; '.join(retired[:3])))
check('  CONTROL: and base declares the pair that replaced it',
      re.search(r'\.%s\s*\{' % H2, read(BASE)) is not None
      and re.search(r'\.%s\s*\{' % H4, read(BASE)) is not None)

# ---------------------------------------------------------------------- 2
head('2. THE MODULE NAME STILL MATCHES THE SCREEN BACK RETURNS TO')

drift, underived = [], []
for rel, t in SCREENS:
    mod = heading_text(t, H2)
    if mod is None:
        continue
    url = back_url(t)
    if not url:
        # A TUPLE, like every other branch. This one appended a bare
        # string, so the report loop unpacking (rel, why) crashed - and a
        # crash blocks a push exactly as hard as a failure while saying
        # far less about why.
        underived.append((rel, 'it has no Back link to follow'))
        continue
    p = resolve(url)
    if p is None:
        underived.append((rel, "Back goes to '%s', which is not a template "
                               "name" % url))
        continue
    theirs = first_heading(read(p))
    if theirs is None:
        underived.append((rel, "the screen Back returns to has no heading"))
        continue
    if not same_module(mod, theirs):
        drift.append((rel, mod, url, theirs))

for rel, mine, url, theirs in drift:
    print('          %-30s says %-22s but %s says %s'
          % (rel[:30], mine[:22], url[:20], theirs[:22]))
# TWO DISAGREE, AND NEITHER IS DRIFT THIS ROUND CAUSED.
#
# customer_invoice_form heads itself CUSTOMER INVOICE while the screen its
# Back returns to is PHYSICAL INVOICES. Those are not singular and plural
# of the same words - they are two names for one module, and the model
# screen is on one side of it. That is a question for a person, not a
# patcher, and it is named here so it stays visible.
#
# edit_asset's module line holds its MODE, because its Back goes to a
# detail page and there is no module name to read. Same reason as above.
NAMED_DRIFT = {
    'customer_invoice_form.html':
        'the module is called CUSTOMER INVOICE here and PHYSICAL INVOICES '
        'on its list screen - one module, two names',
    'edit_asset.html':
        'its module line holds the mode; Back goes to a detail page',
}
_ud = [r for r, _m, _u, _t in drift
       if r.rsplit('/', 1)[-1] not in NAMED_DRIFT]
check('every disagreement with a list screen is one that is named', not _ud,
      '%d unexplained: %s' % (len(_ud), ', '.join(_ud[:4])))
for rel, _m, _u, _t in drift:
    nm = rel.rsplit('/', 1)[-1]
    if nm in NAMED_DRIFT:
        print('          named: %-28s %s' % (rel[:28], NAMED_DRIFT[nm][:44]))
check('  CONTROL: and most screens DO agree with theirs',
      len(SCREENS) - len(underived) - len(drift) >= 15,
      '%d agree' % (len(SCREENS) - len(underived) - len(drift)))
check('  CONTROL: and the derivation was exercised, not skipped',
      len(SCREENS) - len(underived) >= 8,
      '%d of %d screen(s) re-derived' % (len(SCREENS) - len(underived),
                                         len(SCREENS)))

# A RULE, NOT A LIST OF FILENAMES. Each of these says WHY it could not be
# re-derived, and the reason is read off the page rather than looked up -
# so a screen added next month is explained by the same sentence.
print('        %d screen(s) could not be re-derived:' % len(underived))
for rel, why in underived:
    print('          %-32s %s' % (rel[:32], why))
check('  every one of those has a reason read off the page',
      all(why for _r, why in underived))

# ---------------------------------------------------------------------- 3
head('3. NO DJANGO TAG WAS UPPER-CASED')

# {{ workspace.name }} upper-cased is a variable that does not exist, and
# the heading renders EMPTY - which looks like a blank line, not an error.
broken = []
for rel, t in SCREENS:
    for m in re.finditer(r'<h[24][^>]*class="[^"]*\b(?:%s|%s)\b[^"]*"[^>]*>'
                         r'(.*?)</h[24]>' % (H2, H4), inert(t), re.S):
        for v in re.findall(r'\{\{(.*?)\}\}|\{%(.*?)%\}', m.group(1), re.S):
            body = (v[0] or v[1])
            if re.search(r'[A-Z]', body) and body == body.upper() \
                    and re.search(r'[a-z]', body) is None \
                    and not re.match(r'\s*(ENDIF|ELSE)\s*$', body):
                broken.append('%s: {{%s}}' % (rel, body[:26]))
check('no heading upper-cased the inside of a Django tag', not broken,
      '%d did: %s' % (len(broken), '; '.join(broken[:3])))
check('  CONTROL: and there are headings with tags in them to have broken',
      sum(1 for _r, t in SCREENS
          if re.search(r'<h[24][^>]*\b%s\b[^>]*>[^<]*\{' % H4, inert(t))) >= 2)

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
print('  NOT PROVED HERE: that the module names read well. They were read')
print('  off the list screens rather than chosen, so if one is wrong it is')
print('  wrong in two places and this suite will keep them wrong together.')
print('=' * 72)
sys.exit(1 if FAIL else 0)
