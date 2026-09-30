# -*- coding: utf-8 -*-
"""SECTION T, ROUND T4 - MANAGE LEASE AGREEMENTS GETS A FILTER

Demetri: "When are we doing the filters for the Manage Lease Agreements,
etc.?"

WHAT THE SCREEN DOES TODAY. The view is one line:

    tenants = tenant.objects.all().order_by(...)

Every tenant who has ever been on a lease, past ones included, in one
table, with no search, no filter and no way to see only the current ones.
The page exists to UPLOAD / VIEW / DELETE a lease agreement, so the list
you actually want - the tenants with no document attached - is the one
thing it cannot show you.

WHAT IT GETS, all four agreed on 30 Sep:

    Search       tenant name OR property name, one box
    Property     the properties tenants are actually in, from the data
    Agreement    attached / missing
    Lease        expired / active, from the end date against today

AND IT OPENS ON CURRENT TENANTS, with `Include past tenants` beside Back
- the pattern Tenants and Payment Behaviour already use, so a third
screen behaves like the two next to it. That is a change to what the page
shows on arrival and it is measured both ways.

GET, NOT POST, AND THE HOUSE IS ALREADY SPLIT. Of the eleven pages that
filter, five POST the form and six use GET - in three spellings between
them (`GET`, `get`, and the default). There is no standard here to
mirror, so this round picks the one that is right for THIS page and
reports the split:

  - the page's POST is already taken. `action=upload` and `action=delete`
    post to this same view, and a filter POST would have to be told apart
    from a file upload.
  - the toggle Demetri asked for is a LINK. A GET filter means the link
    can carry the filter, so switching to past tenants keeps your search.
  - and the upload and delete forms carry no action, so they post to the
    current URL - query string included. The three redirects at the end
    become redirect(request.get_full_path()), so uploading a document
    leaves you on the same filtered list instead of back at all tenants.
    On a page whose job is uploading, that is the difference between a
    filter you use and one you use once.

THE PROPERTY LIST IS READ FROM THE DATA, and from the UNFILTERED rows -
a list that narrowed to the choice just made would be a one-way door.
It also follows the current/past toggle, so a property whose only tenant
has left is not offered while you are looking at current tenants.

Backups: .bak_leasefilter. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_leasefilter'
CRLF = {}

PAGE = 'tenant_lease_agreement.html'
VIEW = os.path.join('pages', 'views', 'tenants.py')


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
            raise SystemExit('T4: %s is not a byte copy' % bak)


def patch(path, text, pairs, what, counts=None):
    for i, (was, now) in enumerate(pairs):
        a = eol(path, was)
        want = (counts or {}).get(i, 1)
        if text.count(a) != want:
            raise SystemExit('T4: %s - anchor %d of %d is there %d time(s), '
                             'not %d:\n%s' % (what, i + 1, len(pairs),
                                              text.count(a), want, was[:90]))
        text = text.replace(a, eol(path, now), want)
    return text


# ==========================================================================
# THE VIEW
# ==========================================================================
V0_WAS = """from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render"""
V0_NOW = """from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render"""

V1_WAS = """    tenants = tenant.objects.all().order_by('prop__prop_country', 'prop__prop_name', 'tenant_name')"""
V1_NOW = """    # THE FILTER - 30 Sep 2026. Four things, all of them agreed, and all
    # of them read from GET. The house is split five POST to six GET, so
    # there is no standard to mirror; GET is right here because this
    # view's POST already belongs to action=upload and action=delete,
    # and because the current/past toggle is a link that has to be able
    # to carry the filter with it. See test_lease_filter.py.
    search = request.GET.get('search', '').strip()
    selected_property = request.GET.get('propname', '')
    selected_agreement = request.GET.get('agreement', '')
    selected_lease = request.GET.get('lease', '')
    show_all = request.GET.get('all') == '1'

    tenants = tenant.objects.all()

    # CURRENT TENANTS UNLESS ASKED. The screen used to open on every
    # tenant who has ever held a lease; Tenants and Payment Behaviour
    # both open on the current ones with the same toggle, and this is
    # now the third.
    if not show_all:
        tenants = tenants.filter(tenant_current='Yes')

    # ONE BOX, TWO COLUMNS. Tenant or property, because those are the
    # two things the table shows and either one is how you would look.
    if search:
        tenants = tenants.filter(Q(tenant_name__icontains=search)
                                 | Q(prop__prop_name__icontains=search))

    if selected_property:
        tenants = tenants.filter(prop__prop_name=selected_property)

    # ATTACHED OR MISSING. A FileField with nothing in it is the empty
    # string on some rows and NULL on others - the model allows both -
    # so both have to be named or `missing` would quietly under-report.
    if selected_agreement == 'attached':
        tenants = tenants.exclude(tenant_lease_agreement='').exclude(
            tenant_lease_agreement__isnull=True)
    elif selected_agreement == 'missing':
        tenants = tenants.filter(Q(tenant_lease_agreement='')
                                 | Q(tenant_lease_agreement__isnull=True))

    # EXPIRED OR ACTIVE, against today. A row with no end date is in
    # neither: it cannot be said to have expired, and calling it active
    # would be an invention.
    today = date.today()
    if selected_lease == 'expired':
        tenants = tenants.filter(tenant_lease_end_date__lt=today)
    elif selected_lease == 'active':
        tenants = tenants.filter(tenant_lease_end_date__gte=today)

    tenants = tenants.order_by('prop__prop_country', 'prop__prop_name', 'tenant_name')

    # THE PROPERTIES IN THE FILTER are the ones tenants are actually in,
    # read from the data and NOT from the filtered rows - a list that
    # narrowed to the choice just made would be a one-way door. Same
    # line as properties_page. It does follow the current/past toggle,
    # so a property whose only tenant has left is not offered while you
    # are looking at the current ones.
    if show_all:
        offer = props.objects.filter(tenant__isnull=False)
    else:
        offer = props.objects.filter(tenant__tenant_current='Yes')

    # WHAT THE TOGGLE CARRIES. The filter minus `all`, so the link to
    # past tenants keeps the search and the selects you already set.
    keep = request.GET.copy()
    keep.pop('all', None)
    keep = keep.urlencode()"""

V2_WAS = """    context = {
        'tenants': tenants,
    }
    return render(request, 'tenant_lease_agreement.html', context)"""
V2_NOW = """    context = {
        'tenants': tenants,
        'props': offer.distinct().order_by('prop_country', 'prop_name'),
        'search_query': search,
        'selected_property': selected_property,
        'selected_agreement': selected_agreement,
        'selected_lease': selected_lease,
        'show_all': show_all,
        'filter_qs': (keep + '&') if keep else '',
    }
    return render(request, 'tenant_lease_agreement.html', context)"""

# THE THREE REDIRECTS. The upload and delete forms carry no action, so
# they post to the current URL and its query string survives the POST -
# it is the redirect afterwards that used to throw the filter away.
# THE INDENTS MATTER. There are three of these at two depths - 12 and
# 24 - and the shallower literal is a SUBSTRING of the deeper lines, so
# anchoring on the text alone counted three of a thing there is one of.
# Each anchor therefore starts at its own newline.
V3_WAS = """
            return redirect('tenant_lease_agreement')"""
V3_NOW = """
            # BACK TO THE SAME FILTERED LIST, not to all tenants.
            # get_full_path() is this page plus its query string, so an
            # upload leaves you where you were. 30 Sep 2026.
            return redirect(request.get_full_path())"""
V4_WAS = """
                        return redirect('tenant_lease_agreement')"""
V4_NOW = """
                        return redirect(request.get_full_path())"""

VIEW_PAIRS = [(V0_WAS, V0_NOW), (V1_WAS, V1_NOW), (V2_WAS, V2_NOW),
              (V3_WAS, V3_NOW), (V4_WAS, V4_NOW)]
VIEW_COUNTS = {3: 1, 4: 2}

# ==========================================================================
# THE PAGE
# ==========================================================================
P1_WAS = """<!-- Action Buttons -->
<div class="page-action-buttons page-action-buttons-single">
    <a href="{% url 'admin_apms' %}" class="btn action-back" role="button">
        <i class="fas fa-arrow-left"></i> Back
    </a>
