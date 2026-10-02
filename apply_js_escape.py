# -*- coding: utf-8 -*-
"""SECTION J, ROUND J-1 - A NAME WITH AN APOSTROPHE IN IT

Demetri asked one question about DB-4: "Is this for the P&L in Financials
as well as the P&L in Dashboard?"

The answer was no, and finding out why turned a one-template fix into
this. DB-4 repaired ONE inline handler that pasted a filename into a
JavaScript string literal. The same shape is in 19 templates.

==========================================================================
THE DEFECT, IN ONE LINE
==========================================================================
    onclick="viewLeaseAgreement('{{ tresults.tenant_lease_agreement.url }}',
                                '{{ tresults.tenant_name }}')"

A tenant called O'Brien closes that string early and the handler does not
PARSE. Not a runtime error on an odd path - a syntax error, so the button
does nothing at all, silently, every time, for that tenant.

AND THE SOURCE LOOKS CORRECT, which is why this has survived. Django
autoescapes, so the template output carries O&#x27;Brien - a proper HTML
entity. The browser decodes it while parsing the ATTRIBUTE and hands the
JavaScript parser a bare apostrophe inside a quoted string. Two languages
nested in one attribute; the escaping covers the outer one only.

Django has the filter for the inner one, and this tree already uses it in
38 places: |escapejs.

==========================================================================
THE CENSUS
==========================================================================
Every inline event handler in every template - onclick, onchange,
onsubmit, oninput, onkeydown, onblur and the rest - and every {{ }} that
sits inside a single-quoted JavaScript string literal in one:

    192 interpolations
     45 already |escapejs
    147 unprotected, across 20 templates

(The first pass said 183 / 38 / 145 across 19. It walked pages/templates
with its own os.walk and never saw crs/templates - the second app. X0
built alv_tree.roots() precisely so that nothing would do that again, and
this round did it anyway. The tree-wide gate below is what caught it.)

The ones that will be met in ordinary use:

    tenant.html                    8   a tenant's name, a lease filename
    tenant_lease_agreement.html    8   the same, twice over
    title_deeds_management.html   10   a property's name, six times
    properties.html                6   a property's name, a deed filename
    passport_management.html      29   a holder's name, a document number
    celebration_management.html   24   a contact's name, an email
    user_administration.html       6   a username
    property_detail.html           2   THE DASHBOARD P&L - the question
                                       that started this
    asset_detail.html              9   an invoice name, a service provider
    recipe_management.html         8   a recipe name
    unit_conversions_management    6   unit and ingredient names
    meal_plan_calendar.html        6   plan and day names
    preview_imported_recipe.html   5   a recipe document
    projects/projects_detail.html  5   a task name and status
    view_recipe.html               4   a recipe document
    cash_receipts.html             4   see below
    total_expense_details.html     2   an expense document
    ingredient_families.html       2   a family name
    finance/financial_indicators   1   a label

CASH RECEIPTS IS THE ONE THAT SETTLES THE METHOD. It reads

    openPdfViewer('{% url ... %}',
                  'Receipt {{ row.number|escapejs }} - {{ row.payer|escapejs }}',
                  '{{ row.number }}.pdf')

Two of the three arguments were escaped and the third was not, by the
same hand on the same line. Per-site judgement does not survive contact
with a long file. So the rule here is mechanical and total.

==========================================================================
WHAT THIS ROUND DOES, AND WHAT IT REFUSES TO DO
==========================================================================
EVERY interpolation inside a JS string literal in an inline handler gets
|escapejs appended, as the last filter. Including the ones that hold a
number or a date today. Escaping a number costs nothing; deciding which
values are "safe" costs a judgement per site, and a field that is numeric
today can become free text tomorrow - which is exactly how the one
unescaped argument on that Receipts line happened.

APPENDED LAST, so an existing filter chain is untouched:
    {{ x|date:"Y-m-d" }}  ->  {{ x|date:"Y-m-d"|escapejs }}

A HUNDRED AND ELEVEN OTHERS ARE LEFT ALONE, AND NAMED. An interpolation in a
handler but NOT inside a string literal is a bare argument:

    onclick="deleteCategory({{ item.category.ingredient_category_id }})"

|escapejs would not help there - the value is unquoted, so anything
non-numeric is a syntax error with or without it, and the repair is to
add quotes, which changes what the function receives. Every one of the 111
is an id. They are counted and named so this round's silence about them
is a decision rather than an oversight.

AND NOTHING ELSE MOVES. The gate proves it exactly: strip every
occurrence of |escapejs from the new file and from the old, and the two
must be byte-identical. A round that can say that cannot have changed
anything else by accident.

Backups: .bak_jsescape. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_jsescape'
CRLF = {}
SENTINEL = 'test_js_escape.py'
ROOT = os.getcwd()

# Every inline event handler attribute. Double-quoted only, which is what
# the tree uses - the census found no single-quoted handler attribute at
# all, and a handler written that way could not hold a JS string in
# single quotes anyway.
HANDLER = re.compile(r'\bon[a-z]+\s*=\s*"([^"]*)"')
# A single-quoted JavaScript string literal with at least one {{ }} in it.
INSTR = re.compile(r"'(?:[^'\\]|\\.)*?\{\{.*?\}\}(?:[^'\\]|\\.)*?'", re.S)
VAR = re.compile(r'\{\{\s*(.+?)\s*\}\}', re.S)
HTML_C = re.compile(r'<!--.*?-->', re.S)

# What the census measured, written down so the suite reads the same
# numbers and the two cannot drift.
EXPECT = {
    'passport_management.html': 29,
    'celebration_management.html': 24,
    'title_deeds_management.html': 10,
    'asset_detail.html': 9,
    'recipe_management.html': 8,
    'tenant.html': 8,
    'tenant_lease_agreement.html': 8,
    'meal_plan_calendar.html': 6,
    'properties.html': 6,
    'unit_conversions_management.html': 6,
    'user_administration.html': 6,
    'preview_imported_recipe.html': 5,
    'projects/projects_detail.html': 5,
    'cash_receipts.html': 4,
    'view_recipe.html': 4,
    'ingredient_families.html': 2,
    'property_detail.html': 2,
    'total_expense_details.html': 2,
    'finance/financial_indicators.html': 1,
    # FOUND BY THE TREE-WIDE GATE, NOT BY THE CENSUS.
    #
    # The census that opened this round walked pages/templates with its
    # own os.walk and missed this file entirely, because THERE IS A
    # SECOND APP: crs/templates. alv_tree.roots() has known about both
    # all along - that is what X0 built it for, and what X0's register
    # exists to stop happening again - and the hand-rolled walk made the
    # exact mistake X0 was created to end.
    #
    # It is the cash_receipts shape again, too: the country NAME is
    # escaped and the country CODE beside it is not, on the same line.
    'crs/country_list.html': 2,
}
TOTAL = sum(EXPECT.values())
# 45, NOT THE 38 THE CENSUS FIRST REPORTED - the same blind spot, found
# the same way. 38 was a pages/templates figure; crs/templates holds the
# other seven. Measured across alv_tree.templates(), which is the only
# count that means anything.
ALREADY_SAFE = 45
# 111, NOT 98 - the pages/templates-only census again. crs/templates
# holds the other thirteen, every one of them a primary key.
BARE_ARGS = 111


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('J1: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('J1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


def filters_of(expr):
    """The filter names in a {{ }} body, ignoring any | inside a quoted
    filter argument - `{{ x|default:"a|b" }}` has one filter, not two."""
    out, depth, cur, q = [], 0, '', None
    for ch in expr:
        if q:
            cur += ch
            if ch == q:
                q = None
            continue
        if ch in '"\'':
            q = ch
            cur += ch
            continue
        if ch == '|':
            out.append(cur)
            cur = ''
            continue
        cur += ch
    out.append(cur)
    return [x.strip().split(':')[0] for x in out[1:]]


def protect(text):
    """Append |escapejs to every {{ }} inside a JS string literal in an
    inline handler. Returns (new_text, how_many_changed).

    WORKS BACKWARDS THROUGH THE FILE. Every insertion lengthens the text,
    so editing front-to-back invalidates every offset found after it. The
    first draft did that and silently mangled the long files, where it
    matters most.
    """
    blanked = HTML_C.sub(lambda m: ' ' * len(m.group(0)), text)
    edits = []
    for h in HANDLER.finditer(blanked):
        base = h.start(1)
        for lit in INSTR.finditer(h.group(1)):
            for v in VAR.finditer(lit.group(0)):
                if 'escapejs' in filters_of(v.group(1)):
                    continue
                # the offset of the closing }} of this {{ }}, in the file
                end = base + lit.start() + v.end()
                edits.append((end, v.group(1)))
    out, n = text, 0
    for end, expr in sorted(edits, reverse=True):
        close = out.index('}}', end - 2) if out[end - 2:end] == '}}' else None
        if close is None:
            raise SystemExit('J1: lost the closing }} for %r' % expr[:40])
        # insert immediately before the closing }}, keeping any trailing
        # space the author wrote
        i = close
        while i > 0 and out[i - 1] in ' \t':
            i -= 1
        out = out[:i] + '|escapejs' + out[i:]
        n += 1
    return out, n


def census(text):
    """(unprotected, already-safe) inside JS string literals."""
    blanked = HTML_C.sub(lambda m: ' ' * len(m.group(0)), text)
    bad = safe = 0
    for h in HANDLER.finditer(blanked):
        for lit in INSTR.finditer(h.group(1)):
            for v in VAR.finditer(lit.group(0)):
                if 'escapejs' in filters_of(v.group(1)):
                    safe += 1
                else:
                    bad += 1
    return bad, safe


print('=' * 74)
print('SECTION J, ROUND J-1 - A NAME WITH AN APOSTROPHE IN IT%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)
print('')
print('  %-38s %6s %6s' % ('template', 'fixed', 'was'))
print('  ' + '-' * 70)

# THE TREE, NOT A ROOT OF THIS ROUND'S OWN. alv_tree.templates() walks
# every root there is - pages/templates AND crs/templates - which is the
# whole reason X0 built it, and the reason this round found a file its
# own census had missed.
PATHS = dict((alv_tree.rel(p), p) for p in alv_tree.templates())
missing = sorted(set(EXPECT) - set(PATHS))
if missing:
    raise SystemExit('J1: the census names %s, which the tree does not have'
                     % missing[:3])

done = {}
for rel in sorted(EXPECT):
    p = PATHS[rel]
    t, raw = read(p)
    bad, safe = census(t)
    if bad == 0:
        print('  %-38s %6s %6d' % (rel, 'done', safe))
        done[rel] = 0
        continue
    if bad != EXPECT[rel]:
        raise SystemExit('J1: %s has %d unprotected, the census said %d - '
                         'the file has changed under this round' %
                         (rel, bad, EXPECT[rel]))
    new, n = protect(t)
    if n != bad:
        raise SystemExit('J1: %s - found %d and changed %d' % (rel, bad, n))
    # NOTHING ELSE MOVED, PROVED EXACTLY.
    if new.replace('|escapejs', '') != t.replace('|escapejs', ''):
        raise SystemExit('J1: %s changed something other than the filter' % rel)
    if not CHECK:
        back_up(p, raw)
        write(p, new)
    done[rel] = n
    print('  %-38s %6d %6d' % (rel, n, safe))

print('  ' + '-' * 70)
print('  %-38s %6d' % ('', sum(done.values())))

# ==========================================================================
print('')
print('  THE SCOPE GUARD THAT READ THE LIVE FILE')
print('  ' + '-' * 70)
# test_filter_on_close.py carries a SCOPE GUARD on recipe_management.html:
# "every edit falls in one of the five places this round declared". It
# diffs that round's backup against the page - and it reads the page
# LIVE, so it is not measuring what that round did. It is measuring
# everything that has happened to the file since.
#
# J-1 added |escapejs at eight sites in that file and the guard called
# them strays. It was right to notice and wrong about whose they were.
#
# alv_rounds.as_left_by() IS THE TOOL FOR THIS, and the house already has
# it: the file as THAT round left it, found by walking forward to the next
# backup. A scope guard that reads it measures its own round forever,
# whatever lands afterwards. Only section 5 changes - every other check in
# that file wants the live page and keeps it.
FC = os.path.join(ROOT, 'test_filter_on_close.py')
ft, fraw = read(FC)
if 'as_left_by' in ft:
    print('  test_filter_on_close.py            already done')
else:
    ft = swap(ft, """try:
    from alv_rounds import ROUNDS
