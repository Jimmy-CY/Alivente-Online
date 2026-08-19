#!/usr/bin/env python3
"""
apply_tenant_payment_days.py
============================

Surface the tenant payment-behaviour report in the UI, as a screen reached
from the Tenants page button row - next to Open Invoices and Lease Renewals,
which is the same family: tenant-level financial behaviour.

Built to match lease_timeline_view exactly rather than inventing a pattern:
a view in pages/views/tenants.py under the READ permission tier
(auth.can_access_tenants), a template extending base.html with the house
report-container / report-title-main / back-button classes, and one route.

What it changes
---------------
  pages/views/tenants.py          + tenant_payment_days_view, + imports,
                                    + docstring entries
  pages/urls.py                   + one route, beside lease-timeline
  pages/templates/tenant.html     + one desktop button, + one mobile
                                    "More" menu item
  pages/templates/                + tenant_payment_days.html (new)
  pages/models.py                   comment corrected - invoice_paid_date now
                                    HAS a reader

No migration: nothing about the data model changes, only what is read.

A note on zero
--------------
Payment terms of 0 days is a real answer - "due on the invoice date" - not a
missing one. The view tests `is not None`, never truthiness, so a tenant on
0-day terms is measured rather than silently dropped into "not set".

Idempotent. Backs each file up on first run (.bak_paydays). Re-running after
a successful run is a no-op. Run from the project root:

    python apply_tenant_payment_days.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))

VIEWS = os.path.join(ROOT, 'pages', 'views', 'tenants.py')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
TENANT_HTML = os.path.join(ROOT, 'pages', 'templates', 'tenant.html')
NEW_HTML = os.path.join(ROOT, 'pages', 'templates', 'tenant_payment_days.html')
MODELS = os.path.join(ROOT, 'pages', 'models.py')

SENTINEL = 'tenant_payment_days_view'


# ---------------------------------------------------------------------------
# file I/O that preserves encoding and line endings
# ---------------------------------------------------------------------------

def sniff(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return raw.decode(enc).replace('\r\n', '\n'), enc, nl


def write_back(path, text, enc, nl, suffix):
    bak = path + suffix
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with open(path, 'w', encoding=enc, newline='') as fh:
        fh.write(text.replace('\n', nl) if nl == '\r\n' else text)


# ---------------------------------------------------------------------------
# 1. pages/views/tenants.py
# ---------------------------------------------------------------------------

IMPORT_OLD = 'from datetime import datetime\n'
IMPORT_NEW = 'from datetime import date, datetime\n'

MODEL_IMPORT_OLD = 'from ..models import PhysicalInvoiceProfile, props, tenant\n'
MODEL_IMPORT_NEW = 'from ..models import PhysicalInvoiceProfile, invoices, props, tenant\n'

DOC_FN_OLD = '- lease_timeline_view    : Per-property tenant lease timeline UI.\n'
DOC_FN_NEW = ('- lease_timeline_view    : Per-property tenant lease timeline UI.\n'
              '- tenant_payment_days_view : How many days each tenant actually\n'
              '                           takes to pay, against agreed terms.\n')

DOC_AUTH_OLD = '                                       lease_timeline_view)\n'
DOC_AUTH_NEW = ('                                       lease_timeline_view,\n'
                '                                       tenant_payment_days_view)\n')

VIEW = '''

# Days past the agreed terms before a tenant is flagged as slow.
#
# Not zero, deliberately. Terms across this portfolio are 0 - rent is due on
# the invoice date - so a knife-edge at zero would flag every tenant who pays
# on the 2nd rather than the 1st, and the colour would stop carrying any
# information. A week absorbs weekends, bank value dating and the ordinary
# rhythm of a standing order without hiding real drift: a tenant averaging 10+
# days past terms is genuinely behaving differently from one averaging 2.
PAYMENT_GRACE_DAYS = 7

# Nothing dated before this is in scope. The paid date only began being recorded
# when the feature went live, so every earlier invoice can say exactly one thing
# - unknown - and a list of unknowns made a tenant with a clean record look like
# a tenant with a problem.
#
# The one thing that is NOT thrown away is money: an unpaid invoice from before
# the cutoff is still a debt, so it is counted and totalled beneath the unpaid
# list rather than listed. Hidden because it illustrates nothing, not because it
# does not matter.
#
# Applies with ?all=1 too - a lease that ended before this date contributes
# nothing either way.
PAYMENT_DATA_STARTS = date(2026, 8, 1)


@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def tenant_payment_days_view(request):
    """How many days does each tenant actually take to pay?

    Measures `invoice_paid_date - invoice_date` per invoice and summarises it
    per tenant against the terms agreed on the lease
    (`tenant.tenant_payment_terms`).

    Three things to know about the numbers.

    First, the history is short and starts hard at PAYMENT_DATA_STARTS. Rent is
    monthly, so each tenant contributes roughly one measurement a month - about
    six before an average means much. The payment count sits under every tenant
    name so a thin average is never mistaken for a settled one.

    Second, a tenant with no measurement yet is simply absent from the table,
    counted in `summary.no_measurement_yet`. There is deliberately no section
    listing them with reasons: before the cutoff the only available reason was
    "unknown".

    Third, terms of 0 days is a real answer - due on the invoice date - so
    every test here is `is not None`, never truthiness. Reading 0 as "not set"
    would quietly drop exactly the tenants who pay on presentation.

    The paid date is stamped when the invoice is marked Paid. Here the bank is
    checked and invoices marked daily, so it is a faithful proxy for the day
    the money arrived.
    """
    show_all = request.GET.get('all') == '1'
    today = date.today()

    tenants = tenant.objects.select_related('prop').order_by('tenant_name')
    if not show_all:
        tenants = tenants.filter(tenant_current__iexact='Yes')

    rows, outstanding = [], []
    no_measurement_yet = 0
    old_unpaid_count, old_unpaid_total = 0, 0.0

    for t in tenants:
        invs = list(invoices.objects.filter(tenant=t).order_by('invoice_date'))

        measured, unpaid = [], []
        for inv in invs:
            if inv.invoice_date is None:
                continue

            in_scope = inv.invoice_date >= PAYMENT_DATA_STARTS
            is_paid = (inv.invoice_paid or '').strip().lower() == 'yes'

            if in_scope and inv.invoice_paid_date:
                measured.append({
                    'invoice_date': inv.invoice_date,
                    'paid_date': inv.invoice_paid_date,
                    'days': (inv.invoice_paid_date - inv.invoice_date).days,
                    'amount': inv.effective_amount,
                })

            if not is_paid:
                if in_scope:
                    unpaid.append({
                        'tenant': t,
                        'invoice': inv,
                        'age': (today - inv.invoice_date).days,
                    })
                else:
                    # Still a real debt, so it is counted and totalled rather
                    # than dropped - just not listed, because a row from before
                    # the cutoff has no payment behaviour to illustrate.
                    old_unpaid_count += 1
                    old_unpaid_total += float(inv.effective_amount or 0)

        outstanding.extend(unpaid)

        if not measured:
            # No section explaining why. Before the cutoff the paid date was not
            # recorded, so the only available explanation was "unknown", and a
            # list of unknowns made a clean tenant look like a problem one. The
            # tenant simply is not in the table yet; the count below says so.
            no_measurement_yet += 1
            continue

        days = [m['days'] for m in measured]
        ordered = sorted(days)
        mid = len(ordered) // 2
        median = (float(ordered[mid]) if len(ordered) % 2
                  else (ordered[mid - 1] + ordered[mid]) / 2.0)

        avg = sum(days) / float(len(days))
        terms = t.tenant_payment_terms
        vs_terms = (avg - terms) if terms is not None else None

        if vs_terms is None:
            band = 'unknown'
        elif vs_terms <= PAYMENT_GRACE_DAYS:
            band = 'ontime'
        elif vs_terms <= PAYMENT_GRACE_DAYS * 2:
            band = 'slight'
        else:
            band = 'late'

        rows.append({
            'tenant': t,
            'n': len(days),
            'provisional': len(days) < 6,
            'avg': avg,
            'median': median,
            'best': min(days),
            'worst': max(days),
            'last': days[-1],
            'terms': terms,
            'vs_terms': vs_terms,
            'band': band,
            'measured': list(reversed(measured)),
        })

    # Slowest first: that is the order worth reading.
    rows.sort(key=lambda r: r['avg'], reverse=True)
    outstanding.sort(key=lambda o: o['age'], reverse=True)

    all_days = [m['days'] for r in rows for m in r['measured']]
    summary = {
        'tenants_measured': len(rows),
        'payments_measured': len(all_days),
        'portfolio_avg': (sum(all_days) / float(len(all_days))) if all_days else None,
        'flagged': len([r for r in rows if r['band'] in ('slight', 'late')]),
        'missing_terms': len([r for r in rows if r['terms'] is None]),
        'no_measurement_yet': no_measurement_yet,
        'old_unpaid_count': old_unpaid_count,
        'old_unpaid_total': old_unpaid_total,
        'outstanding_total': sum(float(o['invoice'].effective_amount or 0)
                                 for o in outstanding),
    }

    context = {
        'rows': rows,
        'outstanding': outstanding,
        'summary': summary,
        'show_all': show_all,
        'today': today,
        'grace': PAYMENT_GRACE_DAYS,
        'data_starts': PAYMENT_DATA_STARTS,
    }
    return render(request, 'tenant_payment_days.html', context)
'''


# ---------------------------------------------------------------------------
# 2. pages/urls.py
# ---------------------------------------------------------------------------

URL_OLD = "    path('lease-timeline/', views.lease_timeline_view, name='lease_timeline'),\n"
URL_NEW = (
    "    path('lease-timeline/', views.lease_timeline_view, name='lease_timeline'),\n"
    "    path('tenant-payment-days/', views.tenant_payment_days_view,\n"
    "         name='tenant_payment_days'),\n"
)


# ---------------------------------------------------------------------------
# 3. pages/templates/tenant.html - both button rows
# ---------------------------------------------------------------------------

BTN_OLD = ('      <a href="{% url \'lease_renewal_report\' %}" '
           'class="btn btn-info action-secondary">Lease Renewals</a>\n')
BTN_NEW = (BTN_OLD +
           '      <a href="{% url \'tenant_payment_days\' %}" '
           'class="btn btn-info action-secondary">Payment Behaviour</a>\n')

MENU_OLD = ('          <a href="{% url \'lease_renewal_report\' %}" '
            'class="action-more-item" role="menuitem">\n'
            '            <i class="fas fa-sync-alt"></i> Lease Renewals\n'
            '          </a>\n')
MENU_NEW = (MENU_OLD +
            '          <a href="{% url \'tenant_payment_days\' %}" '
            'class="action-more-item" role="menuitem">\n'
            '            <i class="fas fa-stopwatch"></i> Payment Behaviour\n'
            '          </a>\n')


# ---------------------------------------------------------------------------
# 4. pages/models.py - the comment is now out of date
# ---------------------------------------------------------------------------

MODELS_OLD = ('    # Date the invoice was marked paid. Captured automatically in save() below\n'
              '    # for FUTURE use (e.g. a "traditionally pays late" signal in analytics); no\n'
              '    # current report reads it. Null while the invoice is unpaid.\n')

MODELS_NEW = ('    # Date the invoice was marked paid, stamped automatically in save() below.\n'
              '    # Read by the tenant payment-behaviour report (tenant_payment_days_view)\n'
              '    # and by the tenant_payment_days management command. Null while unpaid.\n'
              '    # History starts 3 Aug 2026, when this field was added: anything marked\n'
              '    # paid before then has no date and cannot be reconstructed.\n')


def patch_views():
    src, enc, nl = sniff(VIEWS)
    if SENTINEL in src:
        return 'skip', src, enc, nl
    for name, anchor in (('datetime import', IMPORT_OLD),
                         ('model import', MODEL_IMPORT_OLD),
                         ('docstring functions', DOC_FN_OLD),
                         ('docstring auth tiers', DOC_AUTH_OLD)):
        n = src.count(anchor)
        if n != 1:
            return ('! tenants.py: %s anchor matched %d times, expected 1' % (name, n),
                    None, None, None)
    src = src.replace(IMPORT_OLD, IMPORT_NEW, 1)
    src = src.replace(MODEL_IMPORT_OLD, MODEL_IMPORT_NEW, 1)
    src = src.replace(DOC_FN_OLD, DOC_FN_NEW, 1)
    src = src.replace(DOC_AUTH_OLD, DOC_AUTH_NEW, 1)
    src = src.rstrip('\n') + '\n' + VIEW.rstrip('\n') + '\n'
    return 'ok', src, enc, nl


def patch_urls():
    src, enc, nl = sniff(URLS)
    if 'tenant_payment_days' in src:
        return 'skip', src, enc, nl
    n = src.count(URL_OLD)
    if n != 1:
        return '! urls.py: lease-timeline anchor matched %d times, expected 1' % n, None, None, None
    return 'ok', src.replace(URL_OLD, URL_NEW, 1), enc, nl


def patch_tenant_html():
    src, enc, nl = sniff(TENANT_HTML)
    if 'tenant_payment_days' in src:
        return 'skip', src, enc, nl
    for name, anchor in (('desktop button', BTN_OLD), ('mobile menu item', MENU_OLD)):
        n = src.count(anchor)
        if n != 1:
            return ('! tenant.html: %s anchor matched %d times, expected 1' % (name, n),
                    None, None, None)
    src = src.replace(BTN_OLD, BTN_NEW, 1)
    src = src.replace(MENU_OLD, MENU_NEW, 1)
    return 'ok', src, enc, nl


def patch_models():
    src, enc, nl = sniff(MODELS)
    if 'tenant_payment_days_view' in src:
        return 'skip', src, enc, nl
    n = src.count(MODELS_OLD)
    if n != 1:
        # Cosmetic only - never block the real work over a stale comment.
        return 'skip-soft', src, enc, nl
    return 'ok', src.replace(MODELS_OLD, MODELS_NEW, 1), enc, nl


def main():
    for path in (VIEWS, URLS, TENANT_HTML, MODELS):
        if not os.path.exists(path):
            print('! %s not found - run from the project root' % path)
            return 1

    results = {}
    for name, fn in (('views', patch_views), ('urls', patch_urls),
                     ('tenant_html', patch_tenant_html), ('models', patch_models)):
        status, text, enc, nl = fn()
        if status.startswith('!'):
            print(status)
            print('  Aborting - nothing written.')
            return 1
        results[name] = (status, text, enc, nl)

    template_exists = os.path.exists(NEW_HTML)
    if all(s[0].startswith('skip') for s in results.values()) and template_exists:
        print('= already applied - nothing to do')
        return 0

    if CHECK:
        print('= check only: every anchor matched, nothing written')
        for name, (status, _, _, _) in results.items():
            print('    %-12s %s' % (name, status))
        print('    %-12s %s' % ('template', 'exists' if template_exists else 'would create'))
        return 0

    targets = {'views': VIEWS, 'urls': URLS, 'tenant_html': TENANT_HTML, 'models': MODELS}
    for name, (status, text, enc, nl) in results.items():
        if status == 'ok':
            write_back(targets[name], text, enc, nl, '.bak_paydays')
            print('+ %s patched' % os.path.relpath(targets[name], ROOT))
        elif status == 'skip-soft':
            print('~ %s comment already differs - left alone (cosmetic only)'
                  % os.path.relpath(targets[name], ROOT))
        else:
            print('= %s already patched' % os.path.relpath(targets[name], ROOT))

    with open(NEW_HTML, 'w', encoding='utf-8', newline='\r\n') as fh:
        fh.write(TEMPLATE)
    print('+ pages/templates/tenant_payment_days.html written')

    print('')
    print('Backups: .bak_paydays alongside each changed file.')
    print('Verify:  python -m py_compile pages/views/tenants.py pages/urls.py')
    print('         python manage.py check')
    print('Then:    Tenants page -> Payment Behaviour')
    return 0


# ---------------------------------------------------------------------------
# 5. the new template
# ---------------------------------------------------------------------------

TEMPLATE = '''{% extends 'base.html' %}
{% load static %}

{% block title %}Tenant Payment Behaviour{% endblock %}

{% block content %}
<div class="report-container">
  <div class="report-content">

    <div class="header-container">
      <div class="report-title-container">
        <h2 class="report-title-main">Tenant Payment Behaviour</h2>
        <h3 class="report-title-sub">Days from invoice to payment &middot; {{ today }}</h3>
      </div>
      <a href="{% url 'tenant' %}" class="btn btn-info back-button" role="button">
        <i class="fas fa-arrow-left"></i> Back
      </a>
    </div>

    {% if summary.payments_measured %}
    <div class="pd-summary">
      <div class="pd-stat">
        <div class="pd-stat-value">{{ summary.payments_measured }}</div>
        <div class="pd-stat-label">payments measured</div>
      </div>
      <div class="pd-stat">
        <div class="pd-stat-value">{{ summary.tenants_measured }}</div>
        <div class="pd-stat-label">tenants with data</div>
      </div>
      <div class="pd-stat">
        <div class="pd-stat-value">{{ summary.portfolio_avg|floatformat:1 }}</div>
        <div class="pd-stat-label">average days to pay</div>
      </div>
      <div class="pd-stat {% if summary.flagged %}pd-stat-warn{% endif %}">
        <div class="pd-stat-value">{{ summary.flagged }}</div>
        <div class="pd-stat-label">flagged slow</div>
      </div>
    </div>
    {% endif %}

    <div class="pd-toolbar">
      {% if show_all %}
        <a href="{% url 'tenant_payment_days' %}" class="btn btn-outline-secondary btn-sm">
          <i class="fas fa-user-check"></i> Current tenants only
        </a>
      {% else %}
        <a href="{% url 'tenant_payment_days' %}?all=1" class="btn btn-outline-secondary btn-sm">
          <i class="fas fa-users"></i> Include past tenants
        </a>
      {% endif %}
      {% if summary.no_measurement_yet %}
        <!-- The section that used to list these, with a reason each, is gone.
             The count remains so they are not silently dropped. -->
        <span class="pd-note">
          {{ summary.no_measurement_yet }} tenant{{ summary.no_measurement_yet|pluralize }}
          not shown &mdash; no payment recorded yet since {{ data_starts }}.
        </span>
      {% endif %}
      {% if summary.missing_terms %}
        <span class="pd-terms-warning">
          <i class="fas fa-exclamation-triangle"></i>
          {{ summary.missing_terms }} tenant{{ summary.missing_terms|pluralize }} without payment
          terms on the lease &mdash; their VS TERMS cannot be calculated.
        </span>
      {% endif %}
    </div>

    {% if rows %}
    <div class="pd-table-wrap">
      <table class="pd-table">
        <thead>
          <tr>
            <th class="pd-col-name">Tenant</th>
            <th class="pd-col-prop">Property</th>
            <th class="pd-num">Terms</th>
            <th class="pd-num">Avg</th>
            <th class="pd-num">Median</th>
            <th class="pd-num">Best</th>
            <th class="pd-num">Worst</th>
            <th class="pd-num">Last</th>
            <th class="pd-num">vs Terms</th>
            <th class="pd-col-toggle"></th>
          </tr>
        </thead>
        <tbody>
          {% for r in rows %}
          <tr class="pd-row pd-band-{{ r.band }}">
            <td class="pd-col-name" data-label="Tenant">
              <span class="pd-name">{{ r.tenant.tenant_name }}</span>
              <!-- Replaces both the old n column and the "provisional" chip.
                   How much an average rests on is the single most important
                   thing about it here, and "1 payment" says that outright
                   where a label like "provisional" made you go and look. -->
              <span class="pd-count">{{ r.n }} payment{{ r.n|pluralize }}</span>
            </td>
            <td class="pd-col-prop" data-label="Property">{{ r.tenant.prop.prop_name }}</td>
            <td class="pd-num" data-label="Terms">
              {% if r.terms is None %}<span class="pd-muted">not set</span>
              {% else %}{{ r.terms }}d{% endif %}
            </td>
            <td class="pd-num pd-strong" data-label="Avg">{{ r.avg|floatformat:1 }}</td>
            <td class="pd-num" data-label="Median">{{ r.median|floatformat:1 }}</td>
            <td class="pd-num" data-label="Best">{{ r.best }}</td>
            <td class="pd-num" data-label="Worst">{{ r.worst }}</td>
            <td class="pd-num" data-label="Last">{{ r.last }}</td>
            <td class="pd-num" data-label="vs Terms">
              {% if r.vs_terms is None %}<span class="pd-muted">n/a</span>
              {% else %}
                <span class="pd-badge pd-badge-{{ r.band }}">
                  {% if r.vs_terms > 0 %}+{% endif %}{{ r.vs_terms|floatformat:1 }}
                </span>
              {% endif %}
            </td>
            <td class="pd-col-toggle">
              <button type="button" class="pd-toggle" data-target="pd-detail-{{ r.tenant.tenant_id }}"
                      aria-expanded="false" aria-label="Show every measured payment">
                <i class="fas fa-chevron-down"></i>
              </button>
            </td>
          </tr>
          <tr class="pd-detail" id="pd-detail-{{ r.tenant.tenant_id }}" hidden>
            <td colspan="10">
              <div class="pd-detail-inner">
                <div class="pd-detail-title">Every measured payment &mdash; most recent first</div>
                <table class="pd-detail-table">
                  <tr>
                    <th>Invoiced</th><th>Paid</th><th class="pd-num">Days</th><th class="pd-num">Amount</th>
                  </tr>
                  {% for m in r.measured %}
                  <tr>
                    <td>{{ m.invoice_date }}</td>
                    <td>{{ m.paid_date }}</td>
                    <td class="pd-num">{{ m.days }}</td>
                    <td class="pd-num">&euro;{{ m.amount|floatformat:2 }}</td>
                  </tr>
                  {% endfor %}
                </table>
              </div>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    <p class="pd-legend">
      <strong>vs Terms</strong> is the average minus the days agreed on the lease
      &mdash; positive means slower than agreed. Rent here is due on the invoice date,
      so a tenant is only <em>flagged</em> once that gap exceeds
      <strong>{{ grace }} days</strong>: green within grace, amber to
      {{ grace|add:grace }} days, red beyond. Sorted slowest first.
      Paid dates have only been recorded since {{ data_starts }} and rent is monthly, so
      each tenant gains about one payment a month &mdash; read the ranking rather than the
      absolute numbers until the counts under each name reach about six.
    </p>
    {% else %}
    <div class="pd-empty">
      <i class="fas fa-hourglass-half"></i>
      <p><strong>Nothing measurable yet.</strong></p>
      <p>A payment can only be measured when its invoice has both a date and a paid date,
         and paid dates only began being recorded on {{ data_starts }}.</p>
    </div>
    {% endif %}

    {% if outstanding %}
    <div class="pd-section">
      <h4 class="pd-section-title">
        Currently unpaid ({{ outstanding|length }})
        <span class="pd-section-note">&mdash; oldest first, &euro;{{ summary.outstanding_total|floatformat:2 }} in total</span>
      </h4>
      <div class="pd-table-wrap">
        <table class="pd-table pd-table-compact">
          <thead>
            <tr>
              <th>Tenant</th><th>Property</th><th>Invoiced</th>
              <th class="pd-num">Age</th><th class="pd-num">Amount</th>
            </tr>
          </thead>
          <tbody>
            {% for o in outstanding %}
            <tr class="{% if o.age > 30 %}pd-band-late{% elif o.age > grace %}pd-band-slight{% endif %}">
              <td data-label="Tenant">{{ o.tenant.tenant_name }}</td>
              <td data-label="Property">{{ o.tenant.prop.prop_name }}</td>
              <td data-label="Invoiced">{{ o.invoice.invoice_date }}</td>
              <td class="pd-num" data-label="Age">{{ o.age }}d</td>
              <td class="pd-num" data-label="Amount">&euro;{{ o.invoice.effective_amount|floatformat:2 }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
      {% if summary.old_unpaid_count %}
      <!-- Counted, not listed. An old unpaid invoice illustrates no payment
           behaviour - there is no paid date to measure - but it is still money
           owed, so the figure stays visible. -->
      <p class="pd-note pd-note-block">
        Plus {{ summary.old_unpaid_count }} unpaid invoice{{ summary.old_unpaid_count|pluralize }}
        dated before {{ data_starts }}, totalling
        <strong>&euro;{{ summary.old_unpaid_total|floatformat:2 }}</strong> &mdash; not listed
        here because they predate the payment tracking, but still outstanding.
      </p>
      {% endif %}
    </div>
    {% endif %}

  </div>
</div>

<style>
/* ==================== DESKTOP ==================== */

.report-container {
    display: flex;
    justify-content: center;
    width: 100%;
    padding: 20px;
    min-height: 80vh;
}

.report-content {
    width: 95%;
    max-width: 1400px;
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.header-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    gap: 16px;
}

.report-title-container {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    flex: 1;
    min-width: 0;
}

.report-title-main {
    font-size: 1.8rem;
    color: #2c3e50;
    margin: 0;
    font-weight: bold;
    text-transform: uppercase;
}

.report-title-sub {
    font-size: 1.1rem;
    color: #6c757d;
    margin: 5px 0 0 0;
    font-weight: normal;
}

.back-button { flex-shrink: 0; }

/* ---- summary strip ---- */
.pd-summary {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 20px;
}
.pd-stat {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 14px 16px;
    text-align: center;
}
.pd-stat-value { font-size: 1.7rem; font-weight: 700; color: #2c3e50; line-height: 1.1; }
.pd-stat-label {
    font-size: 0.78rem;
    color: #6c757d;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin-top: 4px;
}
.pd-stat-warn { background: #fff8e6; border-color: #ffe0a3; }
.pd-stat-warn .pd-stat-value { color: #b8860b; }

/* ---- toolbar ---- */
.pd-toolbar {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 14px;
}
.pd-terms-warning {
    font-size: 0.85rem;
    color: #8a6d3b;
    background: #fcf8e3;
    border: 1px solid #faebcc;
    border-radius: 5px;
    padding: 5px 10px;
}

/* ---- main table ---- */
.pd-table-wrap { overflow-x: auto; }
.pd-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}
.pd-table thead th {
    background: #2c3e50;
    color: white;
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    white-space: nowrap;
}
.pd-table tbody td {
    padding: 10px 12px;
    border-bottom: 1px solid #eef0f2;
    vertical-align: middle;
}
.pd-table tbody tr.pd-row:hover { background: #f6fafc; }
.pd-num { text-align: right; white-space: nowrap; }
.pd-table thead th.pd-num { text-align: right; }
.pd-strong { font-weight: 700; color: #2c3e50; }
.pd-name { font-weight: 600; color: #2c3e50; }
.pd-muted { color: #95a5a6; }
.pd-mono { font-family: 'Courier New', monospace; }

/* Sits under the name, quiet enough to ignore when it says "14 payments" and
   noticeable enough to catch when it says "1 payment". */
.pd-count {
    display: block;
    font-size: 0.75rem;
    color: #95a5a6;
    margin-top: 2px;
}

/* Colour carries the same message as the sign, for anyone scanning fast. */
.pd-row.pd-band-ontime { border-left: 4px solid #27ae60; }
.pd-row.pd-band-slight { border-left: 4px solid #f39c12; }
.pd-row.pd-band-late   { border-left: 4px solid #e74c3c; }
.pd-row.pd-band-unknown{ border-left: 4px solid #bdc3c7; }

.pd-badge {
    display: inline-block;
    min-width: 52px;
    text-align: center;
    padding: 3px 8px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.82rem;
}
.pd-badge-ontime { background: #e8f8f0; color: #1e8449; }
.pd-badge-slight { background: #fdf3e3; color: #b9770e; }
.pd-badge-late   { background: #fdecea; color: #c0392b; }
.pd-badge-unknown{ background: #f2f3f4; color: #7f8c8d; }

tr.pd-band-slight td { background: #fffdf7; }
tr.pd-band-late td   { background: #fef8f7; }

/* ---- expandable detail ---- */
.pd-col-toggle { width: 40px; text-align: center; }
.pd-toggle {
    background: transparent;
    border: 1px solid #dfe4e8;
    border-radius: 5px;
    color: #7f8c8d;
    width: 28px;
    height: 28px;
    cursor: pointer;
    transition: all 0.2s ease;
}
.pd-toggle:hover { background: #ecf0f1; color: #2c3e50; }
.pd-toggle[aria-expanded="true"] i { transform: rotate(180deg); }
.pd-toggle i { transition: transform 0.2s ease; font-size: 12px; }

.pd-detail td { background: #fafbfc; padding: 0 !important; }
.pd-detail-inner { padding: 14px 18px 18px 18px; }
.pd-detail-title {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #7f8c8d;
    margin-bottom: 8px;
}
.pd-detail-table { width: 100%; max-width: 620px; border-collapse: collapse; font-size: 0.86rem; }
.pd-detail-table th {
    text-align: left;
    color: #7f8c8d;
    font-weight: 600;
    border-bottom: 1px solid #e1e5e9;
    padding: 5px 10px;
}
.pd-detail-table td { padding: 5px 10px; border-bottom: 1px solid #eef0f2; }

.pd-legend { font-size: 0.85rem; color: #7f8c8d; margin-top: 12px; }

/* ---- sections ---- */
.pd-section { margin-top: 34px; }
.pd-section-title {
    font-size: 1.05rem;
    color: #2c3e50;
    font-weight: 700;
    border-bottom: 2px solid #ecf0f1;
    padding-bottom: 8px;
    margin-bottom: 14px;
}
.pd-section-note { font-weight: 400; color: #7f8c8d; font-size: 0.9rem; }

/* Counts for things deliberately not listed. Quiet, but never absent - a
   suppressed row that leaves no trace reads as "there was nothing". */
.pd-note {
    font-size: 0.85rem;
    color: #7f8c8d;
}
.pd-note-block {
    margin: 12px 0 0 0;
    padding: 10px 14px;
    background: #f8f9fa;
    border-left: 3px solid #dfe4e8;
    border-radius: 0 5px 5px 0;
}
.pd-note-block strong { color: #2c3e50; }

.pd-empty {
    text-align: center;
    padding: 50px 20px;
    color: #7f8c8d;
}
.pd-empty i { font-size: 2.4rem; color: #bdc3c7; margin-bottom: 12px; }
.pd-empty p { margin: 4px 0; }

.pd-table-compact tbody td { padding: 8px 12px; }

/* ==================== MOBILE ==================== */
@media (max-width: 768px) {
    .report-container { padding: 10px; }
    .report-content { width: 100%; padding: 16px; }
    .report-title-main { font-size: 1.25rem; }
    .report-title-sub { font-size: 0.9rem; }
    .pd-summary { grid-template-columns: repeat(2, 1fr); }

    /* Cards, not a squeezed table: nine numeric columns are unreadable at
       phone width, and horizontal scrolling hides exactly the column that
       matters. */
    .pd-table thead { display: none; }
    .pd-table, .pd-table tbody, .pd-table tr, .pd-table td { display: block; width: 100%; }
    .pd-table tbody tr.pd-row {
        border: 1px solid #e9ecef;
        border-radius: 8px;
        margin-bottom: 12px;
        padding: 6px 4px;
        background: white;
    }
    .pd-table tbody td {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #f4f6f7;
        padding: 7px 12px;
        text-align: right;
    }
    .pd-table tbody td:last-child { border-bottom: none; }
    .pd-table tbody td::before {
        content: attr(data-label);
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        color: #95a5a6;
        font-weight: 600;
        text-align: left;
        margin-right: 12px;
    }
    .pd-table tbody td.pd-col-name {
        background: #f8f9fa;
        border-radius: 6px 6px 0 0;
        font-size: 1rem;
        flex-wrap: wrap;
    }
    /* The name cell is a flex row on mobile, so the count needs its own line
       explicitly - display:block alone does nothing to a flex item. */
    .pd-col-name .pd-count { flex-basis: 100%; text-align: right; }
    .pd-col-toggle { width: 100%; }
    .pd-col-toggle::before { content: "Detail"; }
    .pd-detail td { display: block; }
    .pd-detail-table { font-size: 0.8rem; }
    .pd-detail-table th, .pd-detail-table td { padding: 4px 6px; }
}
</style>

<script>
(function () {
  // Progressive enhancement: the detail rows are plain hidden table rows, so
  // the page is still complete and readable if this never runs.
  document.querySelectorAll('.pd-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var row = document.getElementById(btn.getAttribute('data-target'));
      if (!row) { return; }
      var open = row.hasAttribute('hidden');
      if (open) { row.removeAttribute('hidden'); } else { row.setAttribute('hidden', ''); }
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  });
})();
</script>
{% endblock %}
'''


if __name__ == '__main__':
    sys.exit(main())
