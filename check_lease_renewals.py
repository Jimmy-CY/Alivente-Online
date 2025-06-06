from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta, date
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mysql.connector
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check for lease renewals and send email notification if data exists'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-email',
            action='store_true',
            help='Force send email even if no data (for testing)',
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting lease renewal check...')
        
        try:
            # Get the data that would be displayed in the report
            tenants_needing_renewal, vacant_properties = self.get_renewal_data()
            
            # Count total records
            total_records = len(tenants_needing_renewal) + len(vacant_properties)
            
            self.stdout.write(f'Found {total_records} items requiring attention')
            
            # If there's data or force email is enabled, send notification
            if total_records > 0 or options['force_email']:
                success = self.send_notification_email(tenants_needing_renewal, vacant_properties, total_records)
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'Email notification sent - {total_records} items found')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('Failed to send email notification')
                    )
            else:
                self.stdout.write('No lease renewals or vacant properties found - no email sent')
                
        except Exception as e:
            logger.error(f'Error in lease renewal check: {str(e)}')
            self.stdout.write(
                self.style.ERROR(f'Error occurred: {str(e)}')
            )

    def get_renewal_data(self):
        """Get lease renewal data using the same logic as the lease_renewal_report view"""
        mydb = None
        my_cursor = None
        try:
            mydb = mysql.connector.connect(
                host=settings.DATABASES['default']['HOST'],
                port=settings.DATABASES['default']['PORT'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                database=settings.DATABASES['default']['NAME'],
                auth_plugin=settings.DATABASES['default']['AUTH_PLUGIN'],
            )
            my_cursor = mydb.cursor()
            today = date.today()
            tenants = []
            vacant_properties = []

            # Get all current tenants
            my_cursor.execute("""
                SELECT prop.prop_name, prop.prop_country, tenant.tenant_type, tenant.tenant_name,
                tenant.tenant_contact_person, tenant.tenant_contact_number, tenant.tenant_email,
                tenant.tenant_deposit, tenant.tenant_lease_start_date, tenant.tenant_lease_end_date,
                tenant.tenant_rental_type, tenant.tenant_renewal, tenant.tenant_renewal_period,
                tenant.tenant_rent, tenant.tenant_levies, tenant.tenant_payment_terms,
                tenant.tenant_current
                FROM railway.tenant
                JOIN railway.prop ON prop.prop_id = tenant.prop_id
                WHERE tenant.tenant_current = 'Yes'
                ORDER BY prop.prop_country ASC, prop.prop_name ASC
            """)
            tenant_rows = my_cursor.fetchall()

            # Get properties with active tenants
            my_cursor.execute("""
                SELECT prop.prop_name
                FROM railway.tenant
                JOIN railway.prop ON prop.prop_id = tenant.prop_id
                WHERE tenant.tenant_current = 'Yes'
                ORDER BY prop.prop_country ASC, prop.prop_name ASC
            """)
            prop_active_tenant = [row[0] for row in my_cursor.fetchall()]

            # Get all active properties available for rent
            my_cursor.execute("""
                SELECT prop.prop_name
                FROM railway.prop
                WHERE prop.prop_status = 'Active'
                AND prop.prop_available_for_rent = 'Yes'
                ORDER BY prop.prop_country ASC, prop.prop_name ASC
            """)
            active_properties = [row[0] for row in my_cursor.fetchall()]

            # Process tenants needing renewal
            for row in tenant_rows:
                lease_end_date = row[9]  # tenant_lease_end_date
                if not lease_end_date:
                    continue
                    
                renewal_period = int(row[12])  # tenant_renewal_period
                renewal_date = lease_end_date - timedelta(days=renewal_period)
                warning_date = renewal_date - timedelta(days=30)
                
                if today >= warning_date:
                    tenants.append({
                        'prop_name': row[0],
                        'prop_country': row[1],
                        'tenant_type': row[2],
                        'tenant_name': row[3],
                        'tenant_contact_person': row[4],
                        'tenant_contact_number': row[5],
                        'tenant_email': row[6],
                        'tenant_deposit': row[7],
                        'tenant_lease_start_date': row[8].strftime('%Y-%m-%d') if row[8] else '',
                        'tenant_lease_end_date': row[9].strftime('%Y-%m-%d') if row[9] else '',
                        'tenant_rental_type': row[10],
                        'tenant_renewal': row[11],
                        'tenant_renewal_period': row[12],
                        'tenant_rent': row[13],
                        'tenant_levies': row[14],
                        'tenant_payment_terms': row[15],
                        'renewal_date': renewal_date.strftime('%Y-%m-%d'),
                        'needs_renewal': True
                    })

            # Process vacant properties
            vacant_properties = [{'prop_name': prop} for prop in active_properties if prop not in prop_active_tenant]

            return tenants, vacant_properties

        finally:
            if my_cursor:
                my_cursor.close()
            if mydb and mydb.is_connected():
                mydb.close()

    def send_notification_email(self, tenants_needing_renewal, vacant_properties, total_records):
        """Send email notification about lease renewals using your existing email pattern"""
        
        smtp_object = None
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = "demetrimanias@gmail.com"
            msg['To'] = "demetrimanias@gmail.com"
            msg['Subject'] = f"Lease Renewal Report - {total_records} Items Require Attention"
            
            # Create the email body
            renewal_count = len(tenants_needing_renewal)
            vacant_count = len(vacant_properties)
            
            body_lines = [
                "Dear User,",
                "",
                f"The daily lease renewal check has found {total_records} items requiring your attention:",
                ""
            ]
            
            if renewal_count > 0:
                body_lines.append(f" • {renewal_count} tenant(s) requiring lease renewal")
            
            if vacant_count > 0:
                body_lines.append(f" • {vacant_count} vacant property(ies) needing new tenants")
            
            body_lines.extend([
                "",
                "Please log in to the system to view the full Lease Renewal Report.",
                "",
                f"Report generated: {timezone.now().strftime('%Y-%m-%d at %H:%M')}",
                "",
                "Thanks,",
                "Alivente Property Management System"
            ])
            
            body = "\n".join(body_lines)
            msg.attach(MIMEText(body, 'plain'))
            
            # SMTP setup with more detailed error handling
            smtp_object = smtplib.SMTP('smtp.gmail.com', 587)
            smtp_object.ehlo()
            smtp_object.starttls()
            
            email = "demetrimanias@gmail.com"
            password = "nfvb been waqz wwks"
            
            smtp_object.login(email, password)
            
            # Send email
            text = msg.as_string()
            smtp_object.sendmail(email, "demetrimanias@gmail.com", text)
            
            logger.info('Lease renewal notification email sent successfully')
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication Error: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP Error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending lease renewal notification email: {e}")
            return False
        finally:
            if smtp_object:
                try:
                    smtp_object.quit()
                except:
                    pass