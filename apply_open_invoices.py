#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Open Invoices joins the table standard, and stops deciding rows in HTML.

Migration #5. Two changes, deliberately in one round because either alone
leaves the page half-right.

THE STYLING. `invoices.html` styles `.table-container table thead th` - a
DESCENDANT selector at (0,1,3) against base's `.alv-table thead th` at (0,1,2).
It wins on SPECIFICITY, not on document order, so no amount of reordering
would have let base's header through: the navy `#2c3e50` band had to be
deleted. The page also carries `.table-container { overflow: hidden }`, which
is the exact fault base's own comment measured - hidden makes the container
the scroll container for any sticky descendant, so the header it is about to
gain would sit 615px above the viewport instead of at top:0.

THE ROWS. The table decided its own contents in the template: three nested
loops over props x tenants x invoices, keeping the combinations where all
three line up. Two consequences beyond the arithmetic:

  * the template can never know whether it printed anything, so the page
    cannot have the standard's empty state - and an empty result looks
    exactly like a failed load; and
  * due date and days overdue are computed here by two template tags AND
    again, identically, in `open_invoices_report`. One fact, two places,
    which is precisely the shape that made lease_renewal_report and
    tenant_report disagree about a declined renewal.

So the rows are built once, in the view, in the order the nested loops
produced them: property index, then tenant index, then invoice order. Not by
re-deriving a sort key - `props.objects.filter(prop_name=...)` carries NO
`order_by`, so its order is the database's and cannot be reconstructed from
the fields. The positions are what the loops used, so the positions are what
this uses.

TWO THINGS FOUND WHILE READING, both fixed here because the round rebuilds
the markup they live in:

  * The filter dropdowns were populated from the FILTERED lists. Select
    property X and the property dropdown then contains only X - you cannot
    move to property Y without clearing first. `all_props` and `all_tenants`
    were already in the context and already unused. One word each.
  * The Paid control becomes a POST form, because that is what an icon action
    is on every migrated page (see physical_invoice_list). `invoices_commit`
    ignores `request.method`, so it accepts the POST unchanged and the email
    path is untouched. It still ACCEPTS a GET - closing that is a one-line
    decorator, deliberately left for its own round.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT  = os.path.dirname(os.path.abspath(__file__))
TPL   = os.path.join(ROOT, 'pages', 'templates')
PAGE  = os.path.join(TPL, 'invoices.html')
BASE  = os.path.join(TPL, 'base.html')
VIEW  = os.path.join(ROOT, 'pages', 'views', 'invoices.py')
CHECK = '--check' in sys.argv
SUFFIX = '.bak_openinv'


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def one(t, needle, what):
    n = t.count(needle)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %s'
                 % (what, n, needle[:110]))


# ===================================================================== VIEW

