# -*- coding: utf-8 -*-
"""apply_customer_view.py - round NV-1d, 16 Oct 2026.

A VIEW BUTTON NEEDS SOMETHING TO VIEW.

Demetri, after a full check of the Invoices module:

  "On Customers (In Invoices), can we add a View button next to the Edit
   and Delete?"


THERE WAS NO CUSTOMER TO VIEW                                    MEASURED
============================================================================
The routes are list, add, edit and delete. There is no customer detail
screen in this application, so a View icon had nowhere to go - which is
why this is a round and not a one-line markup change.

Two shapes were possible and the second was chosen because he had
already described it, for receipts, in the same batch of findings:

  "the Receipt Number should be clickable and it should offer a view of
   the Receipt Details, without showing the PDF - similar to the
   Physical Invoice."

So: a read-only DETAILS MODAL, not a new page.


AND THE LIST ALREADY HIDES FOUR FIELDS WORTH SHOWING
============================================================================
    InvoiceCustomer      on the list      in the modal
    name                 yes
    customer_id_label    yes
    email_to             yes
    invoice_count        yes (annotate)
    billing_address                       YES
    billing_tel                           YES
    email_cc                              YES
    email_body                            YES

The modal is therefore not a second copy of the row - it is the half of
the record the table has no room for. No new route and no new query: the
view already loads the objects and only built five keys out of them.
These four are every remaining field on the model that a reader would
recognise; created_at and updated_at are not shown, because nobody asked
what a customer record's own timestamps are.


MARKUP, NOT innerHTML - CC-1'S DAY SHEETS, EXACTLY
============================================================================
One hidden div per customer inside the modal body; the script unhides one
and writes a title. That is the whole of the script.

CC-1 took this decision on 15 Oct and wrote down the argument: base
offers two pop-up patterns and the other one builds its div as a STRING
in JavaScript. VB-1 had just spent a round on four controls that sat
three-quarters wrong for weeks because no census could see them, so

    markup a gate can read is worth more than markup that is convenient
    to generate

and the patcher refuses if anything but an empty clear is written into
this page with innerHTML.

AND THE GATE TESTS WHAT IS WRITTEN, NOT WHETHER A WORD APPEARS. The
first cut banned `innerHTML` and refused the page's own deliberate
`tags.innerHTML = ''`, which CLEARS the filter chips before rebuilding
them with createTextNode - the careful thing, not the careless one.


THE PAGE SHADOWS `$`, WHICH IS THE FIND OF THE ROUND              MEASURED
============================================================================
Inside the filter IIFE, line 240 of this page is

    function $(id) { return document.getElementById(id); }

That is where every piece of DOM wiring on this page lives, and it is
the obvious place to add a click handler. A handler written there as
`$(document).on('click', ...)` throws on load - getElementById(document)
is null, and null has no .on - which is exactly what the first draft of
this round did, and what a browser control printed back:

    TypeError: Cannot read properties of null (reading 'on')

So the handler is plain DOM in its OWN IIFE, and reaches Bootstrap by
its real name - `window.jQuery('#customerModal').modal('show')` - rather
than relying on `$` meaning one thing in this scope and another thing
twenty lines up. A page-local helper that borrows a global name is
invisible to every text check and fatal at runtime.


THE STRIP, AND THE MOBILE BAR'S COLUMN COUNT
============================================================================
View is a LOOK, so it sorts FIRST - before Edit (CHANGE) and Delete
(DESTROY) - and alv_rowactions is what says so rather than the markup.

A LOOK needs no permission, which changes the mobile bar's arithmetic:

    can_edit_invoices      View + Edit + Delete    (unnamed: 3 is base's
                                                    own default)
    read-only              View + Edit (disabled)  cols-2

So the bar's column count becomes conditional. That is not a flourish:
the read-only branch today has ONE control in a two-column grid, and
after this it has two. The class is chosen where the count is known.

AND THAT FALSIFIES A SENTINEL, WHICH IS THIS ROUND'S JOB TO RE-POINT.
Push-PendingChanges claims `mobile-action-bar cols-2` on this page, and
the conditional class makes that string false. test_sentinels names it
by line within one run, so the row is re-pointed here.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alv_tree

code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

SUFFIX = '.bak_custview'
PAGE = 'customer_list.html'
VIEW = os.path.join('pages', 'views', 'physical_invoices.py')
ME = 'test_customer_view.py'
PATCHER = 'apply_customer_view.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
BH = 'test_bar_height.py'
IB = 'test_icon_buttons.py'
TI = 'test_table_invoices.py'
CHECK = False

# THE ICON CENSUS HAS TWO CLAIMS ABOUT THIS PAGE, and the sheet
# falsifies both. One is a CEILING on how many rules the page still
# keeps for itself - T2 brought it to four and allowed six - and the
# sheet's four rows rules make eight. The other names
# `mobile-action-bar cols-2` as a literal, which the conditional class
# breaks. Both re-pointed here, because a round that falsifies a claim
# fixes the claim.
LEFT_WAS, LEFT_NOW = 6, 10

CONVERTED_WAS, CONVERTED_NOW = 87, 88
ALIAS_WAS, ALIAS_NOW = 85, 87
ALIAS_P_WAS, ALIAS_S_WAS = 42, 43
ALIAS_P_NOW, ALIAS_S_NOW = 43, 44

# The View button is one more control in a table row.
ROW_WAS_N, ROW_NOW_N = 113, 114

SHEET_ROWS = 7

# ---------------------------------------------------------------- the view
VIEW_WAS = """        rows.append({
            "pk": c.pk,
            "name": c.name,
            "customer_id_label": c.customer_id_label,
            "email_to": c.email_to,
            "invoice_count": c.n_invoices,
        })"""

VIEW_NOW = """        rows.append({
            "pk": c.pk,
            "name": c.name,
            "customer_id_label": c.customer_id_label,
            "email_to": c.email_to,
            "invoice_count": c.n_invoices,
            # NV-1d, 16 Oct 2026 - THE HALF OF THE RECORD THE TABLE HAS
            # NO ROOM FOR. Demetri asked for a View button beside Edit
            # and Delete, and there is no customer detail route in this
            # application - list, add, edit, delete - so View opens a
            # read-only sheet, the shape he described for receipts in
            # the same batch of findings.
            #
            # NO NEW QUERY AND NO NEW ROUTE. The loop already holds the
            # object; it was building five keys out of it. These four
            # are every remaining field on the model a reader would
            # recognise.
            "billing_address": c.billing_address,
            "billing_tel": c.billing_tel,
            "email_cc": c.email_cc,
            "email_body": c.email_body,
        })"""

# ------------------------------------------------------------- the strip
STRIP_WAS = """              <div class="row-actions">
              {% if perms.auth.can_edit_invoices %}
                <a href="{% url 'customer_edit' row.pk %}" class="icon-action-btn icon-edit" title="Edit Customer">"""

STRIP_NOW = """              <div class="row-actions">
              {# NV-1d, 16 Oct 2026 - View is a LOOK, so it sorts FIRST, #}
              {# and alv_rowactions is what says that rather than this #}
              {# markup. It is OUTSIDE the permission test: reading a #}
              {# record you can already see every other column of needs #}
              {# no permission to edit invoices. #}
                <button type="button" class="icon-action-btn icon-view js-cust-view"
                        data-cust="{{ row.pk }}" data-name="{{ row.name }}"
                        title="View Customer" aria-label="View Customer">
                  <i class="fas fa-eye"></i>
                </button>
              {% if perms.auth.can_edit_invoices %}
                <a href="{% url 'customer_edit' row.pk %}" class="icon-action-btn icon-edit" title="Edit Customer">"""

BAR_WAS = """            <td class="mobile-action-bar cols-2">
              {% if perms.auth.can_edit_invoices %}
                <a href="{% url 'customer_edit' row.pk %}" class="mobile-action-btn">"""

BAR_NOW = """            {# NV-1d - THE COLUMN COUNT IS CHOSEN WHERE THE COUNT IS #}
            {# KNOWN. View needs no permission, so the bar draws three #}
            {# controls for an editor and two for a reader. Before this #}
            {# round the read-only branch put ONE control in a #}
            {# two-column grid. #}

            {# AND THREE IS THE DEFAULT, SO IT IS NOT NAMED. base #}
            {# declares cols-1, cols-2 and cols-4 and deliberately no #}
            {# cols-3, because .mobile-action-bar is already #}
            {# repeat(3, 1fr) - ten pages wear the bare class for #}
            {# exactly that reason. The first cut of this round asked #}
            {# for `cols-3`, which styles nothing: a dead class name, #}
            {# which is what CC-1 and TB-1a both deleted rather than #}
            {# respell. #}
            <td class="mobile-action-bar{% if not perms.auth.can_edit_invoices %} cols-2{% endif %}">
              <button type="button" class="mobile-action-btn js-cust-view"
                      data-cust="{{ row.pk }}" data-name="{{ row.name }}">
                <i class="fas fa-eye mobile-action-icon icon-color-view"></i>
                <span class="mobile-action-label">View</span>
              </button>
              {% if perms.auth.can_edit_invoices %}
                <a href="{% url 'customer_edit' row.pk %}" class="mobile-action-btn">"""

# -------------------------------------------------------------- the modal
MODAL_ANCHOR = """<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>"""

MODAL_NEW = """<!-- NV-1d, 16 Oct 2026 - THE CUSTOMER SHEET, AS MARKUP.

     One hidden div per customer. The script unhides the one that was
     asked for and writes a title; that is the whole of the script.

     CC-1 took this decision on 15 Oct and wrote down why: base offers
     two pop-up patterns and the other one builds its div as a STRING in
     JavaScript. VB-1 had just spent a round on four controls that sat
     three-quarters wrong for weeks because no census could see them -
     markup a gate can read is worth more than markup that is
     convenient to generate. -->
<div class="modal fade" id="customerModal" tabindex="-1" role="dialog"
     aria-labelledby="customerModalLabel" aria-hidden="true">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title" id="customerModalLabel">Customer</h5>
                <button type="button" class="close" data-dismiss="modal"
                        aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body" id="customerModalBody">
                {% for row in rows %}
                <div class="cust-sheet" id="cust-sheet-{{ row.pk }}" hidden>
                    <div class="cust-sheet-row"><span class="cust-sheet-key">Customer</span><span class="cust-sheet-val">{{ row.name }}</span></div>
                    <div class="cust-sheet-row"><span class="cust-sheet-key">Customer ID</span><span class="cust-sheet-val">{{ row.customer_id_label|default:"-" }}</span></div>
                    <div class="cust-sheet-row"><span class="cust-sheet-key">Billing address</span><span class="cust-sheet-val">{{ row.billing_address|default:"-"|linebreaksbr }}</span></div>
                    <div class="cust-sheet-row"><span class="cust-sheet-key">Telephone</span><span class="cust-sheet-val">{{ row.billing_tel|default:"-" }}</span></div>
                    <div class="cust-sheet-row"><span class="cust-sheet-key">Email to</span><span class="cust-sheet-val">{{ row.email_to|default:"-" }}</span></div>
                    <div class="cust-sheet-row"><span class="cust-sheet-key">Email CC</span><span class="cust-sheet-val">{{ row.email_cc|default:"-" }}</span></div>
                    <div class="cust-sheet-row"><span class="cust-sheet-key">Invoices</span><span class="cust-sheet-val">{{ row.invoice_count }}</span></div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
""" + MODAL_ANCHOR

CSS_ANCHOR = """  /* the form is out of the layout in base - .mobile-action-bar > form */
}"""

CSS_NEW = """  /* the form is out of the layout in base - .mobile-action-bar > form */
}

/* NV-1d, 16 Oct 2026 - the customer sheet's rows. A key and a value per
   line, which is the shape base already draws on a phone card: the
   label on the left, the value on the right, and the value wrapping
   under it when there is no room. Written in base's tokens. */
.cust-sheet-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: baseline;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid var(--alv-line-soft);
}
.cust-sheet-row:last-child { border-bottom: 0; }
.cust-sheet-key {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--alv-ink-soft);
  flex-shrink: 0;
}
.cust-sheet-val {
  color: var(--alv-ink);
  text-align: right;
  word-break: break-word;
}"""

JS_ANCHOR = """    chips();
  });"""

JS_NEW = """    chips();
  });"""

HANDLER_ANCHOR = """})();
</script>"""

HANDLER_NEW = """})();

/* NV-1d, 16 Oct 2026 - THE VIEW BUTTON, IN ITS OWN IIFE AND WITHOUT `$`.

   Line 240 above, inside the filter IIFE, is

       function $(id) { return document.getElementById(id); }

   which is where every piece of DOM wiring on this page lives and so is
   the obvious place to put a click handler. Written there,
   `$(document).on('click', ...)` throws on load - getElementById of a
   document is null and null has no .on. The first draft of this round
   did exactly that, and a browser control printed back
   `TypeError: Cannot read properties of null (reading 'on')`.

   So: plain DOM, and Bootstrap by its real name. A page-local helper
   that borrows a global name is invisible to every text check and fatal
   at runtime. */
(function () {
  "use strict";
  document.addEventListener('click', function (e) {
    var btn = e.target.closest ? e.target.closest('.js-cust-view') : null;
    if (!btn) { return; }
    var sheet = document.getElementById('cust-sheet-' + btn.dataset.cust);
    if (!sheet) { return; }
    var sheets = document.querySelectorAll('.cust-sheet');
    for (var i = 0; i < sheets.length; i++) { sheets[i].hidden = true; }
    sheet.hidden = false;
    /* textContent, not innerHTML: a customer name is data somebody
       typed, which is the rule the chip builder below already keeps. */
    document.getElementById('customerModalLabel').textContent =
        btn.dataset.name || 'Customer';
    if (window.jQuery) {
      window.jQuery('#customerModal').modal('show');
    }
  });
})();
</script>"""


# -------------------------------------------- the alignment probe's gap
# test_table_invoices section 5b measures whether the Actions heading
# sits over its buttons, by stripping the Django tags out of the row and
# rendering what is left. Its stripper removes {% %} tags and {{ }}
# variables and does NOT remove {# #} COMMENTS - so this round's
# explanation of why View sorts first was rendered as visible TEXT
# inside .row-actions, pushing the buttons 1050px right of the heading.
#
# THE MARKUP IS FINE; THE PROBE WAS MEASURING SOMETHING THAT IS NOT ON
# THE SCREEN, which is step 5 of the pre-flight in one line. Django
# strips {# #} before anything renders. The new line goes FIRST, because
# a comment can contain a {% %} tag.
TI_WAS = r"""    frag = re.sub(r'\{\{[^}]*\}\}', 'x', re.sub(r'\{%[^%]*%\}', '', frag))"""

TI_NOW = r"""    # NV-1d, 16 Oct 2026 - AND {# #} COMMENTS, which Django strips
    # before anything renders and this stripper did not. A comment left
    # in the fragment is rendered as text, and it moved the buttons
    # 1050px right of the heading this section measures. First, because
    # a comment can contain a {% %} tag.
    frag = re.sub(r'\{#.*?#\}', '', frag, flags=re.S)
    frag = re.sub(r'\{\{[^}]*\}\}', 'x', re.sub(r'\{%[^%]*%\}', '', frag))"""

# ------------------------------------------------------------- registers
SENT_WAS = """    @{ File = 'pages\\templates\\customer_list.html';       Text = 'mobile-action-bar cols-2'; What = 'and its two mobile actions say so' },"""

SENT_NOW = """    @{ File = 'pages\\templates\\customer_list.html';       Text = '{% if not perms.auth.can_edit_invoices %} cols-2'; What = 'and the mobile bar asks for as many columns as it draws controls - three being base own default, so unnamed' },"""

IB_BAR_WAS = """check('the mobile bar declares its two columns', 'mobile-action-bar cols-2' in CT)"""

IB_BAR_NOW = """# NV-1d, 16 Oct 2026 - IT DECLARES AS MANY AS IT DRAWS. View needs no
# permission, so the bar draws three controls for an editor and two for
# a reader, and the class is chosen where the count is known. Three is
# NOT named, because base declares cols-1, cols-2 and cols-4 and
# deliberately no cols-3 - .mobile-action-bar is already repeat(3, 1fr).
check('the mobile bar declares as many columns as it draws',
      '{% if not perms.auth.can_edit_invoices %} cols-2' in CT)
# ASKED OF THE CLASS ATTRIBUTE, not of the page: the markup carries a
# comment that spells cols-3 in order to say why it is not used, and a
# page-wide test finds its own reasoning. Fifth time in four rounds.
_bar_cls = re.search(r'<td class="(mobile-action-bar[^"]*)"', CT)
check('  and names nothing when it draws three, because three is the '
      'default', bool(_bar_cls) and 'cols-3' not in _bar_cls.group(1))"""

SENT_ANCHOR = """    # -------------------------------------------- HL-1, 12 Oct 2026"""

SENT_NEW = """    # ------------------------------------------------ NV-1d, 16 Oct 2026
    # Demetri asked for a View button beside Edit and Delete on
    # Customers. There is no customer detail route, so View opens a
    # read-only sheet - the shape he described for receipts in the same
    # batch - carrying the four fields the table has no room for.
    @{ File = 'pages\\templates\\customer_list.html'; Text = 'js-cust-view'; What = 'Customers has a View, and it needs no edit permission' },
    @{ File = 'pages\\templates\\customer_list.html'; Text = 'cust-sheet-row'; What = 'and what it shows is MARKUP a gate can read, not a built string' },
    # NAMED AS THE ROW BUILDS IT. `billing_address` alone is in this
    # file three times already - a profile read, an edit POST and a
    # create - so the bare word could never have failed.
    @{ File = 'pages\\views\\physical_invoices.py'; Text = '"billing_address": c.billing_address'; What = 'the four hidden fields reach the template without a new query' },
    # -------------------------------------------- HL-1, 12 Oct 2026"""

SUITE_WAS = """    'test_notify_icon.py'
)"""

SUITE_NOW = """    'test_notify_icon.py',
    'test_customer_view.py'
)"""

TREE_WAS = """    'test_notify_icon.py',
]"""

TREE_NOW = """    'test_notify_icon.py',
    # NV-1d, 16 Oct 2026 - Customers gains a View, and because there is
    # no detail route it opens a read-only sheet built as markup. Wide
    # from birth.
    'test_customer_view.py',
]"""

ROUNDS_WAS = """    '.bak_notifyicon',
]"""

ROUNDS_NOW = """    '.bak_notifyicon',
    # NV-1d, 16 Oct 2026 - a View button on Customers, opening a
    # read-only sheet with the four fields the table has no room for.
    # The mobile bar's column count becomes conditional, because a LOOK
    # needs no permission.
    '.bak_custview',
]"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('NV-1d REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, was, now, where):
    once(text, was, where)
    return text.replace(fit(text, was), fit(text, now), 1)


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def js_of(t):
    return '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script\s*>', t, re.S))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    page = alv_tree.path_of(PAGE)
    view = os.path.join(root, VIEW)

    # ---------------------------------------------------------------- 0
    if 'js-cust-view' in code_only(read(page)):
        print('NV-1d  already applied - Customers has a View.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # THERE IS NO CUSTOMER DETAIL ROUTE, which is the whole reason this
    # is a modal. Asserted, because if one ever appears the right answer
    # changes from a sheet to a link.
    urls = read(os.path.join(root, 'pages', 'urls.py'))
    named = set(re.findall(r"name=[\"']([a-z_]*customer[a-z_]*)[\"']",
                           urls))
    if 'customer_detail' in named:
        refuse('pages/urls.py now has a customer_detail route, so View '
               'should be a LINK and not a modal. Named: %s'
               % sorted(named))
    for need in ('customer_list', 'customer_edit', 'customer_delete'):
        if need not in named:
            refuse('pages/urls.py does not name %s, so this round is '
                   'reading a different application' % need)

    # AND THE FOUR FIELDS EXIST ON THE MODEL.
    models = read(os.path.join(root, 'pages', 'models.py'))
    m = re.search(r'class InvoiceCustomer\b.*?(?=\nclass )', models, re.S)
    if not m:
        refuse('pages/models.py has no InvoiceCustomer')
    fields = set(re.findall(r'(?m)^\s{4}(\w+)\s*=\s*models\.', m.group(0)))
    for f in ('billing_address', 'billing_tel', 'email_cc', 'email_body'):
        if f not in fields:
            refuse('InvoiceCustomer has no %s, and this round shows it'
                   % f)

    # ---------------------------------------------------------------- 2
    s = read(view)
    # SCOPED TO THE ROW THIS ROUND BUILDS. billing_address appears three
    # times already in this file - a profile read, an edit POST and a
    # create - all in other functions, and a file-wide test refused a
    # correct round on them. Fourth time this week that a check searched
    # a whole file for something that belongs to one place.
    if '"billing_address": c.billing_address' in python_code_only(s):
        refuse('%s: customer_list already builds billing_address' % VIEW)
    out[view] = swap(s, VIEW_WAS, VIEW_NOW, '%s (customer_list rows)'
                     % VIEW)

    # AND THE FOUR LAND IN customer_list's OWN LOOP, not in one of the
    # other three rows.append in that file. Scoped, because the first
    # cut of this check was file-wide.
    fn = out[view][out[view].index('def customer_list'):]
    fn = fn[:fn.index('\ndef ')] if '\ndef ' in fn else fn
    for f in ('billing_address', 'billing_tel', 'email_cc', 'email_body'):
        if '"%s": c.%s' % (f, f) not in fn:
            refuse('%s: %s is not in customer_list own loop' % (VIEW, f))

    # ---------------------------------------------------------------- 3
    s = read(page)
    s = swap(s, STRIP_WAS, STRIP_NOW, '%s (the desktop strip)' % PAGE)
    s = swap(s, BAR_WAS, BAR_NOW, '%s (the phone bar)' % PAGE)
    s = swap(s, MODAL_ANCHOR, MODAL_NEW, '%s (the modal)' % PAGE)
    s = swap(s, CSS_ANCHOR, CSS_NEW, '%s (the sheet rules)' % PAGE)
    s = swap(s, HANDLER_ANCHOR, HANDLER_NEW, '%s (the handler)' % PAGE)
    out[page] = s

    # ---------------------------------------------------------------- 4
    # GATES.
    body = code_only(s)
    js = js_of(body)

    # THE GATE TESTS WHAT IS WRITTEN, NOT WHETHER A WORD APPEARS. The
    # first cut banned innerHTML and refused the page's own
    # `tags.innerHTML = ''`, which CLEARS the chips before rebuilding
    # them with createTextNode - the careful thing, not the careless one.
    for m2 in re.finditer(r'innerHTML\s*=\s*([^;\n]+)', js):
        rhs = m2.group(1).strip()
        if rhs not in ("''", '""'):
            refuse('%s: innerHTML is assigned %s. The sheet is MARKUP on '
                   'this page; an empty clear is the only write allowed '
                   'here.' % (PAGE, rhs))

    # THE HANDLER MUST NOT USE `$`, because this page shadows it.
    # FOUND BY ITS CODE, NOT BY ITS COMMENT. code_only() strips comments
    # inside <script>, which is the whole point of it, so slicing at the
    # round's own note found nothing and refused a correct round.
    key = "closest('.js-cust-view')"
    if key not in js:
        refuse('%s: the handler did not land' % PAGE)
    hs = js[js.rindex('(function', 0, js.index(key)):]
    if re.search(r'(?<![\w.])\$\s*\(', hs):
        refuse('%s: the new handler uses $(, and line 240 of this page '
               'defines $ as getElementById. Use window.jQuery.' % PAGE)
    if 'window.jQuery' not in hs:
        refuse('%s: the handler does not reach Bootstrap by its real '
               'name' % PAGE)
    if 'function $(id) { return document.getElementById(id); }' not in js:
        refuse('%s: the $ shadow this round works around is gone, so the '
               'comment explaining it is now wrong' % PAGE)

    # ONE SHEET PER ROW, SEVEN ROWS EACH, AS MARKUP.
    if body.count('class="cust-sheet"') != 1:
        refuse('%s: expected one cust-sheet template inside the for loop'
               % PAGE)
    sheet = re.search(r'<div class="cust-sheet"[^>]*>(.*?)\n\s*</div>',
                      body, re.S)
    if not sheet or sheet.group(1).count('cust-sheet-row') != SHEET_ROWS:
        refuse('%s: the sheet draws %d row(s), expected %d'
               % (PAGE, sheet.group(1).count('cust-sheet-row')
                  if sheet else 0, SHEET_ROWS))
    if body.count('id="customerModal"') != 1:
        refuse('%s: the modal is not declared once' % PAGE)

    # VIEW IS FIRST, AND OUTSIDE THE PERMISSION TEST.
    strip = re.search(r'<div class="row-actions">(.*?)</div>', body, re.S)
    if not strip:
        refuse('%s: no row-action strip' % PAGE)
    if strip.group(1).index('js-cust-view') > strip.group(1).index(
            'icon-edit'):
        refuse('%s: View does not come first in the strip' % PAGE)
    before_if = strip.group(1).split('{% if perms')[0]
    if 'js-cust-view' not in before_if:
        refuse('%s: View is inside the permission test, and reading a '
               'record is not editing invoices' % PAGE)

    # THE BAR ASKS FOR AS MANY COLUMNS AS IT DRAWS.
    if ('{% if not perms.auth.can_edit_invoices %} cols-2'
            not in body):
        refuse('%s: the bar column count is not conditional' % PAGE)
    # AND cols-3 IS NOT NAMED, because base does not declare it: three
    # is .mobile-action-bar's own grid. A class with no rule is dead
    # weight exactly as a rule with no element is a bug.
    # ASKED OF THE CLASS ATTRIBUTE, not of the page: the explanation
    # beside this markup spells cols-3 in order to say why it is not
    # used, and a page-wide test would find its own reasoning. Fifth
    # time in four rounds.
    _bar = re.search(r'<td class="(mobile-action-bar[^"]*)"', body)
    if _bar and 'cols-3' in _bar.group(1):
        refuse('%s: the bar asks for cols-3, which base does not '
               'declare - three columns are .mobile-action-bar own grid'
               % PAGE)
    bphone = read(alv_tree.path_of('base.html'))
    if '.mobile-action-bar.cols-3' in bphone:
        refuse('base now declares cols-3, so this round should name it '
               'rather than relying on the default')
    if not re.search(r'\.mobile-action-bar\s*\{[^}]*repeat\(3,\s*1fr\)',
                     bphone):
        refuse('base no longer defaults the bar to three columns, and '
               'this round leaves the editor arm unnamed on that basis')
    # COUNTED AS A CLASS, so the handler's own selector is not a third
    # control. `js-cust-view` appears three times on this page: two
    # class attributes and one closest() call.
    n_view = len(re.findall(r'class="[^"]*\bjs-cust-view\b[^"]*"', body))
    if n_view != 2:
        refuse('%s: %d View control(s), expected 2 - the desktop strip '
               'and the phone bar' % (PAGE, n_view))

    try:
        import alv_rowactions as RA
        if not RA.FAMILY['view'] < RA.FAMILY['edit'] < RA.FAMILY['delete']:
            refuse('alv_rowactions no longer sorts view, edit, delete in '
                   'that order, and this round put them in it on its word')
    except ImportError:
        refuse('alv_rowactions is not importable, and the order of the '
               'strip rests on it')

    # ---------------------------------------------------------------- 5
    p = os.path.join(root, PS1)
    s = read(p)
    if ME in s:
        refuse('%s already lists this round' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suite list)' % PS1)
    # THE FALSIFIED ROW, RE-POINTED. The conditional class makes the old
    # claim false, and test_sentinels names it by line within one run.
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the falsified sentinel)' % PS1)
    s = swap(s, SENT_ANCHOR, SENT_NEW, '%s (the gate rows)' % PS1)
    out[p] = s

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), ROUNDS_WAS, ROUNDS_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'NV-1d, 16 Oct 2026 - this round own suite. Customers '
                  'gains a View that opens a read-only sheet, after '
                  'Demetri asked for a View button beside Edit and '
                  'Delete and there was no customer detail screen to '
                  'send it to.',
                  '%s (the converted count)' % WD)

    p = os.path.join(root, BH)
    out[p] = bump(read(p), 'N_BAR, N_ROW, N_MODAL = 267, %d, 95',
                  ROW_WAS_N, ROW_NOW_N,
                  'NV-1d, 16 Oct 2026 - the View button in the desktop '
                  'strip, which is inside a table.',
                  '%s (the table-row census)' % BH)

    p = os.path.join(root, IB)
    s = read(p)
    if 'cust-sheet-row' in s:
        refuse('%s already knows about the sheet' % IB)
    s = bump(s, 'len(_left) <= %d,', LEFT_WAS, LEFT_NOW,
             'NV-1d, 16 Oct 2026 - the customer sheet brings four rules '
             'of its own: cust-sheet-row, its last-child, and the key '
             'and value spans. They are a page component base has no '
             'name for, like .cust-inline-form beside them, and the '
             'same two of slack is kept.',
             '%s (the rules left on the page)' % IB)
    s = swap(s, IB_BAR_WAS, IB_BAR_NOW, '%s (the bar claim)' % IB)
    out[p] = s

    p = os.path.join(root, TI)
    s = read(p)
    if 'NV-1d, 16 Oct 2026 - AND {# #} COMMENTS' in s:
        refuse('%s already strips Django comments' % TI)
    out[p] = swap(s, TI_WAS, TI_NOW, '%s (the tag stripper)' % TI)

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'NV-1d, 16 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # ---------------------------------------------------------------- 6
    if CHECK:
        print('NV-1d --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('NV-1d applied.')
    print('   Customers has a View, and it sorts FIRST because a LOOK')
    print('         does - alv_rowactions says so, not the markup')
    print('   it opens a read-only sheet, because there is no customer')
    print('         detail route - checked, not assumed')
    print('   the sheet carries the FOUR fields the table has no room')
    print('         for, with no new route and no new query')
    print('   built as MARKUP a gate can read, not a string')
    print('   the handler uses window.jQuery, because line 240 of this')
    print('         page defines $ as getElementById')
    print('   the phone bar asks for cols-2 when it draws two, and')
    print('         names nothing when it draws three, because three is')
    print('         base own default and cols-3 styles nothing')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
