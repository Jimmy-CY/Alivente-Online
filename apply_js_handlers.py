# -*- coding: utf-8 -*-
"""SECTION J, ROUND J-2 - THE HANDLERS JAVASCRIPT WRITES

J-1 put |escapejs on 147 Django variables that sit inside JavaScript string
literals, and the defect it fixed was this one:

    onsubmit="return confirm('DELETE TENANT: {{ tresults.tenant_name }} ...')"

    tenant      confirm dialog      form submitted
    Smith       shown               only on OK
    O'Brien     NEVER APPEARS       yes, regardless

A name with an apostrophe closed the JS string early, the handler became a
SYNTAX ERROR, and there was no function left to return false from.

J-1 COULD NOT REACH THE HANDLERS THAT JAVASCRIPT ITSELF WRITES. A Django
filter runs when Django renders the page; a button built by a template
literal in a <script> block never passes through one. Seven of those carry
a user-supplied string, and this is what they do with it:

    recipe_management.html  deleteRecipe(${id}, '${recipe.recipe_name}')
                            NO ESCAPING AT ALL - three sites

    recipe_management.html  duplicateRecipe(${id},
                              '${recipe.recipe_name.replace(/'/g, "\\'")}')
                            apostrophes only - three sites

    act_expense.html        reportViewInvoice(\\'' + e.doc_url + '\\', ...
                            NO ESCAPING AT ALL - one site

So Delete, on a recipe whose name contains an apostrophe, in the list that
the live search re-renders, does NOTHING. Not a wrong dialog - no dialog,
because there is no handler. The three Duplicate buttons survive an
apostrophe and still break on a double quote, which closes the ATTRIBUTE
rather than the string, or on a backslash, which escapes the escape.

And the Report drill's invoice icon is dead for any invoice whose filename
has an apostrophe in it. test_pl_invoice_icon.py has been saying so since
DB-4 shipped - "SAME defect, different modal, named rather than quietly
left" - with a detail line reading "not found - has it been fixed?". This
is the round that answers it, and that check is rewritten here to assert
the fix rather than the fault.

==========================================================================
THE HOUSE ANSWER IS NOT A BETTER ESCAPE. IT IS NO STRING AT ALL.
==========================================================================
DB-4 settled this on act_expense itself. A value does not go into a
handler; it goes into a DATA ATTRIBUTE, and ONE DELEGATED LISTENER reads
it back:

    <i class="verify-icon" data-invoice-url="..." data-filename="...">

    document.addEventListener('click', function (e) {
        var icon = e.target.closest('.verify-icon');
        ...
        viewInvoiceQuick(icon.getAttribute('data-invoice-url'), ...);
    });

There is no JS string to close early, because there is no JS string. The
value is attribute text, the browser's own parser decodes it, and the
delegated listener survives the table being re-rendered underneath it -
which is the other half of why DB-4 did it this way.

==========================================================================
WHAT THIS ROUND CONVERTS - THIRTEEN SITES, TWO PAGES
==========================================================================
recipe_management.html, twelve buttons in four renderings of the same list:

    6  written by Django, carrying {{ recipe.recipe_name|escapejs }}
    6  written by JavaScript, carrying ${recipe.recipe_name}

THE SIX DJANGO ONES ARE NOT BROKEN, AND THEY ARE CONVERTED ANYWAY. That is
deliberate and it is DB-4's lesson repeated: "the same two attributes, so
the icon works in the table AND in the modal that injects the table, with
one spelling between them." A page where half the buttons are wired one way
and half the other is a page where the next change fixes one half.

act_expense.html, one icon in the Report drill. Its delegated listener
already exists - DB-4 installed it - so this round widens that listener's
selector from `.verify-icon` to `.verify-icon, .report-invoice-icon` rather
than adding a second one. reportViewInvoice() then has no callers and no
reason to exist: it did exactly what viewInvoiceQuick() does, down to the
'Expense Invoice' title and the split('/').pop(), so it goes.

AND ONE HELPER, SPELLED THE WAY THIS APP ALREADY SPELLS IT. act_expense
carries escapeHtml() and uses it for the description cell two lines below
the icon it forgot. recipe_management has no such helper; it gets the same
one, byte for byte, rather than a second spelling of the same five
replacements.

Backups: .bak_jshandlers. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_jshandlers'
CRLF = {}
ROOT = os.getcwd()


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('J2: %s is not a byte copy' % bak)


def swap(text, old, new, what, path, times=1):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != times:
        raise SystemExit('J2: %s appears %d times, not %d' % (what, c, times))
    return text.replace(o, n)


SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script>', re.S)

# The two shapes, counted before anything is touched. EXACT COUNTS, and the
# patcher refuses rather than doing half.
DJANGO = re.compile(
    r'onclick="(duplicate|delete)Recipe\(\{\{ recipe\.recipe_id \}\}, '
    r"'\{\{ recipe\.recipe_name\|escapejs \}\}'\)\"")
JSLIT = re.compile(
    r'onclick="(duplicate|delete)Recipe\(\$\{recipe\.recipe_id\}, '
    r"'\$\{recipe\.recipe_name(?:\.replace\(/'/g, \"\\\\'\"\))?\}'\)\"")

EXPECT_DJANGO = 6
EXPECT_JS = 6

print('=' * 74)
print('SECTION J, ROUND J-2 - THE HANDLERS JAVASCRIPT WRITES%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# THE CENSUS, BEFORE ANYTHING MOVES.
# ==========================================================================
RM = alv_tree.path_of('recipe_management.html')
AE = alv_tree.path_of('act_expense.html')
rm, rm_raw = read(RM)

d_hits = DJANGO.findall(rm)
j_hits = JSLIT.findall(rm)
print('  recipe_management.html   %d Django-written, %d JavaScript-written'
      % (len(d_hits), len(j_hits)))
unescaped = len(re.findall(
    r"deleteRecipe\(\$\{recipe\.recipe_id\}, '\$\{recipe\.recipe_name\}'",
    rm))
print('      of which %d escape NOTHING at all - every deleteRecipe'
      % unescaped)
print('-' * 74)

ESCAPE_HTML = '''
// ESCAPE WHAT GOES INTO AN ATTRIBUTE - J-2, 2 Oct 2026.
//
// Spelled exactly as act_expense.html spells it, because a second spelling
// of the same five replacements is a second thing to get wrong. The data
// attributes below are built by template literals into innerHTML, so a
// recipe name carrying " or < or & has to arrive as attribute text and not
// as markup.
function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// AND THE TWO LISTENERS THAT READ THEM BACK.
//
// DELEGATED, ON document, FOR THE REASON DB-4 WROTE DOWN ON act_expense:
// this list is re-rendered from scratch by the live search, the A-Z filter
// and the favourites toggle, and a handler bound to the buttons themselves
// would go with them every time. One listener outlives every re-render.
//
// THERE IS NO JS STRING HERE TO CLOSE EARLY, which is the whole point. The
// name is attribute text; the browser's own parser decodes it and hands it
// over whole, apostrophes, quotes, backslashes and all.
document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('.recipe-duplicate-btn');
    if (!btn) { return; }
    e.preventDefault();
    duplicateRecipe(btn.getAttribute('data-recipe-id'),
                    btn.getAttribute('data-recipe-name') || '', btn);
});

document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('.recipe-delete-btn');
    if (!btn) { return; }
    e.preventDefault();
    deleteRecipe(btn.getAttribute('data-recipe-id'),
                 btn.getAttribute('data-recipe-name') || '');
});

'''

if 'J-2, 2 Oct 2026' in rm:
    print('  recipe_management.html   already done')
else:
    if len(d_hits) != EXPECT_DJANGO or len(j_hits) != EXPECT_JS:
        raise SystemExit('J2: expected %d Django and %d JS sites, found '
                         '%d and %d' % (EXPECT_DJANGO, EXPECT_JS,
                                        len(d_hits), len(j_hits)))

    rm = DJANGO.sub(
        'data-recipe-id="{{ recipe.recipe_id }}" '
        'data-recipe-name="{{ recipe.recipe_name }}"', rm)
    rm = JSLIT.sub(
        'data-recipe-id="${recipe.recipe_id}" '
        'data-recipe-name="${escapeHtml(recipe.recipe_name)}"', rm)

    # duplicateRecipe reached for the button through the GLOBAL event
    # object. Inside a delegated listener that still happens to work in
    # Chrome, and relying on window.event is how a handler stops working on
    # the day someone tests it in another browser. The button is passed.
    rm = swap(rm, '''function duplicateRecipe(recipeId, recipeName) {
    if (confirm(`Duplicate "${recipeName}"?\\n\\nThis will create a copy with all ingredients and instructions.`)) {
        const btn = event.target.closest('button, a');''',
              '''function duplicateRecipe(recipeId, recipeName, sourceBtn) {
    if (confirm(`Duplicate "${recipeName}"?\\n\\nThis will create a copy with all ingredients and instructions.`)) {
        // THE BUTTON IS PASSED IN - J-2, 2 Oct 2026. This read it off the
        // global `event`, which a delegated listener does not reliably
        // give you. sourceBtn comes from the listener; the fallback keeps
        // any caller that still arrives the old way working.
        const btn = sourceBtn || (window.event && window.event.target
                                  .closest('button, a'));
        if (!btn) { return; }''',
              'duplicateRecipe reaching for the global event', RM)

    rm = swap(rm, 'function deleteRecipe(recipeId, recipeName) {',
              ESCAPE_HTML.lstrip('\n')
              + 'function deleteRecipe(recipeId, recipeName) {',
              'the head of deleteRecipe', RM)

    if not CHECK:
        back_up(RM, rm_raw)
        write(RM, rm)
    print('  recipe_management.html   %d onclicks -> data attributes, '
          '2 delegated listeners' % (len(d_hits) + len(j_hits)))

# ==========================================================================
# act_expense.html - the Report drill icon, onto the listener DB-4 built.
# ==========================================================================
ae, ae_raw = read(AE)

if 'J-2, 2 Oct 2026' in ae:
    print('  act_expense.html         already done')
else:
    ae = swap(ae,
              """                        var inv = e.doc_url
                            ? '<i class="fas fa-file-alt report-invoice-icon" title="View invoice" onclick="reportViewInvoice(\\'' + e.doc_url + '\\', \\'' + (e.doc_name || 'invoice') + '\\')"></i>'
