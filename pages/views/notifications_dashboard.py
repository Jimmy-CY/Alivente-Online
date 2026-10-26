"""
Notifications dashboard view and data aggregation.

Extracted from the legacy pages/views/main.py during the modular views
split (section ### NOTIFICATIONS ###).

NOT to be confused with pages/views/notifications.py, which holds the
notification *settings* views (admin/personal preferences). This module
is the notification *dashboard data* layer.

Functions
---------
- notifications_dashboard       : AJAX-aware Django view - returns JSON
                                  on XHR, the template on normal load.
- get_notification_data         : Main aggregator; returns all counts +
                                  detail rows. Used by this view AND by
                                  pages/views/home.py for the "Today"
                                  panel.
- get_expenses_waiting_approval : SQL helper.
- get_expenses_waiting_payment  : SQL helper.
- get_expiring_leases           : SQL helper.
- get_declined_renewals         : SQL helper.
- get_overdue_invoices          : SQL helper.
- get_invoices_waiting_approval : ORM helper (NB-1, 26 Oct 2026) - draft
                                  physical invoices, the ones his daily
                                  approval e-mail lists.

The 5 SQL helpers run raw mysql.connector queries (legacy from when
this logic lived in a management command). A future pass could migrate
them to the Django ORM and consolidate with similar logic elsewhere
(finance.py vacancy management, issues.py lease_renewal_report, etc.).
"""

import logging
from datetime import date, datetime, timedelta

import mysql.connector

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import connection as django_connection
from django.http import JsonResponse
from django.shortcuts import render


@login_required
@permission_required('auth.can_access_dashboard', raise_exception=True)
def notifications_dashboard(request):
    """
    Notifications Dashboard view - shows property management alerts and status
    """
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request - return JSON data
        try:
            notification_data = get_notification_data()
            # ES-9, 26 Oct 2026 - Lease Signing is superuser only (ES-8),
            # so nobody else is handed its rows or its count; their box
            # is drawn greyed.
            if not request.user.is_superuser:
                notification_data.pop('leasesNeedingAction', None)
                notification_data.get('summary', {}).pop(
                    'leasesNeedingAction', None)
            return JsonResponse(notification_data)
        except Exception as e:
            return JsonResponse({
                'error': f'Error loading notification data: {str(e)}'
            })
    else:
        # Regular page load - return template
        return render(request, 'notifications.html')


def get_notification_data():
    """Every count and detail list the dashboards show.

    NB-1, 26 Oct 2026 - PHYSICAL INVOICES WAITING FOR APPROVAL join the
    legacy six, his request: "I do receive an email, but would like to see
    it there." They come from the ORM, OUTSIDE the mysql.connector block
    below, so a failure there (it returns zeros) does not also hide the
    drafts, and a failure here does not take the six down with it.
    """
    data = _get_legacy_notification_data()
    try:
        drafts = get_invoices_waiting_approval()
    except Exception as e:                                   # noqa: BLE001
        logging.getLogger(__name__).error(
            'invoices waiting approval: %s', e)
        drafts = []
    data.setdefault('summary', {})['invoicesWaitingApproval'] = len(drafts)
    data['invoicesWaitingApproval'] = drafts
    # ES-9, 26 Oct 2026 - LEASES NEEDING ACTION, his eighth box. Kept out
    # of anything a non-superuser receives: notifications_dashboard drops
    # it for them, and Home's payload filter drops every key it does not
    # know, this one included.
    try:
        leases = get_leases_needing_action()
    except Exception as e:                                   # noqa: BLE001
        logging.getLogger(__name__).error('leases needing action: %s', e)
        leases = []
    data['summary']['leasesNeedingAction'] = len(leases)
    data['leasesNeedingAction'] = leases
    return data


def get_leases_needing_action():
    """Envelopes that need somebody to DO something - ES-9, 26 Oct 2026.

    His decision: signed and waiting for approval, and declined or expired
    ones - "any lease that needs some sort of action". A declined or
    expired envelope STOPS COUNTING once it has been dealt with: its
    tenancy has a lease attached, a newer envelope was started for that
    tenancy, or the envelope was deleted.
    """
    from django.urls import reverse
    from pages.models import LeaseSigning
    rows = []
    for env in (LeaseSigning.pending_approval()
                .select_related('tenant', 'tenant__prop')
                .order_by('completed_at', 'pk')):
        rows.append(_lease_row(env, 'Signed - awaiting approval',
                               env.completed_at, reverse))
    closed = (LeaseSigning.objects
              .filter(status__in=(LeaseSigning.EXPIRED,
                                  LeaseSigning.DECLINED))
              .select_related('tenant', 'tenant__prop')
              .order_by('pk'))
    for env in closed:
        t = env.tenant
        if t.tenant_lease_agreement:
            continue
        if LeaseSigning.objects.filter(tenant_id=t.pk, pk__gt=env.pk).exists():
            continue
        what = ('Declined by the tenant' if env.status == LeaseSigning.DECLINED
                else 'Expired before everybody signed')
        rows.append(_lease_row(env, what, env.expires_at
                               if env.status == LeaseSigning.EXPIRED
                               else None, reverse))
    return rows


