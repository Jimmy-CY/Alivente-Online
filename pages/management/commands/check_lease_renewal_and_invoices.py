"""
Daily-cron management command: invoice creation + notifications.

Run nightly (also supports --force and --dry-run). In order it:
  1. Creates this month's invoices for active tenants that lack one
  2. Gathers vacant properties, expiring/declined lease renewals, and
     overdue invoices, then emails a consolidated property-management report
  3. Emails separate notifications for expiring passports/IDs (1st & 15th
     only, per workspace), new leases to upload, today's celebrations, and
     yesterday's issue comments

Email sending: most notifications build their MIME message inline and send
over SMTP directly; the property-management report goes through
_send_email_with_retry (generous timeout + backoff). Issue-comments
rendering/sending is delegated to pages.email_utils.send_issue_comments_email.
"""

import logging
import os
import smtplib
import socket
import sys
import time
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection, connections

from pages.email_utils import (
    ADMIN_USER_INITIALS,
    format_email_recipients_for_header,
    get_email_recipients,
    send_issue_comments_email,
)
from pages.models import CelebrationEvent, Contact, Passport, issues_details

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check lease renewals, vacant properties, outstanding invoices, passport expiries, and create new invoices if needed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without sending emails or creating invoices (for testing)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force run even if not scheduled time',
        )

    def handle(self, *args, **options):
        self.dry_run = options.get('dry_run', False)
        self.force_run = options.get('force', False)

        self.stdout.write('=== STARTING LEASE RENEWAL, INVOICE CHECK, PASSPORT CHECK, AND INVOICE CREATION ===')
        self.stdout.write(f'Current working directory: {os.getcwd()}')
        self.stdout.write(f'Python path: {sys.executable}')
        self.stdout.write(f'Dry run mode: {self.dry_run}')

        # Test environment variables
        email_password = os.environ.get('EMAIL_PASSWORD')
        if email_password:
            self.stdout.write('✅ EMAIL_PASSWORD environment variable found')
        else:
            self.stdout.write('❌ EMAIL_PASSWORD environment variable NOT found')
            if not self.dry_run:
                return

        # Test database connection using Django's connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write('✅ Database connection successful')
        except Exception as e:
            self.stdout.write(f'❌ Database connection failed: {e}')
            logger.error(f'Database connection failed: {e}')
            return

        self.stdout.write('Starting invoice creation, lease renewal, invoice checks, and passport expiry checks...')

        try:
            # Sync tenant Active/Inactive from the lease dates BEFORE anything
            # else, so invoices and the report use the correct current tenants.
            if self.dry_run:
                call_command('refresh_tenant_active', '--dry-run')
            else:
                call_command('refresh_tenant_active')
                
            # First, create invoices if needed
            created_invoices_count = self.create_invoices()

            # Prepare upcoming-month physical-invoice drafts + approval reminder.
            # (prepare has no --dry-run; skip it entirely on a dry run.)
            if not self.dry_run:
                try:
                    call_command('prepare_physical_invoices')
                except Exception as e:
                    self.stdout.write(f'\u26a0\ufe0f  prepare_physical_invoices failed: {e}')
                    logger.error(f'prepare_physical_invoices failed: {e}', exc_info=True)

            # Send approved physical invoices (numbers, emails PDF, links/stamps
            # the collection rows just created above). Runs AFTER create_invoices()
            # on purpose, so the collection rows exist to link.
            try:
                call_command('send_physical_invoices', dry_run=self.dry_run)
            except Exception as e:
                self.stdout.write(f'\u26a0\ufe0f  send_physical_invoices failed: {e}')
                logger.error(f'send_physical_invoices failed: {e}', exc_info=True)

            # Then get all the data with property details
            vacant_properties, expiring_leases, declined_renewals, overdue_invoices = self.get_all_property_details()

            # Check for expiring passports
            expiring_passports = self.get_expiring_passports()

            # Check for new leases that need to be uploaded
            new_leases_to_upload = self.get_new_leases_to_upload()

            # Check for today's celebrations
            todays_celebrations = self.get_todays_celebrations()

            vacant_count = len(vacant_properties)
            expiring_count = len(expiring_leases)
            declined_count = len(declined_renewals)
            overdue_count = len(overdue_invoices)
            passport_count = len(expiring_passports)
            new_lease_count = len(new_leases_to_upload)
            celebration_count = len(todays_celebrations)

            self.stdout.write(f'Invoices created today: {created_invoices_count}')
            self.stdout.write(f'Vacant properties: {vacant_count}')
            self.stdout.write(f'Expiring leases (pending): {expiring_count}')
            self.stdout.write(f'Declined renewals (need new tenants): {declined_count}')
            self.stdout.write(f'Overdue invoices: {overdue_count}')
            self.stdout.write(f'Expiring passports (within 6 months): {passport_count}')
            self.stdout.write(f'New leases to upload: {new_lease_count}')
            self.stdout.write(f'Celebrations today: {celebration_count}')

            # Check if action is needed for property management email
            if vacant_count > 0 or expiring_count > 0 or declined_count > 0 or overdue_count > 0 or created_invoices_count > 0:
                self.stdout.write('Action needed! Sending property management notification...')

                if self.dry_run:
                    self.stdout.write('DRY RUN: Would send property management email here')
                    result = True
                else:
                    result = self.run_notification_function(vacant_properties, expiring_leases, declined_renewals, overdue_invoices, created_invoices_count)

                self.stdout.write(f'Property management email function returned: {result}')
            else:
                self.stdout.write('No property management action needed')

            # Send separate passport expiry notification if needed
            if passport_count > 0:
                self.stdout.write('Expiring passports detected! Sending passport notification...')

                if self.dry_run:
                    self.stdout.write('DRY RUN: Would send passport expiry email here')
                    passport_result = True
                else:
                    passport_result = self.send_passport_expiry_notification(expiring_passports)

                self.stdout.write(f'Passport expiry email function returned: {passport_result}')
            else:
                self.stdout.write('No expiring passports found')

            # Send new lease upload reminder if needed
            if new_lease_count > 0:
                self.stdout.write('New leases need to be uploaded! Sending upload reminder...')

                if self.dry_run:
                    self.stdout.write('DRY RUN: Would send new lease upload reminder email here')
                    lease_upload_result = True
                else:
                    lease_upload_result = self.send_new_lease_upload_reminder(new_leases_to_upload)

                self.stdout.write(f'New lease upload reminder email function returned: {lease_upload_result}')
            else:
                self.stdout.write('No new lease uploads needed')

            # Send celebration notification if needed
            if celebration_count > 0:
                self.stdout.write('Celebrations today! Sending celebration notification...')

                if self.dry_run:
                    self.stdout.write('DRY RUN: Would send celebration notification email here')
                    celebration_result = True
                else:
                    celebration_result = self.send_celebration_notification(todays_celebrations)

                self.stdout.write(f'Celebration notification email function returned: {celebration_result}')
            else:
                self.stdout.write('No celebrations today')

            # Check for issue comments captured yesterday
            issue_comments, issue_comments_date = self.get_yesterdays_issue_comments()
            issue_comment_count = len(issue_comments)
            self.stdout.write(f'Issue comments from {issue_comments_date}: {issue_comment_count}')

            # Send issue comments notification if needed
            if issue_comment_count > 0:
                self.stdout.write('Issue comments from yesterday found! Sending issue comments notification...')

                if self.dry_run:
                    self.stdout.write('DRY RUN: Would send issue comments email here')
                    issue_comments_result = True
                else:
                    issue_comments_result = self.send_issue_comments_notification(issue_comments, issue_comments_date)

                self.stdout.write(f'Issue comments email function returned: {issue_comments_result}')
            else:
                self.stdout.write('No issue comments from yesterday')

        except Exception as e:
            self.stdout.write(f'❌ Error during execution: {e}')
            logger.error(f'Error during command execution: {e}', exc_info=True)
            raise
        finally:
            # Clean up database connections
            try:
                connections.close_all()
            except Exception as e:
                logger.warning(f'Error closing database connections: {e}')

        self.stdout.write('=== LEASE RENEWAL, INVOICE CHECK, PASSPORT CHECK, AND INVOICE CREATION COMPLETED ===')

    def _collection_amount(self, rent, levies, bill_levies, physical_invoice):
        """Stored collection amount for a tenant's monthly invoice.

        rent (+levies when Bill Communal Fees is on) (+19% VAT on RENT ONLY
        when Generate Physical Invoice is on -- communal is never VAT-rated),
        so the amount equals the physical invoice total for those tenants.
        VAT follows settings.PHYSICAL_INVOICE_VAT_RATE (default 0.19), the same
        source the physical invoice uses.

        NOTE: this arithmetic equals the physical invoice total for the seeded
        rent/communal lines. Once the send cron + water line land, that cron
        overwrites physical-invoice tenants' amounts with the exact pi.total
        (which also covers water and any manual draft edits).
        """
        vat_rate = Decimal(str(getattr(settings, "PHYSICAL_INVOICE_VAT_RATE", "0.19")))
        rent = Decimal(rent or 0)
        levies = Decimal(levies or 0)
        amount = rent
        if bill_levies:
            amount += levies
        if physical_invoice:
            amount += rent * vat_rate
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def create_invoices(self):
        """Create invoices for current month if they don't already exist"""
        today = date.today()
        months = ('Month','January','February','March','April','May','June',
                 'July','August','September','October','November','December')

        current_month = months[today.month]
        current_year = today.year

        self.stdout.write(f'Checking invoice creation for {current_month} {current_year}')

        try:
            with connection.cursor() as cursor:
                # Get all current active tenants
                cursor.execute("""
                    SELECT prop.prop_id, prop.prop_name, prop.prop_country, prop.prop_status, tenant.tenant_id,
                           tenant.tenant_rent, tenant.tenant_levies,
                           tenant.tenant_bill_levies, tenant.tenant_physical_invoice_required
                    FROM railway.tenant
                    JOIN railway.prop ON prop.prop_id = tenant.prop_id
                    WHERE tenant.tenant_current = 'Yes' AND prop.prop_status = 'Active'
                    ORDER BY tenant.tenant_id ASC
                """)
                tenants = cursor.fetchall()

                # Get ALL invoices for the current month/year (paid or unpaid)
                cursor.execute("""
                    SELECT invoice.invoice_id, invoice.tenant_id, invoice.invoice_date, invoice.invoice_paid
                    FROM railway.invoice
                    WHERE MONTH(invoice.invoice_date) = %s AND YEAR(invoice.invoice_date) = %s
                    ORDER BY invoice.invoice_date ASC
                """, [today.month, today.year])
                existing_invoices = cursor.fetchall()

                # Determine new invoice date (1st of current month)
                months_mapping = (('January','01'),('February','02'),('March','03'),('April','04'),
                                ('May','05'),('June','06'),('July','07'),('August','08'),
                                ('September','09'),('October','10'),('November','11'),('December','12'))

                for name, number in months_mapping:
                    if name == current_month:
                        temp_date = f'01-{number}-{current_year}'
                        new_invoice_date = datetime.strptime(temp_date, '%d-%m-%Y').date()
                        break

                created_count = 0

                # Create new invoices for tenants who don't have one for this month
                for tenant in tenants:
                    tenant_id = tenant[4]
                    # Check if invoice already exists for this tenant and date
                    already_exists = any(inv[1] == tenant_id and inv[2] == new_invoice_date for inv in existing_invoices)

                    if not already_exists:
                        # rent (+levies if billed) (+VAT on rent if physical invoice)
                        invoice_amount = self._collection_amount(
                            tenant[5], tenant[6], bool(tenant[7]), bool(tenant[8])
                        )
                        if not self.dry_run:
                            cursor.execute(
                                "INSERT INTO invoice (tenant_id, invoice_date, invoice_paid, invoice_amount) VALUES (%s, %s, %s, %s)",
                                [tenant_id, new_invoice_date, 'No', invoice_amount]
                            )
                        created_count += 1

                if created_count > 0:
                    if self.dry_run:
                        self.stdout.write(f'DRY RUN: Would create {created_count} new invoices for {new_invoice_date}')
                    else:
                        # Django handles the commit automatically for management commands
                        self.stdout.write(f'✅ Created {created_count} new invoices for {new_invoice_date}')
                else:
                    self.stdout.write(f'ℹ️  No new invoices created - they already exist for {new_invoice_date}')

                return created_count

        except Exception as e:
            self.stdout.write(f'❌ Error creating invoices: {e}')
            logger.error(f'Error creating invoices: {e}', exc_info=True)
            return 0

    def get_all_property_details(self):
        """Get detailed property, lease, and invoice information with renewal status logic"""
        today = date.today()

        try:
            with connection.cursor() as cursor:
                # Get current tenants with detailed lease info INCLUDING renewal status
                cursor.execute("""
                    SELECT prop.prop_name, prop.prop_country, tenant.tenant_name,
                           tenant.tenant_lease_end_date, tenant.tenant_renewal_period,
                           tenant.tenant_payment_terms, tenant.tenant_renewal_status
                    FROM railway.tenant
                    JOIN railway.prop ON prop.prop_id = tenant.prop_id
                    WHERE tenant.tenant_current = 'Yes'
                    ORDER BY prop.prop_country ASC, prop.prop_name ASC
                """)
                tenant_rows = cursor.fetchall()

                # Get properties with current tenants (just names)
                cursor.execute("""
                    SELECT prop.prop_name
                    FROM railway.tenant
                    JOIN railway.prop ON prop.prop_id = tenant.prop_id
                    WHERE tenant.tenant_current = 'Yes'
                """)
                prop_active_tenant = [row[0] for row in cursor.fetchall()]

                # Get all active properties available for rent with details
                cursor.execute("""
                    SELECT prop.prop_name, prop.prop_country
                    FROM railway.prop
                    WHERE prop.prop_status = 'Active'
                    AND prop.prop_available_for_rent = 'Yes'
                    ORDER BY prop.prop_country ASC, prop.prop_name ASC
                """)
                active_properties_data = cursor.fetchall()

                # Process leases with renewal status logic
                expiring_leases = []
                declined_renewals = []

                for row in tenant_rows:
                    prop_name = row[0]
                    prop_country = row[1]
                    tenant_name = row[2]
                    lease_end_date = row[3]
                    renewal_period = int(row[4]) if row[4] else 30  # Default to 30 if None
                    renewal_status = row[6] if row[6] else 'pending'  # Default to pending if None

                    renewal_date = lease_end_date - timedelta(days=renewal_period)
                    warning_date = renewal_date

                    if today >= warning_date:
                        if renewal_status == 'pending':
                            # Normal renewal case - add to expiring leases
                            expiring_leases.append({
                                'prop_name': prop_name,
                                'prop_country': prop_country,
                                'tenant_name': tenant_name,
                                'lease_end_date': lease_end_date.strftime('%Y-%m-%d'),
                                'renewal_date': renewal_date.strftime('%Y-%m-%d')
                            })
                        elif renewal_status == 'declined':
                            # Tenant declined renewal - add to declined renewals
                            declined_renewals.append({
                                'prop_name': prop_name,
                                'prop_country': prop_country,
                                'tenant_name': tenant_name,
                                'lease_end_date': lease_end_date.strftime('%Y-%m-%d'),
                                'message': 'CURRENT TENANT NOT RENEWING LEASE - NEED NEW TENANT'
                            })
                        # If renewal_status == 'new_lease_signed', do nothing (exclude from both lists)

                # Find vacant properties with details
                vacant_properties = []
                for prop_data in active_properties_data:
                    prop_name = prop_data[0]
                    prop_country = prop_data[1]

                    if prop_name not in prop_active_tenant:
                        vacant_properties.append({
                            'prop_name': prop_name,
                            'prop_country': prop_country
                        })

                # Get outstanding invoices
                overdue_invoices = self.get_outstanding_invoices(cursor, today)

                return vacant_properties, expiring_leases, declined_renewals, overdue_invoices

        except Exception as e:
            self.stdout.write(f'❌ Error getting property details: {e}')
            logger.error(f'Error getting property details: {e}', exc_info=True)
            return [], [], [], []

    def get_outstanding_invoices(self, cursor, today):
        """Get properties with overdue invoices only"""
        try:
            # Get properties with overdue invoices using proper JOIN based on your models
            cursor.execute("""
                SELECT DISTINCT prop.prop_name, prop.prop_country, tenant.tenant_name,
                       tenant.tenant_payment_terms, tenant.tenant_rent,
                       invoice.invoice_date,
                       COALESCE(invoice.invoice_amount, tenant.tenant_rent) AS invoice_amount
                FROM railway.invoice
                JOIN railway.tenant ON invoice.tenant_id = tenant.tenant_id
                JOIN railway.prop ON tenant.prop_id = prop.prop_id
                WHERE invoice.invoice_paid = 'No'
                AND tenant.tenant_current = 'Yes'
                ORDER BY prop.prop_country ASC, prop.prop_name ASC, invoice.invoice_date ASC
            """)

            invoice_data = cursor.fetchall()

            # Group invoices by property/tenant, but only include overdue ones
            properties_dict = {}

            for row in invoice_data:
                prop_name = row[0]
                prop_country = row[1]
                tenant_name = row[2]
                payment_terms = int(row[3]) if row[3] else 0
                tenant_rent = row[4]
                invoice_date = row[5]
                invoice_amount = row[6]

                # Calculate due date based on invoice date and payment terms
                due_date = invoice_date + timedelta(days=payment_terms)

                # Only include if invoice is overdue
                if due_date < today:
                    # Calculate days overdue
                    days_overdue = (today - due_date).days

                    # Create unique key for each property/tenant combination
                    property_key = f"{prop_name}_{tenant_name}"

                    if property_key not in properties_dict:
                        properties_dict[property_key] = {
                            'prop_name': prop_name,
                            'prop_country': prop_country,
                            'tenant_name': tenant_name,
                            'tenant_rent': tenant_rent,
                            'payment_terms': payment_terms,
                            'invoices': []
                        }

                    properties_dict[property_key]['invoices'].append({
                        'invoice_date': invoice_date.strftime('%Y-%m-%d'),
                        'due_date': due_date.strftime('%Y-%m-%d'),
                        'days_overdue': days_overdue,
                        'amount': invoice_amount,
                        'overdue': True
                    })

            # Convert dictionary to list
            properties_with_overdue_invoices = list(properties_dict.values())

            return properties_with_overdue_invoices

        except Exception as e:
            self.stdout.write(f'❌ Error getting outstanding invoices: {e}')
            logger.error(f'Error getting outstanding invoices: {e}', exc_info=True)
            return []

    def get_expiring_passports(self):
        """Get passports expiring within 6 months OR already expired (only active documents with expiry dates)"""
        today = date.today()
        six_months_from_now = today + timedelta(days=180)

        try:
            # Query passports expiring within 6 months OR already expired
            # Only include documents with:
            # 1. An expiry date (not blank)
            # 2. Status = 'active'
            # 3. Expiry date within 6 months or already expired
            expiring_passports = Passport.objects.filter(
                expiry_date__isnull=False,  # Must have an expiry date
                status='active',             # Must be active status
                expiry_date__lte=six_months_from_now  # Expiring within 6 months or already expired
            ).order_by('expiry_date')

            passport_list = []
            for passport in expiring_passports:
                days_until_expiry = (passport.expiry_date - today).days

                passport_list.append({
                    'holder_name': passport.holder_name,
                    'document_type': passport.get_document_type_display(),
                    'document_number': passport.document_number,
                    'country_of_issue': passport.country_of_issue,
                    'expiry_date': passport.expiry_date.strftime('%Y-%m-%d'),
                    'days_until_expiry': days_until_expiry,
                    'already_expired': passport.expiry_date < today,
                    'workspace_id': passport.workspace_id,
                })

            self.stdout.write(f'Found {len(passport_list)} active passports with expiry dates expiring within 6 months (or already expired)')
            return passport_list

        except Exception as e:
            self.stdout.write(f'❌ Error getting expiring passports: {e}')
            logger.error(f'Error getting expiring passports: {e}', exc_info=True)
            return []

    def get_new_leases_to_upload(self):
        """Get tenants with renewal status 'new_lease_signed' where lease end date is today"""
        today = date.today()

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT prop.prop_name, prop.prop_country, tenant.tenant_name,
                           tenant.tenant_lease_end_date
                    FROM railway.tenant
                    JOIN railway.prop ON prop.prop_id = tenant.prop_id
                    WHERE tenant.tenant_current = 'Yes'
                    AND tenant.tenant_renewal_status = 'new_lease_signed'
                    AND tenant.tenant_lease_end_date = %s
                    ORDER BY prop.prop_country ASC, prop.prop_name ASC
                """, [today])

                lease_rows = cursor.fetchall()

                leases_to_upload = []
                for row in lease_rows:
                    leases_to_upload.append({
                        'prop_name': row[0],
                        'prop_country': row[1],
                        'tenant_name': row[2],
                        'lease_end_date': row[3].strftime('%Y-%m-%d')
                    })

                self.stdout.write(f'Found {len(leases_to_upload)} new lease(s) that need to be uploaded today')
                return leases_to_upload

        except Exception as e:
            self.stdout.write(f'❌ Error getting new leases to upload: {e}')
            logger.error(f'Error getting new leases to upload: {e}', exc_info=True)
            return []

    def get_todays_celebrations(self):
        """Get celebrations occurring today - returns dict with events grouped by recipient"""
        today = date.today()

        try:
            # Get all contacts with their events
            contacts = Contact.objects.all().prefetch_related('celebration_events')

            # Group celebrations by recipient email
            celebrations_by_recipient = {}

            for contact in contacts:
                for event in contact.celebration_events.all():
                    next_date = event.get_next_occurrence()
                    if next_date and next_date == today:
                        # Calculate age for birthdays (if birth year is known)
                        age = None
                        if event.event_type == 'birthday' and event.event_date.year != 1900:
                            age = today.year - event.event_date.year

                        celebration_data = {
                            'contact_name': contact.name,
                            'relationship': contact.get_relationship_display(),
                            'event_type': event.get_event_type_display(),
                            'age': age,
                            'notes': event.notes if event.notes else None
                        }

                        # Get list of emails who should be notified for this specific event
                        notify_emails = event.get_notification_emails()

                        # Add this celebration to each recipient's list
                        for email in notify_emails:
                            if email not in celebrations_by_recipient:
                                celebrations_by_recipient[email] = []
                            celebrations_by_recipient[email].append(celebration_data)

            self.stdout.write(f'Found celebrations for {len(celebrations_by_recipient)} recipient(s)')
            return celebrations_by_recipient

        except Exception as e:
            self.stdout.write(f'❌ Error getting today\'s celebrations: {e}')
            logger.error(f'Error getting today\'s celebrations: {e}', exc_info=True)
            return {}

    def send_celebration_notification(self, celebrations_by_recipient):
        """Send email notification for today's celebrations - personalized per recipient"""
        smtp_object = None

        if not celebrations_by_recipient:
            self.stdout.write('No celebrations today')
            return True

        # Helper function for ordinal suffix
        def get_ordinal_suffix(day):
            """Return ordinal suffix for a day (1st, 2nd, 3rd, etc.)"""
            if 10 <= day % 100 <= 20:
                suffix = 'th'
            else:
                suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
            return suffix

        try:
            self.stdout.write('=== SENDING CELEBRATION NOTIFICATIONS ===')

            # Get email settings from environment variables
            email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
            email_port = int(os.environ.get('EMAIL_PORT', 465))
            email_user = os.environ.get('EMAIL_USER', 'demetrimanias@gmail.com')
            email_password = os.environ.get('EMAIL_PASSWORD')
            email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
            email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'

            if not email_password:
                self.stdout.write('❌ EMAIL_PASSWORD environment variable not set')
                return False

            # SMTP setup (reuse connection for all emails)
            if email_use_ssl:
                smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=60)
            else:
                smtp_object = smtplib.SMTP(email_host, email_port, timeout=60)
                smtp_object.ehlo()
                if email_use_tls:
                    smtp_object.starttls()

            smtp_object.login(email_user, email_password)

            today = date.today()
            formatted_date = f"{today.day}{get_ordinal_suffix(today.day)} {today.strftime('%B %Y')}"

            # Send personalized email to each recipient
            for recipient_email, todays_celebrations in celebrations_by_recipient.items():
                celebration_count = len(todays_celebrations)

                self.stdout.write(f'📧 Sending {celebration_count} celebration(s) to {recipient_email}')

                # Create message
                msg = MIMEMultipart('alternative')
                msg['From'] = email_user
                msg['To'] = recipient_email

                # Determine correct grammar
                celebration_word = "Celebration" if celebration_count == 1 else "Celebrations"

                msg['Subject'] = f"🎉 {celebration_word} Today - {formatted_date} ({celebration_count})"

                # Build HTML email body
                html_body = f"""
                <html>
                <head>
                <style>
                p {{ margin: 0; padding: 0; }}
                ul {{ margin: 0; padding: 0; padding-left: 20px; }}
                li {{ margin: 0; padding: 0; margin-bottom: 15px; }}
                .celebration {{ color: #667eea; font-weight: bold; }}
                .birthday {{ color: #28a745; }}
                .nameday {{ color: #6f42c1; }}
                .anniversary {{ color: #17a2b8; }}
                .custom {{ color: #fd7e14; }}
                </style>
                </head>
                <body>
                    <p>Hey, Hey !!!</p>
                    <br>
                    <p><b><u class="celebration">TODAY'S {celebration_word.upper()}:</u></b></p>
                    <p>{"The person below has a" if celebration_count == 1 else "The people below have a"} special day today, {formatted_date}:</p>
                    <br>
                    <ul>"""

                for celebration in todays_celebrations:
                    event_type_lower = celebration['event_type'].lower()

                    # Determine CSS class for color coding
                    if 'birthday' in event_type_lower:
                        css_class = 'birthday'
                        icon = '🎂'
                    elif 'nameday' in event_type_lower:
                        css_class = 'nameday'
                        icon = '🎊'
                    elif 'anniversary' in event_type_lower:
                        css_class = 'anniversary'
                        icon = '💐'
                    else:
                        css_class = 'custom'
                        icon = '🎉'

                    html_body += f"""
                    <li>
                        <span class="{css_class}"><b>{icon} {celebration['contact_name']}</b></span> - {celebration['event_type']}"""

                    if celebration['age']:
                        html_body += f" (Turning {celebration['age']})"

                    html_body += f" ({celebration['relationship']})"

                    if celebration['notes']:
                        html_body += f"<br><i>Note: {celebration['notes']}</i>"

                    html_body += "</li>"

                html_body += """
                    </ul>
                    <br>
                    <p><b>REMINDER:</b></p>
                    <p>Don't forget to reach out and wish them a wonderful day!</p>
                </body>
                </html>
                """

                # Create plain text version
                text_body = f"""Hey, Hey !!!

    TODAY'S {celebration_word.upper()}:

    {"The person below has a" if celebration_count == 1 else "The people below have a"} special day today, {formatted_date}:

    """

                for celebration in todays_celebrations:
                    event_type_lower = celebration['event_type'].lower()

                    # Determine icon
                    if 'birthday' in event_type_lower:
                        icon = '🎂'
                    elif 'nameday' in event_type_lower:
                        icon = '🎊'
                    elif 'anniversary' in event_type_lower:
                        icon = '💐'
                    else:
                        icon = '🎉'

                    text_body += f"\n- {icon} {celebration['contact_name']} - {celebration['event_type']}"

                    if celebration['age']:
                        text_body += f" (Turning {celebration['age']})"

                    text_body += f" ({celebration['relationship']})"

                    if celebration['notes']:
                        text_body += f"\n  Note: {celebration['notes']}"

                    text_body += "\n"

                text_body += """
    REMINDER:
    Don't forget to reach out and wish them a wonderful day!"""

                # Attach both HTML and plain text versions
                part1 = MIMEText(text_body, 'plain')
                part2 = MIMEText(html_body, 'html')

                msg.attach(part1)
                msg.attach(part2)

                # Send email to this recipient
                text = msg.as_string()
                smtp_object.sendmail(email_user, [recipient_email], text)

                self.stdout.write(f'✅ Celebration email sent to {recipient_email}')

            logger.info(f'Celebration notifications sent to {len(celebrations_by_recipient)} recipient(s)')
            return True

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP Authentication Error: {e}"
            logger.error(error_msg)
            self.stdout.write(f'❌ {error_msg}')
            return False
        except smtplib.SMTPException as e:
            error_msg = f"SMTP Error: {e}"
            logger.error(error_msg)
            self.stdout.write(f'❌ {error_msg}')
            return False
        except Exception as e:
            error_msg = f"Error sending celebration notification email: {e}"
            logger.error(error_msg, exc_info=True)
            self.stdout.write(f'❌ {error_msg}')
            return False
        finally:
            if smtp_object:
                try:
                    smtp_object.quit()
                except Exception:
                    pass

    def send_issue_comments_notification(self, comments, report_date):
        """Send daily email with previous day's issue comments. Delegates rendering to email_utils."""
        if not comments:
            self.stdout.write('No issue comments from yesterday')
            return True

        formatted_date = report_date.strftime('%Y/%m/%d')
        comment_count = len(comments)
        comment_word = "Comment" if comment_count == 1 else "Comments"

        recipients = get_email_recipients('issue_comments_daily')
        self.stdout.write('=== SENDING ISSUE COMMENTS NOTIFICATION ===')
        self.stdout.write(f'Issue Comments Email TO: {", ".join(recipients["to"])}')
        if recipients['cc']:
            self.stdout.write(f'Issue Comments Email CC: {", ".join(recipients["cc"])}')

        ok = send_issue_comments_email(
            comments=comments,
            subject=f"Issue {comment_word} - {formatted_date}",
            header_label=f"DAILY ISSUE COMMENTS REPORT - {formatted_date}",
            intro_text=(f"The following {comment_count} {comment_word.lower()} "
                        f"{'was' if comment_count == 1 else 'were'} added to issues yesterday:"),
            recipients=recipients,
        )

        if ok:
            self.stdout.write('Issue comments notification email sent successfully!')
            logger.info('Issue comments notification email sent successfully')
        else:
            self.stdout.write('Failed to send issue comments notification email')

        return ok

    def send_new_lease_upload_reminder(self, new_leases_to_upload):
        """Send email reminder to upload new lease agreements"""
        smtp_object = None
        lease_count = len(new_leases_to_upload)

        if lease_count == 0:
            self.stdout.write('No new leases to upload')
            return True

        try:
            self.stdout.write('=== SENDING NEW LEASE UPLOAD REMINDER ===')

            # Get email settings from environment variables
            email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
            email_port = int(os.environ.get('EMAIL_PORT', 465))
            email_user = os.environ.get('EMAIL_USER', 'demetrimanias@gmail.com')
            email_password = os.environ.get('EMAIL_PASSWORD')
            email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
            email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'

            # Use the standard email recipients utility
            recipients = get_email_recipients('new_lease_upload')

            # DEBUG: Show who will receive the email
            self.stdout.write(f'📧 New Lease Upload Email TO: {", ".join(recipients["to"])}')
            if recipients['cc']:
                self.stdout.write(f'📧 New Lease Upload Email CC: {", ".join(recipients["cc"])}')

            if not email_password:
                self.stdout.write('❌ EMAIL_PASSWORD environment variable not set')
                return False

            # Create message
            # Get recipients with TO/CC split
            recipients = get_email_recipients('new_lease_upload')

            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = email_user
            msg['To'] = format_email_recipients_for_header(recipients['to'])
            if recipients['cc']:
                msg['Cc'] = format_email_recipients_for_header(recipients['cc'])

            # Determine correct grammar
            lease_word = "Lease" if lease_count == 1 else "Leases"
            agreement_word = "Agreement" if lease_count == 1 else "Agreements"

            msg['Subject'] = f"URGENT: Upload New {lease_word} {agreement_word} ({lease_count})"

            # Build HTML email body
            html_body = f"""
            <html>
            <head>
            <style>
            p {{ margin: 0; padding: 0; }}
            ul {{ margin: 0; padding: 0; padding-left: 20px; }}
            li {{ margin: 0; padding: 0; margin-bottom: 15px; }}
            .urgent {{ color: #cc0000; font-weight: bold; }}
            </style>
            </head>
            <body>
                <p>Dear User,</p>
                <br>
                <p><b><u class="urgent">NEW LEASE AGREEMENT UPLOAD REQUIRED:</u></b></p>
                <p>The following {"lease has" if lease_count == 1 else "leases have"} ended today and {"a new lease agreement needs" if lease_count == 1 else "new lease agreements need"} to be uploaded to the system:</p>
                <br>
                <ul>"""

            for lease in new_leases_to_upload:
                html_body += f"""
                <li>
                    <b>{lease['prop_name']} ({lease['prop_country']})</b><br>
                    Tenant: {lease['tenant_name']}<br>
                    Previous Lease End Date: {lease['lease_end_date']}<br>
                    <span class="urgent">⚠️ NEW LEASE AGREEMENT MUST BE UPLOADED TODAY</span>
                </li>"""

            html_body += """
                </ul>
                <br>
                <p><b>ACTION REQUIRED:</b></p>
                <p>Please log into the Alivente Online System at <a href="https://alivente.online">alivente.online</a> and upload the new lease agreement document(s) immediately.</p>
                <br>
                <p><b>Steps to Upload:</b></p>
                <ol>
                    <li>Navigate to the Tenants section</li>
                    <li>Find the tenant listed above</li>
                    <li>Click on "Edit Tenant"</li>
                    <li>Update the Lease Start Date, Lease End Date, Deposit, Rental and Renewal Status</li>            
                    <li>Save the changes</li>
                    <li>Upload the new lease agreement in the "Administration --> Manage Lease Agreements" module</li>
                </ol>
                <br>
                <p>Best regards,<br>
                Alivente Property Management System<br>
                Automated Lease Management</p>
            </body>
            </html>
            """

            # Create plain text version
            text_body = f"""Dear User,

NEW LEASE AGREEMENT UPLOAD REQUIRED:

The following {"lease has" if lease_count == 1 else "leases have"} ended today and {"a new lease agreement needs" if lease_count == 1 else "new lease agreements need"} to be uploaded to the system:

"""

            for lease in new_leases_to_upload:
                text_body += f"""
- {lease['prop_name']} ({lease['prop_country']})
  Tenant: {lease['tenant_name']}
  Previous Lease End Date: {lease['lease_end_date']}
  ⚠️ NEW LEASE AGREEMENT MUST BE UPLOADED TODAY

"""

            text_body += """ACTION REQUIRED:
Please log into the Alivente Online System at alivente.online and upload the new lease agreement document(s) immediately.

Steps to Upload:
1. Navigate to the Tenants section
2. Find the tenant listed above
3. Click on "Edit Tenant"
4. Update the Lease Start Date, Lease End Date, Deposit, Rental and Renewal Status
5. Save the changes
6. Upload the new lease agreement in the "Administration --> Manage Lease Agreements" module

Best regards,
Alivente Property Management System
Automated Lease Management"""

            # Attach both HTML and plain text versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')

            msg.attach(part1)
            msg.attach(part2)

            # SMTP setup
            if email_use_ssl:
                smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=60)
            else:
                smtp_object = smtplib.SMTP(email_host, email_port, timeout=60)
                smtp_object.ehlo()
                if email_use_tls:
                    smtp_object.starttls()

            smtp_object.login(email_user, email_password)

            # Send email
            text = msg.as_string()
            smtp_object.sendmail(email_user, recipients['all'], text)

            self.stdout.write('✅ New lease upload reminder email sent successfully!')
            logger.info('New lease upload reminder email sent successfully')
            return True

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP Authentication Error: {e}"
            logger.error(error_msg)
            self.stdout.write(f'❌ {error_msg}')
            return False
        except smtplib.SMTPException as e:
            error_msg = f"SMTP Error: {e}"
            logger.error(error_msg)
            self.stdout.write(f'❌ {error_msg}')
            return False
        except Exception as e:
            error_msg = f"Error sending new lease upload reminder email: {e}"
            logger.error(error_msg, exc_info=True)
            self.stdout.write(f'❌ {error_msg}')
            return False
        finally:
            if smtp_object:
                try:
                    smtp_object.quit()
                except Exception:
                    pass

    def send_passport_expiry_notification(self, expiring_passports):
        """Send passport expiry notifications, one email per workspace.

        Workspace-aware (Phase 4.5): groups expiring passports by their workspace
        and sends each workspace's documents only to that workspace's configured
        recipients. Workspaces with no recipients configured are skipped silently
        — there's no global fallback for personal notifications, because that
        would leak one household's expiry dates to another household's inboxes.
        """
        from collections import defaultdict
        from pages.models import Workspace

        passport_count = len(expiring_passports)

        if passport_count == 0:
            self.stdout.write('No expiring passports to notify about')
            return True

        # Only on 1st or 15th of the month.
        today = date.today()
        if today.day not in [1, 15]:
            self.stdout.write(
                f'📅 Passport notification skipped - only sent on 1st or 15th of month '
                f'(Today is {today.day}th)'
            )
            self.stdout.write(
                f'   Found {passport_count} expiring passport(s), but no email will be sent today'
            )
            return True

        self.stdout.write('=== SENDING PASSPORT EXPIRY NOTIFICATIONS (per workspace) ===')
        self.stdout.write(f'📅 Today is the {today.day}th - sending workspace-scoped notifications')

        # Group by workspace_id
        by_workspace_id = defaultdict(list)
        orphaned = []
        for p in expiring_passports:
            if p.get('workspace_id'):
                by_workspace_id[p['workspace_id']].append(p)
            else:
                orphaned.append(p)

        if orphaned:
            self.stdout.write(
                f'  ⚠️  {len(orphaned)} passport(s) have no workspace assigned — these will be skipped. '
                f'Backfill manually if needed.'
            )

        workspaces_notified = 0
        workspaces_skipped = 0
        overall_ok = True

        for workspace_id, passports in by_workspace_id.items():
            try:
                workspace = Workspace.objects.get(pk=workspace_id)
            except Workspace.DoesNotExist:
                self.stdout.write(f'  ⚠️  Orphan workspace_id={workspace_id} on passport — skipping')
                continue

            recipients = get_email_recipients('document_expiry', workspace=workspace)
            if not recipients['all']:
                self.stdout.write(
                    f'  ⏭️  Workspace "{workspace.name}": no recipients configured — '
                    f'skipping {len(passports)} passport(s)'
                )
                workspaces_skipped += 1
                continue

            self.stdout.write(
                f'  📧 Workspace "{workspace.name}": sending {len(passports)} passport(s)'
            )
            self.stdout.write(f'     TO: {", ".join(recipients["to"])}')
            if recipients['cc']:
                self.stdout.write(f'     CC: {", ".join(recipients["cc"])}')

            ok = self._send_passport_expiry_email_for_workspace(workspace, passports, recipients)
            if ok:
                workspaces_notified += 1
            else:
                overall_ok = False

        self.stdout.write(
            f'Passport notifications complete: {workspaces_notified} sent, '
            f'{workspaces_skipped} skipped (no recipients)'
        )
        return overall_ok

    def _send_passport_expiry_email_for_workspace(self, workspace, passports, recipients):
        """Build and send one passport-expiry email for a single workspace."""
        smtp_object = None
        passport_count = len(passports)

        try:
            email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
            email_port = int(os.environ.get('EMAIL_PORT', 465))
            email_user = os.environ.get('EMAIL_USER', 'demetrimanias@gmail.com')
            email_password = os.environ.get('EMAIL_PASSWORD')
            email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
            email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'

            if not email_password:
                self.stdout.write('❌ EMAIL_PASSWORD environment variable not set')
                return False

            msg = MIMEMultipart('alternative')
            msg['From'] = email_user
            msg['To'] = format_email_recipients_for_header(recipients['to'])
            if recipients['cc']:
                msg['Cc'] = format_email_recipients_for_header(recipients['cc'])
            msg['Subject'] = (
                f"Alert - Documents Expiring Within 6 Months "
                f"({passport_count}) - {workspace.name}"
            )

            html_body = f"""
            <html>
            <head>
            <style>
            p {{ margin: 0; padding: 0; }}
            ul {{ margin: 0; padding: 0; padding-left: 20px; }}
            li {{ margin: 0; padding: 0; margin-bottom: 15px; }}
            .expired {{ color: red; font-weight: bold; }}
            .expiring-soon {{ color: orange; font-weight: bold; }}
            .warning {{ color: #cc0000; font-weight: bold; }}
            .normal {{ color: #4a4a4a; font-weight: bold; }}
            .workspace-name {{ color: #6c757d; font-style: italic; }}
            </style>
            </head>
            <body>
                <p>Dear User,</p>
                <br>
                <p><b><u>DOCUMENT EXPIRY ALERT:</u></b></p>
                <p class="workspace-name">Workspace: {workspace.name}</p>
                <br>
                <p>The following document(s) are expiring within the next 6 months and require renewal action:</p>
                <br>
                <ul>"""

            for passport in passports:
                days = passport['days_until_expiry']

                if days < 0:
                    urgency_text = f"<span class='expired'>EXPIRED {abs(days)} days ago!</span>"
                elif days <= 30:
                    urgency_text = f"<span class='warning'>URGENT - Expires in {days} days!</span>"
                elif days <= 90:
                    urgency_text = f"<span class='expiring-soon'>Expires in {days} days</span>"
                else:
                    urgency_text = f"<span class='normal'>Expires in {days} days</span>"

                html_body += f"""
                <li>
                    <b>{passport['holder_name']}</b> - {passport['document_type']}<br>
                    Document Number: {passport['document_number']}<br>
                    Country of Issue: {passport['country_of_issue']}<br>
                    Expiry Date: {passport['expiry_date']}<br>
                    {urgency_text}
                </li>"""

            html_body += """
                </ul>
                <br>
                <p><b>ACTION REQUIRED:</b></p>
                <p>Please begin the renewal process for these documents as soon as possible to avoid any travel disruptions or legal issues.</p>
                <br>
                <p>Please log into the Alivente Online System at <a href="https://alivente.online">alivente.online</a> for additional details and to manage passport/ID records.</p>
                <br>
                <p>Best regards,<br>
                Alivente Property Management System<br>
                Automated Passport/ID Monitoring</p>
            </body>
            </html>
            """

            text_body = f"""Dear User,

DOCUMENT EXPIRY ALERT:
Workspace: {workspace.name}

The following document(s) are expiring within the next 6 months and require renewal action:

"""
            for passport in passports:
                days = passport['days_until_expiry']
                if days < 0:
                    urgency_text = f"EXPIRED {abs(days)} days ago!"
                elif days <= 30:
                    urgency_text = f"URGENT - Expires in {days} days!"
                elif days <= 90:
                    urgency_text = f"Expires in {days} days"
                else:
                    urgency_text = f"Expires in {days} days"

                text_body += f"""
- {passport['holder_name']} - {passport['document_type']}
  Document Number: {passport['document_number']}
  Country of Issue: {passport['country_of_issue']}
  Expiry Date: {passport['expiry_date']}
  {urgency_text}

"""

            text_body += """ACTION REQUIRED:
Please begin the renewal process for these documents as soon as possible to avoid any travel disruptions or legal issues.

Please log into the Alivente Online System at alivente.online for additional details and to manage passport/ID records.

Best regards,
Alivente Property Management System
Automated Passport/ID Monitoring"""

            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            if email_use_ssl:
                smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=60)
            else:
                smtp_object = smtplib.SMTP(email_host, email_port, timeout=60)
                smtp_object.ehlo()
                if email_use_tls:
                    smtp_object.starttls()

            smtp_object.login(email_user, email_password)
            smtp_object.sendmail(email_user, recipients['all'], msg.as_string())

            self.stdout.write(f'    ✅ Sent to workspace "{workspace.name}"')
            logger.info(f'Passport expiry email sent for workspace {workspace.name}')
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication Error: {e}")
            self.stdout.write(f'    ❌ SMTP Auth Error: {e}')
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP Error: {e}")
            self.stdout.write(f'    ❌ SMTP Error: {e}')
            return False
        except Exception as e:
            logger.error(f"Error sending passport expiry email for workspace {workspace.name}: {e}", exc_info=True)
            self.stdout.write(f'    ❌ Error: {e}')
            return False
        finally:
            if smtp_object:
                try:
                    smtp_object.quit()
                except Exception:
                    pass

    def _send_email_with_retry(self, msg, from_addr, to_addrs, label='Email',
                               max_attempts=3, base_delay=5):
        """Send a MIME message via SMTP with a generous timeout + retry/backoff.

        A fresh connection is opened on every attempt (a timed-out socket
        cannot be reused). Returns True on success, False if every attempt
        fails. Authentication errors fail fast because retrying will not help.
        """
        email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.environ.get('EMAIL_PORT', 465))
        email_user = os.environ.get('EMAIL_USER', 'demetrimanias@gmail.com')
        email_password = os.environ.get('EMAIL_PASSWORD')
        email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
        email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'

        if not email_password:
            self.stdout.write('[X] EMAIL_PASSWORD environment variable not set')
            return False

        payload = msg.as_string()
        last_error = None

        for attempt in range(1, max_attempts + 1):
            smtp_object = None
            try:
                if email_use_ssl:
                    smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=60)
                else:
                    smtp_object = smtplib.SMTP(email_host, email_port, timeout=60)
                    smtp_object.ehlo()
                    if email_use_tls:
                        smtp_object.starttls()
                smtp_object.login(email_user, email_password)
                smtp_object.sendmail(from_addr, to_addrs, payload)
                self.stdout.write(
                    '[OK] %s sent successfully (attempt %d/%d)'
                    % (label, attempt, max_attempts)
                )
                logger.info('%s sent successfully on attempt %d' % (label, attempt))
                return True
            except smtplib.SMTPAuthenticationError as e:
                last_error = 'SMTP Authentication Error: %s' % (e,)
                logger.error(last_error)
                self.stdout.write('[X] %s' % last_error)
                return False
            except (smtplib.SMTPException, socket.timeout, OSError) as e:
                last_error = '%s: %s' % (type(e).__name__, e)
                logger.warning(
                    '%s send attempt %d/%d failed: %s'
                    % (label, attempt, max_attempts, last_error)
                )
                self.stdout.write(
                    '[!] %s send attempt %d/%d failed: %s'
                    % (label, attempt, max_attempts, last_error)
                )
            finally:
                if smtp_object is not None:
                    try:
                        smtp_object.quit()
                    except Exception:
                        pass

            if attempt < max_attempts:
                delay = base_delay * attempt
                self.stdout.write('    Retrying in %ds...' % delay)
                time.sleep(delay)

        self.stdout.write(
            '[X] %s failed after %d attempts. Last error: %s'
            % (label, max_attempts, last_error)
        )
        logger.error(
            '%s failed after %d attempts: %s'
            % (label, max_attempts, last_error)
        )
        return False

    def run_notification_function(self, vacant_properties, expiring_leases, declined_renewals, overdue_invoices, created_invoices_count):
        """Send email notification for lease renewals, vacant properties, declined renewals, overdue invoices, and invoice creation"""
        smtp_object = None

        vacant_count = len(vacant_properties)
        expiring_count = len(expiring_leases)
        declined_count = len(declined_renewals)
        overdue_count = len(overdue_invoices)

        try:
            self.stdout.write('=== SENDING PROPERTY MANAGEMENT NOTIFICATION ===')

            # Get email settings from environment variables
            email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
            email_port = int(os.environ.get('EMAIL_PORT', 465))
            email_user = os.environ.get('EMAIL_USER', 'demetrimanias@gmail.com')
            email_password = os.environ.get('EMAIL_PASSWORD')
            email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
            email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'
            recipients = get_email_recipients('daily_report')

            # DEBUG: Show who will receive the email
            self.stdout.write(f'📧 Daily Report Email TO: {", ".join(recipients["to"])}')
            if recipients['cc']:
                self.stdout.write(f'📧 Daily Report Email CC: {", ".join(recipients["cc"])}')

            if not email_password:
                self.stdout.write('❌ EMAIL_PASSWORD environment variable not set')
                return False

            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = email_user
            msg['To'] = format_email_recipients_for_header(recipients['to'])
            if recipients['cc']:
                msg['Cc'] = format_email_recipients_for_header(recipients['cc'])
            msg['Subject'] = "Alert - Invoices, Leases and Vacant Properties"

            # Build HTML email body with formatting
            html_body = f"""
            <html>
            <head>
            <style>
            p {{ margin: 0; padding: 0; }}
            ul {{ margin: 0; padding: 0; padding-left: 20px; }}
            li {{ margin: 0; padding: 0; }}
            </style>
            </head>
            <body>
                <p>Dear User,</p>
                <br>
                <p><b><u>REPORT SUMMARY:</u></b><br>"""

            # Only show lines with counts > 0
            if created_invoices_count > 0:
                html_body += f"• New Invoices Created: {created_invoices_count}<br>"
            if vacant_count > 0:
                html_body += f"• Vacant Properties: {vacant_count}<br>"
            if expiring_count > 0:
                html_body += f"• Expiring Leases (Pending): {expiring_count}<br>"
            if declined_count > 0:
                html_body += f"• Declined Renewals (Need New Tenants): {declined_count}<br>"
            if overdue_count > 0:
                html_body += f"• Tenants with Overdue Invoices: {overdue_count}<br>"

            html_body += "</p><br>"

            # Add invoice creation summary if any were created
            if created_invoices_count > 0:
                today = date.today()
                months = ('','January','February','March','April','May','June',
                         'July','August','September','October','November','December')
                current_month = months[today.month]

                # Correct grammar for singular vs plural
                if created_invoices_count == 1:
                    invoice_text = "There was 1 new invoice that was automatically created"
                else:
                    invoice_text = f"There were {created_invoices_count} new invoices that were automatically created"

                html_body += f"""<p><b><u>INVOICE CREATION SUMMARY ({created_invoices_count}):</u></b><br>
                {invoice_text} today for {current_month} {today.year}.</p><br>"""

            # Add detailed vacant properties list
            if vacant_count > 0:
                # Correct grammar for singular vs plural
                property_word = "property" if vacant_count == 1 else "properties"
                property_verb = "is" if vacant_count == 1 else "are"
                tenant_word = "tenant" if vacant_count == 1 else "tenants"

                html_body += f"""<p><b><u>VACANT {property_word.upper()} ({vacant_count}):</u></b><br>
                This {property_word} {property_verb} active and available for rent but currently has no {tenant_word}. Contact estate agents ASAP.</p><ul>""" if vacant_count == 1 else f"""<p><b><u>VACANT {property_word.upper()} ({vacant_count}):</u></b><br>
                These {property_word} {property_verb} active and available for rent but currently have no {tenant_word}. Contact estate agents ASAP.</p><ul>"""

                for prop in vacant_properties:
                    html_body += f"<li><b>{prop['prop_name']} ({prop['prop_country']})</b></li>"
                html_body += """</ul><br>"""

            # Add detailed expiring leases list (PENDING renewals only)
            if expiring_count > 0:
                # Correct grammar for singular vs plural
                lease_word = "lease" if expiring_count == 1 else "leases"
                tenant_word = "tenant" if expiring_count == 1 else "tenants"
                tenant_verb = "has a" if expiring_count == 1 else "have"

                html_body += f"""<p><b><u>EXPIRING {lease_word.upper()} - PENDING RENEWALS ({expiring_count}):</u></b><br>
                This {tenant_word} {tenant_verb} {lease_word} expiring soon that requires a renewal discussion. Contact the {tenant_word} ASAP.</p><ul>""" if expiring_count == 1 else f"""<p><b><u>EXPIRING {lease_word.upper()} - PENDING RENEWALS ({expiring_count}):</u></b><br>
                These {tenant_word} {tenant_verb} {lease_word} expiring soon that require renewal discussions. Contact the {tenant_word} ASAP.</p><ul>"""

                for lease in expiring_leases:
                    html_body += f"<li><b>{lease['prop_name']} ({lease['prop_country']})</b> - Tenant: {lease['tenant_name']}<br>"
                    html_body += f"(Lease ends: {lease['lease_end_date']} | Renewal due by: {lease['renewal_date']})</li>"
                html_body += """</ul><br>"""

            # Add detailed declined renewals list
            if declined_count > 0:
                # Correct grammar for singular vs plural
                tenant_word = "tenant" if declined_count == 1 else "tenants"
                tenant_verb = "has" if declined_count == 1 else "have"
                property_word = "property" if declined_count == 1 else "properties"
                property_verb = "will need a new tenant" if declined_count == 1 else "will need new tenants"

                if declined_count == 1:
                    html_body += f"""<p><b><u>DECLINED RENEWALS - NEED NEW TENANT ({declined_count}):</u></b><br>
                    This {tenant_word} has declined lease renewal. This {property_word} {property_verb}. Contact estate agents ASAP.</p><ul>"""
                else:
                    html_body += f"""<p><b><u>DECLINED RENEWALS - NEED NEW TENANTS ({declined_count}):</u></b><br>
                    These {tenant_word} {tenant_verb} declined lease renewals. These {property_word} {property_verb}. Contact estate agents ASAP.</p><ul>"""

                for declined in declined_renewals:
                    html_body += f"<li><b>{declined['prop_name']} ({declined['prop_country']})</b> - Current Tenant: {declined['tenant_name']}<br>"
                    html_body += f"(Lease ends: {declined['lease_end_date']} - {declined['message']})</li>"
                html_body += """</ul><br>"""

            # Add detailed overdue invoices list
            if overdue_count > 0:
                # Correct grammar for singular vs plural
                tenant_word = "tenant" if overdue_count == 1 else "tenants"
                tenant_verb = "has an" if overdue_count == 1 else "have"
                invoice_word = "invoice" if overdue_count == 1 else "invoices"

                html_body += f"""<p><b><u>{tenant_word.upper()} WITH OVERDUE {invoice_word.upper()} ({overdue_count}):</u></b><br>
                This {tenant_word} {tenant_verb} overdue {invoice_word} that requires immediate attention. Contact {tenant_word} ASAP.</p><ul>""" if overdue_count == 1 else f"""<p><b><u>{tenant_word.upper()} WITH OVERDUE {invoice_word.upper()} ({overdue_count}):</u></b><br>
                These {tenant_word} {tenant_verb} overdue {invoice_word} that require immediate attention. Contact {tenant_word} ASAP.</p><ul>"""

                for property_invoice in overdue_invoices:
                    html_body += f"<li><b>{property_invoice['prop_name']} ({property_invoice['prop_country']})</b> - Tenant: {property_invoice['tenant_name']}<br>"
                    for invoice in property_invoice['invoices']:
                        html_body += f"&nbsp;&nbsp;• Due: {invoice['due_date']} - €{invoice['amount']}<br>"
                    html_body += "</li>"
                html_body += """</ul><br>"""

            html_body += """<p>Please log into the Alivente Online System for additional details.</p>
                <br>
                <p>Best regards,<br>
                Alivente Property Management System<br>
                Automated Report</p>
            </body>
            </html>
            """

            # Create plain text version as backup
            text_body = f"""Dear User,

REPORT SUMMARY:"""

            # Only show lines with counts > 0
            if created_invoices_count > 0:
                text_body += f"\n • New Invoices Created: {created_invoices_count}"
            if vacant_count > 0:
                text_body += f"\n • Vacant Properties: {vacant_count}"
            if expiring_count > 0:
                text_body += f"\n • Expiring Leases (Pending): {expiring_count}"
            if declined_count > 0:
                text_body += f"\n • Declined Renewals (Need New Tenants): {declined_count}"
            if overdue_count > 0:
                text_body += f"\n • Tenants with Overdue Invoices: {overdue_count}"

            text_body += "\n\n"

            # Add invoice creation summary if any were created
            if created_invoices_count > 0:
                today = date.today()
                months = ('','January','February','March','April','May','June',
                         'July','August','September','October','November','December')
                current_month = months[today.month]

                # Correct grammar for singular vs plural
                if created_invoices_count == 1:
                    invoice_text = "There was 1 new invoice that was automatically created"
                else:
                    invoice_text = f"There were {created_invoices_count} new invoices that were automatically created"

                text_body += f"""INVOICE CREATION SUMMARY ({created_invoices_count}):
{invoice_text} today for {current_month} {today.year}.

"""

            # Add detailed vacant properties list
            if vacant_count > 0:
                # Correct grammar for singular vs plural
                property_word = "property" if vacant_count == 1 else "properties"
                property_verb = "is" if vacant_count == 1 else "are"
                tenant_word = "tenant" if vacant_count == 1 else "tenants"

                if vacant_count == 1:
                    text_body += f"""VACANT {property_word.upper()} ({vacant_count}):
This {property_word} {property_verb} active and available for rent but currently has no {tenant_word}. Contact estate agents ASAP."""
                else:
                    text_body += f"""VACANT {property_word.upper()} ({vacant_count}):
These {property_word} {property_verb} active and available for rent but currently have no {tenant_word}. Contact estate agents ASAP."""

                for prop in vacant_properties:
                    text_body += f"\n • {prop['prop_name']} ({prop['prop_country']})"
                text_body += f"\n\n"

            # Add detailed expiring leases list (PENDING renewals only)
            if expiring_count > 0:
                # Correct grammar for singular vs plural
                lease_word = "lease" if expiring_count == 1 else "leases"
                tenant_word = "tenant" if expiring_count == 1 else "tenants"
                tenant_verb = "has a" if expiring_count == 1 else "have"

                if expiring_count == 1:
                    text_body += f"""EXPIRING {lease_word.upper()} - PENDING RENEWALS ({expiring_count}):
This {tenant_word} {tenant_verb} {lease_word} expiring soon that requires a renewal discussion. Contact the {tenant_word} ASAP."""
                else:
                    text_body += f"""EXPIRING {lease_word.upper()} - PENDING RENEWALS ({expiring_count}):
These {tenant_word} {tenant_verb} {lease_word} expiring soon that require renewal discussions. Contact the {tenant_word} ASAP."""

                for lease in expiring_leases:
                    text_body += f"\n • {lease['prop_name']} ({lease['prop_country']}) - Tenant: {lease['tenant_name']}"
                    text_body += f"\n   (Lease ends: {lease['lease_end_date']} | Renewal due by: {lease['renewal_date']})"
                text_body += f"\n\n"

            # Add detailed declined renewals list
            if declined_count > 0:
                # Correct grammar for singular vs plural
                tenant_word = "tenant" if declined_count == 1 else "tenants"
                tenant_verb = "has" if declined_count == 1 else "have"
                property_word = "property" if declined_count == 1 else "properties"
                property_verb = "will need a new tenant" if declined_count == 1 else "will need new tenants"

                if declined_count == 1:
                    text_body += f"""DECLINED RENEWALS - NEED NEW TENANT ({declined_count}):
This {tenant_word} has declined lease renewal. This {property_word} {property_verb}. Contact estate agents ASAP."""
                else:
                    text_body += f"""DECLINED RENEWALS - NEED NEW TENANTS ({declined_count}):
These {tenant_word} {tenant_verb} declined lease renewals. These {property_word} {property_verb}. Contact estate agents ASAP."""

                for declined in declined_renewals:
                    text_body += f"\n • {declined['prop_name']} ({declined['prop_country']}) - Current Tenant: {declined['tenant_name']}"
                    text_body += f"\n   (Lease ends: {declined['lease_end_date']} - {declined['message']})"
                text_body += f"\n\n"

            # Add detailed overdue invoices list
            if overdue_count > 0:
                # Correct grammar for singular vs plural
                tenant_word = "tenant" if overdue_count == 1 else "tenants"
                tenant_verb = "has an" if overdue_count == 1 else "have"
                invoice_word = "invoice" if overdue_count == 1 else "invoices"

                if overdue_count == 1:
                    text_body += f"""{tenant_word.upper()} WITH OVERDUE {invoice_word.upper()} ({overdue_count}):
This {tenant_word} {tenant_verb} overdue {invoice_word} that requires immediate attention. Contact {tenant_word} ASAP."""
                else:
                    text_body += f"""{tenant_word.upper()} WITH OVERDUE {invoice_word.upper()} ({overdue_count}):
These {tenant_word} {tenant_verb} overdue {invoice_word} that require immediate attention. Contact {tenant_word} ASAP."""

                for property_invoice in overdue_invoices:
                    text_body += f"\n • {property_invoice['prop_name']} ({property_invoice['prop_country']}) - Tenant: {property_invoice['tenant_name']}"
                    for invoice in property_invoice['invoices']:
                        text_body += f"\n     - Due: {invoice['due_date']} - €{invoice['amount']}"
                text_body += f"\n\n"

            text_body += """Please log into the Alivente Online System for additional details.

Best regards,
Alivente Property Management System
Automated Report"""

            # Attach both HTML and plain text versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')

            msg.attach(part1)
            msg.attach(part2)

            # Send with a generous timeout and retry/backoff so a single
            # transient SMTP timeout does not silently drop the daily report.
            return self._send_email_with_retry(
                msg, email_user, recipients['all'],
                label='Property management notification email',
            )

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP Authentication Error: {e}"
            logger.error(error_msg)
            self.stdout.write(f'❌ {error_msg}')
            return False
        except smtplib.SMTPException as e:
            error_msg = f"SMTP Error: {e}"
            logger.error(error_msg)
            self.stdout.write(f'❌ {error_msg}')
            return False
        except Exception as e:
            error_msg = f"Error sending property management email: {e}"
            logger.error(error_msg, exc_info=True)
            self.stdout.write(f'❌ {error_msg}')
            return False
        finally:
            if smtp_object:
                try:
                    smtp_object.quit()
                except Exception:
                    pass

    def get_yesterdays_issue_comments(self):
        """Get all comments added to issues yesterday, with parent issue and property context."""
        yesterday = date.today() - timedelta(days=1)

        admin_users_upper = [u.upper() for u in ADMIN_USER_INITIALS]

        try:
            comments_qs = issues_details.objects.filter(
                issues_details_date=yesterday
            ).select_related('issues', 'issues__prop').order_by(
                'issues__prop__prop_name', 'issues__issues_heading', 'issues_details_id'
            )

            comment_list = []
            for c in comments_qs:
                issue = c.issues
                if issue and issue.prop:
                    property_name = issue.prop.prop_name
                    property_country = getattr(issue.prop, 'prop_country', '') or ''
                elif issue:
                    property_name = 'Unknown Property'
                    property_country = ''
                else:
                    property_name = 'Unknown Property'
                    property_country = ''

                user_initials = (c.issues_details_user or '').strip()
                is_admin = user_initials.upper() in admin_users_upper

                comment_list.append({
                    'comment': c.issues_details_comment or '',
                    'user': user_initials or 'Unknown',
                    'is_admin': is_admin,
                    'date': c.issues_details_date.strftime('%Y/%m/%d') if c.issues_details_date else '',
                    'issue_heading': (issue.issues_heading if issue else None) or 'Untitled Issue',
                    'issue_description': (issue.issues_description if issue else '') or '',
                    'issue_status': (issue.issues_status if issue else None) or 'Unknown',
                    'prop_name': property_name,
                    'prop_country': property_country,
                })

            self.stdout.write(f'Found {len(comment_list)} issue comment(s) from {yesterday}')
            return comment_list, yesterday

        except Exception as e:
            self.stdout.write(f'❌ Error getting yesterday\'s issue comments: {e}')
            logger.error(f'Error getting yesterday\'s issue comments: {e}', exc_info=True)
            return [], yesterday