import mysql.connector
from django.conf import settings
from datetime import date, timedelta

def notification_count(request):
    """
    Context processor to add notification count to all templates
    """
    if not request.user.is_authenticated:
        return {'notification_count': 0}
    
    try:
        # Get the notification data
        notification_data = get_notification_summary()
        total_count = (
            notification_data.get('vacantProperties', 0) +
            notification_data.get('expiringLeases', 0) +
            notification_data.get('declinedRenewals', 0) +
            notification_data.get('overdueInvoices', 0) +
            notification_data.get('expensesWaitingApproval', 0) +
            notification_data.get('expensesWaitingPayment', 0)
        )
        return {'notification_count': total_count}
    except Exception as e:
        # Log the error if needed
        return {'notification_count': 0}

def get_notification_summary():
    """
    Get just the summary counts for notifications (optimized version)
    """
    mydb = mysql.connector.connect(
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        database=settings.DATABASES['default']['NAME'],
    )
    
    my_cursor = mydb.cursor()
    today = date.today()
    
    try:
        # Count vacant properties
        vacant_count = get_vacant_properties_count(my_cursor)
        
        # Count expiring leases
        expiring_count = get_expiring_leases_count(my_cursor, today)
        
        # Count declined renewals
        declined_count = get_declined_renewals_count(my_cursor, today)
        
        # Count overdue invoices
        overdue_count = get_overdue_invoices_count(my_cursor, today)
        
        # Count expenses waiting for approval
        approval_count = get_expenses_waiting_approval_count(my_cursor)
        
        # Count expenses waiting for payment
        payment_count = get_expenses_waiting_payment_count(my_cursor)
        
        return {
            'vacantProperties': vacant_count,
            'expiringLeases': expiring_count,
            'declinedRenewals': declined_count,
            'overdueInvoices': overdue_count,
            'expensesWaitingApproval': approval_count,
            'expensesWaitingPayment': payment_count
        }
        
    finally:
        if mydb.is_connected():
            my_cursor.close()
            mydb.close()

def get_vacant_properties_count(cursor):
    """Get count of vacant properties"""
    # Get properties with current tenants
    cursor.execute("""
        SELECT COUNT(DISTINCT prop.prop_id)
        FROM railway.tenant
        JOIN railway.prop ON prop.prop_id = tenant.prop_id
        WHERE tenant.tenant_current = 'Yes'
    """)
    occupied_count = cursor.fetchone()[0]
    
    # Get all active properties available for rent
    cursor.execute("""
        SELECT COUNT(*)
        FROM railway.prop
        WHERE prop.prop_status = 'Active'
        AND prop.prop_available_for_rent = 'Yes'
    """)
    total_active = cursor.fetchone()[0]
    
    return max(0, total_active - occupied_count)

def get_expiring_leases_count(cursor, today):
    """Get count of expiring leases"""
    cursor.execute("""
        SELECT COUNT(*)
        FROM railway.tenant
        WHERE tenant.tenant_current = 'Yes'
        AND COALESCE(tenant.tenant_renewal_status, 'pending') = 'pending'
        AND DATE_SUB(tenant.tenant_lease_end_date, INTERVAL tenant.tenant_renewal_period DAY) <= %s
    """, (today,))
    return cursor.fetchone()[0]

def get_declined_renewals_count(cursor, today):
    """Get count of declined renewals"""
    cursor.execute("""
        SELECT COUNT(*)
        FROM railway.tenant
        WHERE tenant.tenant_current = 'Yes'
        AND tenant.tenant_renewal_status = 'declined'
        AND DATE_SUB(DATE_SUB(tenant.tenant_lease_end_date, INTERVAL tenant.tenant_renewal_period DAY), INTERVAL 30 DAY) <= %s
    """, (today,))
    return cursor.fetchone()[0]