</div>"""
P1_NOW = """<!-- Action Buttons. The -single modifier is gone with the second and
     third control: it exists to push a lone Back to the right, and base
     already puts Back on the right when there is something beside it. -->
<div class="page-action-buttons">
    {% if show_all %}
      <a href="{% url 'tenant_lease_agreement' %}?{{ filter_qs }}" class="btn action-secondary" role="button">
        <i class="fas fa-user-check"></i> Current tenants only
      </a>
    {% else %}
      <a href="{% url 'tenant_lease_agreement' %}?{{ filter_qs }}all=1" class="btn action-secondary" role="button">
        <i class="fas fa-users"></i> Include past tenants
      </a>
    {% endif %}

    <button type="button" class="btn action-filter" id="filterBtn"
            aria-pressed="false" aria-controls="filterPanel"
            aria-label="Show filters">
      <i class="fas fa-filter"></i><span class="action-filter-label"> Filter</span><span class="action-filter-count" data-count="0"></span>
    </button>

    <a href="{% url 'admin_apms' %}" class="btn action-back" role="button">
        <i class="fas fa-arrow-left"></i> Back
    </a>
</div>

<div class="alv-filter-active" id="activeFilters">
  <span class="alv-filter-active-label">Active filters:</span>
  <div class="filter-tags" id="filterTags"></div>