""",
              """                        // THE ICON CARRIES THE VALUES, IT DOES NOT CALL WITH THEM -
                        // J-2, 2 Oct 2026. This built an onclick by string
                        // concatenation with no escaping of any kind, so an
                        // invoice filename containing an apostrophe made the
                        // handler a syntax error and the icon did nothing at
                        // all. The two attributes are the ones DB-4 chose for
                        // the icon in the table below; the listener that reads
                        // them is the same one.
                        var inv = e.doc_url
                            ? '<i class="fas fa-file-alt report-invoice-icon" title="View invoice" data-invoice-url="' + escapeHtml(e.doc_url) + '" data-filename="' + escapeHtml(e.doc_name || 'invoice') + '"></i>'
""",
              'the Report drill invoice icon', AE)

    ae = swap(ae, "    var icon = e.target.closest && e.target.closest('.verify-icon');",
              "    // WIDENED IN J-2, 2 Oct 2026 to cover the Report drill's icon as\n"
              "    // well. One listener, one pair of attributes, two modals - rather\n"
              "    // than a second listener that would drift from this one.\n"
              "    var icon = e.target.closest\n"
              "        && e.target.closest('.verify-icon, .report-invoice-icon');",
              'the delegated listener selector', AE)

    ae = swap(ae, """    window.reportViewInvoice = function(url, name) {
        if (typeof openPdfViewer === 'function') {
            openPdfViewer(url, 'Expense Invoice', (name || '').split('/').pop() || 'invoice');
        } else {
            window.open(url, '_blank');
        }
    };

