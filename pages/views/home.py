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
from .notifications_dashboard import get_notification_data


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
    candidates = [
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

    # Today panel - build for authenticated users with dashboard access
    # (same permission gating as the Notifications Dashboard view itself).
    today_items = []
    notification_data_json = '{}'
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
            # Embed full data (counts + detail rows) so modals open instantly
            # without a second round-trip. ~few KB of JSON.
            try:
                notification_data_json = json.dumps(notification_data, default=str)
            except Exception:
                notification_data_json = '{}'

    return render(request, "home.html", {
        "props": results,
        "tenant": tresults,
        "supplier": sresults,
        "perms_map": perms,
        "today_items": today_items,
        "notification_data_json": notification_data_json,
    })