def _lease_row(env, what, when, reverse):
    t = env.tenant
    return {
        'envelope_id': env.pk,
        'tenant': t.tenant_display_name or t.tenant_name or '',
        'property_name': (getattr(t.prop, 'prop_name', '') or '')
        if t.prop_id else '',
        'status': what,
        'date': when.strftime('%Y-%m-%d') if when else '',
        'url': reverse('lease_signing_detail', args=[env.pk]),
    }


def get_invoices_waiting_approval():
    """Draft physical invoices - tenant and customer - oldest first.

    STATUS DRAFT IS THE WHOLE TEST, the same one the Physical Invoices list
    pills as Draft and the approval reminder counts: nothing is sent until
    it is approved, so every draft is waiting on somebody.
    """
    from pages.models import PhysicalInvoice
    rows = []
    qs = (PhysicalInvoice.objects
          .filter(status=PhysicalInvoice.STATUS_DRAFT)
          .select_related('tenant', 'tenant__prop')
          .order_by('invoice_date', 'physical_invoice_id'))
    for pi in qs:
        t = pi.tenant if pi.tenant_id else None
        rows.append({
            'invoice_id': pi.pk,
            'invoice_date': pi.invoice_date.strftime('%Y-%m-%d')
            if pi.invoice_date else '',
            'name': pi.bill_name or (t.tenant_display_name if t else ''),
            'kind': 'Tenant' if t else 'Customer',
            'property_name': (getattr(t.prop, 'prop_name', '') or '')
            if t else '',
            'total': float(pi.total or 0),
            'currency': pi.currency or 'EUR',
        })
    return rows