""",
              """    // reportViewInvoice() WAS HERE, and it is gone in J-2, 2 Oct 2026.
    // It had one caller, the icon above, which no longer calls anything -
    // and its body was viewInvoiceQuick() rewritten: the same
    // openPdfViewer, the same 'Expense Invoice' title, the same
    // split('/').pop(). Two spellings of one behaviour is one of them
    // waiting to drift.

""",
              'the reportViewInvoice function', AE)

    if not CHECK:
        back_up(AE, ae_raw)
        write(AE, ae)
    print('  act_expense.html         icon onto data attributes, listener '
          'widened, reportViewInvoice removed')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
rm = read(RM)[0]
ae = read(AE)[0]

# NOT ONE HANDLER ON EITHER PAGE STILL CARRIES A NAME OR A URL.
left = DJANGO.findall(rm) + JSLIT.findall(rm)
if left:
    raise SystemExit('J2: %d recipe onclick(s) still carry the name' % len(left))
for pat, what in (
        (r"deleteRecipe\([^)]*recipe_name", 'deleteRecipe with a name'),
        (r"duplicateRecipe\(\$\{[^)]*recipe_name", 'duplicateRecipe with a name'),
        (r"onclick=\"[^\"]*Recipe\(", 'an onclick calling a Recipe function')):
    n = len(re.findall(pat, rm))
    if n:
        raise SystemExit('J2: %d site(s) left with %s' % (n, what))
print('  recipe_management: 0 handlers carry a recipe name (was %d)'
      % (EXPECT_DJANGO + EXPECT_JS))

n_id = len(re.findall(r'data-recipe-id="', rm))
n_nm = len(re.findall(r'data-recipe-name="', rm))
if n_id != EXPECT_DJANGO + EXPECT_JS or n_nm != n_id:
    raise SystemExit('J2: %d data-recipe-id and %d data-recipe-name, '
                     'expected %d of each'
                     % (n_id, n_nm, EXPECT_DJANGO + EXPECT_JS))
print('  and %d buttons carry both attributes' % n_id)

# THE JAVASCRIPT-WRITTEN ONES ESCAPE; THE DJANGO-WRITTEN ONES DO NOT NEED
# TO, because Django autoescapes an attribute by default - and a |escapejs
# left on one would be WRONG now: it escapes for a JS string, and this is
# no longer a JS string.
js_attrs = re.findall(r'data-recipe-name="\$\{([^}]*)\}"', rm)
if not js_attrs or any('escapeHtml(' not in a for a in js_attrs):
    raise SystemExit('J2: a JS-written data-recipe-name does not escape: %s'
                     % js_attrs)
if len(js_attrs) != EXPECT_JS:
    raise SystemExit('J2: %d JS-written attributes, expected %d'
                     % (len(js_attrs), EXPECT_JS))
if 'data-recipe-name="{{ recipe.recipe_name|escapejs }}"' in rm:
    raise SystemExit('J2: a Django attribute still carries |escapejs - that '
                     'filter escapes for a JS string, and this is an '
                     'attribute')
print('  the %d JavaScript-written ones escape; the %d Django ones are '
      'autoescaped' % (EXPECT_JS, EXPECT_DJANGO))

# ONE HELPER, ONE SPELLING, ON BOTH PAGES.
BODY = (r"""return String(s == null ? '' : s).replace(/&/g, '&amp;')"""
        r""".replace(/</g, '&lt;').replace(/>/g, '&gt;')"""
        r""".replace(/"/g, '&quot;').replace(/'/g, '&#39;');""")
