# -*- coding: utf-8 -*-
"""test_colour_census.py - 30 Oct 2026.

RELEASE 41 - THE COLOUR-LITERAL CENSUS GETS AN OWNER. His plan of 29-30
October: a guard, not a sweep. Nothing on any page changes.

The house colours are tokens - var(--alv-accent), var(--alv-ink) and the
rest, defined once in base.html. Rounds B-1 to B-7 turned ~1,500 raw hex
colours into tokens, and nothing stopped new ones arriving afterwards.
This suite freezes what is left: 539 literals on 70 templates, counted per
template. A template may only go DOWN.

    - A template that gains a hex colour fails, by name.
    - A template that loses one fails too, until its number here is
      lowered - so the gain is locked in and cannot be spent later.
    - base.html is not counted: it is where the tokens are defined.
    - Standalone templates (PDF bodies, emails, the signing pages, the
      connectivity page) cannot read base's tokens and keep their
      literals by necessity. They are frozen like the rest; one that
      genuinely needs a new colour raises its number here, with a reason.

What counts as a literal: #rgb, #rgba, #rrggbb or #rrggbbaa as a value,
in markup, CSS or script, with template and HTML/CSS/JS comments
stripped (alv_tree.code_only). Not an element id in a selector
(#add-btn), not a link to an anchor (href="#top"), not a character
reference (&#123;). Section 2 proves each of those.
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

ME = 'test_colour_census.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
GATE = J(ROOT, PS1)

# A hex colour as a value. Not preceded by a word character, &, /, # or -
# (an id, a path, a character reference, a doubled #), and not followed by
# one (a longer id such as #add-btn, or a non-hex word).
HEX = re.compile(r'(?<![\w&/#-])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|'
                 r'[0-9a-fA-F]{3,4})(?![\w-])')

CEILING = {
    'act_expense.html': 26,
    'admin_apms.html': 1,
    'cash_receipt_detail.html': 2,
    'categories_management.html': 2,
    'celebration_calendar.html': 1,
    'comments_report.html': 1,
    'components/pdf_viewer.html': 9,
    'crs/submission_detail.html': 2,
    'customer_invoice_form.html': 7,
    'dashboard_pl.html': 15,
    'error_pages/connectivity_error.html': 24,
    'finance/cashflow_forecast.html': 6,
    'finance/financial_indicators.html': 16,
    'finance/vacancy_management.html': 7,
    'finance_expense.html': 1,
    'finance_expense_add.html': 3,
    'finance_expense_edit.html': 4,
    'finance_expense_line_types.html': 1,
    'finance_expense_line_types_add.html': 1,
    'finance_expense_line_types_edit.html': 2,
    'finance_expense_types.html': 1,
    'finance_pl_act.html': 8,
    'finance_revenue.html': 2,
    'finance_revenue_line_types.html': 1,
    'finance_revenue_types.html': 1,
    'finance_valuations_add.html': 1,
    'finance_valuations_edit.html': 5,
    'fsr.html': 14,
    'fsr_email.html': 9,
    'generate_lease_agreement.html': 1,
    'help_modal_shell.html': 3,
    'help_page.html': 12,
    'home.html': 16,
    'household_member_management.html': 1,
    'import_recipe.html': 4,
    'ingredient_base_units_management.html': 34,
    'invoices/physical_invoice.html': 20,
    'lease_agreement_report.html': 1,
    'lease_sign_styles.html': 23,
    'lease_timeline.html': 4,
    'manual_pdf.html': 51,
    'map_ingredients_nutrition.html': 6,
    'meal_plan_shopping_list.html': 1,
    'measurement_units_management.html': 8,
    'occupancy_trends.html': 4,
    'personal.html': 1,
    'personal_notification_settings.html': 1,
    'physical_invoice_edit.html': 7,
    'physical_invoice_list.html': 3,
    'preview_imported_recipe.html': 11,
    'projects/project_gantt.html': 12,
    'projects/project_task_list.html': 1,
    'projects/project_tasks_edit.html': 1,
    'properties_edit.html': 2,
    'property_assets.html': 2,
    'property_report.html': 2,
    'receipts/cash_receipt.html': 19,
    'recipe_management.html': 52,
    'recipe_pdf.html': 20,
    'supplier_report.html': 1,
    'tenant_add.html': 1,
    'tenant_edit.html': 1,
    'tenant_payment_days.html': 1,
    'tenant_report.html': 2,
    'total_expense_details.html': 4,
    'unit_conversions_management.html': 3,
    'unit_conversions_wizard.html': 2,
    'user_permissions.html': 1,
    'view_recipe.html': 21,
    'wcim_recipe_quick_view.html': 6,
}

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
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402


def literals(text):
    """The hex colour literals in a template's text, comments stripped."""
    t = T.code_only(text)
    t = re.sub(r'href="#[^"]*"', '', t)
    return HEX.findall(t)