ROWS_HELPER = '''

def _open_invoice_rows(open_invoices, shown_props, shown_tenants):
    """One row per open invoice, in the order the template's loops produced.

    The template used to do this itself:

        for p in props: for t in tenant: for i in invoices:
            if i.tenant_id == t.tenant_id and t.prop_id == p.prop_id

    which is O(props x tenants x invoices) comparisons to print a few dozen
    rows, and - because the decision is taken inside the loop - leaves the
    template unable to say whether it printed any.

    ORDER IS REPRODUCED BY POSITION, NOT BY SORT KEY. `shown_props` may be
    `props.objects.filter(prop_name=...)`, which carries no `order_by`, so
    its order is whatever the database returned and cannot be rebuilt from
    prop_country and prop_name. The loops walked these lists in order, so the
    index in each list is the sort key, with the invoice's own position last.

    A row is skipped on exactly the two conditions the `{% if %}` skipped on:
    the invoice's tenant is not in `shown_tenants`, or that tenant's property
    is not in `shown_props`.
    """
    tenant_at, tenant_by_id = {}, {}
    for i, t in enumerate(shown_tenants):
        if t.tenant_id not in tenant_by_id:      # first wins, as the loop did
            tenant_at[t.tenant_id] = i
            tenant_by_id[t.tenant_id] = t
    prop_at, prop_by_id = {}, {}
    for i, p in enumerate(shown_props):
        if p.prop_id not in prop_by_id:
            prop_at[p.prop_id] = i
            prop_by_id[p.prop_id] = p

    today = date.today()
    ordered = []
    for pos, inv in enumerate(open_invoices):
        t = tenant_by_id.get(inv.tenant_id)
        if t is None:
            continue
        p = prop_by_id.get(t.prop_id)
        if p is None:
            continue
        # Same arithmetic as calculate_due_date / calculate_days_overdue, and
        # the same as open_invoices_report. It is written here once now.
        #
        # The None guard is not defensive habit - it is fidelity. The old tag
        # returned the invoice date unchanged when it had nothing to add to,
        # and 0 days overdue from there, so an invoice with no date rendered
        # a blank-dated row rather than raising. Dropping the guard would turn
        # that row into a 500.
        terms = t.tenant_payment_terms or 0
        if inv.invoice_date:
            due = inv.invoice_date + timedelta(days=int(terms))
            overdue = (today - due).days if today > due else 0
        else:
            due, overdue = None, 0
        ordered.append(((prop_at[p.prop_id], tenant_at[t.tenant_id], pos), {
            'invoice_id':   inv.invoice_id,
            'prop_name':    p.prop_name,
            'prop_country': p.prop_country,
            'tenant_name':  t.tenant_name,
            'amount':       inv.effective_amount,
            'invoice_date': inv.invoice_date,
            'due_date':     due,
            'days_overdue': overdue,
            'is_overdue':   overdue > 0,
        }))
    ordered.sort(key=lambda pair: pair[0])
    return [row for _, row in ordered]

'''

OLD_CONTEXT = '''    context = {
        "invoices": iresults,
        "tenant": filtered_tenants,  # Filtered tenants for display
        "props": filtered_props,     # Filtered props for display
        "all_props": all_props,      # All props for dropdown
        "all_tenants": all_tenants,  # All tenants for dropdown
        "selected_property": prop_output if prop_output != "All" else "",
        "selected_tenant": tenant_output if tenant_output != "All" else "",
    }'''

NEW_CONTEXT = '''    context = {
        # The rows the table draws, decided here rather than by three nested
        # loops in the template. `filtered_*` still say WHICH rows; they are
        # no longer what the dropdowns are built from.
        "rows": _open_invoice_rows(iresults, filtered_props, filtered_tenants),
        # The dropdowns list EVERY property and tenant. They used to be built
        # from the filtered lists, so choosing property X left the property
        # dropdown holding only X - you could not move to Y without clearing
        # first. Both of these were already in this context and unused.
        "all_props": all_props,
        "all_tenants": all_tenants,
        "selected_property": prop_output if prop_output != "All" else "",
        "selected_tenant": tenant_output if tenant_output != "All" else "",
    }'''


def patch_view(text):
    if '_open_invoice_rows' in text:
        return text, 0
    one(text, OLD_CONTEXT, 'the invoices_page context')
    text = text.replace(OLD_CONTEXT, NEW_CONTEXT, 1)
    # WHERE the helper goes is load-bearing, and getting it wrong is silent.
    #
    # `open_invoices_report` carries the identical decorator pair, so
    # anchoring on `@login_required` matched twice. Anchoring on the `def`
    # line instead is unique - and inserts the helper BETWEEN the decorators
    # and the function they belong to. The result is valid Python that
    # compiles cleanly: the decorators land on the HELPER, and invoices_page
    # is left with no @login_required and no @permission_required at all.
    #
    # So the insertion point is the first line of invoices_page's decorator
    # block, found by walking back from the def, and the self-check below
    # reads the decorators off the parsed tree rather than trusting this.
    anchor = 'def invoices_page(request):'
    one(text, anchor, 'the invoices_page definition')
    lines = text.split('\n')
    at = next(i for i, l in enumerate(lines) if l.startswith(anchor))
    while at > 0 and lines[at - 1].lstrip().startswith('@'):
        at -= 1
    lines[at:at] = ROWS_HELPER.strip('\n').split('\n') + ['', '']
    return '\n'.join(lines), 2


