from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections, connection
from datetime import date, timedelta, datetime
from .email_utils import get_email_recipients, format_email_recipients_for_header
import os
import sys
import logging

# Set up logging
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
            # First, create invoices if needed
            created_invoices_count = self.create_invoices()
            
            # Then get all the data with property details
            vacant_properties, expiring_leases, declined_renewals, overdue_invoices = self.get_all_property_details()
            
            # Check for expiring passports
            expiring_passports = self.get_expiring_passports()
            
            # NEW: Check for new leases that need to be uploaded
            new_leases_to_upload = self.get_new_leases_to_upload()
            
            vacant_count = len(vacant_properties)
            expiring_count = len(expiring_leases)
            declined_count = len(declined_renewals)
            overdue_count = len(overdue_invoices)
            passport_count = len(expiring_passports)
            new_lease_count = len(new_leases_to_upload)
            
            self.stdout.write(f'Invoices created today: {created_invoices_count}')
            self.stdout.write(f'Vacant properties: {vacant_count}')
            self.stdout.write(f'Expiring leases (pending): {expiring_count}')
            self.stdout.write(f'Declined renewals (need new tenants): {declined_count}')
            self.stdout.write(f'Overdue invoices: {overdue_count}')
            self.stdout.write(f'Expiring passports (within 6 months): {passport_count}')
            self.stdout.write(f'New leases to upload: {new_lease_count}')
            
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
            
            # NEW: Send new lease upload reminder if needed
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
                    SELECT prop.prop_id, prop.prop_name, prop.prop_country, prop.prop_status, tenant.tenant_id 
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
                        if not self.dry_run:
                            cursor.execute(
                                "INSERT INTO invoice (tenant_id, invoice_date, invoice_paid) VALUES (%s, %s, %s)",
                                [tenant_id, new_invoice_date, 'No']
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
                       invoice.invoice_date
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
        from pages.models import Passport  # Adjust import based on your app name
        
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
                    'already_expired': passport.expiry_date < today
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
    
    def send_new_lease_upload_reminder(self, new_leases_to_upload):
        """Send email reminder to upload new lease agreements"""
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
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
            
            # Send only to demetrimanias@gmail.com
            email_to_list = ['demetrimanias@gmail.com']
            
            if not email_password:
                self.stdout.write('❌ EMAIL_PASSWORD environment variable not set')
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = email_user
            msg['To'] = email_to_list[0]
            
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
• {lease['prop_name']} ({lease['prop_country']})
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
                smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
            else:
                smtp_object = smtplib.SMTP(email_host, email_port, timeout=10)
                smtp_object.ehlo()
                if email_use_tls:
                    smtp_object.starttls()
            
            smtp_object.login(email_user, email_password)
            
            # Send email
            text = msg.as_string()
            smtp_object.sendmail(email_user, email_to_list, text)
            
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
                except:
                    pass
    
    def send_passport_expiry_notification(self, expiring_passports):
        """Send separate email notification for expiring passports - only on 1st or 15th of month"""
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        smtp_object = None
        passport_count = len(expiring_passports)
        
        if passport_count == 0:
            self.stdout.write('No expiring passports to notify about')
            return True
        
        # Check if today is 1st or 15th of the month
        today = date.today()
        if today.day not in [1, 15]:
            self.stdout.write(f'📅 Passport notification skipped - only sent on 1st or 15th of month (Today is {today.day}th)')
            self.stdout.write(f'   Found {passport_count} expiring passport(s), but no email will be sent today')
            return True
        
        try:
            self.stdout.write('=== SENDING PASSPORT EXPIRY NOTIFICATION ===')
            self.stdout.write(f'📅 Today is the {today.day}th - sending passport expiry notification')
            
            # Get email settings from environment variables
            email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
            email_port = int(os.environ.get('EMAIL_PORT', 465))
            email_user = os.environ.get('EMAIL_USER', 'demetrimanias@gmail.com')
            email_password = os.environ.get('EMAIL_PASSWORD')
            email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
            email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'
            
            # Use the standard email recipients utility
            email_to_list = get_email_recipients('passport_expiry')
            
            if not email_password:
                self.stdout.write('❌ EMAIL_PASSWORD environment variable not set')
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = email_user
            msg['To'] = format_email_recipients_for_header(email_to_list)
            msg['Subject'] = f"Alert - Documents Expiring Within 6 Months ({passport_count})"
            
            # Build HTML email body
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
            </style>
            </head>
            <body>
                <p>Dear User,</p>
                <br>
                <p><b><u>DOCUMENT EXPIRY ALERT:</u></b></p>
                <p>The following document(s) are expiring within the next 6 months and require renewal action:</p>
                <br>
                <ul>"""
            
            for passport in expiring_passports:
                days = passport['days_until_expiry']
                
                # Color code based on urgency
                if days < 0:
                    urgency_class = "expired"
                    urgency_text = f"<span class='expired'>EXPIRED {abs(days)} days ago!</span>"
                elif days <= 30:
                    urgency_class = "warning"
                    urgency_text = f"<span class='warning'>URGENT - Expires in {days} days!</span>"
                elif days <= 90:
                    urgency_class = "expiring-soon"
                    urgency_text = f"<span class='expiring-soon'>Expires in {days} days</span>"
                else:
                    urgency_class = "normal"
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
            
            # Create plain text version
            text_body = f"""Dear User,

    DOCUMENT EXPIRY ALERT:

    The following document(s) are expiring within the next 6 months and require renewal action:

    """
            
            for passport in expiring_passports:
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
    • {passport['holder_name']} - {passport['document_type']}
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
            
            # Attach both HTML and plain text versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # SMTP setup
            if email_use_ssl:
                smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
            else:
                smtp_object = smtplib.SMTP(email_host, email_port, timeout=10)
                smtp_object.ehlo()
                if email_use_tls:
                    smtp_object.starttls()
            
            smtp_object.login(email_user, email_password)
            
            # Send email
            text = msg.as_string()
            smtp_object.sendmail(email_user, email_to_list, text)
            
            self.stdout.write('✅ Passport expiry notification email sent successfully!')
            logger.info('Passport expiry notification email sent successfully')
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
            error_msg = f"Error sending passport expiry email: {e}"
            logger.error(error_msg, exc_info=True)
            self.stdout.write(f'❌ {error_msg}')
            return False
        finally:
            if smtp_object:
                try:
                    smtp_object.quit()
                except:
                    pass
    
    def run_notification_function(self, vacant_properties, expiring_leases, declined_renewals, overdue_invoices, created_invoices_count):
        """Send email notification for lease renewals, vacant properties, declined renewals, overdue invoices, and invoice creation"""
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
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
            email_to_list = get_email_recipients('daily_report')
            
            if not email_password:
                self.stdout.write('❌ EMAIL_PASSWORD environment variable not set')
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = email_user
            msg['To'] = format_email_recipients_for_header(email_to_list)
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
                        html_body += f"&nbsp;&nbsp;• Due: {invoice['due_date']} - €{property_invoice['tenant_rent']}<br>"
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
                        text_body += f"\n     - Due: {invoice['due_date']} - €{property_invoice['tenant_rent']}"
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
            
            # UPDATED SMTP setup with environment variable configuration
            if email_use_ssl:
                # Use SSL connection (typically port 465)
                smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
            else:
                # Use regular SMTP connection (typically port 587)
                smtp_object = smtplib.SMTP(email_host, email_port, timeout=10)
                smtp_object.ehlo()
                if email_use_tls:
                    smtp_object.starttls()
            
            smtp_object.login(email_user, email_password)
            
            # Send email
            text = msg.as_string()
            smtp_object.sendmail(email_user, email_to_list, text)
            
            self.stdout.write('✅ Property management notification email sent successfully!')
            logger.info('Property management notification email sent successfully')
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
            error_msg = f"Error sending property management email: {e}"
            logger.error(error_msg, exc_info=True)
            self.stdout.write(f'❌ {error_msg}')
            return False
        finally:
            if smtp_object:
                try:
                    smtp_object.quit()
                except:
                    pass