</div>

<!-- Collapsible Filter Panel. Frame, field and chips are all base's -
     H1 moved the frame there and D4 the field, so this page writes no
     rule of its own. -->
<div class="alv-filter filter-panel" id="filterPanel">
  <div class="filter-header">
    <h5 class="filter-title">
      <i class="fas fa-filter"></i> <span class="filter-title-text">Lease Agreement Filters</span><span class="filter-title-text-mobile">Filters</span>
    </h5>
    <button type="button" id="clearAllBtn" class="btn btn-outline-secondary btn-sm">
      <i class="fas fa-times-circle"></i> <span class="clear-all-text">Clear All</span><span class="clear-all-text-mobile">Clear</span>
    </button>
  </div>

  <div class="filter-content" id="filterContent">
    <form action="{% url 'tenant_lease_agreement' %}" method="get" id="filterForm">
      {% if show_all %}<input type="hidden" name="all" value="1">{% endif %}
      <div class="filter-grid">
        <div class="filter-group">
          <label class="filter-label" for="searchInput">
            <i class="fas fa-search"></i> <strong>Search</strong>
          </label>
          <div class="search-input-group">
            <input type="text"
                   name="search"
                   id="searchInput"
                   class="form-control search-input"
                   placeholder="Tenant or property name..."
                   value="{{ search_query|default:'' }}">
            <button type="button" class="search-btn" id="searchBtn" aria-label="Search">
              <i class="fas fa-search"></i>
            </button>
          </div>
        </div>

        <div class="filter-group">
          <label class="filter-label" for="propertySelect">
            <i class="fas fa-building"></i> <strong>Property</strong>
          </label>
          <select name="propname" class="form-control filter-select" id="propertySelect">
            <option value="">All Properties</option>
            {% for p in props %}
              <option value="{{ p.prop_name }}" {% if selected_property == p.prop_name %}selected{% endif %}>{{ p.prop_name }}</option>
            {% endfor %}
          </select>
        </div>

        <div class="filter-group">
          <label class="filter-label" for="agreementSelect">
            <i class="fas fa-file-contract"></i> <strong>Agreement</strong>
          </label>
          <select name="agreement" class="form-control filter-select" id="agreementSelect">
            <option value="">All Agreements</option>
            <option value="attached" {% if selected_agreement == 'attached' %}selected{% endif %}>Attached</option>
            <option value="missing" {% if selected_agreement == 'missing' %}selected{% endif %}>Missing</option>
          </select>
        </div>

        <div class="filter-group">
          <label class="filter-label" for="leaseSelect">
            <i class="fas fa-calendar-times"></i> <strong>Lease</strong>
          </label>
          <select name="lease" class="form-control filter-select" id="leaseSelect">
            <option value="">All Leases</option>
            <option value="active" {% if selected_lease == 'active' %}selected{% endif %}>Active</option>
            <option value="expired" {% if selected_lease == 'expired' %}selected{% endif %}>Expired</option>
          </select>
        </div>
      </div>
    </form>
  </div>