# ==========================================================================
head('1. THE CENSUS - every template at or below its number')
# ==========================================================================
now, seen = {}, set()
for p in T.templates():
    rel = T.rel(p).replace(os.sep, '/')
    seen.add(rel)
    if rel == 'base.html':
        continue
    n = len(literals(read(p)))
    if n:
        now[rel] = n
rose = sorted((r, CEILING.get(r, 0), n) for r, n in now.items()
              if n > CEILING.get(r, 0))
for r, was_n, n in rose:
    print('         %-44s %d -> %d   use a var(--alv-...) token' % (r, was_n, n))
ok(not rose, 'no template has gained a hex colour literal',
   ', '.join('%s %d->%d' % x for x in rose))
fell = sorted((r, c, now.get(r, 0)) for r, c in CEILING.items()
              if now.get(r, 0) < c)
for r, c, n in fell:
    print('         %-44s %d -> %d   lower CEILING to lock it in' % (r, c, n))
ok(not fell, '  and none has lost one without its number here being '
   'lowered', ', '.join('%s %d->%d' % x for x in fell))
ok(sum(now.values()) == sum(CEILING.values()),
   '  %d literals on %d templates, the number frozen here'
   % (sum(CEILING.values()), len(CEILING)),
   '%d on %d' % (sum(now.values()), len(now)))
gone = sorted(r for r in CEILING if r not in seen)
ok(not gone, '  and every template named here still exists', gone)

# ==========================================================================
head('2. CONTROLS - the detector finds what it should and nothing else')
# ==========================================================================
ok(len(literals('<style>.a { color: #0e7c8b; background:#FFF; }</style>'))
   == 2, 'CONTROL: it finds a 6-digit and a 3-digit colour')
ok(len(literals('<div style="border:1px solid #ddd"></div>')) == 1,
   'CONTROL: and one in a style attribute')
ok(len(literals("<script>var c = ['#2b6a86', '#55606bcc'];</script>")) == 2,
   'CONTROL: and one in script, 8-digit included')
ok(literals('<style>#add-btn { width: 1px } #cafe-list{}</style>') == [],
   'CONTROL: not an element id in a selector')
ok(literals('<a href="#bed">x</a>') == [], 'CONTROL: not a link to an anchor')
ok(literals('<p>&#123; &#x26;</p>') == [],
   'CONTROL: not a character reference')
ok(literals('<style>/* #abcdef */</style>{# #fff #}<!-- #000 -->') == [],
   'CONTROL: not in a comment')
ok(literals('<style>.a{color:var(--alv-accent)}</style>') == [],
   'CONTROL: a token is not a literal')
base = read(T.join('base.html'))
ok(len(literals(base)) > 0,
   'CONTROL: base.html does carry literals - it defines the tokens - '
   'which is why it is not counted')

# ==========================================================================
head('3. REGISTERED')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, '%s is on the push gate suite list' % ME)
ok(ME in T.CONVERTED, '  and in alv_tree.CONVERTED - it walks every root')
wd = read(J(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