# ================================================================= TEMPLATE

OLD_TABLE_START = '''  <!-- Invoices Table -->
  <div class="table-container">
    <table class="table table-bordered table-striped invoices-table">'''

NEW_TABLE = '''  <!-- Invoices Table -->
  <div class="table-container">
    <table class="table alv-table invoices-table">
      <thead>
        <tr>
          <th style="width: 22%">Property</th>
          <th style="width: 10%">Country</th>
          <th style="width: 20%">Tenant</th>
          <th class="num" style="width: 11%">Amount</th>
          <th style="width: 12%">Invoice Date</th>
          <th style="width: 12%">Due Date</th>
          <th class="num" style="width: 8%">Days Overdue</th>
          <th class="desktop-action-cell cell-actions" style="width: 5%">Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for row in rows %}
          <tr>
            <td data-label="Property">{{ row.prop_name }}</td>
            <td data-label="Country">{{ row.prop_country }}</td>
            <td data-label="Tenant">{{ row.tenant_name }}</td>
            <td data-label="Amount" class="num amount-cell">&euro;{{ row.amount|floatformat:0 }}</td>
            <td data-label="Invoice Date">{{ row.invoice_date|date:"Y-m-d" }}</td>
            <td data-label="Due Date">{{ row.due_date|date:"Y-m-d" }}</td>
            <td data-label="Days Overdue" class="num overdue-cell{% if row.is_overdue %} is-overdue{% endif %}">{{ row.days_overdue }}</td>
            <td data-label="Actions" class="desktop-action-cell cell-actions">
              {% if perms.auth.can_edit_invoices %}
                <form method="post" action="{% url 'invoices_commit' row.invoice_id %}" class="inv-inline-form">
                  {% csrf_token %}
                  <button type="submit" class="icon-action-btn icon-approve" title="Mark as paid" aria-label="Mark as paid">
                    <i class="fas fa-check"></i>
                  </button>
                </form>
              {% else %}
                <span class="icon-action-btn icon-approve is-disabled" title="You do not have permission to mark invoices paid" aria-disabled="true">
                  <i class="fas fa-check"></i>
                </span>
              {% endif %}
            </td>
            <td class="mobile-action-bar cols-1">
              {% if perms.auth.can_edit_invoices %}
                <form method="post" action="{% url 'invoices_commit' row.invoice_id %}" class="inv-inline-form-mobile">
                  {% csrf_token %}
                  <button type="submit" class="mobile-action-btn">
                    <i class="fas fa-check mobile-action-icon icon-color-approve"></i>
                    <span class="mobile-action-label">Mark as Paid</span>
                  </button>
                </form>
              {% else %}
                <span class="mobile-action-btn mobile-action-disabled">
                  <i class="fas fa-check mobile-action-icon"></i>
                  <span class="mobile-action-label">Mark as Paid</span>
                </span>
              {% endif %}
            </td>
          </tr>
        {% endfor %}
      </tbody>
    </table>

    {% if not rows %}
      {# An empty tbody looks exactly like a failed load. #}
      <div class="alv-empty">
        <i class="fas fa-file-invoice-dollar"></i>
        <div class="alv-empty-title">No open invoices</div>
        <div class="alv-empty-hint">
          Either everything is paid, or the filters above are hiding it.
        </div>
      </div>
    {% endif %}
  </div>'''

# The dropdowns list everything, not the filtered subset.
DROPDOWN_FIXES = [
    ('the property dropdown lists every property',
     '{% for prop in props %}', '{% for prop in all_props %}'),
    ('the tenant dropdown lists every tenant',
     '{% for tenant_item in tenant %}', '{% for tenant_item in all_tenants %}'),
]