</div>

<style>
/* THE COLUMN COUNT IS THE PAGE'S, and only the column count. H1 moved
   the filter FRAME into base but not grid-template-columns, because the
   number of fields differs: Suppliers has two, Tenants three, this has
   four. The phone override below is the ninth identical copy of one
   rule and belongs in base - reported in test_lease_filter.py, not
   fixed here. 30 Sep 2026. */
.filter-grid { grid-template-columns: 2fr 1fr 1fr 1fr; }
@media screen and (max-width: 768px) {
    .filter-grid { grid-template-columns: 1fr; gap: 12px; }
}
</style>"""

# The page's own controller, in the house dialect: the selects submit on
# change, the search box submits on Enter or on the button, the chips are
# built from the CONTROL values, and base derives the count from the
# chips. Nothing here records whether the panel is open - that is base's
# one class on the panel, and the reason seven mechanisms became one.
P2_WAS = """function viewDocument(documentUrl, documentName, tenantName) {"""
P2_NOW = """/* ===== THE FILTER, page side ===== 30 Sep 2026 ======================
   Four controls, and the same shape as Properties and Tenants. The
   selects submit on change; the search box submits on Enter or on its
   button, NOT on every keystroke. The chips are built from the control
   values and base counts them - see the alv-filter script in base.html,
   which owns the open state and the count. [test_lease_filter.py] */
document.addEventListener('DOMContentLoaded', function () {
    updateActiveFilters();
    ['propertySelect', 'agreementSelect', 'leaseSelect'].forEach(function (id) {
        var el = document.getElementById(id);
        if (el) {
            el.addEventListener('change', function () {
                document.getElementById('filterForm').submit();
            });
        }
    });
    var box = document.getElementById('searchInput');
    if (box) {
        box.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                document.getElementById('filterForm').submit();
            }
        });
    }
    var go = document.getElementById('searchBtn');
    if (go) {
        go.addEventListener('click', function () {
            document.getElementById('filterForm').submit();
        });
    }
    var clear = document.getElementById('clearAllBtn');
    if (clear) {
        clear.addEventListener('click', function () {
            ['searchInput', 'propertySelect', 'agreementSelect',
             'leaseSelect'].forEach(function (id) {
                var el = document.getElementById(id);
                if (el) { el.value = ''; }
            });
            document.getElementById('filterForm').submit();
        });
    }
});

function updateActiveFilters() {
    var tags = document.getElementById('filterTags');
    if (!tags) { return; }
    var say = {attached: 'Attached', missing: 'Missing',
               active: 'Active', expired: 'Expired'};
    var of = [
        ['search', 'Search', 'searchInput'],
        ['property', 'Property', 'propertySelect'],
        ['agreement', 'Agreement', 'agreementSelect'],
        ['lease', 'Lease', 'leaseSelect']
    ];
    tags.innerHTML = '';
    of.forEach(function (row) {
        var el = document.getElementById(row[2]);
        if (!el || !el.value) { return; }
        var shown = say[el.value] || el.value;
        var chip = document.createElement('span');
        chip.className = 'filter-tag';
        /* textContent, not a template string - a tenant called Smith &
           Co would otherwise arrive as markup. */
        chip.textContent = row[1] + ': ' + shown + ' ';
        var x = document.createElement('button');
        x.className = 'remove-tag';
        x.type = 'button';
        x.setAttribute('aria-label', 'Remove the ' + row[1] + ' filter');
        x.textContent = '\\u00d7';
        x.addEventListener('click', function () { clearFilter(row[0]); });
        chip.appendChild(x);
        tags.appendChild(chip);
    });
}

function clearFilter(which) {
    var id = {search: 'searchInput', property: 'propertySelect',
              agreement: 'agreementSelect', lease: 'leaseSelect'}[which];
    var el = id && document.getElementById(id);
    if (el) { el.value = ''; }
    document.getElementById('filterForm').submit();
}

