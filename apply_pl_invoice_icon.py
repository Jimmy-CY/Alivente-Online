# -*- coding: utf-8 -*-
"""SECTION DB, ROUND DB-4 - AN INVOICE NAMED O'BRIEN COULD NOT BE OPENED

Demetri: "I should be able to click on an icon and view the actual
expenses attachment" - the Actual Expense drill-down on the P&L.

THAT PART IS ALREADY DONE, and this round's first draft said it was not.
An earlier round, apply_pl_invoice.py, wired it; window.viewInvoiceQuick
is defined in finance_pl_act.html and the icon's inline onclick resolves
to it; test_pl_invoice.py drives a real click and proves the viewer opens
on the right document. The first draft grepped for
`function viewInvoiceQuick`, found nothing because it is written
`window.viewInvoiceQuick = function (...)`, and concluded a working
function was missing. Seventh measuring-instrument correction in three
rounds, the same shape every time: the check was narrower than the thing.

==========================================================================
WHAT IS ACTUALLY BROKEN, MEASURED
==========================================================================
The icon fires through an onclick built by string interpolation:

    onclick="viewInvoiceQuick('{{ ...document.url }}',
                              '{{ ...document.name }}')"

Driven in Chromium, the same click on both markups:

    x.pdf                 old: opens          new: opens
    O'Brien March.pdf     old: SyntaxError    new: opens
                               "missing ) after argument list"

SO ANY INVOICE WITH AN APOSTROPHE IN ITS NAME CANNOT BE OPENED, from the
Expenses table or from the P&L drill-down. The handler is not wrong at
runtime - it never parses.

AND DJANGO'S AUTOESCAPING DOES NOT HELP, which is the part worth
understanding. It escapes HTML: the apostrophe arrives in the template
output as &#x27;. The browser decodes that while parsing the ATTRIBUTE,
and hands the JavaScript parser a plain apostrophe inside a single-quoted
string literal. Two languages nested in one attribute, and the escaping
only covers the outer one. A data attribute has no inner language - the
browser hands the value to script as a string, whatever is in it.

------------------------------------------------
AND A HANDLER THAT HAS NEVER RUN, ON ANY ROW, EVER
------------------------------------------------
finance_pl_act.html carries setupInvoiceIconHandlers(), written for an
icon that keeps its document in data attributes. It opens:

    if ($icon.attr('onclick')) { return; }

"Guarded on the onclick so an icon with both does not open the viewer
twice." Sound reasoning - and every icon carries an onclick and none
carries the attributes, so it has returned on every row of every
drill-down since it was written. A piece of machinery with a comment
describing work it does not do.

==========================================================================
THE FIX - ONE MECHANISM, TWO PAGES
==========================================================================
    act_expense.html    the icon carries data-invoice-url and
                        data-filename, no onclick, and the page binds one
                        delegated handler calling viewInvoiceQuick - the
                        pdf_viewer component, unchanged.
    finance_pl_act.html the dead guard goes. Its handler then runs, for
                        the first time, and calls its own
                        window.viewInvoiceQuick, which already works.

Delegated on both, because the live-search filter re-draws the rows and a
handler bound to the elements would go with them.

THE OTHER TWO CALLERS ARE LEFT ALONE, AND NAMED:
  the Manage modal's "View Document" launcher - a button in a form, not a
  table icon, with no interpolation in it;
  the Report drill's reportViewInvoice - built by JS string concatenation
  and carrying THE SAME apostrophe defect. It is reached from a different
  modal, filled by a different endpoint, and fixing it means changing how
  that table is built. Named here so it is not mistaken for something
  nobody noticed, and it is the obvious next bite.

Backups: .bak_plicon. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_plicon'
CRLF = {}
SENTINEL = 'test_pl_invoice_icon.py'
ROOT = os.getcwd()


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


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('DB4: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    """Replace exactly once, in the file's own line endings, and refuse an
    anchor that lands mid-line. A3's lesson."""
    o, n = eol(path, old), eol(path, new)
    c = text.count(o)
    if c != 1:
        raise SystemExit('DB4: %s appears %d times, not once' % (what, c))
    i = text.index(o)
    if i and not o.startswith(('\n', '\r')) and text[i - 1] not in '\n\r':
        raise SystemExit('DB4: the anchor for %s starts MID-LINE (after %r)'
                         % (what, text[i - 1]))
    return text.replace(o, n)