# CSS the round removes outright. Each either styles something base owns, or
# styles a class this page no longer contains.
DROP = (
    # base owns the shell, and its `overflow: clip` is deliberate.
    '.table-container',
    # (0,1,3) descendant rules that BEAT base's .alv-table on specificity.
    '.table-container table',
    '.table-container table thead th',
    '.table-container table tbody td',
    '.table-container table tbody tr:hover',
    # nothing on this page has carried btn-info since the button sweep.
    '.btn-info',
    '.btn-info:hover',
    # the filter round renamed this container to .alv-filter-active in the
    # markup and left its rule behind - one of the eleven on the list.
    '.active-filters',
    # base's mobile card view does all of this now.
    '.invoices-table',
    '.invoices-table thead',
    '.invoices-table, .invoices-table tbody, .invoices-table tr',
    '.invoices-table tr',
    '.invoices-table tr:hover',
    '.invoices-table td',
    '.invoices-table td:first-child',
    '.invoices-table td:not(:first-child)::before',
    # the mark-as-paid button is an icon action now.
    '.btn-paid',
    '.btn-paid:hover',
    '.invoices-table td.action-cell',
    '.invoices-table td.action-cell::before',
    '.invoices-table td.action-cell .btn-paid',
)

# Declaration-level edits: the rule stays, some of it goes or changes.
DECL_SET = {
    # The days really are overdue, so red is right - it moves onto the token,
    # as .highlight-red and .lease-end-red did before it.
    'td.overdue-cell.is-overdue': {'color': 'var(--alv-bad)'},
}

EXTRA_CSS = """
    /* An inline form is how a state-changing icon button is written on every
       migrated page. It must not become a layout box of its own. */
    .inv-inline-form { display: inline; }
    .inv-inline-form button { background: none; border: 0; padding: 0; }
"""

# base gains ONE line. `.mobile-action-bar` already ships `.cols-2` and
# `.cols-4`; a page with a single action had no way to say so and its button
# came out a third of the card wide. This is a NAME on a pattern that exists,
# the same move `.icon-duplicate` was on `--alv-edit`.
BASE_ANCHOR = '        .mobile-action-bar.cols-2 { grid-template-columns: repeat(2, 1fr); }'
BASE_ADD = ('        .mobile-action-bar.cols-1 { grid-template-columns: 1fr; }\n'
            + BASE_ANCHOR)

# Debris the filter round left in this page's script, and the two dead
# locals that went with it.
JS_DEAD = '''    // Auto-expand filter panel on mobile if there are active filters
    if (false) {
        const filterContent = document.getElementById('filterContent');
        const toggleIcon = document.getElementById('filterToggleIcon');
        const filterPanel = document.getElementById('filterPanel');
        if (filterContent && !filterContent.classList.contains('show')) {
            filterContent.classList.add('show');
            toggleIcon.classList.add('rotated');
            filterPanel.classList.add('expanded');
        }
    }
'''


def edit_css(text):
    """Drop DROP outright; edit declarations in DECL_SET.

    An emptied rule is removed rather than written back as `sel {}` - the
    lease-renewal round's finding: an empty rule reads as a hook somebody
    left deliberately.
    """
    dropped = touched = 0
    missing = list(DROP)
    for a, z in [(m.start(1), m.end(1)) for m in
                 re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S)][::-1]:
        css = text[a:z]
        out, cur = [], 0
        for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
            sel = ' '.join(re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split())
            if sel in DROP:
                out.append(css[cur:m.start()]); cur = m.end(); dropped += 1
                while sel in missing:
                    missing.remove(sel)
                continue
            if sel not in DECL_SET:
                continue
            body = before = m.group(2)
            for prop, val in DECL_SET[sel].items():
                body = re.sub(r'(%s\s*:\s*)[^;}]*' % re.escape(prop),
                              r'\g<1>' + val, body, flags=re.I)
            if body != before:
                out.append(css[cur:m.start()])
                if body.strip().strip(';'):
                    out.append('%s{%s}' % (m.group(1), body)); touched += 1
                cur = m.end()
        if out:
            out.append(css[cur:])
            text = text[:a] + ''.join(out) + text[z:]
    if missing:
        sys.exit('! these rules were expected and not found:\n   - %s'
                 % '\n   - '.join(sorted(set(missing))))
    return text, dropped, touched