def _get_legacy_notification_data():
    """
    Get notification data by running similar queries to the management command
    """
    logger = logging.getLogger(__name__)
    mydb = None
    my_cursor = None

    try:
        mydb = mysql.connector.connect(
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            database=settings.DATABASES['default']['NAME'],
        )

        my_cursor = mydb.cursor()
        today = date.today()

        # Get vacant properties. Imported here (not at module top) to avoid
        # a circular import between this module and .properties.
        from .properties import get_vacant_properties
        vacant_properties = get_vacant_properties(my_cursor)

        # Get expiring leases (pending renewals)
        expiring_leases = get_expiring_leases(my_cursor, today)

        # Get declined renewals
        declined_renewals = get_declined_renewals(my_cursor, today)

        # Get overdue invoices
        overdue_invoices = get_overdue_invoices(my_cursor, today)

        # Get expenses waiting for approval
        expenses_waiting_approval = get_expenses_waiting_approval(my_cursor)

        # Get expenses waiting for payment
        expenses_waiting_payment = get_expenses_waiting_payment(my_cursor)

        return {
            'summary': {
                'vacantProperties': len(vacant_properties),
                'expiringLeases': len(expiring_leases),
                'declinedRenewals': len(declined_renewals),
                'overdueInvoices': len(overdue_invoices),
                'expensesWaitingApproval': len(expenses_waiting_approval),
                'expensesWaitingPayment': len(expenses_waiting_payment)
            },
            'vacantProperties': vacant_properties,
            'expiringLeases': expiring_leases,
            'declinedRenewals': declined_renewals,
            'overdueInvoices': overdue_invoices,
            'expensesWaitingApproval': expenses_waiting_approval,
            'expensesWaitingPayment': expenses_waiting_payment,
            'lastUpdated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except mysql.connector.Error as e:
        logger.error(f"MySQL connection error in get_notification_data: {e}")
        # Return empty data structure on error
        return {
            'summary': {
                'vacantProperties': 0,
                'expiringLeases': 0,
                'declinedRenewals': 0,
                'overdueInvoices': 0,
                'expensesWaitingApproval': 0,
                'expensesWaitingPayment': 0
            },
            'vacantProperties': [],
            'expiringLeases': [],
            'declinedRenewals': [],
            'overdueInvoices': [],
            'expensesWaitingApproval': [],
            'expensesWaitingPayment': [],
            'lastUpdated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        logger.error(f"Unexpected error in get_notification_data: {e}")
        # Return empty data structure on error
        return {
            'summary': {
                'vacantProperties': 0,
                'expiringLeases': 0,
                'declinedRenewals': 0,
                'overdueInvoices': 0,
                'expensesWaitingApproval': 0,
                'expensesWaitingPayment': 0
            },
            'vacantProperties': [],
            'expiringLeases': [],
            'declinedRenewals': [],
            'overdueInvoices': [],
            'expensesWaitingApproval': [],
            'expensesWaitingPayment': [],
            'lastUpdated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    finally:
        # Always close cursor and connection
        if my_cursor:
            try:
                my_cursor.close()
            except:
                pass
        if mydb and mydb.is_connected():
            try:
                mydb.close()
            except:
                pass
        # Also close Django's connection
        django_connection.close()


def get_expenses_waiting_approval(cursor):
    """Get expenses that require approval (status = 'require_approval')"""
    cursor.execute("""
        SELECT ae.act_expense_id, ae.act_expense_date, ae.act_expense_description,
               ae.act_expense_amount, p.prop_name
        FROM railway.act_expense ae
        JOIN railway.prop p ON ae.prop_id = p.prop_id
        WHERE ae.act_expense_approved = 'No'
        AND ae.act_expense_paid = 'No'
        ORDER BY ae.act_expense_date ASC
    """)

    expenses_data = cursor.fetchall()
    expenses_waiting_approval = []

    for row in expenses_data:
        expenses_waiting_approval.append({
            'expense_id': row[0],
            'expense_date': row[1].strftime('%Y-%m-%d') if row[1] else '',
            'description': row[2] or '',
            'amount': float(row[3]) if row[3] else 0.0,
            'property_name': row[4] or '',
            'expense_type': 'General Expense',  # You might want to add this field to your database
            'submitted_date': row[1].strftime('%Y-%m-%d') if row[1] else ''
        })

    return expenses_waiting_approval


def get_expenses_waiting_payment(cursor):
    """Get expenses that are approved but not yet paid"""
    cursor.execute("""
        SELECT ae.act_expense_id, ae.act_expense_date, ae.act_expense_description,
               ae.act_expense_amount, p.prop_name
        FROM railway.act_expense ae
        JOIN railway.prop p ON ae.prop_id = p.prop_id
        WHERE ae.act_expense_approved = 'Yes'
        AND ae.act_expense_paid = 'No'
        ORDER BY ae.act_expense_date ASC
    """)

    expenses_data = cursor.fetchall()
    expenses_waiting_payment = []

    for row in expenses_data:
        expenses_waiting_payment.append({
            'expense_id': row[0],
            'expense_date': row[1].strftime('%Y-%m-%d') if row[1] else '',
            'description': row[2] or '',
            'amount': float(row[3]) if row[3] else 0.0,
            'property_name': row[4] or '',
            'expense_type': 'General Expense',  # You might want to add this field to your database
            'approved_date': row[1].strftime('%Y-%m-%d') if row[1] else ''  # Using expense date as approximation
        })

    return expenses_waiting_payment


def get_expiring_leases(cursor, today):
    """Active leases inside their own renewal window, still pending.

    DB-9, 2 Oct 2026 - AND A CORRECTION TO DB-8. Demetri, on Live: expiring
    leases are determined by the lease agreement and the tenant's Renewal
    Period, so the 90-day test must go and only leases inside their renewal
    period may appear - on the panel, in this tile, and in the modal the
    tile opens, with the count matching.

    DB-8 SAW TWO RULES AND PICKED THE WRONG ONE. The panel said 3 and this
    tile said 2; DB-8 moved the tile onto the panel's rule. The tile was
    right. This round moves everything onto the renewal period instead -
    through ONE function, because the alternative is a copied rule, and a
    copied rule is two rules again the first time either is edited.

    IT WAS NEVER TWO. Measured while fixing it: this tile used `period or
    0`, the report uses `period or 30`, and the Declined tile subtracted a
    further 30 days. Four answers, three of them on this screen.

    `cursor` IS UNUSED AND KEPT ON PURPOSE - the caller hands it to six
    helpers in a row and the other five still need it.
                                                  [test_renewal_window.py]
    """
    del cursor  # see the note above - deliberately unused
    from pages.services.portfolio_insights import renewal_due

    out = []
    for row in renewal_due(today=today, status='pending'):
        end = row['lease_end']
        out.append({
            'prop_name': row['prop_name'],
            'prop_country': row['prop_country'],
            'tenant_name': row['tenant_name'],
            # T2-4 - passed through from portfolio_insights, which
            # holds a model object and joins the two names there.
            'tenant_display_name': row.get('tenant_display_name')
            or row['tenant_name'],
            'lease_end_date': end.strftime('%Y-%m-%d') if end else '',
            'days_to_end': row['days_to_end'],
            'renewal_date': row['renewal_date'].strftime('%Y-%m-%d'),
            'renewal_status': row['renewal_status'],
        })
    return out


def get_declined_renewals(cursor, today):
    """Active leases inside their renewal window whose tenant has declined.

    DB-9, 2 Oct 2026. The SAME boundary as the tile above and the Lease
    Renewal Report - this used to subtract a further 30 days, so a declined
    renewal appeared a month before the matching pending one would have.
    Nothing recorded why; the Lease Renewal Report carries the other half of
    the answer in a comment, where the extra 30 days is struck out and
    labelled "the old notification".

    `cursor` IS UNUSED AND KEPT ON PURPOSE, as above.
                                                  [test_renewal_window.py]
    """
    del cursor  # see the note above - deliberately unused
    from pages.services.portfolio_insights import renewal_due

    return [{
        'prop_name': row['prop_name'],
        'prop_country': row['prop_country'],
        'tenant_name': row['tenant_name'],
        'tenant_display_name': row.get('tenant_display_name')
        or row['tenant_name'],                              # T2-4
        'lease_end_date': (row['lease_end'].strftime('%Y-%m-%d')
                           if row['lease_end'] else ''),
        'message': 'CURRENT TENANT NOT RENEWING LEASE - NEED NEW TENANT',
    } for row in renewal_due(today=today, status='declined')]


def _tenant_model():
    """The tenant model, imported late - .properties imports this module."""
    from pages.models import tenant
    return tenant


def get_overdue_invoices(cursor, today):
    """Get properties with overdue invoices"""
    cursor.execute("""
        SELECT prop.prop_name, prop.prop_country, tenant.tenant_name,
               tenant.tenant_2_name,
               tenant.tenant_payment_terms, tenant.tenant_rent,
               invoice.invoice_date, invoice.invoice_id, invoice.invoice_amount
        FROM railway.invoice
        JOIN railway.tenant ON invoice.tenant_id = tenant.tenant_id
        JOIN railway.prop ON tenant.prop_id = prop.prop_id
        WHERE invoice.invoice_paid = 'No'
        AND tenant.tenant_current = 'Yes'
        ORDER BY prop.prop_country ASC, prop.prop_name ASC, invoice.invoice_date ASC
    """)

    invoice_data = cursor.fetchall()

    # Create a flat list of overdue invoices instead of grouping
    overdue_invoices_list = []

    # ES-9, 26 Oct 2026 - THE COLUMNS WHERE THE SELECT PUTS THEM. T2-4 (24
    # Oct) added tenant.tenant_2_name to the SELECT at position 3 and left
    # these reads where they were: payment terms read the second tenant's
    # name, the invoice date read the RENT, and `invoice_date + timedelta`
    # raised int + timedelta - which get_notification_data swallowed by
    # returning ZERO FOR ALL SIX BOXES, whenever any current tenant had an
    # unpaid invoice. Found by his push gate, on his local data.
    # ES-9 - and the model the display name asks was never imported here,
    # so its line raised NameError the first time it was reached.
    tenant = _tenant_model()
    for row in invoice_data:
        prop_name = row[0]
        prop_country = row[1]
        tenant_name = row[2]
        tenant_2_name = row[3]
        payment_terms = int(row[4]) if row[4] else 0
        tenant_rent = row[5]
        invoice_date = row[6]
        invoice_id = row[7]
        # Effective billed amount: prefer the stored per-invoice amount (the
        # physical-invoice total, or rent + communal fees when Bill Communal
        # Fees is on) and fall back to bare rent only when nothing was stored.
        # Mirrors invoices.effective_amount and the daily report's COALESCE.
        invoice_amount = row[8]
        effective_amount = invoice_amount if invoice_amount is not None else tenant_rent

        # Calculate due date based on invoice date and payment terms
        due_date = invoice_date + timedelta(days=payment_terms)

        # Only include if invoice is overdue
        if due_date < today:
            # Calculate days overdue
            days_overdue = (today - due_date).days

            overdue_invoices_list.append({
                'prop_name': prop_name,
                'prop_country': prop_country,
                'tenant_name': tenant_name,
                # T2-4, 24 Oct 2026 - THIS ROW HAS NO MODEL OBJECT.
                # It is built from raw sql, so it asks the model's
                # staticmethod for the join rather than writing a
                # second one here. Two joins would be two separators.
                'tenant_display_name': tenant.joint_name(
                    tenant_name, tenant_2_name),
                'tenant_rent': effective_amount,
                'invoice_date': invoice_date.strftime('%Y-%m-%d'),
                'due_date': due_date.strftime('%Y-%m-%d'),
                'days_overdue': days_overdue,
                'invoice_id': invoice_id
            })

    return overdue_invoices_list