def code_only(text):
    """Comments blanked, length preserved. A check that a name is absent
    must not read the note recording its removal - six gates across the
    last two rounds got that wrong before the instrument was fixed."""
    def blank(m):
        return re.sub(r'[^\n]', ' ', m.group(0))
    text = re.sub(r'<!--.*?-->', blank, text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', blank, text, flags=re.S)
    return re.sub(r'/\*.*?\*/', blank, text, flags=re.S)


print('=' * 74)
print('SECTION DB, ROUND DB-4 - THE INVOICE ICON ON THE P&L DRILL%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
print('')
print('  THE ICON CARRIES ITS DOCUMENT, NOT A FUNCTION CALL')
print('  ' + '-' * 70)

AE = alv_tree.join('act_expense.html')
at, araw = read(AE)

if 'data-invoice-url' in at:
    print('  act_expense.html             already done')
else:
    at = swap(at, '''                <i class="fas {{ badge.1 }} verify-icon verify-{{ badge.0 }}"
                   onclick="viewInvoiceQuick('{{ expense.act_expense_document.url }}', '{{ expense.act_expense_document.name }}')"
                   title="{{ badge.2 }} - click to view invoice"></i>
''', '''                {# DATA, NOT A FUNCTION CALL - DB-4, 2 Oct 2026. #}
                {# #}
                {# TWO REASONS, AND THE SECOND IS A BUG. #}
                {# #}
                {# ONE, AND IT IS A BUG: the filename went into a #}
                {# JavaScript string literal inside an HTML attribute. #}
                {# Measured in Chromium - an invoice named with an #}
                {# apostrophe gives `missing ) after argument list` and #}
                {# the handler never parses, so that document cannot be #}
                {# opened at all, here or in the P&L drill-down. #}
                {# #}
                {# DJANGO'S AUTOESCAPING DOES NOT COVER IT. It escapes #}
                {# HTML, so the apostrophe arrives as an entity; the #}
                {# browser decodes that while parsing the ATTRIBUTE and #}
                {# hands the JS parser a bare apostrophe inside a quoted #}
                {# string. Two languages in one attribute, one of them #}
                {# escaped. A data attribute has no inner language. #}
                {# #}
                {# TWO: this table is INJECTED into the P&L Actual #}
                {# Expense modal, which takes table.table out of a fetch #}
                {# of this page. finance_pl_act.html has carried a #}
                {# handler reading these two attributes all along, and #}
                {# could never use it while the icon had an onclick. #}
                <i class="fas {{ badge.1 }} verify-icon verify-{{ badge.0 }}"
                   data-invoice-url="{{ expense.act_expense_document.url }}"
                   data-filename="{{ expense.act_expense_document.name }}"
                   title="{{ badge.2 }} - click to view invoice"></i>
''', 'the verify icon', AE)

    at = swap(at, '''function viewInvoiceQuick(documentUrl, documentName) {
''', '''// ONE DELEGATED HANDLER, BECAUSE THE ICON NO LONGER CALLS ANYTHING.
// DB-4 took the onclick off it - see the note on the markup - so this
// page binds the click itself. Delegated, because the rows are re-drawn
// by the live-search filter and a handler bound to the elements would
// go with them.
//
// THE SAME TWO ATTRIBUTES finance_pl_act.html's own handler reads, so
// the icon works in the table AND in the modal that injects the table,
// with one spelling between them.          [test_pl_invoice_icon.py]
document.addEventListener('click', function (e) {
    var icon = e.target.closest && e.target.closest('.verify-icon');
    if (!icon) { return; }
    var url = icon.getAttribute('data-invoice-url');
    if (!url) { return; }
    e.preventDefault();
    viewInvoiceQuick(url, icon.getAttribute('data-filename') || 'invoice');
});

function viewInvoiceQuick(documentUrl, documentName) {
''', 'the delegated handler', AE)

    if not CHECK:
        back_up(AE, araw)
        write(AE, at)
    print('  act_expense.html             the icon carries data-invoice-url '
          '/ data-filename,')
    print('  %-28s and one delegated handler opens the viewer' % '')

# ==========================================================================
print('')
print('  AND THE HANDLER THAT WAS WAITING FOR IT')
print('  ' + '-' * 70)

PL = alv_tree.join('finance_pl_act.html')
pt, praw = read(PL)

if 'DB-4' in pt:
    print('  finance_pl_act.html          already done')
else:
    pt = swap(pt, """        // For any invoice icon that carries its document in data attributes
        // rather than an onclick. Guarded on the onclick so an icon with both
        // does not open the viewer twice.
        $(document).off('click', '.verify-icon').on('click', '.verify-icon', function(e) {
            var $icon = $(this);
            if ($icon.attr('onclick')) { return; }
""", """        // For any invoice icon that carries its document in data attributes
        // rather than an onclick.
        //
        // THE GUARD THAT USED TO BE HERE MADE THIS UNREACHABLE - DB-4,
        // 2 Oct 2026. It read
        //
        //     if ($icon.attr('onclick')) { return; }
        //
        // and its reason was sound: an icon carrying BOTH an onclick and
        // the data attributes would open the viewer twice. But every icon
        // carried an onclick and none carried the attributes, so this
        // returned on every row of every drill-down and the handler never
        // ran once. Worse, the onclick it deferred to named a function
        // from act_expense.html's script - and this modal injects that
        // page's TABLE, not its script - so the click reached nothing at
        // all.
        //
        // act_expense.html writes the two attributes and no onclick now,
        // so there is nothing left to guard against.
        //                                  [test_pl_invoice_icon.py]
        $(document).off('click', '.verify-icon').on('click', '.verify-icon', function(e) {
            var $icon = $(this);
""", 'the onclick guard', PL)
    if not CHECK:
        back_up(PL, praw)
        write(PL, pt)
    print('  finance_pl_act.html          the guard goes - it was returning '
          'on every row')

# ==========================================================================
print('')
print('  THE LEDGER THAT OWNED THIS BEHAVIOUR')
print('  ' + '-' * 70)
# test_pl_invoice.py belongs to the round that MADE the icon work, and it
# asserts two things DB-4 changes: that the handler is guarded, and that
# its fixture row is "the icon exactly as act_expense.html renders it".
# The second matters most - a fixture whose comment says it mirrors the
# page, and does not, is how a suite goes on passing while the page
# breaks.
GUARD_OLD = (
    "check('  guarded, so an icon with BOTH does not open twice',\n"
    '      "if ($icon.attr(\'onclick\')) { return; }" in JS)\n')
GUARD_NEW = (
    '# MOVED by DB-4, 2 Oct 2026. This asserted the handler was guarded\n'
    "# with `if ($icon.attr('onclick')) { return; }` - correct for the\n"
    '# round that wrote it, which left the onclick in place and added the\n'
    '# delegated fallback beside it.\n'
    '#\n'
    '# THE GUARD MEANT THE FALLBACK NEVER RAN. Every icon carried an\n'
    '# onclick, so it returned on every row of every drill-down: the\n'
    '# onclick did the work and this handler was machinery that described\n'
    '# itself and did nothing. DB-4 took the onclick off the icon - it\n'
    '# pasted a FILENAME into a JavaScript string literal, and an invoice\n'
    "# named O'Brien March.pdf gave `missing ) after argument list` - so\n"
    '# there is nothing left to guard against and the handler finally\n'
    '# does the job it was written for.\n'
    "check('  the guard is GONE, because nothing carries an onclick now',\n"
    '      "if ($icon.attr(\'onclick\')) { return; }" not in JS)\n'
    "check('    and the delegated handler is what opens the viewer',\n"
    '      "data(\'invoice-url\')" in JS)\n')

ROW_OLD = (
    "            '<i class=\"fas %s verify-icon verify-%s\" '\n"
    "            'onclick=\"viewInvoiceQuick(\\'%s\\', \\'%s\\')\" '\n")
ROW_NEW = (
    '            # DATA ATTRIBUTES SINCE DB-4, 2 Oct 2026. This function\n'
    '            # says it builds the icon "exactly as act_expense.html\n'
    '            # renders it", and the page stopped writing an onclick:\n'
    '            # it pasted a filename into a JavaScript string literal\n'
    "            # inside an HTML attribute, and O'Brien March.pdf gave\n"
    '            # `missing ) after argument list`.\n'
    "            '<i class=\"fas %s verify-icon verify-%s\" '\n"
    "            'data-invoice-url=\"%s\" data-filename=\"%s\" '\n")

# AND SECTION 4's HISTORICAL CONTROL NEEDS THE HISTORICAL ICON.
#
# It re-runs the OLD handler against `row()` to show the viewer stayed
# empty before that round. Point it at the new markup and it still fails
# to open the viewer, but for a different reason, and its sentence - "the
# inline onclick threw" - becomes untrue. A control that reproduces a
# different state from the one it names is not a control.
#
# So the legacy shape gets its own builder, used ONLY there. row() is for
# what the page renders today; legacy_row() is for what it rendered then.
LEGACY_DEF = (
    "def legacy_row(url, name, glyph='fa-check-circle', tone='success'):\n"
    '    """The icon as act_expense.html rendered it BEFORE DB-4 - with the\n'
    '    inline onclick. Section 4 is a HISTORICAL control: it re-runs the\n'
    "    handler of an earlier round, and it has to be given that round's\n"
    '    markup or it is reproducing some third state that never existed.\n'
    '    """\n'
    '    return row(url, name, glyph, tone).replace(\n'
    "        'data-invoice-url=\"%s\" data-filename=\"%s\" ' % (url, name),\n"
    '        \'onclick="viewInvoiceQuick(\\\'%s\\\', \\\'%s\\\')" \'\n'
    '        % (url, name))\n'
    '\n'
    '\n'
    'async def click_icon(body, extra_js=\'\'):\n')

# AND A CLAIM THAT EXPIRED BY DESIGN.
#
# test_ai_models.py (R1, yesterday) asserted its own suffix was "near the
# end of ROUNDS, which is where a new round belongs" - true the day it
# was written, and false four rounds later, which is now. ROUNDS is
# APPEND-ONLY: every later round pushes an earlier one further from the
# end, so that check could only ever have been right once and would fail
# from here to the end of the project.
#
# ORDER IS THE DURABLE CLAIM. What actually matters about a suffix's
# place in ROUNDS is that it comes AFTER the round it builds on - that is
# what as_left_by() walks - and position from the end says nothing about
# that. DB-4 found it because DB-4's sweep is the fourth one since.
AI = os.path.join(ROOT, 'test_ai_models.py')
ait, airaw = read(AI)
if 'append-only' in ait:
    print('  test_ai_models.py            already done')
else:
    ait = swap(ait, """    ok(ROUNDS[-1] == SUFFIX or SUFFIX in ROUNDS[-4:],
       '  near the end of it, which is where a new round belongs',
       ROUNDS[-3:])
""", """    # AFTER THE ROUND IT BUILDS ON, not near the end - DB-4, 2 Oct
    # 2026. This read "near the end of it, which is where a new round
    # belongs", and ROUNDS is append-only: four rounds later R1 is no
    # longer near the end, and never will be again. A claim that can
    # only be true on the day it is written is not a claim.
    #
    # What the order is FOR is as_left_by(), which walks forward from a
    # suffix to find the next backup of a file. So the thing worth
    # asserting is that this round sits after the one before it.
    ok(ROUNDS.count(SUFFIX) == 1, '  exactly once', ROUNDS.count(SUFFIX))
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_filtersinrc'),
       '  and AFTER .bak_filtersinrc, the round it followed - which is '
       'what as_left_by() walks, and the only thing the order has to say',
       '%d vs %d' % (ROUNDS.index(SUFFIX),
                     ROUNDS.index('.bak_filtersinrc')))
""", 'the expiring position claim', AI)
    if not CHECK:
        back_up(AI, airaw)
        write(AI, ait)
    print('  test_ai_models.py            "near the end" was true for one '
          'day; order is the claim')

PI = os.path.join(ROOT, 'test_pl_invoice.py')
it, iraw = read(PI)
if 'DB-4' in it:
    print('  test_pl_invoice.py           already done')
else:
    it = swap(it, GUARD_OLD, GUARD_NEW, 'the guard assertion', PI)
    it = swap(it, ROW_OLD, ROW_NEW, 'the fixture row', PI)
    it = swap(it, "async def click_icon(body, extra_js=''):\n", LEGACY_DEF,
              'the legacy row builder', PI)
    it = swap(it,
              "        await pg.set_content('<body>' + row('/media/x.pdf', "
              "'x.pdf') + '</body>')\n",
              "        await pg.set_content('<body>' + legacy_row("
              "'/media/x.pdf', 'x.pdf') + '</body>')\n",
              'the historical control markup', PI)
    if not CHECK:
        back_up(PI, iraw)
        write(PI, it)
    print('  test_pl_invoice.py           the guard claim moves, and its '
          'fixture matches the page again')

# ==========================================================================
print('')
print('  REGISTRATION')
print('  ' + '-' * 70)
for rel, old, new, what, mark in (
        ('alv_rounds.py', "    '.bak_tabs',\n]\n",
         "    '.bak_tabs',\n    '%s',\n]\n" % SUFFIX,
         'the end of ROUNDS', SUFFIX),
        ('Push-PendingChanges.ps1', "    'test_tabs.py'\n)\n",
         "    'test_tabs.py'\n"
         "    # The invoice icon on the P&L Actual Expense drill-down. It\n"
         "    # was on screen and could not fire: the icon called a\n"
         "    # function from a script the modal never injects, and the\n"
         "    # handler written for it returned early on every row. Its\n"
         "    # section 4 clicks the icon in BOTH places and reads back\n"
         "    # which document opened.\n"
         "    'test_pl_invoice_icon.py'\n)\n", 'the end of $suites',
         SENTINEL),
        ('Push-PendingChanges.ps1',
         "    @{ File = 'pages\\templates\\finance_pl_act.html'; "
         "Text = 'isGreen'; What = 'and the colour test is gone'; "
         "Absent = $true; Code = $true },\n",
         "    @{ File = 'pages\\templates\\finance_pl_act.html'; "
         "Text = 'isGreen'; What = 'and the colour test is gone'; "
         "Absent = $true; Code = $true },\n"
         "    @{ File = 'pages\\templates\\act_expense.html'; "
         "Text = 'data-invoice-url'; What = 'the invoice icon carries its "
         "document, so the P&A modal that injects this table can open it' },\n"
         "    @{ File = 'pages\\templates\\finance_pl_act.html'; "
         "Text = 'showInvoiceModalLikeExisting('; "
         "What = 'and the drill-down handler calls the viewer THIS file has' "
         "},\n", 'a sentinel for the icon', 'data-invoice-url')):
    path = os.path.join(ROOT, rel)
    tt, rr = read(path)
    # GUARDED ON A STRING UNIQUE TO WHAT THIS ENTRY ADDS. The first
    # draft derived the marker from the replacement text and got
    # `test_tabs.py` - the ANCHOR, already present - so it declared the
    # $suites entry done before writing it.
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
    print('  CHECK ONLY - every anchor matched exactly once, nothing written')
    print('=' * 74)
    raise SystemExit(0)

ae_now, pl_now = read(AE)[0], read(PL)[0]
ae_code, pl_code = code_only(ae_now), code_only(pl_now)

# THE ICON CARRIES NO onclick, ON EITHER SIDE OF THE INJECTION.
m = re.search(r'<i class="fas \{\{ badge\.1 \}\} verify-icon[^>]*>', ae_code)
if not m:
    raise SystemExit('DB4: the verify icon could not be found')
if 'onclick' in m.group(0):
    raise SystemExit('DB4: the verify icon still carries an onclick')
for a in ('data-invoice-url', 'data-filename'):
    if a not in m.group(0):
        raise SystemExit('DB4: the verify icon does not carry %s' % a)
print('  the icon carries its document in data attributes and no onclick')

# AND NOTHING INTERPOLATES A FILENAME INTO A JAVASCRIPT STRING ON IT.
if re.search(r"onclick=\"[^\"]*\{\{[^}]*document\.name", ae_code):
    raise SystemExit('DB4: a filename is still interpolated into an onclick')
print('  and no filename is interpolated into a JavaScript string literal')

# THE HANDLER NO LONGER REFUSES EVERY ICON.
# THE FUNCTION'S OWN BODY, found by matching braces rather than by
# guessing at an indentation. code_only() blanks the comments INSIDE it
# to spaces of the same length, so a closing brace at column 4 is no
# longer a reliable landmark - and the first draft of this gate looked
# for one and crashed.
# AND WITH THE // COMMENTS OUT OF IT TOO. code_only() blanks CSS, HTML
# and Django comments; a JavaScript line comment is none of those, and
# the note this round left inside the handler QUOTES the guard it
# removed - so the gate read its own record as the defect. That is the
# eighth time this project has made that mistake, and the fix is the
# same one every time: strip the record before looking for the thing.
#
# Anchored at the line start, as the push gate's own NoComments is, so
# that `https://` inside a string is not mistaken for a comment.
pl_js = re.sub(r'(?m)^\s*//.*$', '', pl_code)
_i = pl_js.index('function setupInvoiceIconHandlers')
_d, _j = 0, pl_js.index('{', _i)
for _k in range(_j, len(pl_js)):
    if pl_js[_k] == '{':
        _d += 1
    elif pl_js[_k] == '}':
        _d -= 1
        if _d == 0:
            break
h = pl_js[_i:_k + 1]
if "attr('onclick')" in h:
    raise SystemExit('DB4: the P&L handler still returns early on an onclick')
if 'window.viewInvoiceQuick' not in h:
    raise SystemExit('DB4: the P&L handler no longer calls its viewer')
print('  the P&L handler drops the guard and still calls its own viewer')

# AND THAT VIEWER REALLY IS DEFINED IN THIS FILE.
#
# CHECKED AS AN ASSIGNMENT, NOT A DECLARATION. This round's first draft
# grepped for `function viewInvoiceQuick`, found nothing, and concluded
# the handler called something that did not exist. It is written
# `window.viewInvoiceQuick = function (...)`, forty lines above, and it
# works - it saves the drill scroll position and splits the stored path
# down to a file name. Seventh measuring-instrument correction in three
# rounds, and the same shape: the check was narrower than the thing.
if not re.search(r'window\.viewInvoiceQuick\s*=\s*function', pl_code):
    raise SystemExit('DB4: window.viewInvoiceQuick is not defined here')
if 'function showInvoiceModalLikeExisting' not in pl_code:
    raise SystemExit('DB4: showInvoiceModalLikeExisting is not defined here')
print('  and both its viewer and the window.viewInvoiceQuick wrapper are '
      'defined there')

# BOTH PAGES READ THE SAME TWO ATTRIBUTE NAMES.
for name, txt in (('act_expense.html', ae_code),
                  ('finance_pl_act.html', pl_code)):
    for a in ('invoice-url', 'filename'):
        if a not in txt:
            raise SystemExit('DB4: %s does not read data-%s' % (name, a))
print('  and both pages read the same two attribute names')

# THE MARKUP STILL CLOSES, AND THE SCRIPTS STILL BALANCE.
for p, name in ((AE, 'act_expense.html'), (PL, 'finance_pl_act.html')):
    body = re.sub(r'<(script|style)\b.*?</\1>', '', code_only(read(p)[0]),
                  flags=re.S)
    n = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
    if n:
        raise SystemExit('DB4: %s has %+d unbalanced <div>' % (name, n))
    for blk in re.findall(r'<script[^>]*>(.*?)</script>',
                          code_only(read(p)[0]), re.S):
        if blk.count('{') != blk.count('}'):
            raise SystemExit('DB4: %s has an unbalanced script block' % name)
print('  every <div> closes and every script balances on both')

# EVERY DJANGO COMMENT THIS ROUND WROTE IS ONE LINE, CLOSED ONCE. F3's
# lesson: a comment spanning lines never matches and renders as prose,
# and one that writes the closing marker inside its own text ends early.
for i, line in enumerate(read(AE)[0].split('\n'), 1):
    if '{#' in line and '#}' not in line:
        raise SystemExit('DB4: act_expense.html:%d opens a Django comment it '
                         'does not close on the same line' % i)
    if line.count('{#') and line.count('#}') > line.count('{#'):
        raise SystemExit('DB4: act_expense.html:%d closes one early' % i)
print('  and every Django comment is one line, closed once')

# NO LITERAL COLOUR ENTERED EITHER PAGE.
for p, name in ((AE, 'act_expense.html'), (PL, 'finance_pl_act.html')):
    a = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', code_only(read(p)[0])))
    b = len(re.findall(r'#[0-9a-fA-F]{3,6}\b',
                       code_only(read(p + SUFFIX)[0])))
    if a > b:
        raise SystemExit('DB4: %s gained %d literal colour(s)' % (name, a - b))
    print('  %-24s literal colours %3d -> %3d' % (name, b, a))

# EVERY SENTINEL IN THE PUSH GATE STILL RESOLVES - F3's lesson, and it
# cost a push. They are tested before a single suite runs.
_Q = r"'((?:[^']|'')*)'|\"((?:[^\"]|\"\")*)\""
SENT_FIELD = re.compile(r"\b(File|Text|What)\s*=\s*(?:%s)" % _Q)
SENT_FLAG = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")


def sentinels(ps_text):
    out = []
    for line in ps_text.split('\n'):
        if '@{' not in line or 'File' not in line:
            continue
        f = {}
        for k, sq, dq in SENT_FIELD.findall(line):
            f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
        for k, v in SENT_FLAG.findall(line):
            f[k] = (v == 'true')
        if 'File' in f and 'Text' in f:
            out.append(f)
    return out


def sentinel_strip(t):
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    t = re.sub(r'(?m)^\s*//.*$', '', t)
    return re.sub(r'(?m)^\s*#.*$', '', t)


ps_text = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))[0]
rows = sentinels(ps_text)
raw = len(re.findall(r'@\{ *File *=', ps_text))
if len(rows) != raw:
    raise SystemExit('DB4: the push gate has %d sentinel rows and this reader '
                     'parsed %d' % (raw, len(rows)))
stale = []
for r in rows:
    p = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(p):
        stale.append('%s FILE MISSING' % r['File'])
        continue
    body = read(p)[0]
    if r.get('Code'):
        body = sentinel_strip(body)
    if (r['Text'].lower() in body.lower()) != (not r.get('Absent')):
        stale.append('%s  %s  %r' % (r['File'],
                                     'NOT FOUND' if not r.get('Absent')
                                     else 'IS BACK', r['Text'][:60]))
if stale:
    raise SystemExit('DB4: %d push-gate sentinel(s) no longer resolve:\n   %s'
                     % (len(stale), '\n   '.join(stale[:6])))
print('  and all %d push-gate sentinels still resolve' % len(rows))

print('-' * 74)
print('  An invoice named O\'Brien March.pdf can be opened. It could not be,')
print('  from either screen, because its name was pasted into a JavaScript')
print('  string literal inside an HTML attribute.')
print('=' * 74)
