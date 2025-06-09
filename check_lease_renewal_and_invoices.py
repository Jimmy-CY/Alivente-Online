from django.core.management.base import BaseCommand
from django.conf import settings
from datetime import date, timedelta
import mysql.connector
import os

class Command(BaseCommand):
    help = 'Check lease renewals and vacant properties, send notifications if needed'
    
    def handle(self, *args, **options):
        self.stdout.write('Starting lease renewal and invoice checks...')
        
        # Get the data using the same logic as your view
        vacant_count, expiring_count = self.get_property_counts()
        
        self.stdout.write(f'Vacant properties: {vacant_count}')
        self.stdout.write(f'Expiring leases: {expiring_count}')
        
        # Check if action is needed
        if vacant_count == 0 and expiring_count == 0:
            self.stdout.write('No action needed - no vacant properties or expiring leases')
            return
        
        # Action needed - call your function XYZ
        if vacant_count > 0 or expiring_count > 0:
            self.stdout.write('Action needed! Running notification function...')
            self.run_notification_function(vacant_count, expiring_count)
    
    def get_property_counts(self):
        """Get the same data as your view function"""
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
        
        try:
            # Get current tenants with lease info
            my_cursor.execute("""
                SELECT prop.prop_name, tenant.tenant_lease_end_date, tenant.tenant_renewal_period
                FROM railway.tenant
                JOIN railway.prop ON prop.prop_id = tenant.prop_id
                WHERE tenant.tenant_current = 'Yes'
            """)
            tenant_rows = my_cursor.fetchall()
            
            # Get properties with current tenants
            my_cursor.execute("""
                SELECT prop.prop_name
                FROM railway.tenant
                JOIN railway.prop ON prop.prop_id = tenant.prop_id
                WHERE tenant.tenant_current = 'Yes'
            """)
            prop_active_tenant = [row[0] for row in my_cursor.fetchall()]
            
            # Get all active properties available for rent
            my_cursor.execute("""
                SELECT prop.prop_name
                FROM railway.prop
                WHERE prop.prop_status = 'Active'
                AND prop.prop_available_for_rent = 'Yes'
            """)
            active_properties = [row[0] for row in my_cursor.fetchall()]
            
            # Count expiring leases
            expiring_count = 0
            for row in tenant_rows:
                lease_end_date = row[1]  # tenant_lease_end_date
                renewal_period = int(row[2])  # tenant_renewal_period
                renewal_date = lease_end_date - timedelta(days=renewal_period)
                warning_date = renewal_date - timedelta(days=30)
                
                if today >= warning_date:
                    expiring_count += 1
            
            # Count vacant properties
            vacant_count = len([prop for prop in active_properties if prop not in prop_active_tenant])
            
            return vacant_count, expiring_count
            
        finally:
            if mydb.is_connected():
                my_cursor.close()
                mydb.close()
    
    def run_notification_function(self, vacant_count, expiring_count):
        """Send email notification for lease renewals and vacant properties"""
        import smtplib
        import logging
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        logger = logging.getLogger(__name__)
        smtp_object = None
        
        try:
            self.stdout.write('=== SENDING LEASE RENEWAL NOTIFICATION ===')
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = "demetrimanias@gmail.com"
            msg['To'] = "demetrimanias@gmail.com"
            msg['Subject'] = "Daily Property Management Alert - Lease Renewals & Vacant Properties"
            
            # Build email body based on counts
            body = f"""Dear Property Management Team,

Daily property status alert from Alivente Property Management System:

SUMMARY:
 • Vacant Properties: {vacant_count}
 • Expiring Leases: {expiring_count}

"""
            
            # Add details if there are issues
            if vacant_count > 0:
                body += f"""VACANT PROPERTIES ({vacant_count}):
These properties are active and available for rent but currently have no tenants.
Action needed: Review marketing and leasing efforts.

"""
            
            if expiring_count > 0:
                body += f"""EXPIRING LEASES ({expiring_count}):
These tenants have leases expiring soon and may need renewal discussions.
Action needed: Contact tenants to discuss lease renewals.

"""
            
            body += """Please log into the Alivente system to view detailed reports and take appropriate action.

Best regards,
Alivente Property Management System
Automated Daily Report"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # SMTP setup with detailed error handling
            smtp_object = smtplib.SMTP('smtp.gmail.com', 587)
            smtp_object.ehlo()
            smtp_object.starttls()
            
            email = "demetrimanias@gmail.com"
            password = os.environ.get('EMAIL_PASSWORD')
            
            if not password:
                self.stdout.write('❌ EMAIL_PASSWORD environment variable not set')
                return False
            
            smtp_object.login(email, password)
            
            # Send email
            text = msg.as_string()
            smtp_object.sendmail(email, "demetrimanias@gmail.com", text)
            
            self.stdout.write('✅ Lease renewal notification email sent successfully!')
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication Error: {e}")
            self.stdout.write(f'❌ SMTP Authentication Error: {e}')
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP Error: {e}")
            self.stdout.write(f'❌ SMTP Error: {e}')
            return False
        except Exception as e:
            logger.error(f"Error sending lease renewal email: {e}")
            self.stdout.write(f'❌ Error sending email: {e}')
            return False
        finally:
            if smtp_object:
                try:
                    smtp_object.quit()
                except:
                    pass