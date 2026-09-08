"""apply_heading_prefix.py - the brand moves off the heading and into the tab.

    python apply_heading_prefix.py --check      dry run, writes nothing
    python apply_heading_prefix.py

Run from the repo root.

WHAT THIS ROUND IS ABOUT

`ALIVENTE ONLINE - ` heads 66 pages. It is identical on all of them, so it
distinguishes nothing - and there are 53 distinct title lines, every one of
which is already unique without it. On a phone the content column is about
360px and those seventeen characters fill the whole first line before the
title starts saying anything. The brand is meanwhile already on screen three
times: the sidebar logo image plus the word ALIVENTE, the top-nav brand
image, and the footer copyright line.

On the pages that carry a record name it is worse. SEVEN OF THE TWELVE real
property names in the repo's own Dump20250718.sql already contain a dash
(`Athens - Second Floor`, `Apolloneon - Demetri`, `Ionion - Villa 24`), so
the prefix rule produces, on today's data:

    ALIVENTE ONLINE - PROPERTY ASSETS - ATHENS - SECOND FLOOR

Three identical dashes doing three different jobs. That is not a worst case
anyone invented; it is 7 of 12 properties.

THE ARGUMENT AGAINST, AND WHAT ANSWERS IT. Reports print. base's mobile
override reads `@media (max-width: 991px)` WITH NO `screen` KEYWORD, and A4
portrait is about 718 CSS px - so it fires on paper and hides the sidebar.
The logo really does vanish from a printed page. What survives is the footer
copyright, which sits inside the content div and is not marked .no-print, so
the brand is still on the paper. A brand at the TOP of a printed report
belongs in the report title component, not on 66 screens.

(That is the same accidental-media-query bug the print block's own comment
records for the 768px breakpoint. Two instances now, same cause.)

WHAT ELSE THE SURVEY FOUND, AND WHY THIS ROUND FIXES IT TOO

The browser tab had already drifted FIVE ways across 106 base-extending
templates: 80 bare with no brand, 12 EMPTY, 7 prefixed, 6 `X | Alivente
Online`, 1 `X - Alivente Online`. The twelve empties render a blank tab
today. Since the brand is moving to the tab, the tab has to be made
consistent in the same round or the move lands on a mess.

The separator is the pipe because SIX PAGES ALREADY USE IT. Picking the
convention that exists beats inventing one.

THE ONE EXCEPTION, NAMED RATHER THAN BURIED

error_pages/connectivity_error.html heads itself `ALIVENTE ONLINE` and
nothing else - stripping the prefix would empty it. It is the page shown
when the database is unreachable, where the brand IS the content and the
chrome is not guaranteed to render. It keeps its heading.

HOUSE RULES: idempotent, per-file .bak_pfx backups never overwritten,
--check writes nothing, SELF-CHECK BEFORE WRITING.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
T = os.path.join(os.getcwd(), 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
if not os.path.exists(BASE):
    sys.exit('! pages/templates/base.html not found - run from the repo root')

PREFIX = 'ALIVENTE ONLINE - '
BRAND = 'Alivente Online'
SEP = ' | '

# The page whose heading IS the brand. Not an exception list that grows -
# one page, with a reason that does not generalise.
KEEPS_THE_BRAND = 'error_pages/connectivity_error.html'

# ---------------------------------------------------------------------------
# The 66 pages whose first heading carries the prefix. DERIVED at run time,
# then asserted against this list. Deriving alone would silently do the wrong
# thing on a file somebody edited; a hardcoded table alone goes stale. Both,
# and they have to agree.
# ---------------------------------------------------------------------------
EXPECT_H2 = [
    'act_expense.html', 'act_expense_add.html', 'act_expense_edit.html',
    'admin_apms.html', 'asset_detail.html', 'cash_receipt_add.html',
    'cash_receipts.html', 'customer_form.html', 'customer_invoice_form.html',
    'customer_list.html', 'edit_asset.html',
    'error_pages/connectivity_error.html',
    'finance.html', 'finance/cashflow_forecast.html',
    'finance/financial_indicators.html', 'finance/vacancy_management.html',
    'finance_expense.html', 'finance_expense_add.html',
    'finance_expense_edit.html', 'finance_expense_line_types.html',
    'finance_expense_line_types_add.html',
    'finance_expense_line_types_edit.html', 'finance_expense_types.html',
    'finance_expense_types_add.html', 'finance_expense_types_edit.html',
    'finance_pl_act.html', 'finance_revenue.html', 'finance_revenue_add.html',
    'finance_revenue_edit.html', 'finance_revenue_line_types.html',
    'finance_revenue_line_types_add.html',
    'finance_revenue_line_types_edit.html', 'finance_revenue_types.html',
    'finance_revenue_types_add.html', 'finance_revenue_types_edit.html',
    'finance_valuations.html', 'finance_valuations_add.html',
    'finance_valuations_edit.html', 'fsr.html', 'fsr_add.html',
    'fsr_details.html', 'generate_lease_agreement.html', 'invoices.html',
    'lease_timeline.html', 'login.html', 'notifications.html',
    'occupancy_trends.html', 'passport_management.html', 'personal.html',
    'petty_cash.html', 'petty_cash_add.html', 'physical_invoice_edit.html',
    'physical_invoice_list.html', 'projects/projects.html', 'properties.html',
    'properties_add.html', 'properties_edit.html',
    'property_management_dashboard.html', 'recipe_management.html',
    'suppliers.html',
    'suppliers_add.html', 'suppliers_edit.html', 'tenant.html',
    'tenant_add.html', 'tenant_edit.html', 'tenant_lease_agreement.html',
    'title_deeds_management.html',
]

# The twelve pages whose browser tab is currently EMPTY. The name is what the
# page is, in Title Case, matching the 80 pages that already read that way -
# so an add screen says what it adds rather than repeating its module.
FILL_TAB = {
    'act_expense.html': 'Actual Expenses',
    'act_expense_add.html': 'Add Expense',
    'act_expense_edit.html': 'Edit Expense',
    'lease_renewal_report.html': 'Lease Renewal Report',
    'login.html': 'Login',
    'open_invoices_report.html': 'Outstanding Invoices Report',
    'properties_add.html': 'Add Property',
    'properties_edit.html': 'Edit Property',
    'property_report.html': 'Property Details Report',
    'tenant_add.html': 'Add Tenant',
    'tenant_edit.html': 'Edit Tenant',
    'tenant_report.html': 'Tenant Details Report',
}

# The fourteen tabs that carry the brand locally. base supplies it now, so
# each keeps only its page name. The seven that shouted are put into Title
# Case to match the eighty that do not - a tab is read, not scanned.
STRIP_TAB = {
    'comments_report.html': ('Comments Report | Alivente Online',
                             'Comments Report'),
    'finance.html': ('ALIVENTE ONLINE - FINANCE', 'Finance'),
    'finance/financial_indicators.html':
        ('ALIVENTE ONLINE - FINANCIAL INDICATORS', 'Financial Indicators'),
    'finance/vacancy_management.html':
        ('ALIVENTE ONLINE - VACANCY MANAGEMENT', 'Vacancy Management'),
    'finance_pl_act.html': ('ALIVENTE ONLINE - PROFIT & LOSS',
                            'Profit &amp; Loss'),
    'finance_valuations.html': ('ALIVENTE ONLINE - PROPERTY VALUATIONS',
                                'Property Valuations'),
    'friday_status_report.html': ('Friday Status Report | Alivente Online',
                                  'Friday Status Report'),
    'fsr.html': ('Issues Management | Alivente Online', 'Issues Management'),
    'fsr_add.html': ('Add Issue | Alivente Online', 'Add Issue'),
    'notifications.html': ('ALIVENTE ONLINE - NOTIFICATIONS DASHBOARD',
                           'Notifications Dashboard'),
    'occupancy_trends.html': ('Occupancy Trends - Alivente Online',
                              'Occupancy Trends'),
    'property_management_dashboard.html':
        ('ALIVENTE ONLINE - PROPERTY DASHBOARD', 'Property Dashboard'),
    'resolved_issues_report.html':
        ('Resolved Issues Report | Alivente Online', 'Resolved Issues Report'),
    'supplier_report.html': ('Supplier Details | Alivente Online',
                             'Supplier Details'),
}

# The heading round left this comment on 29 pages. It names the prefix, so it
# becomes false today. A file that documents a rule it no longer follows is
# worse than one that documents nothing.
OLD_NOTE = ('Title in capitals prefixed "ALIVENTE ONLINE - "; subtitle in '
            'sentence case.')
NEW_NOTE = ('Title in capitals, no brand prefix - the brand is in the '
            'browser tab. Subtitle in sentence case.')

# The recipe / meal-plan side is a different application sharing the repo,
# and out of this system's standard. 29 templates.
SKIP = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
        'unit_conversions', 'celebration_', 'import_recipe',
        'map_ingredients', 'measurement_units', 'household_member',
        'categories_management')

# ONE OF THEM IS IN SCOPE ANYWAY, and the reason is this round's own doing.
# recipe_management.html extends base.html, so after this round its browser
# tab reads `Recipe Management | Alivente Online` - and if its heading kept
# the prefix the page would state the brand TWICE, which is a defect this
# round would have introduced. Measured on the complete corpus: it is the
# only recipe-side page whose heading carries the brand.
#
# (Measured only after the whole tree was in front of me. An earlier pass
# of this same survey ran against 10 of the 29 recipe-side templates and
# would have reported the same number by luck. Show-ButtonDrift.py's
# name-based exclusion list has already swept a recipe page by accident
# once; a name-based list is a guess about scope, not a statement of it.)
ALSO_IN_SCOPE = ('recipe_management.html',)

FAIL = []


def want(c, m):
    if not c:
        FAIL.append(m)


def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    return raw, ('\r\n' in raw), raw.replace('\r\n', '\n')


def sub1(t, old, new, what):
    n = t.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1' % (what, n))
    return t.replace(old, new, 1)


def markup_of(t):
    return re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t, flags=re.S)


def rel_of(p):
    return os.path.relpath(p, T).replace(os.sep, '/')


TEMPLATES = []
for _d, _s, _fs in os.walk(T):
    for _f in _fs:
        if _f.endswith('.html'):
            TEMPLATES.append(os.path.join(_d, _f))
TEMPLATES = [p for p in TEMPLATES
             if rel_of(p) in ALSO_IN_SCOPE
             or not any(s in rel_of(p) for s in SKIP)]
TEMPLATES.sort()

# ---------------------------------------------------------------------------
# DERIVE the pages to change, and make the derivation agree with the table.
# ---------------------------------------------------------------------------
found = []
for p in TEMPLATES:
    src = load(p)[2]
    m = re.search(r'<(h1|h2)\b[^>]*>(.*?)</\1>', markup_of(src), re.S | re.I)
    if m and PREFIX.rstrip() in m.group(2):
        found.append(rel_of(p))
    elif m and 'ALIVENTE ONLINE' in m.group(2):
        found.append(rel_of(p))          # connectivity_error: no dash
extra = sorted(set(found) - set(EXPECT_H2))
gone = sorted(set(EXPECT_H2) - set(found))
if extra or gone:
    print('! the tree and the table disagree.')
    if extra:
        print('  in the tree but not the table (a page was added or edited):')
        for x in extra:
            print('     %s' % x)
    if gone:
        print('  in the table but not the tree (already done, or renamed):')
        for x in gone:
            print('     %s' % x)
    if not gone:
        sys.exit('  Read them, then add them to EXPECT_H2. Nothing written.')

CHANGED = {}


def edit(rel, fn):
    """Apply fn to one template, recording the result for the write phase."""
    p = os.path.join(T, rel.replace('/', os.sep))
    if not os.path.exists(p):
        want(False, '%s: not found' % rel)
        return
    orig, crlf, f = CHANGED.get(rel, (None, None, None))
    if orig is None:
        orig, crlf, f = load(p)
    CHANGED[rel] = (orig, crlf, fn(f, rel))


def strip_prefix(f, rel):
    mk = markup_of(f)
    m = re.search(r'<(h1|h2)\b[^>]*>(.*?)</\1>', mk, re.S | re.I)
    if not m:
        want(False, '%s: no heading to change' % rel)
        return f
    whole = m.group(0)
    if PREFIX not in whole:
        return f                         # idempotent: already done
    return sub1(f, whole, whole.replace(PREFIX, '', 1),
                '%s: the heading' % rel)


for rel in EXPECT_H2:
    if rel == KEEPS_THE_BRAND:
        continue
    edit(rel, strip_prefix)


def make_fill(name):
    """Fill an EMPTY {% block title %}, whatever whitespace it holds.

       The first version of this built the replacement two different ways -
       one with %-formatting and one with .replace() - and the .replace()
       branch left a literal `{%% endblock %%}` in eleven files. It shipped
       past the self-check because that check looked for `{% endblock` to
       find the end of the block, did not find it, and matched the NEXT one
       thousands of bytes later; the tab then measured 20KB and the check
       only asked whether it was non-empty. A CHECK THAT CANNOT FAIL IS
       WORSE THAN NO CHECK. There is now one construction, and the check
       below asserts the tab is short and holds no markup."""
    def _f(f, rel):
        m = re.search(r'\{%\s*block title\s*%\}(\s*)\{%\s*endblock[^%]*%\}',
                      f)
        if not m:
            return f                     # already filled, or not empty
        return sub1(f, m.group(0),
                    '{% block title %}' + name + '{% endblock %}',
                    '%s: the tab' % rel)
    return _f


for rel, name in FILL_TAB.items():
    edit(rel, make_fill(name))


def make_strip(was, now):
    def _f(f, rel):
        if was not in f:
            return f                     # already done, or whitespace differs
        return sub1(f, was, now, '%s: the branded tab' % rel)
    return _f


for rel, (was, now) in STRIP_TAB.items():
    edit(rel, make_strip(was, now))


def renote(f, rel):
    return f.replace(OLD_NOTE, NEW_NOTE) if OLD_NOTE in f else f


NOTED = [rel_of(p) for p in TEMPLATES if OLD_NOTE in load(p)[2]]
for rel in NOTED:
    edit(rel, renote)

# ---------------------------------------------------------------------------
# base.html - the tab gains the brand, once, for every page at no cost.
# ---------------------------------------------------------------------------
B_ORIG, B_CRLF, B = load(BASE)
WAS_TITLE = "<title>{% block title %}Hello, world!{% endblock %}</title>"
NEW_TITLE = ("<title>{% block title %}{% endblock %}" + SEP + BRAND
             + "</title>")
if WAS_TITLE in B:
    B = sub1(B, WAS_TITLE, NEW_TITLE, 'BASE: the title tag')
elif NEW_TITLE not in B:
    want(False, 'BASE: the title tag is neither the old one nor the new one - '
                'somebody has edited it; read it before rerunning')

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
want(NEW_TITLE in B, 'BASE: the tab does not carry the brand')
want(B.count(BRAND) >= 1, 'BASE: the brand is not in base at all')
want('Hello, world!' not in B, 'BASE: the placeholder is still there')

for rel, (orig, crlf, f) in CHANGED.items():
    mk = markup_of(f)
    m = re.search(r'<(h1|h2)\b[^>]*>(.*?)</\1>', mk, re.S | re.I)
    if rel in EXPECT_H2 and rel != KEEPS_THE_BRAND:
        want(m is not None and PREFIX not in m.group(0),
             '%s: the heading still carries the prefix' % rel)
        want(m is not None and re.sub(r'<[^>]+>', '', m.group(2)).strip(),
             '%s: the heading is empty now' % rel)
    # THE WORDS OF THE TITLE MUST SURVIVE. This round removes a constant, and
    # nothing else. A round about a prefix must not rename a page.
    om = re.search(r'<(h1|h2)\b[^>]*>(.*?)</\1>',
                   markup_of(orig.replace('\r\n', '\n')), re.S | re.I)
    if om and m:
        was_w = [w for w in re.findall(r'[A-Za-z]{3,}',
                                       re.sub(r'\{[{%#][^}]*[}%#]\}', '',
                                              om.group(2)))
                 if w.upper() not in ('ALIVENTE', 'ONLINE')]
        now = re.sub(r'\{[{%#][^}]*[}%#]\}', '', m.group(2)).upper()
        want(all(w.upper() in now for w in was_w),
             '%s: a word of the title did not survive' % rel)
    # Structure untouched: this round edits text.
    for tag in ('div', 'h2', 'h1'):
        a = (len(re.findall(r'<%s\b' % tag, mk))
             - len(re.findall(r'</%s>' % tag, mk)))
        b = (len(re.findall(r'<%s\b' % tag,
                            markup_of(orig.replace('\r\n', '\n'))))
             - len(re.findall(r'</%s>' % tag,
                              markup_of(orig.replace('\r\n', '\n')))))
        want(a == b, '%s: <%s> balance moved %+d -> %+d' % (rel, tag, b, a))

# THE TAB, CHECKED SO THAT IT CAN ACTUALLY FAIL.
#
# Non-empty is not enough. A malformed replacement left `{%% endblock %%}`
# in the file, the regex below ran past it to the next `{% endblock` in the
# page, and the tab measured twenty thousand bytes of markup - which is
# non-empty, and passed. So: short, no markup, no Django tag, no brand.
for rel, (orig, crlf, f) in CHANGED.items():
    bt = re.search(r'\{%\s*block title\s*%\}(.*?)\{%\s*endblock[^%]*%\}',
                   f, re.S)
    if bt is None:
        want('{% block title %}' not in f,
             '%s: the tab opens but never closes - a malformed replacement'
             % rel)
        continue
    _t = re.sub(r'\s+', ' ', bt.group(1)).strip()
    want(_t != '', '%s: the tab is still empty' % rel)
    want(len(_t) <= 120, '%s: the tab is %d characters - it has swallowed '
         'the page' % (rel, len(_t)))
    want('<' not in _t, '%s: the tab contains markup: %r' % (rel, _t[:60]))
    want('{%' not in _t.replace('{% if', '@').replace('{% else', '@')
         .replace('{% endif', '@'),
         '%s: the tab contains an unexpected Django tag: %r' % (rel, _t[:60]))
    want('%%' not in _t, '%s: the tab holds a literal %%%% - a formatting '
         'bug, which is how this check came to exist' % rel)
    want('livente' not in _t.lower(),
         '%s: the tab still names the brand, which base now adds' % rel)

want(not [r for r in NOTED if OLD_NOTE in CHANGED[r][2]],
     'a round comment still names the prefix')

_kept = load(os.path.join(T, KEEPS_THE_BRAND.replace('/', os.sep)))[2]
want('ALIVENTE ONLINE' in _kept,
     '%s: the one page that keeps the brand lost it' % KEEPS_THE_BRAND)
want(KEEPS_THE_BRAND not in CHANGED
     or PREFIX not in CHANGED[KEEPS_THE_BRAND][2],
     'the exception page was edited by the prefix pass')

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)

# ---------------------------------------------------------------------------
print('  %-46s %6d -> %6d bytes'
      % ('base.html', len(B_ORIG.encode('utf-8')),
         len((B.replace('\n', '\r\n') if B_CRLF else B).encode('utf-8'))))
print('      the tab is now:  %s' % NEW_TITLE)
print()
_n = 0
for rel in sorted(CHANGED):
    orig, crlf, f = CHANGED[rel]
    out = f.replace('\n', '\r\n') if crlf else f
    if out == orig:
        continue
    _n += 1
    print('  %-46s %6d -> %6d bytes'
          % (rel, len(orig.encode('utf-8')), len(out.encode('utf-8'))))
print('\n  %d template(s) changed  (%d headings, %d empty tabs filled, '
      '%d tabs de-branded,\n  %d round comments reworded, 1 page keeps the '
      'brand on purpose)'
      % (_n, len(EXPECT_H2) - 1, len(FILL_TAB), len(STRIP_TAB), len(NOTED)))

if not CHECK:
    bak = BASE + '.bak_pfx'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(B_ORIG)
    with open(BASE, 'w', encoding='utf-8', newline='') as fh:
        fh.write(B.replace('\n', '\r\n') if B_CRLF else B)
    for rel in sorted(CHANGED):
        orig, crlf, f = CHANGED[rel]
        out = f.replace('\n', '\r\n') if crlf else f
        if out == orig:
            continue
        p = os.path.join(T, rel.replace('/', os.sep))
        bak = p + '.bak_pfx'
        if not os.path.exists(bak):
            with open(bak, 'w', encoding='utf-8', newline='') as fh:
                fh.write(orig)
        with open(p, 'w', encoding='utf-8', newline='') as fh:
            fh.write(out)

print('\n  --check: nothing written.' if CHECK else '\n  done.')
