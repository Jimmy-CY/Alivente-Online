"""
Home / landing page view.

Extracted from the legacy pages/views/main.py during the modular views
split. This is the public landing page: it has NO @login_required and
renders for anonymous visitors, building the authenticated extras only
when a user is logged in (so the request.user.is_authenticated checks
below are genuine guards, not always-true - do not flatten them).

Functions
---------
- _build_today_items : Helper. Builds the ordered, non-zero "Today"
                       panel items (urgent -> warning -> info) from the
                       notification summary.
- home               : The landing page. Lists properties / current
                       tenants / suppliers, computes per-area permission
                       flags, and (for authenticated users with
                       dashboard access) builds the cached Today panel.

Cross-module import
-------------------
get_notification_data is imported from .notifications_dashboard (it was
extracted there during the modular split; the former "update this import
when the NOTIFICATIONS section is extracted from main.py" note is now
obsolete - main.py no longer exists - and has been removed).
"""

import json

from django.core.cache import cache
from django.shortcuts import render

from ..models import props, supplier, tenant
from ..services.portfolio_insights import portfolio_insights
from .notifications_dashboard import get_notification_data



# ONE TABLE, TWO USES - HM-1, 8 Oct 2026.
#
# This list lived inside _build_today_items, where it decided which ROWS
# a user may see. The PAYLOAD underneath those rows was serialised whole,
# for every user with dashboard access, amounts and all, and
# buildOverdueContent() in home.html reads item.tenant_rent straight out
# of it. The filter below closes that, and it reads THIS list rather than
# a second one of its own: a category added here is filtered there
# without anybody remembering to, which is the only way two lists stay in
# step. This repo has paid for the other kind more than once.
_TODAY_CANDIDATES = [
        # URGENT (red)
        {
            'key': 'overdueInvoices',
            'category': 'overdue',
            'label': 'Overdue Invoice',
            'label_plural': 'Overdue Invoices',
            'icon': 'fas fa-exclamation-triangle',
            'severity': 'urgent',
            'permission': 'invoices',
        },
        {
            'key': 'vacantProperties',
            'category': 'vacant',
            'label': 'Vacant Property',
            'label_plural': 'Vacant Properties',
            'icon': 'fas fa-home',
            'severity': 'urgent',
            'permission': 'properties',
        },
        {
            'key': 'declinedRenewals',
            'category': 'declined',
            'label': 'Declined Renewal',
            'label_plural': 'Declined Renewals',
            'icon': 'fas fa-times-circle',
            'severity': 'urgent',
            'permission': 'tenants',
        },
        # WARNING (yellow)
        {
            'key': 'expiringLeases',
            'category': 'expiring',
            'label': 'Expiring Lease',
            'label_plural': 'Expiring Leases',
            'icon': 'fas fa-calendar-times',
            'severity': 'warning',
            'permission': 'tenants',
        },
        {
            'key': 'expensesWaitingApproval',
            'category': 'approval',
            'label': 'Expense awaiting approval',
            'label_plural': 'Expenses awaiting approval',
            'icon': 'fas fa-clipboard-check',
            'severity': 'warning',
            'permission': 'expenses',
        },
        # INFO (teal)
        {
            'key': 'expensesWaitingPayment',
            'category': 'payment',
            'label': 'Expense awaiting payment',
            'label_plural': 'Expenses awaiting payment',
            'icon': 'fas fa-credit-card',
            'severity': 'info',
            'permission': 'expenses',
        },
    ]

# Keys of get_notification_data()'s payload that are not categories and
# are not gated: the counts block (filtered on its own, key by key) and
# the timestamp.
_PAYLOAD_ALWAYS = ('summary', 'lastUpdated')


def _filter_notification_data(data, perms):
    """The embedded payload, cut to what this user may actually open.

    FAIL-CLOSED, DELIBERATELY. Anything that is neither in
    _PAYLOAD_ALWAYS nor a category this user has the permission for is
    dropped - including a category nobody has added to _TODAY_CANDIDATES
    yet. Such a category has no button either, so the page loses nothing
    it was drawing; and a detail list added to get_notification_data()
    without a table entry is then invisible by default rather than
    public by default. That is the right way round for a payload with
    money in it.
    """
    if not data:
        return {}
    allowed = set()
    known = set()
    for c in _TODAY_CANDIDATES:
        known.add(c['key'])
        if perms.get(c['permission'], False):
            allowed.add(c['key'])

    out = {}
    for key, value in data.items():
        if key == 'summary':
            out['summary'] = dict(
                (k, v) for k, v in (value or {}).items() if k in allowed)
            continue
        if key in _PAYLOAD_ALWAYS:
            out[key] = value
            continue
        if key in allowed:
            out[key] = value
    return out


def _build_today_items(notification_data):
    """
    Build the ordered list of non-zero Today items for the home page panel.

    Each item is a dict with:
      - label:      singular/plural human heading
      - count:      integer count
      - icon:       Font Awesome class
      - severity:   'urgent' | 'warning' | 'info' (drives the colour)
      - category:   matches the data-category strings used by the modal JS
                    (so we can look up the right detail rows on tap)
      - permission: perms_map key gating visibility

    Returns items in priority order: urgent first, then warning, then info.
    Zero-count items are filtered out so the Today panel only shows
    things the user can act on.
    """
    summary = (notification_data or {}).get('summary', {}) or {}

    # `category` strings MUST match the categories used in the
    # SimpleNotificationDashboard JS class (see home.html / notifications.html):
    # 'vacant', 'expiring', 'declined', 'overdue', 'approval', 'payment'
    candidates = _TODAY_CANDIDATES

    items = []
    for c in candidates:
        count = summary.get(c['key'], 0) or 0
        if count <= 0:
            continue
        items.append({
            'label': c['label_plural'] if count != 1 else c['label'],
            'count': count,
            'icon': c['icon'],
            'severity': c['severity'],
            'category': c['category'],
            'permission': c['permission'],
        })
    return items


