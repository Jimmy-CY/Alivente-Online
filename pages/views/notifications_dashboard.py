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
            return JsonResponse(notification_data)
        except Exception as e:
            return JsonResponse({
                'error': f'Error loading notification data: {str(e)}'
            })
    else:
        # Regular page load - return template
        return render(request, 'notifications.html')


def get_notification_data():
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
    """Get leases that are expiring and pending renewal"""
    cursor.execute("""
        SELECT prop.prop_name, prop.prop_country, tenant.tenant_name,
               tenant.tenant_lease_end_date, tenant.tenant_renewal_period,
               tenant.tenant_renewal_status
        FROM railway.tenant
        JOIN railway.prop ON prop.prop_id = tenant.prop_id
        WHERE tenant.tenant_current = 'Yes'
        ORDER BY prop.prop_country ASC, prop.prop_name ASC
    """)
    tenant_rows = cursor.fetchall()

    expiring_leases = []

    for row in tenant_rows:
        prop_name = row[0]
        prop_country = row[1]
        tenant_name = row[2]
        lease_end_date = row[3]
        renewal_period = int(row[4]) if row[4] is not None else 0
        renewal_status = row[5] if row[5] else 'pending'

        # Skip tenants with no lease end date - we can't compute a renewal date
        if lease_end_date is None:
            continue

        renewal_date = lease_end_date - timedelta(days=renewal_period)
        # NOTE: no extra buffer here - alerts use the renewal date directly.
        # (get_declined_renewals subtracts an additional timedelta(days=30).)
        warning_date = renewal_date

        if today >= warning_date and renewal_status == 'pending':
            expiring_leases.append({
                'prop_name': prop_name,
                'prop_country': prop_country,
                'tenant_name': tenant_name,
                'lease_end_date': lease_end_date.strftime('%Y-%m-%d'),
                'renewal_date': renewal_date.strftime('%Y-%m-%d')
            })

    return expiring_leases


def get_declined_renewals(cursor, today):
    """Get renewals that have been declined"""
    cursor.execute("""
        SELECT prop.prop_name, prop.prop_country, tenant.tenant_name,
               tenant.tenant_lease_end_date, tenant.tenant_renewal_period,
               tenant.tenant_renewal_status
        FROM railway.tenant
        JOIN railway.prop ON prop.prop_id = tenant.prop_id
        WHERE tenant.tenant_current = 'Yes'
        ORDER BY prop.prop_country ASC, prop.prop_name ASC
    """)
    tenant_rows = cursor.fetchall()

    declined_renewals = []

    for row in tenant_rows:
        prop_name = row[0]
        prop_country = row[1]
        tenant_name = row[2]
        lease_end_date = row[3]
        renewal_period = int(row[4]) if row[4] is not None else 0
        renewal_status = row[5] if row[5] else 'pending'

        # Skip tenants with no lease end date - we can't compute a renewal date
        if lease_end_date is None:
            continue

        renewal_date = lease_end_date - timedelta(days=renewal_period)
        warning_date = renewal_date - timedelta(days=30)

        if today >= warning_date and renewal_status == 'declined':
            declined_renewals.append({
                'prop_name': prop_name,
                'prop_country': prop_country,
                'tenant_name': tenant_name,
                'lease_end_date': lease_end_date.strftime('%Y-%m-%d'),
                'message': 'CURRENT TENANT NOT RENEWING LEASE - NEED NEW TENANT'
            })

    return declined_renewals


def get_overdue_invoices(cursor, today):
    """Get properties with overdue invoices"""
    cursor.execute("""
        SELECT prop.prop_name, prop.prop_country, tenant.tenant_name,
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

    for row in invoice_data:
        prop_name = row[0]
        prop_country = row[1]
        tenant_name = row[2]
        payment_terms = int(row[3]) if row[3] else 0
        tenant_rent = row[4]
        invoice_date = row[5]
        invoice_id = row[6]
        # Effective billed amount: prefer the stored per-invoice amount (the
        # physical-invoice total, or rent + communal fees when Bill Communal
        # Fees is on) and fall back to bare rent only when nothing was stored.
        # Mirrors invoices.effective_amount and the daily report's COALESCE.
        invoice_amount = row[7]
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
                'tenant_rent': effective_amount,
                'invoice_date': invoice_date.strftime('%Y-%m-%d'),
                'due_date': due_date.strftime('%Y-%m-%d'),
                'days_overdue': days_overdue,
                'invoice_id': invoice_id
            })

    return overdue_invoices_list