def patch_page(text):
    n = 0
    # -- the table
    i = text.find(OLD_TABLE_START)
    if i < 0:
        sys.exit('! the invoices table was not found as expected')
    one(text, OLD_TABLE_START, 'the invoices table')
    end = text.find('</table>\n  </div>', i)
    if end < 0:
        sys.exit('! the invoices table has no closing </table></div>')
    text = text[:i] + NEW_TABLE + text[end + len('</table>\n  </div>'):]
    n += 1

    # -- the dropdowns
    for what, old, new in DROPDOWN_FIXES:
        one(text, old, what)
        text = text.replace(old, new, 1)
        n += 1

    # -- the dead script block
    if JS_DEAD in text:
        one(text, JS_DEAD, 'the dead filter-expand block')
        text = text.replace(JS_DEAD, '', 1)
        n += 1

    # -- the two locals that block left behind. `hasFilters` is assigned and
    #    never read; base counts .filter-tag itself now.
    old = '''    const activeFiltersDiv = document.getElementById('activeFilters');
'''
    if old in text:
        text = text.replace(old, '', 1); n += 1
    old = "    if (!propertySelect || !tenantSelect || !activeFiltersDiv || !filterTagsDiv) return;"
    if old in text:
        text = text.replace(
            old, "    if (!propertySelect || !tenantSelect || !filterTagsDiv) return;", 1)
        n += 1
    for old in ('    let hasFilters = false;\n', '        hasFilters = true;\n'):
        while old in text:
            text = text.replace(old, '', 1); n += 1

    text, dropped, touched = edit_css(text)

    i = text.rfind('</style>')
    if i < 0:
        sys.exit('! no </style> to append to')
    text = text[:i] + EXTRA_CSS + text[i:]
    return text, n, dropped, touched


def patch_base(text):
    if '.mobile-action-bar.cols-1' in text:
        return text, 0
    one(text, BASE_ANCHOR, 'the mobile action bar column modifiers')
    return text.replace(BASE_ANCHOR, BASE_ADD, 1), 1


def counts(t):
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))
    return dict(ifs=len(re.findall(r'\{%\s*if\b', t)),
                endifs=len(re.findall(r'\{%\s*endif\s*%\}', t)),
                fors=len(re.findall(r'\{%\s*for\b', t)),
                endfors=len(re.findall(r'\{%\s*endfor\s*%\}', t)),
                co=css.count('{'), cc=css.count('}'),
                divs=len(re.findall(r'<div\b', t)),
                closes=len(re.findall(r'</div\s*>', t)))


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        shutil.copy2(p, b)


