# -*- coding: utf-8 -*-
"""apply_owned_from.py - round OF-3, 28 Oct 2026.

RELEASE 33 - OWNED FROM. His decisions of 28 October, taken from the Live
before/after report:

    - Owned From on every property (migration 0112): the first lease
      start, or the date typed on the property; the two seasonal villas
      get the dates he gave (Villa 24 2010, Villa H4 2014).
    - No budget and no revenue counts before it. Pro-rata lines: Option B -
      an unowned property's share drops, owned shares stay as they are.
    - One helper, budget_year_months, behind the P&L, its two drill-downs,
      the expense matrix and Financial Indicators.
    - Add Expense / Add Revenue suggest the Owned From month as Applies
      from for a property's first lines.

Stands on HK-4. Idempotent. Edits backed up to .bak_ownedfrom; ships this
patcher, its suite, migration 0112, Show-OwnedFrom.ps1 and
Fix-CompanyTaxCent.ps1. RUN THE MIGRATION after deploying.
"""
import os
import re
import sys

SUFFIX = '.bak_ownedfrom'
MARK = 'OF-3, 28 Oct 2026'
CHECK = False
CREATES = (
    'test_owned_from.py',
    os.path.join('pages', 'migrations', '0112_prop_owned_from.py'),
    'Show-OwnedFrom.ps1',
    'Fix-CompanyTaxCent.ps1',
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'models.py'), [
        (r'''        help_text="Uncheck to exclude this property from occupancy rate and days-to-fill calculations (e.g., for seasonal rentals)"
    )

    def __str__(self):
''',
         r'''        help_text="Uncheck to exclude this property from occupancy rate and days-to-fill calculations (e.g., for seasonal rentals)"
    )

    # OWNED FROM - OF-3, 28 Oct 2026. His rule, in his words: "We could
    # use the date of the first rental for that property as the date that
    # we owned it from" - the gap between buying and first letting is
    # accepted. Filled from the first lease by migration 0112 and editable
    # on the property. Blank means "use the first lease", and a property
    # with no lease and no date counts as owned all along (seasonal).
    # Nothing - no budget line, no share of a pro-rata line, no revenue -
    # counts in a month before this one. See property_owned_from().
    prop_owned_from = models.DateField(
        blank=True, null=True, verbose_name="Owned From",
        help_text="Budgets and revenue count from this month. Blank = the first lease start.")

    def __str__(self):
'''),
        (r'''

def lease_monthly_rent_levies(prop, year, today=None):
    """(rent[12], levies[12], has_leases) for a property/year from its leases."""
''',
         r'''

# =============================================================================
# OWNED FROM - OF-3, 28 Oct 2026.
#
# His rules, agreed 28 October:
#   - a property is owned from its first lease start (or the date typed on
#     the property, which wins); the gap between buying and first letting
#     is accepted;
#   - no budget, no revenue, in a month before the Owned-from month (any
#     part of a month counts as the month);
#   - OPTION B for pro-rata lines: each owned property keeps its own share,
#     and the share of a property not yet owned simply drops. His words:
#     "the earlier years would be more accurate because we don't burden
#     them with the full amount."
#
# ONE implementation, used by the P&L, its drill-downs, the expense matrix
# and Financial Indicators - so no two screens can disagree about a month.
# =============================================================================
def property_owned_from(prop):
    """The date `prop` counts from, or None for "owned all along"."""
    if getattr(prop, 'prop_owned_from', None):
        return prop.prop_owned_from
    return tenant.objects.filter(prop_id=prop.pk).exclude(
        tenant_lease_start_date__isnull=True).aggregate(
            _m=Min('tenant_lease_start_date'))['_m']


def owned_from_map(prop_ids):
    """{prop_id: date or None} for many properties, in two queries."""
    ids = [i for i in set(prop_ids) if i is not None]
    if not ids:
        return {}
    out = dict(props.objects.filter(prop_id__in=ids)
               .values_list('prop_id', 'prop_owned_from'))
    need = [i for i, d in out.items() if not d]
    if need:
        for pid, d in (tenant.objects.filter(prop_id__in=need)
                       .exclude(tenant_lease_start_date__isnull=True)
                       .values('prop_id')
                       .annotate(_m=Min('tenant_lease_start_date'))
                       .values_list('prop_id', '_m')):
            out[pid] = d
    return out


def owned_months(owned_from, year):
    """Twelve booleans: is the property owned in each month of `year`?"""
    if owned_from is None:
        return [True] * 12
    return [(year, m) >= (owned_from.year, owned_from.month)
            for m in range(1, 13)]


def apply_owned_from(values, owned_from, year):
    """`values` (twelve months) with every month before Owned From as 0."""
    mask = owned_months(owned_from, year)
    return [v if mask[i] else _fh_Decimal('0') for i, v in enumerate(values)]


def budget_year_months(expense_rows, year, with_sources=False):
    """{expense_id: twelve figures} for `year`, for EVERY row given.

    Each row resolved from its effective-dated history exactly as before
    (rows with no history keep their live cells), then every month before
    the property's Owned From set to 0. Pro-rata rows are no exception:
    that IS Option B - the unowned share drops, the owned shares stay.
    With with_sources=True also returns the resolver's provenance map.
    """
    rows = list(expense_rows)
    pids = sorted({r.prop_id for r in rows if r.prop_id is not None})
    res = resolve_year_months_bulk(pids, FinancialFigureHistory.KIND_BUDGET,
                                   year, with_sources=with_sources)
    vmap, prov = res if with_sources else (res, None)
    ofm = owned_from_map(pids)
    out = {}
    for r in rows:
        v = vmap.get(r.expense_id)
        if v is None:
            v = [getattr(r, 'expense_' + m, 0) or 0 for m in _FH_MONTHS]
        out[r.expense_id] = apply_owned_from(list(v), ofm.get(r.prop_id), year)
    return (out, prov) if with_sources else out


def lease_monthly_rent_levies(prop, year, today=None):
    """(rent[12], levies[12], has_leases) for a property/year from its leases."""
'''),
        (r'''    non rental/levies revenue-table rows. Seasonal: the revenue-table rows as-is."""
    rent, lev, has = lease_monthly_rent_levies(prop, year, today)
    if not has:
        return list(prop.revenue_set.all())
    if rental_lt is None:
        rental_lt = lease_line_type(LEASE_ROLE_RENT)
''',
         r'''    non rental/levies revenue-table rows. Seasonal: the revenue-table rows as-is."""
    rent, lev, has = lease_monthly_rent_levies(prop, year, today)
    # OF-3, 28 Oct 2026: nothing counts before the property's Owned From.
    # Lease rent cannot predate the first lease anyway; this is for the
    # revenue table (seasonal and ancillary rows) and a typed date that is
    # later than the first lease. Table rows are handed back as unsaved
    # COPIES when a month is masked - never save what this returns.
    _mask = owned_months(property_owned_from(prop), year)
    if not has:
        return [_owned_copy(r, _mask) for r in prop.revenue_set.all()]
    rent = [v if _mask[i] else 0 for i, v in enumerate(rent)]
    lev = [v if _mask[i] else 0 for i, v in enumerate(lev)]
    if rental_lt is None:
        rental_lt = lease_line_type(LEASE_ROLE_RENT)
'''),
        (r'''    for r in prop.revenue_set.all():
        if not (r.revenue_line_types and r.revenue_line_types.lease_role):
            rows.append(r)
    return rows


''',
         r'''    for r in prop.revenue_set.all():
        if not (r.revenue_line_types and r.revenue_line_types.lease_role):
            rows.append(_owned_copy(r, _mask))
    return rows


def _owned_copy(r, mask):
    """`r` itself when every month is owned, else an unsaved copy with the
    unowned months at 0 - the database row is never touched."""
    if all(mask):
        return r
    import copy as _copy
    c = _copy.copy(r)
    for i, mm in enumerate(_FH_REV_MON):
        if not mask[i]:
            setattr(c, 'revenue_' + mm, _fh_Decimal('0'))
    return c


'''),
        (r'''    is treated as in service all year, unchanged."""
    year = year or _fh_date.today().year
    _first_lease = tenant.objects.filter(prop=prop).exclude(
        tenant_lease_start_date__isnull=True).aggregate(
            _m=Min('tenant_lease_start_date'))['_m']
    if _first_lease is None:
        _start_month = 1                     # no leases -> owned/active all year
    elif _first_lease.year > year:
        return _fh_Decimal('0')              # not yet in service this year
    elif _first_lease.year == year:
        _start_month = _first_lease.month    # first (partial) year
    else:
        _start_month = 1                     # full year
    vals_map = resolve_year_months_bulk([prop.prop_id], FinancialFigureHistory.KIND_BUDGET, year)
    total = _fh_Decimal('0')
    for e in prop.expense_set.all():
        vals = vals_map.get(e.expense_id)
        if vals is not None:
            for _i in range(_start_month - 1, 12):
                total += (vals[_i] or 0)
        else:
            for _i in range(_start_month - 1, 12):
                total += (getattr(e, 'expense_' + _FH_REV_MON[_i], 0) or 0)
    return total

''',
         r'''    is treated as in service all year, unchanged."""
    year = year or _fh_date.today().year
    # OF-3, 28 Oct 2026: "in service from" is now the property's Owned From
    # (the first lease start unless a date is typed on the property), and
    # the months come from the same helper the P&L uses - so the two
    # cannot disagree about a single month.
    total = _fh_Decimal('0')
    for vals in budget_year_months(prop.expense_set.all(), year).values():
        for v in vals:
            total += (v or 0)
    return total

'''),
    ]),
    (os.path.join('pages', 'forms.py'), [
        (r'''            "prop_floor_area",
            "prop_year_built",
            "prop_status",
            "prop_available_for_rent",
''',
         r'''            "prop_floor_area",
            "prop_year_built",
            # OF-3, 28 Oct 2026 - in this list or the form drops it (T2-1).
            "prop_owned_from",
            "prop_status",
            "prop_available_for_rent",
'''),
    ]),
    (os.path.join('pages', 'views', 'finance.py'), [
        (r'''    record_valuation_history, property_value_as_of,
    resolve_year_months_bulk, lease_revenue_rows, current_lease_revenue,
    property_annual_lease_revenue, property_annual_budgeted_expenses,
    property_annual_actual_expenses, _lease_month,
''',
         r'''    record_valuation_history, property_value_as_of,
    resolve_year_months_bulk, lease_revenue_rows, current_lease_revenue,
    budget_year_months,
    property_annual_lease_revenue, property_annual_budgeted_expenses,
    property_annual_actual_expenses, _lease_month,
'''),
        (r'''            pass
    return date.today()


''',
         r'''            pass
    return date.today()


def _owned_info(model):
    """{prop_id: {'from': 'YYYY-MM-01' or None, 'lines': bool}} for the Add
    screens - OF-3, 28 Oct 2026. `lines` says whether the property already
    has rows of `model` (expense or revenue); the screen suggests Owned
    From as the Applies-from date for a property's FIRST lines."""
    from pages.models import owned_from_map
    ids = list(props.objects.values_list('prop_id', flat=True))
    ofm = owned_from_map(ids)
    has = set(model.objects.values_list('prop_id', flat=True).distinct())
    return {str(i): {'from': (ofm[i].replace(day=1).isoformat()
                              if ofm.get(i) else None),
                     'lines': i in has} for i in ids}


'''),
        (r'''    _leased_ids = list(tenant.objects.values_list('prop_id', flat=True).distinct())
    return render(request, "finance_revenue_add.html", {
        "props_data": props.objects.all().order_by('prop_country', 'prop_name'),
        "revenue_types": revenue_types.objects.all(),
''',
         r'''    _leased_ids = list(tenant.objects.values_list('prop_id', flat=True).distinct())
    return render(request, "finance_revenue_add.html", {
        "owned_info": _owned_info(revenue),
        "props_data": props.objects.all().order_by('prop_country', 'prop_name'),
        "revenue_types": revenue_types.objects.all(),
'''),
        (r'''    more than this system can afford.

    IT DOES NOT PRO-RATE. property_annual_budgeted_expenses counts a
    property's budget only from the month it came into service, which is
    right for the P&L - it is answering "what did this cost me". This screen
    answers "how is this charge split", and the charge is distributed by
    value whether or not the property was owned all year. Pro-rating here
    would leave a column summing to less than the charge under a footer
    claiming to be the charge. The template says so under the table.

    Carries no decorators: it is a helper, not a view.
''',
         r'''    more than this system can afford.

    IT COUNTS FROM OWNED FROM - OF-3, 28 Oct 2026, which reverses the old
    "does not pro-rate" decision. That decision was right while the P&L
    drew a full charge and only Financial Indicators trimmed a first year:
    the matrix had to match the charge. His Option B changes the charge
    itself - a property not yet owned carries no share, and the P&L shows
    the smaller total - so the matrix follows, through budget_year_months,
    and each column is still exactly the charge the P&L draws.

    Carries no decorators: it is a helper, not a view.
'''),
        (r'''    blended = []
    for y in years:
        vals_map, prov_map = resolve_year_months_bulk(
            prop_ids, FinancialFigureHistory.KIND_BUDGET, y, with_sources=True)
        # DOES THIS YEAR STRADDLE A CHANGE?
        #
''',
         r'''    blended = []
    for y in years:
        # OF-3, 28 Oct 2026: the same helper the P&L uses, so a property
        # carries nothing here before its Owned From either (Option B) and
        # each column is the charge the P&L draws for that year.
        vals_map, prov_map = budget_year_months(
            [e for _v in by_prop.values() for e in _v['sources']], y,
            with_sources=True)
        # DOES THIS YEAR STRADDLE A CHANGE?
        #
'''),
        (r'''    )
    return render(request, "finance_expense_add.html", {
        "props_data": props_data,
        "expense_types": expense_types.objects.all(),
''',
         r'''    )
    return render(request, "finance_expense_add.html", {
        "owned_info": _owned_info(expense),
        "props_data": props_data,
        "expense_types": expense_types.objects.all(),
'''),
        (r'''    except (TypeError, ValueError):
        _year_int = None
    _year_map = (resolve_year_months_bulk(
        list(expenses.values_list('prop_id', flat=True).distinct()),
        FinancialFigureHistory.KIND_BUDGET, _year_int) if _year_int is not None else None)

    # Create a list of expense items with monthly breakdown
''',
         r'''    except (TypeError, ValueError):
        _year_int = None
    # OF-3, 28 Oct 2026: the same months the P&L cell it opened from drew.
    _year_map = (budget_year_months(expenses, _year_int)
                 if _year_int is not None else None)

    # Create a list of expense items with monthly breakdown
'''),
        (r'''    except (TypeError, ValueError):
        _year_int = None
    _year_map = (resolve_year_months_bulk(
        list(budget_expenses.values_list('prop_id', flat=True).distinct()),
        FinancialFigureHistory.KIND_BUDGET, _year_int) if _year_int is not None else None)

    # Create budget expense items with monthly breakdown (similar to budget_expense_details_view)
''',
         r'''    except (TypeError, ValueError):
        _year_int = None
    # OF-3, 28 Oct 2026: the same months the P&L cell it opened from drew.
    _year_map = (budget_year_months(budget_expenses, _year_int)
                 if _year_int is not None else None)

    # Create budget expense items with monthly breakdown (similar to budget_expense_details_view)
'''),
        (r'''        expenses.extend(prop.expense_set.all())

    _fh_exp_map = resolve_year_months_bulk(selected_prop_ids, FinancialFigureHistory.KIND_BUDGET, selected_year)
    for _e in expenses:
        _vals = _fh_exp_map.get(_e.expense_id)
''',
         r'''        expenses.extend(prop.expense_set.all())

    # OF-3, 28 Oct 2026: every row resolved AND held to its property's
    # Owned From - nothing before it counts, a pro-rata share included
    # (Option B). Rows with no history keep their live cells, as before.
    _fh_exp_map = budget_year_months(expenses, selected_year)
    for _e in expenses:
        _vals = _fh_exp_map.get(_e.expense_id)
'''),
    ]),
    (os.path.join('pages', 'views', 'properties.py'), [
        (r'''    # Worked out on load, so Save can refuse in a dialog on this page rather
    # than storing a message that surfaces on whatever renders next.
    return render(request, "properties_edit.html", {
        "props": [current_property],  # Maintain your existing structure
        "existing_names": list(existing_names),  # Add this for client-side validation
''',
         r'''    # Worked out on load, so Save can refuse in a dialog on this page rather
    # than storing a message that surfaces on whatever renders next.
    # OF-3, 28 Oct 2026 - shown under Owned From, so the date it falls
    # back to is on the screen rather than in the reader's memory.
    _first_lease = (tenant.objects.filter(prop_id=prop_id)
                    .exclude(tenant_lease_start_date__isnull=True)
                    .order_by('tenant_lease_start_date')
                    .values_list('tenant_lease_start_date', flat=True).first())
    return render(request, "properties_edit.html", {
        "first_lease": _first_lease,
        "props": [current_property],  # Maintain your existing structure
        "existing_names": list(existing_names),  # Add this for client-side validation
'''),
        (r'''        'prop_available_for_rent', 'prop_title_deed',
        'prop_title_deed_status', 'prop_electricity', 'prop_water',
        'prop_refuse', 'prop_property_tax', 'prop_sewerage', 'prop_insurance'
    ), pk=prop_id)

''',
         r'''        'prop_available_for_rent', 'prop_title_deed',
        'prop_title_deed_status', 'prop_electricity', 'prop_water',
        'prop_refuse', 'prop_property_tax', 'prop_sewerage', 'prop_insurance',
        'prop_owned_from',     # OF-3, 28 Oct 2026 - deferred = a 2nd query
    ), pk=prop_id)

'''),
    ]),
    (os.path.join('pages', 'templates', 'properties_edit.html'), [
        (r'''            <label for="prop_year_built"><strong>Year Built</strong></label>
            <input type="number" class="form-control" id="prop_year_built" name="prop_year_built" placeholder="Year Built" value="{{results.prop_year_built}}">
          </div>
        </div>
''',
         r'''            <label for="prop_year_built"><strong>Year Built</strong></label>
            <input type="number" class="form-control" id="prop_year_built" name="prop_year_built" placeholder="Year Built" value="{{results.prop_year_built}}">
          </div>
        </div>
    </div>
    {# OF-3, 28 Oct 2026 - Owned From: budgets and revenue count from this month. #}
    <div class="form-row">
        <div class="col-md-4">
          <div class="form-group">
            <label for="prop_owned_from"><strong>Owned From</strong></label>
            <input type="date" class="form-control" id="prop_owned_from" name="prop_owned_from" value="{{ results.prop_owned_from|date:'Y-m-d' }}">
            <small class="text-muted">Budgets and revenue count from this month.{% if first_lease %} The first lease started {{ first_lease|date:'j M Y' }}.{% endif %} Blank uses the first lease.</small>
          </div>
        </div>
'''),
    ]),
    (os.path.join('pages', 'templates', 'properties_add.html'), [
        (r'''            <label for="prop_year_built"><strong>Year Built</strong></label>
            <input type="number" class="form-control" id="prop_year_built" name="prop_year_built" placeholder="Year Built">
          </div>
        </div>
''',
         r'''            <label for="prop_year_built"><strong>Year Built</strong></label>
            <input type="number" class="form-control" id="prop_year_built" name="prop_year_built" placeholder="Year Built">
          </div>
        </div>
    </div>
    {# OF-3, 28 Oct 2026 - Owned From: budgets and revenue count from this month. #}
    <div class="form-row">
        <div class="col-md-4">
          <div class="form-group">
            <label for="prop_owned_from"><strong>Owned From</strong></label>
            <input type="date" class="form-control" id="prop_owned_from" name="prop_owned_from">
            <small class="text-muted">Budgets and revenue count from this month. Blank uses the first lease once there is one.</small>
          </div>
        </div>
'''),
    ]),
    (os.path.join('pages', 'templates', 'property_detail.html'), [
        (r'''                                            <span class="detail-label">Year Built:</span>
                                            <span class="detail-value">{{ property.prop_year_built }}</span>
                                        </div>
                                    </div>
''',
         r'''                                            <span class="detail-label">Year Built:</span>
                                            <span class="detail-value">{{ property.prop_year_built }}</span>
                                        </div>
                                        {# OF-3, 28 Oct 2026 - Owned From: budgets and revenue count from this month. #}
                                        <div class="detail-row">
                                            <span class="detail-label">Owned From:</span>
                                            <span class="detail-value">{{ property.prop_owned_from|date:'j M Y'|default:'First lease' }}</span>
                                        </div>
                                    </div>
'''),
    ]),
    (os.path.join('pages', 'templates', 'property_report.html'), [
        (r'''                        <span class="detail-label">Year Built:</span>
                        <span class="detail-value">{{ property.prop_year_built }}</span>
                    </div>
                </div>
''',
         r'''                        <span class="detail-label">Year Built:</span>
                        <span class="detail-value">{{ property.prop_year_built }}</span>
                    </div>
                    {# OF-3, 28 Oct 2026 - Owned From: budgets and revenue count from this month. #}
                    <div class="detail-row">
                        <span class="detail-label">Owned From:</span>
                        <span class="detail-value">{{ property.prop_owned_from|date:'j M Y'|default:'First lease' }}</span>
                    </div>
                </div>
'''),
    ]),
    (os.path.join('pages', 'templates', 'finance_expense.html'), [
        (r'''        <div class="expense-matrix-note">
            A dash means the property was not in this distribution that year &mdash;
            not that it cost nothing. Figures are <strong>budgeted</strong>, and are
            <strong>not pro-rated</strong> to the months a property was owned, so
            each column is the whole charge for that year. The P&amp;L pro-rates a
            property&rsquo;s first year and will show less for it.
            {% if matrix.blended %}
            A year marked &#8225; <strong>straddles a change</strong>: the charge
''',
         r'''        <div class="expense-matrix-note">
            A dash means the property was not in this distribution that year &mdash;
            {# OF-3, 28 Oct 2026 - the matrix counts from Owned From, as the P&L does. #}
            not that it cost nothing. Figures are <strong>budgeted</strong>, and count
            only from each property&rsquo;s <strong>Owned From</strong> month, exactly as
            the P&amp;L does &mdash; a property not yet owned carries no share, so an
            early column can be smaller than the charge set today.
            {% if matrix.blended %}
            A year marked &#8225; <strong>straddles a change</strong>: the charge
'''),
    ]),
    (os.path.join('pages', 'templates', 'finance_expense_add.html'), [
        (r'''});
</script>

{% endblock %}''',
         r'''});
</script>
{{ owned_info|json_script:"alv-owned-from" }}
<script>
/* APPLIES FROM FOLLOWS OWNED FROM - OF-3, 28 Oct 2026. His decision: when
   the first budget lines go onto a property, suggest its Owned From month,
   so a property bought in March and entered in June still counts from
   March. A property that already has lines keeps 1 January unless it was
   not owned yet then. Never overrides a date the user has typed. */
(function () {
    var info = {};
    try { info = JSON.parse(document.getElementById('alv-owned-from').textContent) || {}; }
    catch (e) { info = {}; }
    var sel = document.getElementById('prop');
    var eff = document.getElementById('effective_date');
    if (!sel || !eff) { return; }
    var dflt = eff.value, touched = false;
    var note = document.createElement('p');
    note.className = 'alv-applies-help alv-owned-note';
    note.hidden = true;
    eff.parentNode.insertBefore(note, eff.nextSibling);
    eff.addEventListener('input', function () { touched = true; note.hidden = true; });
    sel.addEventListener('change', function () {
        if (touched) { return; }
        var o = info[sel.value], want = dflt, why = '';
        if (o && o.from) {
            if (!o.lines) { want = o.from; why = 'it has no budget lines yet'; }
            else if (o.from > dflt) { want = o.from; why = 'it was not owned before then'; }
        }
        eff.value = want;
        if (why) {
            var d = new Date(want + 'T00:00:00');
            note.textContent = 'Set to this property\u2019s Owned From month, ' +
                d.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' }) +
                ', because ' + why + '. Change it if you need to.';
            note.hidden = false;
        } else {
            note.hidden = true;
        }
    });
})();
</script>

{% endblock %}'''),
    ]),
    (os.path.join('pages', 'templates', 'finance_revenue_add.html'), [
        (r'''})();
</script>

{% endif %}
''',
         r'''})();
</script>
{{ owned_info|json_script:"alv-owned-from" }}
<script>
/* APPLIES FROM FOLLOWS OWNED FROM - OF-3, 28 Oct 2026. His decision: when
   the first budget lines go onto a property, suggest its Owned From month,
   so a property bought in March and entered in June still counts from
   March. A property that already has lines keeps 1 January unless it was
   not owned yet then. Never overrides a date the user has typed. */
(function () {
    var info = {};
    try { info = JSON.parse(document.getElementById('alv-owned-from').textContent) || {}; }
    catch (e) { info = {}; }
    var sel = document.getElementById('prop');
    var eff = document.getElementById('effective_date');
    if (!sel || !eff) { return; }
    var dflt = eff.value, touched = false;
    var note = document.createElement('p');
    note.className = 'alv-applies-help alv-owned-note';
    note.hidden = true;
    eff.parentNode.insertBefore(note, eff.nextSibling);
    eff.addEventListener('input', function () { touched = true; note.hidden = true; });
    sel.addEventListener('change', function () {
        if (touched) { return; }
        var o = info[sel.value], want = dflt, why = '';
        if (o && o.from) {
            if (!o.lines) { want = o.from; why = 'it has no revenue lines yet'; }
            else if (o.from > dflt) { want = o.from; why = 'it was not owned before then'; }
        }
        eff.value = want;
        if (why) {
            var d = new Date(want + 'T00:00:00');
            note.textContent = 'Set to this property\u2019s Owned From month, ' +
                d.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' }) +
                ', because ' + why + '. Change it if you need to.';
            note.hidden = false;
        } else {
            note.hidden = true;
        }
    });
})();
</script>

{% endif %}
'''),
    ]),
    (os.path.join('test_expense_matrix.py'), [
        (r'''resolve_year_months_bulk = _res_ns['resolve_year_months_bulk']

_ns = {'expense': expense, 'expense_line_types': expense_line_types,
       'props': props, 'FinancialFigureHistory': FinancialFigureHistory,
       'resolve_year_months_bulk': resolve_year_months_bulk,
       'FH_BASELINE_DATE': FH_BASELINE_DATE,
       'Decimal': Decimal, 'date': date, 'MONTHS': MONTHS}
''',
         r'''resolve_year_months_bulk = _res_ns['resolve_year_months_bulk']

# OF-3, 28 Oct 2026 - the matrix counts through budget_year_months now, the
# helper the P&L uses. Lifted for real, like the resolver above. This stub
# schema has no lease table and no Owned From column, so owned_from_map is
# the one piece stood in for: every property here is owned all along, and
# what Owned From does to a figure is test_owned_from.py's to prove.
_of_ns = {'resolve_year_months_bulk': resolve_year_months_bulk,
          'FinancialFigureHistory': FinancialFigureHistory,
          '_FH_MONTHS': _FH_MONTHS, '_fh_Decimal': Decimal,
          'owned_from_map': lambda ids: {}}
for _fn in ('owned_months', 'apply_owned_from', 'budget_year_months'):
    exec(compile(lift(_MD_SRC, _fn), _fn, 'exec'), _of_ns)
budget_year_months = _of_ns['budget_year_months']

_ns = {'expense': expense, 'expense_line_types': expense_line_types,
       'props': props, 'FinancialFigureHistory': FinancialFigureHistory,
       'resolve_year_months_bulk': resolve_year_months_bulk,
       'budget_year_months': budget_year_months,
       'FH_BASELINE_DATE': FH_BASELINE_DATE,
       'Decimal': Decimal, 'date': date, 'MONTHS': MONTHS}
'''),
        (r'''
# ===========================================================================
head('2. the figures - resolved from history, and NOT pro-rated')
# ===========================================================================

''',
         r'''
# ===========================================================================
head('2. the figures - resolved from history, counted from Owned From')
# ===========================================================================

'''),
        (r'''      M['grand_total'] == sum((r['total'] for r in M['rows']), Decimal('0')))

# THE DECISION THAT MOVES MONEY.
check('NO PRO-RATING: a full twelve months is counted in every year',
      _by['Ionion - Villa 24']['cells'][2] == Decimal('2400'))
# The DOCSTRING names the pro-rating helper while explaining why the matrix
''',
         r'''      M['grand_total'] == sum((r['total'] for r in M['rows']), Decimal('0')))

# THE DECISION THAT MOVES MONEY. OF-3, 28 Oct 2026: the matrix now counts
# from each property's Owned From, as the P&L does (his Option B). Villa 24
# has no lease and no date in this fixture, so it is owned all along and
# still carries a full twelve months - which is what this asks.
check('OWNED ALL YEAR: a full twelve months is counted in every year',
      _by['Ionion - Villa 24']['cells'][2] == Decimal('2400'))
# The DOCSTRING names the pro-rating helper while explaining why the matrix
'''),
        (r'''_called = {n.func.id for n in ast.walk(_h)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
check('  and the helper calls no in-service helper at all',
      'property_annual_budgeted_expenses' not in _called,
      str(sorted(_called))[:70])
''',
         r'''_called = {n.func.id for n in ast.walk(_h)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
check('  and the helper calls no annual in-service total - it shares the '
      'P&L\'s monthly helper instead',
      'property_annual_budgeted_expenses' not in _called,
      str(sorted(_called))[:70])
'''),
        (r'''check('  no cell renders a bare 0.00 - absent is absent, not zero',
      not re.search(r'<td>0\.00</td>', HTML))
check('the note says the figures are not pro-rated',
      'not pro-rated' in HTML and 'P&amp;L pro-rates' in HTML)
check('  and says what a dash means',
      'not that it cost nothing' in HTML)
''',
         r'''check('  no cell renders a bare 0.00 - absent is absent, not zero',
      not re.search(r'<td>0\.00</td>', HTML))
check('the note says the figures count from Owned From, as the P&L does',
      'Owned From</strong> month' in HTML and 'the P&amp;L does' in HTML
      and 'not pro-rated' not in HTML)
check('  and says what a dash means',
      'not that it cost nothing' in HTML)
'''),
    ]),
    (os.path.join('test_matrix_range.py'), [
        (r'''resolve = _ns['resolve_year_months_bulk']

_vns = {'expense': expense, 'expense_line_types': expense_line_types,
        'FinancialFigureHistory': FinancialFigureHistory,
        'FH_BASELINE_DATE': FH_BASELINE_DATE,
        'resolve_year_months_bulk': resolve, 'MONTHS': MONTHS,
        'Decimal': Decimal, 'date': date}
exec(compile(lift(VS, 'expense_matrix'), 'm', 'exec'), _vns)
''',
         r'''resolve = _ns['resolve_year_months_bulk']

# OF-3, 28 Oct 2026 - the matrix counts through budget_year_months now, the
# helper the P&L uses. Lifted for real; this stub schema has no lease table
# and no Owned From column, so owned_from_map is the one piece stood in for
# and every property here is owned all along. test_owned_from.py proves
# what Owned From does to a figure.
_ofns = {'resolve_year_months_bulk': resolve,
         'FinancialFigureHistory': FinancialFigureHistory,
         '_FH_MONTHS': _FH_MONTHS, '_fh_Decimal': Decimal,
         'owned_from_map': lambda ids: {}}
for _fn in ('owned_months', 'apply_owned_from', 'budget_year_months'):
    exec(compile(lift(MD, _fn), _fn, 'exec'), _ofns)

_vns = {'expense': expense, 'expense_line_types': expense_line_types,
        'FinancialFigureHistory': FinancialFigureHistory,
        'FH_BASELINE_DATE': FH_BASELINE_DATE,
        'resolve_year_months_bulk': resolve, 'MONTHS': MONTHS,
        'budget_year_months': _ofns['budget_year_months'],
        'Decimal': Decimal, 'date': date}
exec(compile(lift(VS, 'expense_matrix'), 'm', 'exec'), _vns)
'''),
    ]),
    (os.path.join('test_req_marker.py'), [
        (r'''        'script blocks by design, so the reader cannot see what is '
        'really there. One step on from the entry above it.',
}
suspects = []
''',
         r'''        'script blocks by design, so the reader cannot see what is '
        'really there. One step on from the entry above it.',
    # OF-3, 28 Oct 2026 - the same data island as physical_invoice_edit:
    # #alv-owned-from is written by json_script, and read inside a try.
    'finance_expense_add.html':
        '#alv-owned-from is emitted by Django\'s json_script filter at '
        'render time, and the read is inside a try/catch',
    'finance_revenue_add.html':
        '#alv-owned-from is emitted by Django\'s json_script filter at '
        'render time, and the read is inside a try/catch',
}
suspects = []
'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('OF-3 REFUSED: %s' % msg)


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


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pq = os.path.join(root, PS1)
    if "'test_owned_from.py'" in read(pq):
        print('OF-3 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_housekeeping_four.py'" not in read(pq):
        refuse('HK-4 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, rel)):
            refuse('%s is missing - it ships with this patcher; copy it in '
                   'first.' % rel)

    # ---- THE SWAPS
    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    # ---- REGISTRATION
    q = out.get(pq, read(pq))
    q = swap(q, """    'test_housekeeping_four.py'
)""", """    'test_housekeeping_four.py',
    # OF-3, 28 Oct 2026 - Owned From, and Option B for pro-rata lines.
    'test_owned_from.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'pages/templates/projects/projects_detail.html'; Text = 'data-target="#projectsHelpModal"';""",
        """    @{ File = 'pages/models.py'; Text = 'def budget_year_months('; What = 'OF-3: the one helper that holds every budget figure to its property Owned From - without it the P&L counts years before the property was owned' },
    @{ File = 'pages/templates/projects/projects_detail.html'; Text = 'data-target="#projectsHelpModal"';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_housekeeping_four.py',
]""", """    'test_housekeeping_four.py',
    # OF-3, 28 Oct 2026 - Owned From, and Option B for pro-rata lines.
    'test_owned_from.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_housekeep4',
]""", """    '.bak_housekeep4',
    # OF-3, 28 Oct 2026 - Owned From, and Option B for pro-rata lines.
    '.bak_ownedfrom',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # OF-3, 28 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    md = out[os.path.join(root, 'pages', 'models.py')]
    if 'def budget_year_months(' not in md:
        refuse('the Owned From helper did not land in models.py.')

    if CHECK:
        print('OF-3 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('OF-3 applied - Owned From on every property; nothing counts '
          'before it; Option B for pro-rata lines.')
    print('      NOW RUN THE MIGRATION (0112) after deploying.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