for text, label in ((rm, 'recipe_management.html'), (ae, 'act_expense.html')):
    if text.count('function escapeHtml(s) {') != 1:
        raise SystemExit('J2: %s has %d escapeHtml, expected 1'
                         % (label, text.count('function escapeHtml(s) {')))
    if BODY not in text:
        raise SystemExit('J2: %s spells escapeHtml differently' % label)
print('  escapeHtml is on both pages, once each, spelled identically')

# TWO LISTENERS, DELEGATED ON document.
for cls in ('.recipe-duplicate-btn', '.recipe-delete-btn'):
    if ("e.target.closest('%s')" % cls) not in rm:
        raise SystemExit('J2: no delegated listener for %s' % cls)
if rm.count("document.addEventListener('click'") < 2:
    raise SystemExit('J2: fewer than two delegated click listeners')
print('  and two listeners, delegated on document, outlive every re-render')

# act_expense: ONE LISTENER, BOTH ICONS, NO reportViewInvoice.
if "closest('.verify-icon, .report-invoice-icon')" not in ae:
    raise SystemExit('J2: the delegated listener was not widened')
if ae.count("document.addEventListener('click'") != \
        read(AE + SUFFIX)[0].count("document.addEventListener('click'"):
    raise SystemExit('J2: act_expense gained or lost a click listener - the '
                     'point was to WIDEN the one DB-4 built, not add another')
code = re.sub(r'(?m)^\s*//.*$', '', ae)
code = re.sub(r'<!--.*?-->', '', code, flags=re.S)
if 'reportViewInvoice' in code:
    raise SystemExit('J2: reportViewInvoice is still live in act_expense')
if "onclick=\"reportViewInvoice" in ae:
    raise SystemExit('J2: the Report drill still calls reportViewInvoice')
for attr in ('data-invoice-url="\' + escapeHtml(e.doc_url)',
             'data-filename="\' + escapeHtml(e.doc_name'):
    if attr not in ae:
        raise SystemExit('J2: the Report drill icon is missing %r' % attr)
print('  act_expense: one listener for both icons, reportViewInvoice gone')

# THE MARKUP STILL CLOSES, ON BOTH.
for path, label in ((RM, 'recipe_management.html'), (AE, 'act_expense.html')):
    t = read(path)[0]
    c = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    body = re.sub(r'<(script|style)\b.*?</\1>', '', c, flags=re.S)
    d = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
    if d:
        raise SystemExit('J2: %s has %+d unbalanced <div>' % (label, d))
    for tag, close in (('if', 'endif'), ('for', 'endfor')):
        a = len(re.findall(r'\{%\s*' + tag + r'\b', c))
        b = len(re.findall(r'\{%\s*' + close + r'\s*%\}', c))
        if a != b:
            raise SystemExit('J2: %s has %s %d vs %s %d'
                             % (label, tag, a, close, b))
    for ch, n in (('`', None),):
        pass
print('  every <div>, {% if %} and {% for %} still closes on both pages')

# AND THE BUTTONS ARE STILL BUTTONS - same count, same classes.
for cls in ('recipe-duplicate-btn', 'recipe-delete-btn'):
    a = len(re.findall(r'\b' + cls + r'\b', rm))
    b = len(re.findall(r'\b' + cls + r'\b', read(RM + SUFFIX)[0]))
    # the listeners name each class once more than the markup did
    if a != b + 1:
        raise SystemExit('J2: %s appears %d times, was %d, expected %d'
                         % (cls, a, b, b + 1))
print('  and every Duplicate and Delete button is still there')

print('-' * 74)
print('  A value in a handler is a string waiting to be closed early. These')
print('  thirteen are attributes now, and the browser parses them.')
print('=' * 74)