function viewDocument(documentUrl, documentName, tenantName) {"""

PAGE_PAIRS = [(P1_WAS, P1_NOW), (P2_WAS, P2_NOW)]

# ==========================================================================
print('=' * 74)
print('SECTION T, ROUND T4 - MANAGE LEASE AGREEMENTS GETS A FILTER%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ---- the view -----------------------------------------------------------
vp = os.path.join(alv_tree.roots()[0] if False else os.getcwd(), VIEW)
if not os.path.isfile(vp):
    vp = VIEW
if not os.path.isfile(vp):
    raise SystemExit('T4: %s is not on disk' % VIEW)
v, vraw = read(vp)
print('  %s' % VIEW)
if 'THE FILTER - 30 Sep 2026' in v:
    print('     already filters')
else:
    v = patch(vp, v, VIEW_PAIRS, VIEW, VIEW_COUNTS)
    print('     four things read from GET, and current tenants unless asked')
    print('     the three redirects keep the filter you were looking at')

    # GATES. Python first: a view that does not compile is a 500 on
    # every screen in the module, not a layout bug.
    import ast
    try:
        ast.parse(v)
    except SyntaxError as e:
        raise SystemExit('T4: the patched view does not parse: %s' % e)
    body = re.sub(r'#.*', '', v)
    for must in ("request.GET.get('search'", "request.GET.get('all')",
                 'Q(tenant_name__icontains=search)',
                 "tenants.filter(tenant_current='Yes')",
                 'from django.db.models import Q',
                 "'filter_qs':"):
        if must not in body:
            raise SystemExit('T4: the view does not say %s' % must)
    if body.count('redirect(request.get_full_path())') != 3:
        raise SystemExit('T4: %d redirect(s) keep the query string, not 3'
                         % body.count('redirect(request.get_full_path())'))
    if "redirect('tenant_lease_agreement')" in body:
        raise SystemExit('T4: a redirect still throws the filter away')
    # BOTH SPELLINGS OF AN EMPTY FileField. The model allows blank and
    # null, so `missing` has to name both or it under-reports.
    seg = body[body.find('def tenant_lease_agreement'):]
    seg = seg[:seg.find('\n@login_required')]
    if seg.count('tenant_lease_agreement__isnull=True') != 2 or \
            seg.count("tenant_lease_agreement=''") != 2:
        raise SystemExit('T4: attached/missing does not name both the empty '
                         'string and NULL on both sides')
    if not CHECK:
        back_up(vp, vraw)
        write(vp, v)

# ---- the page -----------------------------------------------------------
q = alv_tree.path_of(PAGE)
t, traw = read(q)
print('  %s' % PAGE)
if 'filterPanel' in t:
    print('     already carries the panel')
else:
    t = patch(q, t, PAGE_PAIRS, PAGE)
    print('     Filter beside Back, a chips row, and a four-field panel')
    print('     the toggle carries the filter with it')

    mk = re.sub(r'<(script|style)\b.*?</\1>', '',
                re.sub(r'<!--.*?-->', '', t, flags=re.S), flags=re.S)
    js = '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script>', t, re.S))
    js = re.sub(r'/\*.*?\*/', ' ', js, flags=re.S)
    css = re.sub(r'/\*.*?\*/', ' ', '\n'.join(
        re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S)), flags=re.S)

    # THE HOUSE PARTS, EXACTLY ONCE EACH.
    for name, n in (('id="filterPanel"', 1), ('id="activeFilters"', 1),
                    ('id="filterTags"', 1), ('id="filterForm"', 1),
                    ('class="action-filter"', 0),
                    ('btn action-filter', 1), ('id="clearAllBtn"', 1),
                    ('id="searchInput"', 1), ('id="propertySelect"', 1),
                    ('id="agreementSelect"', 1), ('id="leaseSelect"', 1),
                    ('page-action-buttons-single', 0),
                    ('Include past tenants', 1),
                    ('Current tenants only', 1)):
        got = mk.count(name)
        if got != n:
            raise SystemExit('T4: %s appears %d time(s) in the markup, not %d'
                             % (name, got, n))
    # THE BUTTON AND THE PANEL AGREE. base finds the panel through
    # aria-controls; a mismatch is a filter button that does nothing.
    m = re.search(r'aria-controls="([^"]+)"', mk)
    if not m or ('id="%s"' % m.group(1)) not in mk:
        raise SystemExit('T4: aria-controls does not name a panel on the page')
    # IT IS A GET FORM, and it carries `all` when `all` is set, or the
    # first change of a select would drop you back to current tenants.
    if not re.search(r'<form action="\{% url .tenant_lease_agreement. %\}"'
                     r' method="get" id="filterForm">', mk):
        raise SystemExit('T4: the filter form is not a GET to this page')
    if not re.search(r'\{% if show_all %\}<input type="hidden" name="all" '
                     r'value="1">\{% endif %\}', mk):
        raise SystemExit('T4: the form does not carry `all`, so changing a '
                         'select would drop you back to current tenants')
    # THE PAGE WRITES NO RULE base ALREADY OWNS. H1 moved the frame and
    # D4 the field; a copy here would be the thing those rounds removed.
    # THE PAGE MAY WRITE grid-template-columns AND NOTHING ELSE. H1 put
    # the frame in base and left the column count out, on purpose - the
    # field count differs per panel. Anything else here would be the
    # copy H1 and D4 removed.
    own = []
    for m in re.finditer(r'([^{}]*(?:\.alv-filter|\.filter-grid|'
                         r'\.filter-header|\.filter-title|\.filter-group|'
                         r'\.filter-label|\.filter-select|\.filter-tag|'
                         r'\.search-input|\.search-btn|\.action-filter)'
                         r'[^{}]*)\{([^}]*)\}', css):
        sel = ' '.join(m.group(1).split())
        decl = set(d.split(':')[0].strip() for d in m.group(2).split(';')
                   if ':' in d)
        if sel != '.filter-grid' or not decl <= {'grid-template-columns',
                                                 'gap'}:
            own.append('%s { %s }' % (sel, ', '.join(sorted(decl))))
    if own:
        raise SystemExit('T4: the page writes %d rule(s) base already owns: '
                         '%s' % (len(own), own[:3]))
    # AND NOTHING RECORDS THE OPEN STATE BUT base.
    for bad in ('filterToggleIcon', 'alvFilterOpen', 'style.cssText',
                'forceExpanded'):
        if bad in js:
            raise SystemExit('T4: the page script mentions %s - base owns the '
                             'open state' % bad)
    # THE CHIPS ARE BUILT AS TEXT. A tenant called Smith & Co must not
    # arrive as markup, and every other page in the house does this with
    # innerHTML +=.
    if 'innerHTML +=' in js or 'innerHTML+=' in js:
        raise SystemExit('T4: the chips are built with innerHTML')
    if 'chip.textContent' not in js:
        raise SystemExit('T4: the chips are not built from textContent')
    for must in ("getElementById('filterForm').submit()", "e.key === 'Enter'",
                 'updateActiveFilters', 'function clearFilter'):
        if must not in js:
            raise SystemExit('T4: the page script does not do %s' % must)
    # DJANGO STILL BALANCES.
    for tag, close in (('if', 'endif'), ('for', 'endfor'),
                       ('block', 'endblock')):
        a = len(re.findall(r'\{%\s*' + tag + r'\b', t))
        b = len(re.findall(r'\{%\s*' + close + r'\b', t))
        if a != b:
            raise SystemExit('T4: %d {%% %s %%} against %d {%% %s %%}'
                             % (a, tag, b, close))
    if not CHECK:
        back_up(q, traw)
        write(q, t)

# ---- what this does NOT touch -------------------------------------------
print('  the other seventeen list screens that still cannot be narrowed')
BARE = ('cash_receipts.html', 'comments_report.html', 'customer_list.html',
        'petty_cash.html', 'finance_expense.html', 'finance_revenue.html',
        'finance_valuations.html', 'title_deeds_management.html',
        'user_administration.html', 'workspace_management.html',
        'crs/country_list.html', 'crs/fi_list.html', 'crs/submission_list.html',
        'projects/project_task_list.html', 'invoices/physical_invoice.html',
        'household_member_management.html', 'property_assets.html')
for rel in BARE:
    w = alv_tree.join(rel.replace('/', os.sep))
    if not os.path.isfile(w):
        raise SystemExit('T4: %s is not where alv_tree says' % rel)
print('     %d named, none of them changed' % len(BARE))

print('-' * 74)
print('  a search box, three selects and a current-or-past toggle - and')
print('  uploading a document leaves you on the list you were working.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