except Exception:
    ROUNDS = []
""", """try:
    from alv_rounds import ROUNDS
except Exception:
    ROUNDS = []
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
""", 'the alv_rounds import', FC)
    # RAW STRINGS. The anchor contains a literal backslash-n, because
    # the line it matches is Python source inside that suite - not a
    # newline. The first draft used an ordinary triple-quoted string and
    # looked for a real line break, and matched nothing.
    ft = swap(ft, r"""    import difflib
    a, b = was.split('\n'), page.split('\n')
""", r"""    import difflib
    # AS THIS ROUND LEFT IT, NOT AS THE PAGE IS TODAY - J-1, 2 Oct 2026.
    #
    # This compared the round's backup against the LIVE file, so it was
    # never measuring this round's scope: it measured every edit any
    # LATER round has made to recipe_management.html. J-1 added
    # |escapejs at eight sites in it and the guard reported eight
    # strays - correctly spotted, wrongly attributed.
    #
    # as_left_by() walks forward to the next backup and returns the file
    # as THIS round left it, so the claim stays about this round however
    # many land afterwards.
    _left = (as_left_by(PATH, SUFFIX, read) if as_left_by else page)
    a, b = was.split('\n'), _left.split('\n')
""", 'the scope diff', FC)
    if not CHECK:
        back_up(FC, fraw)
        write(FC, ft)
    print('  test_filter_on_close.py            its scope guard reads the '
          'file as IT left it')

# ==========================================================================
print('')
print('  REGISTRATION')
print('  ' + '-' * 70)



for rel, old, new, what, mark in (
        ('alv_rounds.py', "    '.bak_plicon',\n]\n",
         "    '.bak_plicon',\n    '%s',\n]\n" % SUFFIX,
         'the end of ROUNDS', SUFFIX),
        ('Push-PendingChanges.ps1', "    'test_pl_invoice_icon.py'\n)\n",
         "    'test_pl_invoice_icon.py'\n"
         "    # A name with an apostrophe in it. 145 values across 19\n"
         "    # templates were pasted into JavaScript string literals in\n"
         "    # inline handlers, so a tenant called O'Brien made the View\n"
         "    # Lease Agreement button a syntax error - it did nothing, in\n"
         "    # silence. Its section 2 renders through Django and clicks in\n"
         "    # Chromium; its section 1 is the gate that catches the next one.\n"
         "    'test_js_escape.py'\n)\n", 'the end of $suites', SENTINEL)):
    path = os.path.join(ROOT, rel)
    tt, rr = read(path)
    if mark in tt:
        print('  %-34s already done' % rel)
        continue
    tt = swap(tt, old, new, what, path)
    if not CHECK:
        back_up(path, rr)
        write(path, tt)
    print('  %-34s %s' % (rel, what))

print('')
print('  GATES')
print('  ' + '-' * 70)
if CHECK:
    print('  skipped - they read the finished files, and --check writes none')
    print('-' * 74)
    print('  CHECK ONLY - nothing written')
    print('=' * 74)
    raise SystemExit(0)

# NOT ONE UNPROTECTED INTERPOLATION LEFT, ANYWHERE IN THE TREE - not just
# in the nineteen. The census is the point of this round; a gate that
# only looked where the round looked would miss the twentieth file.
left, safe_now = [], 0
for p in alv_tree.templates():
    bad, safe = census(read(p)[0])
    safe_now += safe
    if bad:
        left.append('%s: %d' % (alv_tree.rel(p), bad))
if left:
    raise SystemExit('J1: still unprotected:\n   %s' % '\n   '.join(left[:8]))
print('  not one unprotected interpolation left in any template')
print('  and %d are now |escapejs, against %d before' % (safe_now,
                                                         ALREADY_SAFE))
if safe_now != TOTAL + ALREADY_SAFE:
    raise SystemExit('J1: %d protected, expected %d'
                     % (safe_now, TOTAL + ALREADY_SAFE))

# EVERY TEMPLATE STILL TOKENISES. Django's own lexer, so a {{ }} this
# round broke is found here rather than on the deployed site.
from django.template.base import Lexer, TokenType  # noqa: E402
bad_tok = []
for p in alv_tree.templates():
    for tok in Lexer(read(p)[0]).tokenize():
        if tok.token_type is TokenType.VAR and not tok.contents.strip():
            bad_tok.append(alv_tree.rel(p))
if bad_tok:
    raise SystemExit('J1: an empty {{ }} appeared in %s' % bad_tok[:4])
print("  and every template still tokenises under Django's own lexer")

# THE FILTER IS APPENDED LAST, EVERY TIME. |escapejs before another
# filter would be escaped output fed to something else.
mid = []
for rel in sorted(EXPECT):
    t = read(PATHS[rel])[0]
    for h in HANDLER.finditer(HTML_C.sub('', t)):
        for lit in INSTR.finditer(h.group(1)):
            for v in VAR.finditer(lit.group(0)):
                f = filters_of(v.group(1))
                if 'escapejs' in f and f[-1] != 'escapejs':
                    mid.append('%s: %s' % (rel, v.group(1)[:50]))
if mid:
    raise SystemExit('J1: |escapejs is not the last filter:\n   %s'
                     % '\n   '.join(mid[:4]))
print('  and it is the LAST filter at every site, never mid-chain')

# THE 98 BARE ARGUMENTS ARE UNTOUCHED, AND COUNTED.
bare = 0
for p in alv_tree.templates():
    t = HTML_C.sub('', read(p)[0])
    for h in HANDLER.finditer(t):
        body = h.group(1)
        spans = [m.span() for m in INSTR.finditer(body)]
        spans += [m.span() for m in re.finditer(r"'(?:[^'\\]|\\.)*'", body)]
        for v in VAR.finditer(body):
            if not any(a <= v.start() < b for a, b in spans):
                bare += 1
if bare != BARE_ARGS:
    raise SystemExit('J1: %d bare arguments, the census said %d'
                     % (bare, BARE_ARGS))
print('  the %d bare arguments are untouched - escaping an UNQUOTED value '
      'helps' % bare)
print('  nothing, and every one of them is an id')

print('-' * 74)
print("  A tenant called O'Brien can open their lease agreement. So can a")
print("  property called St John's Court open its title deed.")
print('=' * 74)
