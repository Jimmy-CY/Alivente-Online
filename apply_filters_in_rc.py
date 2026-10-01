# -*- coding: utf-8 -*-
"""SECTION F, ROUND F2 - THE TWO SCREENS WITH NO WAY TO NARROW THEM

Demetri walked both and found the same thing: compliant table, compliant
buttons, and no filter at all.

  IN-1  Invoice Customers - "We need to add a filter section."
  RC-1  Receipts          - "Month, Received From, Status ??"

Written in the spelling F1 settled: method="get", no csrf token, submit
on change. Both panels are base's component throughout - the only CSS
either page adds is its own grid-template-columns, which the ALV FILTER
FRAME note in base explicitly leaves to the page.

------------------------------------------------
THE TWO ARE NOT THE SAME SHAPE, AND THE FOOTER IS WHY
------------------------------------------------
Invoice Customers is an ordinary server filter with a live box on top -
the properties.html pattern exactly.

Receipts has a TOTAL ISSUED line in its tfoot, summed in the view. Demetri:
"It should follow the filter." So three of its controls go to the server
(the dates and the status change WHICH ROWS EXIST), and Received From
narrows in the browser as you type - he asked for "an open field that
searches as the user types", and a round trip per keystroke is not that.

That leaves the total having to follow BOTH. It is computed twice, from
the same numbers:

  * THE SERVER sums the rows it is sending, so the page is right on load
    and right with JavaScript turned off.
  * THE BROWSER re-sums the VISIBLE rows whenever the live filter hides
    one, reading data-amount off each row - a string the VIEW wrote with
    '%.2f', not a number scraped back out of formatted display text with
    a currency sign and thousands separators in it.

A MutationObserver watches the rows' style attribute rather than hooking
the search box, because that works whichever order the two scripts were
wired in. base's live-search sets row.style.display and leaves the tfoot
alone - its own note says a row with none of the named cells "is not a
data row - an empty state, a totals line - and is left alone".

--------------------------------
AND THE CURRENCY, WHICH IS A REAL ONE
--------------------------------
CashReceipt.currency is a column with a default of EUR. The old view
summed every row regardless and the template printed the answer behind a
hardcoded euro sign. If a receipt were ever issued in anything else, that
number has been adding unlike things together, silently.

Show-NarrowingData.py was written to ask production. The first run read a
LOCAL database - 127.0.0.1, and the banner said ON THIS MACHINE, which is
exactly what that banner exists for - so the answer is still outstanding.

SO THIS ROUND DOES NOT DEPEND ON THE ANSWER. The total is grouped by
currency on both sides. One currency and it reads as one line, exactly as
before. Two and it reads as two lines, because two is what is true. The
production answer will confirm the build rather than change it.

------------
THE FIELDS
------------
Invoice Customers, agreed with Demetri:
    Customer        text, narrows as you type AND filters on the server
    Customer ID     text
    Invoices        All / With invoices / Without - which finds the
                    customers set up and never billed

Receipts:
    From / To       dates, on receipt_date. Demetri chose a date pair over
                    a month dropdown.
    Received From   text, narrows as you type. payer_name is SNAPSHOTTED
                    onto the receipt at issue, so this matches what was
                    actually typed, not the tenant table.
    Status          All / Issued / Void. is_void is a boolean, so three
                    options cover it exactly.

Backups: .bak_filtersinrc. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_filtersinrc'
CRLF = {}
SENTINEL = 'test_filters_in_rc.py'
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
            raise SystemExit('F2: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    """Replace exactly once, in the file's own line endings, and refuse an
    anchor that lands mid-line.

    A3's lesson, four hours old: an anchor beginning with spaces matches
    inside a MORE deeply indented line, so it edits real code at the wrong
    indentation and leaves a file that will not parse."""
    o, n = eol(path, old), eol(path, new)
    c = text.count(o)
    if c != 1:
        raise SystemExit('F2: %s appears %d times, not once' % (what, c))
    i = text.index(o)
    if i and not o.startswith(('\n', '\r')) and text[i - 1] not in '\n\r':
        raise SystemExit('F2: the anchor for %s starts MID-LINE (after %r)'
                         % (what, text[i - 1]))
    return text.replace(o, n)


print('=' * 74)
print('SECTION F, ROUND F2 - A WAY TO NARROW BOTH SCREENS%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)
print('')
print('  IN-1  INVOICE CUSTOMERS')
print('  ' + '-' * 70)

# ==========================================================================
# IN-1, the view
# ==========================================================================
PI = os.path.join(ROOT, 'pages', 'views', 'physical_invoices.py')
pt, praw = read(PI)
if 'customer_q' in pt:
    print('  pages/views/physical_invoices.py   already done')
else:
    pt = swap(pt,
              'from django.db.models import ExpressionWrapper, F, '
              'IntegerField, ProtectedError\n',
              'from django.db.models import (Count, ExpressionWrapper, F,\n'
              '                              IntegerField, ProtectedError)\n',
              'the db.models import', PI)
    pt = swap(pt, '''def customer_list(request):
    """The saved invoice-customer book."""
    customers = InvoiceCustomer.objects.all().order_by("name")
    rows = []
    for c in customers:
        rows.append({
            "pk": c.pk,
            "name": c.name,
            "customer_id_label": c.customer_id_label,
            "email_to": c.email_to,
            "invoice_count": c.invoices.count(),
        })
    return render(request, "customer_list.html", {"rows": rows})
''', '''def customer_list(request):
    """The saved invoice-customer book, narrowed - IN-1, 1 Oct 2026.

    Three controls, agreed with Demetri: the name, the customer ID, and
    whether the customer has any invoices at all. The third is the one
    worth having - it finds the customers who were set up and never
    billed, which no amount of scrolling makes obvious.

    FROM THE QUERY STRING. method="get" is the house spelling since F1:
    the URL carries the filter, so a narrowed list can be bookmarked and
    sent, Back returns to it, and a refresh is safe.

    ONE QUERY, NOT ONE PER ROW. invoice_count was c.invoices.count()
    inside the loop - a query per customer. It is an annotate now, which
    the has-invoices filter needs anyway: you cannot filter on a number
    you compute in Python after the queryset has been evaluated.
    """
    name_q = (request.GET.get("customer") or "").strip()
    id_q = (request.GET.get("customer_id") or "").strip()
    has_q = (request.GET.get("has_invoices") or "").strip()

    customers = (InvoiceCustomer.objects
                 .annotate(n_invoices=Count("invoices"))
                 .order_by("name"))
    if name_q:
        customers = customers.filter(name__icontains=name_q)
    if id_q:
        customers = customers.filter(customer_id_label__icontains=id_q)
    if has_q == "yes":
        customers = customers.filter(n_invoices__gt=0)
    elif has_q == "no":
        customers = customers.filter(n_invoices=0)

    rows = []
    for c in customers:
        rows.append({
            "pk": c.pk,
            "name": c.name,
            "customer_id_label": c.customer_id_label,
            "email_to": c.email_to,
            "invoice_count": c.n_invoices,
        })
    return render(request, "customer_list.html", {
        "rows": rows,
        # echoed back so the controls hold what was asked for
        "customer_q": name_q,
        "customer_id_q": id_q,
        "has_invoices": has_q,
    })
''', 'customer_list', PI)
    if not CHECK:
        back_up(PI, praw)
        write(PI, pt)
    print('  pages/views/physical_invoices.py   three controls, one query')

# ==========================================================================
# IN-1, the page
# ==========================================================================
CUST_FILTER = '''      <button type="button" class="btn action-filter" id="filterBtn"
              aria-pressed="false" aria-controls="filterPanel"
              aria-label="Show filters">
        <i class="fas fa-filter"></i><span class="action-filter-label"> Filter</span><span class="action-filter-count" data-count="0"></span>
      </button>
      <a href="{% url 'physical_invoice_list' %}" class="btn action-back" aria-label="Back to physical invoices">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
      </a>
    </div>

    {# THE CHIPS. base owns the row, the tag and the x; the page says    #}
    {# which filters are on.                   [test_filters_in_rc.py]  #}
    <div class="alv-filter-active" id="activeFilters">
      <span class="alv-filter-active-label">Active filters:</span>
      <div class="filter-tags" id="filterTags"></div>
    </div>

    <div class="alv-filter filter-panel" id="filterPanel">
      <div class="filter-header">
        <h5 class="filter-title">
          <i class="fas fa-filter"></i> Filters
        </h5>
        <button type="button" id="clearAllBtn" class="btn action-secondary btn-sm">
          <i class="fas fa-times-circle"></i> Clear All
        </button>
      </div>

      <div class="filter-content" id="filterContent">
        {# GET, no csrf token - the house spelling since F1. A GET form   #}
        {# serialises every field into the query string, so a token in    #}
        {# one lands in the address bar and the Referer.                  #}
        <form action="{% url 'customer_list' %}" method="get" id="filterForm">
          <div class="filter-grid">
            <div class="filter-group">
              <label class="filter-label" for="customerInput">
                <i class="fas fa-search"></i> <strong>Customer</strong>
              </label>
              <div class="search-input-group">
                {# data-live-search narrows what is ALREADY on screen as   #}
                {# you type; the same box posts to the server on Enter and #}
                {# leaves a chip. base's note: neither replaces the other. #}
                {# Only ONE box per table may do this - two would hide and #}
                {# show the same rows against each other.                  #}
                <input type="text"
                       name="customer"
                       id="customerInput"
                       class="form-control search-input"
                       data-live-search=".customers-table"
                       data-live-search-cell="Customer"
                       placeholder="Search by customer name..."
                       value="{{ customer_q|default:'' }}">
                <button type="button" class="search-btn" id="searchBtn"
                        aria-label="Search">
                  <i class="fas fa-search"></i>
                </button>
              </div>
            </div>

            <div class="filter-group">
              <label class="filter-label" for="customerIdInput">
                <i class="fas fa-hashtag"></i> <strong>Customer ID</strong>
              </label>
              <input type="text"
                     name="customer_id"
                     id="customerIdInput"
                     class="form-control filter-input"
                     placeholder="Search by customer ID..."
                     value="{{ customer_id_q|default:'' }}">
            </div>

            <div class="filter-group">
              <label class="filter-label" for="hasInvoicesSelect">
                <i class="fas fa-file-invoice"></i> <strong>Invoices</strong>
              </label>
              <select name="has_invoices" class="form-control filter-select"
                      id="hasInvoicesSelect">
                <option value="">All Customers</option>
                <option value="yes" {% if has_invoices == 'yes' %}selected{% endif %}>With invoices</option>
                <option value="no" {% if has_invoices == 'no' %}selected{% endif %}>Without invoices</option>
              </select>
            </div>
          </div>
        </form>
      </div>
    </div>
'''

CUST_CSS = '''{% block content %}
<style>
/* ONE RULE, AND THE PHONE STACK. The first version also carried four
   rules swapping a long label for a short one on a phone - which is
   what properties.html does, copied. test_icon_buttons caps this page's
   leftover CSS and was right to complain: a panel on the Customers page
   does not need its heading to say Customer. The heading is just
   Filters, on every width, and four rules and four spans went with it.
 base owns .filter-grid, .filter-header,
   .filter-title, .filter-group, .filter-label, .filter-select,
   .filter-input, .search-input-group, .search-btn, .filter-tags and
   .filter-tag - and leaves grid-template-columns to the page, because
   how many filters a screen has is the screen's business. Zero literal
   colours.                                   [test_filters_in_rc.py] */
.filter-grid { grid-template-columns: 2fr 1fr 1fr; }
@media screen and (max-width: 768px) { .filter-grid { grid-template-columns: 1fr; } }
</style>
'''

CUST_JS = '''
<script>
/* THE FILTER, WIRED THE WAY EVERY OTHER FILTER PAGE IS WIRED.
   base opens and closes the panel and keeps the count on the button; this
   says what the controls do.              [test_filters_in_rc.py] */
(function () {
  "use strict";
  function $(id) { return document.getElementById(id); }
  function submit() { var f = $('filterForm'); if (f) { f.submit(); } }

  document.addEventListener('DOMContentLoaded', function () {
    var sel = $('hasInvoicesSelect');
    if (sel) { sel.addEventListener('change', submit); }

    /* A TEXT BOX HAS NO USEFUL change EVENT for this - it fires on blur,
       which is not what pressing Enter feels like. Both boxes submit on
       Enter, and the magnifier submits the one beside it. */
    ['customerInput', 'customerIdInput'].forEach(function (id) {
      var box = $(id);
      if (!box) { return; }
      box.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') { e.preventDefault(); submit(); }
      });
    });
    var btn = $('searchBtn');
    if (btn) { btn.addEventListener('click', submit); }

    var clear = $('clearAllBtn');
    if (clear) {
      clear.addEventListener('click', function () {
        ['customerInput', 'customerIdInput'].forEach(function (id) {
          if ($(id)) { $(id).value = ''; }
        });
        if ($('hasInvoicesSelect')) { $('hasInvoicesSelect').value = ''; }
        submit();
      });
    }
    chips();
  });

  function chips() {
    var tags = $('filterTags');
    if (!tags) { return; }
    var name = $('customerInput') ? $('customerInput').value : '';
    var cid = $('customerIdInput') ? $('customerIdInput').value : '';
    var has = $('hasInvoicesSelect') ? $('hasInvoicesSelect').value : '';
    tags.innerHTML = '';
    if (name) { tags.appendChild(chip('Customer: "' + name + '"', 'customerInput')); }
    if (cid) { tags.appendChild(chip('Customer ID: "' + cid + '"', 'customerIdInput')); }
    if (has) {
      tags.appendChild(chip(has === 'yes' ? 'With invoices' : 'Without invoices',
                            'hasInvoicesSelect'));
    }
  }

  /* BUILT WITH textContent, NOT innerHTML. A customer name is data
     somebody typed, and pasting it into markup makes an apostrophe or a
     < into a rendering bug at best. */
  function chip(label, controlId) {
    var span = document.createElement('span');
    span.className = 'filter-tag';
    span.appendChild(document.createTextNode(label + ' '));
    var x = document.createElement('button');
    x.className = 'remove-tag';
    x.type = 'button';
    x.setAttribute('aria-label', 'Remove this filter');
    x.textContent = '\\u00d7';
    x.addEventListener('click', function () {
      var c = document.getElementById(controlId);
      if (c) { c.value = ''; }
      var f = document.getElementById('filterForm');
      if (f) { f.submit(); }
    });
    span.appendChild(x);
    return span;
  }
})();
</script>

{% endblock %}'''

CP = alv_tree.path_of('customer_list.html')
ct, craw = read(CP)
if 'filterPanel' in ct:
    print('  customer_list.html                 already done')
else:
    ct = swap(ct, '{% block content %}\n', CUST_CSS, 'the content block', CP)
    ct = swap(ct,
              '''      <a href="{% url 'physical_invoice_list' %}" class="btn action-back" aria-label="Back to physical invoices">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
      </a>
    </div>
''', CUST_FILTER, 'the action bar', CP)
    ct = ct.rstrip()
    if not ct.endswith(eol(CP, '{% endblock %}')):
        raise SystemExit('F2: customer_list.html does not end in endblock')
    ct = ct[:-len(eol(CP, '{% endblock %}'))].rstrip() + eol(CP, CUST_JS)
    if not CHECK:
        back_up(CP, craw)
        write(CP, ct)
    print('  customer_list.html                 panel, chips, one CSS rule')

print('')
print('  RC-1  RECEIPTS')
print('  ' + '-' * 70)

# ==========================================================================
# RC-1, the view
# ==========================================================================
RP = os.path.join(ROOT, 'pages', 'views', 'receipts.py')
rt, rraw = read(RP)
if 'receipt_totals' in rt:
    print('  pages/views/receipts.py            already done')
else:
    rt = swap(rt, 'from django.utils import timezone\n',
              'from django.utils import timezone\n'
              'from django.utils.dateparse import parse_date\n',
              'the timezone import', RP)
    rt = swap(rt, '''@login_required
@permission_required('auth.can_access_receipts', raise_exception=True)
def cash_receipt_list(request):
    """Issued receipts, newest first.

    The rows are built here rather than in the template - the same reasoning
    as Open Invoices. A template that decides its own rows cannot tell you
    whether it drew any, so it cannot have an empty state.
    """
    qs = (CashReceipt.objects
          .select_related('tenant', 'customer', 'prop')
          .order_by('-receipt_date', '-cash_receipt_id'))
''', '''def _as_date(raw):
    """A date from the query string, or None.

    TWO WAYS A URL CAN CARRY A BAD DATE, AND parse_date TREATS THEM
    DIFFERENTLY. For something it cannot read at all - "not-a-date" - it
    returns None. For something that matches its pattern and is not a real
    date - "2026-13-45" - it RAISES ValueError, because it gets as far as
    building a datetime.date and that fails.

    To this view they are the same thing: a filter it cannot apply. A
    hand-edited address bar is the ordinary way either arrives, and
    showing an unfiltered list is a better answer than a 500. Found by
    test_filters_in_rc.py section 3b, which asked for both.
    """
    try:
        return parse_date((raw or '').strip())
    except ValueError:
        return None


@login_required
@permission_required('auth.can_access_receipts', raise_exception=True)
def cash_receipt_list(request):
    """Issued receipts, newest first, narrowed - RC-1, 1 Oct 2026.

    The rows are built here rather than in the template - the same reasoning
    as Open Invoices. A template that decides its own rows cannot tell you
    whether it drew any, so it cannot have an empty state.

    THREE OF THE FOUR CONTROLS ARE HERE AND ONE IS NOT. From, To and Status
    change WHICH ROWS EXIST, so they are a server filter in the query
    string, the house spelling since F1. Received From narrows in the
    browser as you type - Demetri asked for "an open field that searches as
    the user types", and a round trip per keystroke is not that.

    A BAD DATE IS IGNORED, NOT RAISED. parse_date returns None for anything
    it cannot read, and a hand-edited URL is the ordinary way that happens.
    Dropping the clause shows an unfiltered list; letting it through would
    show a 500 to somebody who mistyped their own address bar.

    AND THE TOTAL IS GROUPED BY CURRENCY. It used to be one blind sum
    printed behind a hardcoded euro sign, while CashReceipt.currency is a
    real column with a default of EUR - so a single receipt in anything else
    made that number add unlike things together, silently. One currency
    still reads as one line. The browser re-sums the same way when the live
    filter hides a row; see the script on the page.
    """
    date_from = _as_date(request.GET.get('from'))
    date_to = _as_date(request.GET.get('to'))
    payer_q = (request.GET.get('payer') or '').strip()
    status_q = (request.GET.get('status') or '').strip()

    qs = (CashReceipt.objects
          .select_related('tenant', 'customer', 'prop')
          .order_by('-receipt_date', '-cash_receipt_id'))
    if date_from:
        qs = qs.filter(receipt_date__gte=date_from)
    if date_to:
        qs = qs.filter(receipt_date__lte=date_to)
    if payer_q:
        qs = qs.filter(payer_name__icontains=payer_q)
    if status_q == 'issued':
        qs = qs.filter(is_void=False)
    elif status_q == 'void':
        qs = qs.filter(is_void=True)
''', 'the cash_receipt_list head', RP)
    rt = swap(rt, '''            'status_display': 'Void' if r.is_void else 'Issued',
            'has_pdf': bool(r.pdf_file),
        })

    total = sum((r['amount'] for r in rows if not r['is_void']), Decimal('0.00'))

    return render(request, "cash_receipts.html", {
        "rows": rows,
        "receipt_total": total,
        "next_number": preview_next(),
    })
''', '''            'status_display': 'Void' if r.is_void else 'Issued',
            'has_pdf': bool(r.pdf_file),
            # A PLAIN STRING FOR THE BROWSER TO ADD UP. Written here with
            # %.2f rather than left to a template filter, so no locale and
            # no thousands separator can ever get into it - the script
            # reads this attribute, never the formatted cell beside it.
            'amount_raw': '%.2f' % (r.amount or Decimal('0.00')),
        })

    # PER CURRENCY, NOT ONE SUM. See the docstring.
    totals = OrderedDict()
    for row in rows:
        if row['is_void']:
            continue
        code = (row['currency'] or 'EUR').strip().upper()
        totals[code] = totals.get(code, Decimal('0.00')) + row['amount']
    receipt_totals = [{'currency': c, 'amount': a,
                       'symbol': '\\u20ac' if c == 'EUR' else c}
                      for c, a in totals.items()]

    return render(request, "cash_receipts.html", {
        "rows": rows,
        "receipt_totals": receipt_totals,
        "next_number": preview_next(),
        # echoed back so the controls hold what was asked for
        "date_from": (request.GET.get('from') or '').strip(),
        "date_to": (request.GET.get('to') or '').strip(),
        "payer_q": payer_q,
        "status_q": status_q,
    })
''', 'the cash_receipt_list tail', RP)
    if 'from collections import OrderedDict' not in rt:
        rt = swap(rt, 'from decimal import Decimal, InvalidOperation\n',
                  'from collections import OrderedDict\n'
                  'from decimal import Decimal, InvalidOperation\n',
                  'the decimal import', RP)
    if not CHECK:
        back_up(RP, rraw)
        write(RP, rt)
    print('  pages/views/receipts.py            four controls, totals by '
          'currency')

# ==========================================================================
# RC-1, the page
# ==========================================================================
REC_FILTER = """    <a href="{% url 'home' %}" class="btn action-back" aria-label="Back to home">
      <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
    </a>
  </div>

  {# THE CHIPS, then the panel. base owns both components; the page says #}
  {# which filters are on.                   [test_filters_in_rc.py]    #}
  <div class="alv-filter-active" id="activeFilters">
    <span class="alv-filter-active-label">Active filters:</span>
    <div class="filter-tags" id="filterTags"></div>
  </div>

  <div class="alv-filter filter-panel" id="filterPanel">
    <div class="filter-header">
      <h5 class="filter-title">
        <i class="fas fa-filter"></i> Filters
      </h5>
      <button type="button" id="clearAllBtn" class="btn action-secondary btn-sm">
        <i class="fas fa-times-circle"></i> Clear All
      </button>
    </div>

    <div class="filter-content" id="filterContent">
      {# GET, no csrf token - the house spelling since F1. #}
      <form action="{% url 'cash_receipt_list' %}" method="get" id="filterForm">
        <div class="filter-grid">
          <div class="filter-group">
            <label class="filter-label" for="fromInput">
              <i class="fas fa-calendar-alt"></i> <strong>From</strong>
            </label>
            <input type="date" name="from" id="fromInput"
                   class="form-control filter-input"
                   value="{{ date_from|default:'' }}">
          </div>

          <div class="filter-group">
            <label class="filter-label" for="toInput">
              <i class="fas fa-calendar-alt"></i> <strong>To</strong>
            </label>
            <input type="date" name="to" id="toInput"
                   class="form-control filter-input"
                   value="{{ date_to|default:'' }}">
          </div>

          <div class="filter-group">
            <label class="filter-label" for="payerInput">
              <i class="fas fa-search"></i> <strong>Received From</strong>
            </label>
            <div class="search-input-group">
              {# NARROWS AS YOU TYPE, and posts on Enter. payer_name is    #}
              {# snapshotted onto the receipt when it is issued, so this   #}
              {# matches what was actually typed, not the tenant table.    #}
              <input type="text"
                     name="payer"
                     id="payerInput"
                     class="form-control search-input"
                     data-live-search=".receipts-table"
                     data-live-search-cell="Received From"
                     placeholder="Search by payer name..."
                     value="{{ payer_q|default:'' }}">
              <button type="button" class="search-btn" id="searchBtn"
                      aria-label="Search">
                <i class="fas fa-search"></i>
              </button>
            </div>
          </div>

          <div class="filter-group">
            <label class="filter-label" for="statusSelect">
              <i class="fas fa-info-circle"></i> <strong>Status</strong>
            </label>
            <select name="status" class="form-control filter-select"
                    id="statusSelect">
              <option value="">All Receipts</option>
              <option value="issued" {% if status_q == 'issued' %}selected{% endif %}>Issued</option>
              <option value="void" {% if status_q == 'void' %}selected{% endif %}>Void</option>
            </select>
          </div>
        </div>
      </form>
    </div>
  </div>
"""

REC_BTN = """    <a href="{% url 'cash_receipt_add' %}" class="btn action-primary action-add-new">
        <i class="fas fa-plus"></i> Issue Receipt
      </a>"""

RP2 = alv_tree.path_of('cash_receipts.html')
rt2, rraw2 = read(RP2)
if 'filterPanel' in rt2:
    print('  cash_receipts.html                 already done')
else:
    # the Filter button, beside Back
    rt2 = swap(rt2,
               """    <a href="{% url 'home' %}" class="btn action-back" aria-label="Back to home">""",
               """    <button type="button" class="btn action-filter" id="filterBtn"
            aria-pressed="false" aria-controls="filterPanel"
            aria-label="Show filters">
      <i class="fas fa-filter"></i><span class="action-filter-label"> Filter</span><span class="action-filter-count" data-count="0"></span>
    </button>
    <a href="{% url 'home' %}" class="btn action-back" aria-label="Back to home">""",
               'the Back link', RP2)
    # THE ANCHOR INCLUDES THE </div> THAT CLOSES THE ACTION BAR, and the
    # first version did not - it matched the three <a> lines only, so the
    # original closer survived AFTER the whole inserted block and the page
    # ended one </div> heavier than it opened. test_div_balance,
    # test_heading_prefix and test_cash_receipts all said so. A clever
    # slice of REC_FILTER was what hid it; the anchor is written out.
    rt2 = swap(rt2, """    <a href="{% url 'home' %}" class="btn action-back" aria-label="Back to home">
      <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
    </a>
  </div>
""", REC_FILTER, 'the end of the action bar', RP2)
    # every row carries what the browser needs to re-add it up
    rt2 = swap(rt2,
               """          <tr{% if row.is_void %} class="rec-void"{% endif %}>""",
               """          {# data-amount is the view's own '%.2f' string, so no  #}
          {# locale or separator can get into the number the script #}
          {# adds up. It never reads the formatted cell.            #}
          <tr{% if row.is_void %} class="rec-void"{% endif %} data-amount="{{ row.amount_raw }}" data-currency="{{ row.currency|default:'EUR' }}" data-void="{% if row.is_void %}1{% else %}0{% endif %}">""",
               'the row', RP2)
    # the footer, per currency
    rt2 = swap(rt2,
               """          <td class="num" data-label="Total issued">&euro; {{ receipt_total|floatformat:2|intcomma }}</td>""",
               """          <td class="num" data-label="Total issued" id="receiptTotal">
            {% for t in receipt_totals %}<div class="receipt-total-line">{{ t.symbol }} {{ t.amount|floatformat:2|intcomma }}</div>{% empty %}<div class="receipt-total-line">&euro; 0.00</div>{% endfor %}
          </td>""",
               'the totals cell', RP2)
    if not CHECK:
        back_up(RP2, rraw2)
        write(RP2, rt2)
    print('  cash_receipts.html                 panel, chips, per-currency '
          'total')

    # the page's own CSS block gains ONE rule, and the script goes in
    # beside it
    rt2, _ = read(RP2)
    REC_TAIL_OLD = "</style>\n\n{% endblock %}"
    REC_TAIL_NEW = """
/* TWO RULES AND THE PHONE STACK - see the note on customer_list for why
   there are not six.
 base owns every filter class; it leaves
   grid-template-columns to the page, because how many filters a screen
   has is the screen's business. Zero literal colours.
                                              [test_filters_in_rc.py] */
.filter-grid { grid-template-columns: 1fr 1fr 2fr 1fr; }
/* one line per currency, so two of them do not run together */
.receipt-total-line + .receipt-total-line { margin-top: 2px; }
@media screen and (max-width: 768px) { .filter-grid { grid-template-columns: 1fr; } }
</style>

<script>
/* THE FILTER, AND THE TOTAL THAT FOLLOWS IT.
   base opens and closes the panel, keeps the count on the button, and
   runs the live search. This says what the controls do and keeps TOTAL
   ISSUED honest while they do it.          [test_filters_in_rc.py] */
(function () {
  "use strict";
  function $(id) { return document.getElementById(id); }
  function submit() { var f = $('filterForm'); if (f) { f.submit(); } }

  document.addEventListener('DOMContentLoaded', function () {
    /* THE DATES AND THE STATUS GO TO THE SERVER, because they change
       which rows exist. Received From does not - it narrows what is
       already here, which is what "searches as the user types" means. */
    ['fromInput', 'toInput', 'statusSelect'].forEach(function (id) {
      var el = $(id);
      if (el) { el.addEventListener('change', submit); }
    });
    var payer = $('payerInput');
    if (payer) {
      payer.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') { e.preventDefault(); submit(); }
      });
    }
    var btn = $('searchBtn');
    if (btn) { btn.addEventListener('click', submit); }

    var clear = $('clearAllBtn');
    if (clear) {
      clear.addEventListener('click', function () {
        ['fromInput', 'toInput', 'payerInput'].forEach(function (id) {
          if ($(id)) { $(id).value = ''; }
        });
        if ($('statusSelect')) { $('statusSelect').value = ''; }
        submit();
      });
    }
    chips();
    watchTotal();
  });

  function chips() {
    var tags = $('filterTags');
    if (!tags) { return; }
    var f = $('fromInput') ? $('fromInput').value : '';
    var t = $('toInput') ? $('toInput').value : '';
    var p = $('payerInput') ? $('payerInput').value : '';
    var s = $('statusSelect') ? $('statusSelect').value : '';
    tags.innerHTML = '';
    if (f) { tags.appendChild(chip('From: ' + f, 'fromInput')); }
    if (t) { tags.appendChild(chip('To: ' + t, 'toInput')); }
    if (p) { tags.appendChild(chip('Received from: "' + p + '"', 'payerInput')); }
    if (s) { tags.appendChild(chip(s === 'void' ? 'Void' : 'Issued', 'statusSelect')); }
  }

  /* BUILT WITH textContent, NOT innerHTML. A payer name is data somebody
     typed, and pasting it into markup makes an apostrophe or a < into a
     rendering bug at best. */
  function chip(label, controlId) {
    var span = document.createElement('span');
    span.className = 'filter-tag';
    span.appendChild(document.createTextNode(label + ' '));
    var x = document.createElement('button');
    x.className = 'remove-tag';
    x.type = 'button';
    x.setAttribute('aria-label', 'Remove this filter');
    x.textContent = '\\u00d7';
    x.addEventListener('click', function () {
      var c = document.getElementById(controlId);
      if (c) { c.value = ''; }
      submit();
    });
    span.appendChild(x);
    return span;
  }

  /* ===== TOTAL ISSUED FOLLOWS THE FILTER =====
     Demetri asked for exactly this. The server sums the rows it sent, so
     the page is right on load and right with this script blocked. When
     the live Received From box hides a row, that sum stops describing
     what is on screen - so it is recomputed HERE, from the same numbers.

     data-amount, NEVER THE CELL. The visible cell carries a currency sign
     and a thousands separator; data-amount is the string the view wrote
     with %.2f. Parsing display text back into a number is how a total
     starts disagreeing with itself.

     A MutationObserver ON THE ROWS, not a handler on the box, because
     base's live-search sets row.style.display and we must run AFTER it
     whichever order the two scripts were wired in.

     GROUPED BY CURRENCY, because CashReceipt.currency is a real column.
     One currency reads as one line, exactly as before. */
  function watchTotal() {
    var table = document.querySelector('.receipts-table');
    var cell = $('receiptTotal');
    if (!table || !table.tBodies[0] || !cell) { return; }
    var body = table.tBodies[0];

    function money(n) {
      var s = n.toFixed(2).split('.');
      return s[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',') + '.' + s[1];
    }

    function recount() {
      var sums = {}, order = [];
      Array.prototype.forEach.call(
        body.querySelectorAll('tr[data-amount]'), function (row) {
          if (row.style.display === 'none') { return; }
          if (row.getAttribute('data-void') === '1') { return; }
          var code = row.getAttribute('data-currency') || 'EUR';
          if (sums[code] === undefined) { sums[code] = 0; order.push(code); }
          sums[code] += parseFloat(row.getAttribute('data-amount')) || 0;
        });
      cell.innerHTML = '';
      if (!order.length) { order = ['EUR']; sums.EUR = 0; }
      order.forEach(function (code) {
        var d = document.createElement('div');
        d.className = 'receipt-total-line';
        d.textContent = (code === 'EUR' ? '\\u20ac' : code) + ' '
          + money(sums[code]);
        cell.appendChild(d);
      });
    }

    try {
      new MutationObserver(recount).observe(
        body, {attributes: true, attributeFilter: ['style'], subtree: true});
    } catch (e) { /* no observer: the server's total stands, which is right */ }
    recount();
  }
})();
</script>

{% endblock %}"""
    rt2 = swap(rt2, REC_TAIL_OLD, REC_TAIL_NEW, "the page's style block", RP2)
    if not CHECK:
        write(RP2, rt2)
    print('  cash_receipts.html                 the total follows the filter')

# ---- THE LEDGERS F2 MOVES ----------------------------------------------
#
# Four lists in three suites are claims about the tree, and this round
# changes what two of its screens are. The rule A2 paid twice for applies:
# BEFORE MOVING A NUMBER, ASK WHICH FILE THE SUITE READS. All four below
# read the LIVE tree - they are censuses, not frozen copies - so all four
# move.
print('')
print('  THE LEDGERS')
print('  ' + '-' * 70)

LF = os.path.join(ROOT, 'test_lease_filter.py')
lt, lraw = read(LF)
if "'customer_list.html': 'get'" in lt:
    print('  test_lease_filter.py               already done')
else:
    # (a) the two screens leave the "cannot be narrowed at all" list. This
    #     is the ledger shape test_print_leaks uses for its queue: a page
    #     comes OFF the list in the round that finishes it, so the list
    #     never names something that was dealt with last week.
    lt = swap(lt,
              "BARE = ('cash_receipts.html', 'comments_report.html', "
              "'customer_list.html',\n",
              "# cash_receipts.html and customer_list.html LEFT THIS LIST on\n"
              "# 1 Oct 2026, Section F round F2 - IN-1 and RC-1 gave both of\n"
              "# them a filter. A screen comes off this list in the round\n"
              "# that narrows it, so the list never names something already\n"
              "# dealt with.\n"
              "BARE = ('comments_report.html',\n",
              'the BARE list', LF)
    # (b) and join the map of who filters how
    lt = swap(lt,
              "       'ingredient_base_units_management.html': 'get',\n"
              "       'recipe_management.html': 'get'}\n",
              "       'ingredient_base_units_management.html': 'get',\n"
              "       'recipe_management.html': 'get',\n"
              "       # ADDED 1 Oct 2026 by F2, written in the spelling F1\n"
              "       # settled a few hours earlier.\n"
              "       'cash_receipts.html': 'get',\n"
              "       'customer_list.html': 'get'}\n",
              'the HOW map', LF)
    lt = swap(lt,
              "ok(n_post == 0 and len(seen) == 11,\n",
              "ok(n_post == 0 and len(seen) == 13,\n",
              'the filter-page count', LF)
    if not CHECK:
        back_up(LF, lraw)
        write(LF, lt)
    print('  test_lease_filter.py               two screens off BARE, two '
          'onto HOW')

RC2 = os.path.join(ROOT, 'test_recipe_chips.py')
rc2t, rc2raw = read(RC2)
if 'fourteen pages wear' in rc2t:
    print('  test_recipe_chips.py               already done')
else:
    rc2t = swap(rc2t,
                "ok(len(house) == 12, 'twelve pages wear the house filter', "
                "len(house))\n",
                "# twelve until 1 Oct 2026; F2 gave Receipts and Invoice\n"
                "# Customers one each.\n"
                "ok(len(house) == 14, 'fourteen pages wear the house filter', "
                "len(house))\n",
                'the house-filter count', RC2)
    rc2t = swap(rc2t, "ok(len(rows) == 12,\n",
                "ok(len(rows) == 14,\n", 'the chip-row count', RC2)
    if not CHECK:
        back_up(RC2, rc2raw)
        write(RC2, rc2t)
    print('  test_recipe_chips.py               twelve -> fourteen')

RF = os.path.join(ROOT, 'test_recipe_filter.py')
rft, rfraw = read(RF)
if 'fourteen pages have one' in rft:
    print('  test_recipe_filter.py              already done')
else:
    rft = swap(rft,
               "ok(len(house) == 12, 'twelve pages have one, all the same', "
               "len(house))\n",
               "# twelve until 1 Oct 2026; F2 gave Receipts and Invoice\n"
               "# Customers one each. The FIFTH list of this shape the round\n"
               "# had to move - five suites each keep their own count of how\n"
               "# many pages carry the house filter, and none of them knows\n"
               "# about the others.\n"
               "ok(len(house) == 14, 'fourteen pages have one, all the same', "
               "len(house))\n",
               'the house-filter count', RF)
    if not CHECK:
        back_up(RF, rfraw)
        write(RF, rft)
    print('  test_recipe_filter.py              twelve -> fourteen')

FC = os.path.join(ROOT, 'test_filter_on_close.py')
ft2, fraw2 = read(FC)
if 'fourteen pages carry' in ft2:
    print('  test_filter_on_close.py            already done')
else:
    ft2 = swap(ft2,
               "ok(len(auto) + len(manual) == 12, 'twelve pages carry the "
               "house filter',\n",
               "# twelve until 1 Oct 2026; F2 gave Receipts and Invoice\n"
               "# Customers one each.\n"
               "ok(len(auto) + len(manual) == 14, 'fourteen pages carry the "
               "house filter',\n",
               'the house-filter count', FC)
    if not CHECK:
        back_up(FC, fraw2)
        write(FC, ft2)
    print('  test_filter_on_close.py            twelve -> fourteen')

FB = os.path.join(ROOT, 'test_filter_box.py')
ft3, fraw3 = read(FB)
if 'thirty-eight uses' in ft3:
    print('  test_filter_box.py                 already done')
else:
    ft3 = swap(ft3,
               "ok(len(paired) + len(bare) == 33,\n"
               "   'thirty-three uses of the two class names across the "
               "tree',\n",
               "# 33 and 28 until 1 Oct 2026. F2 added five: a .filter-input\n"
               "# and a .filter-select on Invoice Customers, two and one on\n"
               "# Receipts. All five are paired with .form-control, which is\n"
               "# what this suite is about, so the bare count does not move.\n"
               "ok(len(paired) + len(bare) == 38,\n"
               "   'thirty-eight uses of the two class names across the "
               "tree',\n",
               'the class-name count', FB)
    ft3 = swap(ft3,
               "ok(len(paired) == 28, '  twenty-eight pair it with "
               ".form-control, and do '\n",
               "ok(len(paired) == 33, '  thirty-three pair it with "
               ".form-control, and do '\n",
               'the paired count', FB)
    if not CHECK:
        back_up(FB, fraw3)
        write(FB, ft3)
    print('  test_filter_box.py                 33 -> 38, 28 -> 33')

# ==========================================================================
print('')
print('  REGISTRATION')
print('  ' + '-' * 70)
for rel, old, new, what in (
        ('alv_rounds.py', "    '.bak_loginemail',\n]\n",
         "    '.bak_loginemail',\n    '%s',\n]\n" % SUFFIX,
         'the end of ROUNDS'),
        ('Push-PendingChanges.ps1', "    'test_login_email.py'\n)\n",
         "    'test_login_email.py'\n"
         "    # The two screens that could not be narrowed, now narrowed.\n"
         "    # Its section 4 drives both through the real views against a\n"
         "    # database it builds itself, and section 5 opens Receipts in a\n"
         "    # browser and types into the live box to watch TOTAL ISSUED\n"
         "    # follow it. Newest, so most likely to be what breaks.\n"
         "    'test_filters_in_rc.py'\n)\n", 'the end of $suites')):
    path = os.path.join(ROOT, rel)
    tt, rr = read(path)
    if (SUFFIX if rel.endswith('.py') else SENTINEL) in tt:
        print('  %-34s already done' % rel)
        continue
    tt = swap(tt, old, new, what, path)
    if not CHECK:
        back_up(path, rr)
        write(path, tt)
    print('  %-34s registered' % rel)

print('')
print('  GATES')
print('  ' + '-' * 70)
if CHECK:
    print('  skipped - they read the finished files, and --check writes none')
    print('-' * 74)
    print('  CHECK ONLY - every anchor matched exactly once, nothing written')
    print('=' * 74)
    raise SystemExit(0)

import ast  # noqa: E402

for mod in ('physical_invoices.py', 'receipts.py'):
    ast.parse(read(os.path.join(ROOT, 'pages', 'views', mod))[0])
print('  both view modules parse')

# NEITHER PANEL POSTS, AND NEITHER CARRIES A TOKEN - F1's rule, which this
# round is the first new work written under.
CLS = re.compile(r'<div[^>]*\bclass="([^"]*)"')


def panel_of(text):
    for m in CLS.finditer(text):
        if 'alv-filter' in m.group(1).split():
            i, d = m.start(), 0
            for mm in re.finditer(r'<div\b|</div\s*>', text[i:]):
                d += 1 if mm.group(0).startswith('<div') else -1
                if d == 0:
                    return text[i:i + mm.end()]
            return text[i:]
    return None


for rel in ('customer_list.html', 'cash_receipts.html'):
    seg = panel_of(read(alv_tree.path_of(rel))[0])
    if seg is None:
        raise SystemExit('F2: %s has no .alv-filter panel' % rel)
    f = re.search(r'<form\b[^>]*>', seg)
    if not f or 'method="get"' not in f.group(0):
        raise SystemExit('F2: %s does not submit by GET' % rel)
    if 'csrf_token' in seg:
        raise SystemExit('F2: %s puts a csrf token in a GET query string'
                         % rel)
    print('  %-22s GET, no token' % rel)

# THE MARKUP STILL CLOSES. Inserting a block whose anchor did not
# consume the closer it re-emits left cash_receipts one </div> heavier
# than it opened, and three suites said so after the fact. This says so
# before the round leaves the sandbox.
for rel in ('customer_list.html', 'cash_receipts.html'):
    body = re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->|\{#.*?#\}', '',
                         read(alv_tree.path_of(rel))[0], flags=re.S),
                  flags=re.S)
    n = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
    if n:
        raise SystemExit('F2: %s has %+d unbalanced <div> - the markup does '
                         'not close' % (rel, n))
    print('  %-22s every <div> closes' % rel)

# ONE LIVE BOX PER TABLE. Two would hide and show the same rows against
# each other, and the last one to run would win.
for rel in ('customer_list.html', 'cash_receipts.html'):
    n = read(alv_tree.path_of(rel))[0].count('data-live-search=')
    if n != 1:
        raise SystemExit('F2: %s has %d live-search boxes, not 1' % (rel, n))
print('  and exactly one live-search box on each')

# NO LITERAL COLOUR ENTERED EITHER PAGE.
for rel in ('customer_list.html', 'cash_receipts.html'):
    now = read(alv_tree.path_of(rel))[0]
    was = read(alv_tree.path_of(rel) + SUFFIX)[0]
    f_now = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', now))
    f_was = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', was))
    if f_now > f_was:
        raise SystemExit('F2: %s gained %d literal colour(s)'
                         % (rel, f_now - f_was))
    print('  %-22s literal colours %d -> %d' % (rel, f_was, f_now))

print('-' * 74)
print('  Invoice Customers and Receipts can both be narrowed. TOTAL ISSUED')
print('  follows the filter, and is grouped by currency rather than adding')
print('  unlike things behind a hardcoded euro sign.')
print('=' * 74)