def home(request):
    results = props.objects.all().order_by('prop_country', 'prop_name')
    tresults = tenant.objects.filter(tenant_current="Yes")
    sresults = supplier.objects.all().order_by('supplier_country', 'supplier_contact_person')

    # Build permission flags for the template
    perms = {}
    if request.user.is_authenticated:
        if request.user.is_superuser:
            # Superusers have access to everything
            perms = {
                'properties': True,
                'tenants': True,
                'suppliers': True,
                'issues': True,
                'dashboard': True,
                'invoices': True,
                'expenses': True,
                'petty_cash': True,
                'financials': True,
                'projects': True,
                'personal': True,
                'administration': True,
            }
        else:
            perms = {
                'properties': request.user.has_perm('auth.can_access_properties'),
                'tenants': request.user.has_perm('auth.can_access_tenants'),
                'suppliers': request.user.has_perm('auth.can_access_suppliers'),
                'issues': request.user.has_perm('auth.can_access_issues'),
                'dashboard': request.user.has_perm('auth.can_access_dashboard'),
                'invoices': request.user.has_perm('auth.can_access_invoices'),
                'expenses': request.user.has_perm('auth.can_access_expenses'),
                'petty_cash': request.user.has_perm('auth.can_access_petty_cash'),
                'financials': request.user.has_perm('auth.can_access_financials'),
                'projects': request.user.has_perm('auth.can_access_projects'),
                'passports':    request.user.has_perm('auth.can_access_passports'),
                'recipes':      request.user.has_perm('auth.can_access_recipes'),
                'celebrations': request.user.has_perm('auth.can_access_celebrations'),
                'crs':          request.user.has_perm('auth.can_access_crs'),
                'personal': (
                    request.user.has_perm('auth.can_access_passports')
                    or request.user.has_perm('auth.can_access_recipes')
                    or request.user.has_perm('auth.can_access_celebrations')
                    or request.user.has_perm('auth.can_access_crs')
                ),
                'administration': request.user.has_perm('auth.can_access_administration'),
            }

    # Portfolio briefing + Today drill-downs - build for authenticated users
    # with dashboard access (same permission gating as the Notifications
    # Dashboard view itself).
    today_items = []
    today_by_category = {}
    notification_data_json = '{}'
    insights = None
    if request.user.is_authenticated and perms.get('dashboard'):
        cache_key = f'home_notification_data_user_{request.user.id}'
        notification_data = cache.get(cache_key)
        if notification_data is None:
            try:
                notification_data = get_notification_data()
                # 30-second TTL - fast page loads, ~minute-fresh counts.
                cache.set(cache_key, notification_data, 30)
            except Exception:
                notification_data = None

        if notification_data:
            all_today_items = _build_today_items(notification_data)
            # Filter out rows the user can't navigate to (permission gated).
            today_items = [
                item for item in all_today_items
                if perms.get(item['permission'], False)
            ]
            # Keyed by category so the template can drop each drill-down into
            # the briefing card it belongs to (e.g. 'overdue' -> Arrears card).
            today_by_category = {item['category']: item for item in today_items}
            # Embed full data (counts + detail rows) so modals open instantly
            # without a second round-trip. ~few KB of JSON.
            # FILTERED BY THE SAME TABLE THAT FILTERS THE BUTTONS -
            # HM-1, 8 Oct 2026. This embedded the WHOLE payload for every
            # user with dashboard access: overdueInvoices,
            # expensesWaitingApproval and expensesWaitingPayment WITH
            # THEIR AMOUNTS, while the rows above were permission-filtered.
            # buildOverdueContent() reads item.tenant_rent straight out of
            # it. A user with dashboard and no expenses permission had
            # every expense amount in their page source.
            #
            # The filter reads _TODAY_CANDIDATES, not a second list of its
            # own: a category added there is filtered here without anybody
            # remembering to, which is the only way two lists stay in step.
            try:
                notification_data_json = json.dumps(
                    _filter_notification_data(notification_data, perms),
                    default=str)
            except Exception:
                notification_data_json = '{}'

        # Portfolio briefing (forward projection, expiries, arrears, churn +
        # AI/templated brief). Read-only; the metrics compute fresh each load
        # while the AI prose is fingerprint-cached inside the service. Wrapped
        # so a briefing hiccup can never take the Home page down.
        # THE AUDIENCE IS can_access_financials - his call, HM-1,
        # 8 Oct 2026, and not is_superuser: the tree already governs
        # income with that permission, and keying Home on superuser alone
        # would have meant a non-superuser with finance access losing the
        # rent roll here while reading every figure in the Finance module.
        # Superusers get the flag unconditionally in the perms map above.
        #
        # The summary handed to the service is the UNFILTERED one: it is
        # read server-side for the vacancy count and never serialised.
        # The page gets the filtered copy, built separately above.
        summary = (notification_data or {}).get('summary', {}) or {}
        try:
            insights = portfolio_insights(today_summary=summary,
                                          income=bool(perms.get('financials')))
        except Exception:
            insights = None

    return render(request, "home.html", {
        "props": results,
        "tenant": tresults,
        "supplier": sresults,
        "perms_map": perms,
        "today_items": today_items,
        "today_by_category": today_by_category,
        "notification_data_json": notification_data_json,
        "insights": insights,
    })