def get_overdue_invoices_count(cursor, today):
    """Get count of overdue invoices"""
    cursor.execute("""
        SELECT COUNT(*)
        FROM railway.invoice
        JOIN railway.tenant ON invoice.tenant_id = tenant.tenant_id
        WHERE invoice.invoice_paid = 'No'
        AND tenant.tenant_current = 'Yes'
        AND DATE_ADD(invoice.invoice_date, INTERVAL COALESCE(tenant.tenant_payment_terms, 0) DAY) < %s
    """, (today,))
    return cursor.fetchone()[0]

def get_expenses_waiting_approval_count(cursor):
    """Get count of expenses waiting for approval"""
    cursor.execute("""
        SELECT COUNT(*)
        FROM railway.act_expense
        WHERE act_expense_approved = 'No' 
        AND act_expense_paid = 'No'
    """)
    return cursor.fetchone()[0]

def get_expenses_waiting_payment_count(cursor):
    """Get count of expenses waiting for payment"""
    cursor.execute("""
        SELECT COUNT(*)
        FROM railway.act_expense
        WHERE act_expense_approved = 'Yes' 
        AND act_expense_paid = 'No'
    """)
    return cursor.fetchone()[0]

def user_preferences(request):
    """Make user menu preference available in all templates"""
    if request.user.is_authenticated:
        try:
            from pages.models import UserProfile
            profile = request.user.profile
            return {
                'menu_preference': profile.menu_preference or 'top',
            }
        except Exception:
            return {'menu_preference': 'top'}
    return {'menu_preference': 'top'}


# ---------------------------------------------------------------------------
# THE MAP PROVIDER. One definition; four templates consume it.
#
# Before this, each of the four pages that draw a map spelled the tile URL out
# itself, and map_view's comment records what that cost: it had drifted to
# CARTO, CARTO began gating those tiles behind a key, and CARTO does not fail
# without one - it returns tiles with API KEY REQUIRED printed into the image.
# The map drew, the pins landed, the console stayed clean, and nobody saw it.
# ---------------------------------------------------------------------------

# osm-carto is Geoapify's rendering of the classic OpenStreetMap style, so the
# map looks the way it looked before OpenStreetMap stopped serving it.
MAP_STYLE = 'osm-carto'

# 18 and not the 20 Geoapify will serve. 20 would be better for dropping a pin
# on one building, and that is a separate change: a round that moves two things
# cannot say which one fixed it.
MAP_MAX_ZOOM = 18

# The attribution is a LINK, not a line of text. Two of these four pages
# credited OpenStreetMap in plain prose, and an unlinked credit is one of the
# reasons the OSM wiki gives for blocking an application.
MAP_ATTRIBUTION = (
    'Powered by <a href="https://www.geoapify.com/">Geoapify</a> '
    '| &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap'
    '</a> contributors'
)

# format=json, not the default geojson, because it returns lat and lon on each
# result exactly as Nominatim did - so the pages that read the answer change by
# one word rather than by a shape.
_TILES = 'https://maps.geoapify.com/v1/tile/%s/{z}/{x}/{y}.png?apiKey=%s'
_GEOCODE = 'https://api.geoapify.com/v1/geocode/search?format=json&limit=1&apiKey=%s&text='


def map_provider(request):
    """Where the map gets its tiles, its words and its address lookup.

    Every value is EMPTY when no key is configured, and the templates treat
    empty as "say so". A missing key is a setting nobody has filled in; it
    should not look like a broken page.
    """
    from django.conf import settings as _settings
    key = (getattr(_settings, 'GEOAPIFY_KEY', '') or '').strip()
    return {
        'MAP_KEY_PRESENT': bool(key),
        'MAP_TILE_URL': (_TILES % (MAP_STYLE, key)) if key else '',
        'MAP_GEOCODE_URL': (_GEOCODE % key) if key else '',
        'MAP_ATTRIBUTION': MAP_ATTRIBUTION,
        'MAP_MAX_ZOOM': MAP_MAX_ZOOM,
    }