def main():
    vsrc, psrc, bsrc = read(VIEW), read(PAGE), read(BASE)
    done = '_open_invoice_rows' in vsrc and 'alv-table invoices-table' in psrc
    if done:
        print('  invoices (view + template)  already migrated')
        print('\n  0 file(s) changed')
        return

    vout, vn = patch_view(vsrc)
    pout, pn, dropped, touched = patch_page(psrc)
    bout, bn = patch_base(bsrc)

    bad = []
    a, b = counts(psrc), counts(pout)
    if b['ifs'] != b['endifs']:
        bad.append('template if/endif do not balance (%d/%d)' % (b['ifs'], b['endifs']))
    if b['fors'] != b['endfors']:
        bad.append('template for/endfor do not balance (%d/%d)' % (b['fors'], b['endfors']))
    if b['co'] != b['cc']:
        bad.append('CSS braces do not balance (%d/%d)' % (b['co'], b['cc']))
    if b['divs'] != b['closes']:
        bad.append('div tags do not balance (%d/%d)' % (b['divs'], b['closes']))
    # THE THREE LOOPS MUST BE GONE. That is the round.
    if b['fors'] != a['fors'] - 2:
        bad.append('expected to lose exactly two {%% for %%} loops, went %d -> %d'
                   % (a['fors'], b['fors']))
    for dead in ('table-bordered table-striped', 'calculate_due_date',
                 'calculate_days_overdue', 'iresults', 'tresults',
                 'btn-paid', 'invoice_tags'):
        if dead in pout:
            bad.append('%s survived in the template' % dead)
    # the template must not still be reading what the view stopped sending
    for gone in ('{% for prop in props %}', '{% for tenant_item in tenant %}'):
        if gone in pout:
            bad.append('a dropdown still reads a filtered list: %s' % gone)
    for want in ('class="table alv-table invoices-table"', '{% for row in rows %}',
                 'alv-empty-title', 'mobile-action-bar cols-1',
                 'desktop-action-cell cell-actions', 'var(--alv-bad)'):
        if want not in pout:
            bad.append('expected in the template and missing: %s' % want)
    if 'def _open_invoice_rows' not in vout:
        bad.append('the row builder did not land in the view')
    if '"rows": _open_invoice_rows(' not in vout:
        bad.append('the context does not carry rows')
    if '.mobile-action-bar.cols-1' not in bout:
        bad.append('base did not gain cols-1')
    # PARSE IT AND READ THE DECORATORS OFF THE TREE.
    #
    # compile() is not enough and this round proved it. The first version of
    # this patcher inserted the helper between invoices_page's decorators and
    # its def. That compiles - it is valid Python - and it moves
    # @login_required and @permission_required onto the HELPER, leaving the
    # page view open to anybody. A string check would not have seen it
    # either, because every line it looked for was still present.
    try:
        import ast
        tree = ast.parse(vout)
        funcs = {n.name: n for n in tree.body
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        if 'invoices_page' not in funcs:
            bad.append('invoices_page is no longer a module-level function')
        else:
            def deco_names(fn):
                out = set()
                for d in fn.decorator_list:
                    node = d.func if isinstance(d, ast.Call) else d
                    out.add(getattr(node, 'id', getattr(node, 'attr', '?')))
                return out
            have = deco_names(funcs['invoices_page'])
            for want in ('login_required', 'permission_required'):
                if want not in have:
                    bad.append('invoices_page LOST @%s - the helper was '
                               'inserted inside its decorator block' % want)
            if 'permission_required' in have:
                src = ast.get_source_segment(vout, funcs['invoices_page']) or ''
                if 'can_access_invoices' not in vout.split('def invoices_page')[0][-400:]:
                    bad.append('invoices_page is not guarded by can_access_invoices')
            if '_open_invoice_rows' in funcs and deco_names(funcs['_open_invoice_rows']):
                bad.append('the row helper picked up decorators that belong '
                           'to invoices_page: %s'
                           % ', '.join(sorted(deco_names(funcs['_open_invoice_rows']))))
    except SyntaxError as e:
        bad.append('the patched view does not parse: %s' % e)
    if bad:
        sys.exit('! Open Invoices self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    print('  pages/views/invoices.py     row builder + context   (%d edit(s))' % vn)
    print('  invoices.html               markup:%d  rules dropped:%d  rewritten:%d'
          % (pn, dropped, touched))
    print('  base.html                   mobile action bar gains cols-1 (%d)' % bn)
    print('     the three nested loops are gone: %d {%% for %%} -> %d'
          % (a['fors'], b['fors']))
    if not CHECK:
        for p, out in ((VIEW, vout), (PAGE, pout), (BASE, bout)):
            backup(p)
            with open(p, 'w', encoding='utf-8') as f:
                f.write(out)
    print('\n  3 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
