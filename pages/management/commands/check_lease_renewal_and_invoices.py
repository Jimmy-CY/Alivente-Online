from django.core.management.base import BaseCommand
from django.conf import settings
from datetime import date, timedelta, datetime
import mysql.connector
import os
import sys

class Command(BaseCommand):
    help = 'Check lease renewals, vacant properties, outstanding invoices, and create new invoices if needed'
    
    def handle(self, *args, **options):
        self.stdout.write('=== STARTING LEASE RENEWAL, INVOICE CHECK, AND INVOICE CREATION ===')
        self.stdout.write(f'Current working directory: {os.getcwd()}')
        self.stdout.write(f'Python path: {sys.executable}')
        
        # Test environment variables
        email_password = os.environ.get('EMAIL_PASSWORD')
        if email_password:
            self.stdout.write('✅ EMAIL_PASSWORD environment variable found')
        else:
            self.stdout.write('❌ EMAIL_PASSWORD environment variable NOT found')
            return
        
        # Test database connection
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write('✅ Database connection successful')
        except Exception as e:
            self.stdout.write(f'❌ Database connection failed: {e}')
            return
        
        self.stdout.write('Starting invoice creation, lease renewal and invoice checks...')
        
        # First, create invoices if needed
        created_invoices_count = self.create_invoices()
        
        # Then get all the data with property details
        vacant_properties, expiring_leases, overdue_invoices = self.get_all_property_details()
        
        vacant_count = len(vacant_properties)
        expiring_count = len(expiring_leases)
        overdue_count = len(overdue_invoices)
        
        self.stdout.write(f'Invoices created today: {created_invoices_count}')
        self.stdout.write(f'Vacant properties: {vacant_count}')
        self.stdout.write(f'Expiring leases: {expiring_count}')
        self.stdout.write(f'Overdue invoices: {overdue_count}')
        
        # Check if action is needed (including invoice creation)
        if vacant_count == 0 and expiring_count == 0 and overdue_count == 0 and created_invoices_count == 0:
            self.stdout.write('No action needed - no vacant properties, expiring leases, overdue invoices, or new invoices created')
            return
        
        # Action needed - send notification
        if vacant_count > 0 or expiring_count > 0 or overdue_count > 0 or created_invoices_count > 0:
            self.stdout.write('Action needed! Running notification function...')
            result = self.run_notification_function(vacant_properties, expiring_leases, overdue_invoices, created_invoices_count)
            self.stdout.write(f'Email function returned: {result}')
        
        self.stdout.write('=== LEASE RENEWAL, INVOICE CHECK, AND INVOICE CREATION COMPLETED ===')
    
    def create_invoices(self):
        """Create invoices for current month if they don't already exist"""
        today = date.today()
        months = ('Month','January','February','March','April','May','June',
                 'July','August','September','October','November','December')
        
        current_month = months[today.month]
        current_year = today.year
        
        self.stdout.write(f'Checking invoice creation for {current_month} {current_year}')
        
        mydb = mysql.connector.connect(
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            database=settings.DATABASES['default']['NAME'],
            auth_plugin=settings.DATABASES['default']['AUTH_PLUGIN'],
        )
        
        my_cursor = mydb.cursor()
        
        try:
            # Get all current active tenants
            my_cursor.execute("""
                SELECT prop.prop_id, prop.prop_name, prop.prop_country, prop.prop_status, tenant.tenant_id 
                FROM railway.tenant 
                JOIN railway.prop ON prop.prop_id = tenant.prop_id 
                WHERE tenant.tenant_current = 'Yes' AND prop.prop_status = 'Active' 
                ORDER BY tenant.tenant_id ASC
            """)
            tenants = my_cursor.fetchall()
            
            # Get existing unpaid invoices
            my_cursor.execute("""
                SELECT invoice.invoice_id, invoice.tenant_id, invoice.invoice_date, invoice.invoice_paid 
                FROM railway.invoice 
                WHERE invoice.invoice_paid = 'No' 
                ORDER BY invoice.invoice_date ASC
            """)
            existing_invoices = my_cursor.fetchall()
            
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
                    sql = "INSERT INTO invoice (tenant_id, invoice_date, invoice_paid) VALUES (%s, %s, %s)"
                    my_cursor.execute(sql, (tenant_id, new_invoice_date, 'No'))
                    created_count += 1
            
            if created_count > 0:
                mydb.commit()
                self.stdout.write(f'✅ Created {created_count} new invoices for {new_invoice_date}')
            else:
                self.stdout.write(f'ℹ️  No new invoices created - they already exist for {new_invoice_date}')
            
            return created_count
            
        except Exception as e:
            self.stdout.write(f'❌ Error creating invoices: {e}')
            return 0
        finally:
            if mydb.is_connected():
                my_cursor.close()
                mydb.close()
    
    def get_all_property_details(self):
        """Get detailed property, lease, and invoice information"""
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
            # Get current tenants with detailed lease info
            my_cursor.execute("""
                SELECT prop.prop_name, prop.prop_country, tenant.tenant_name, 
                       tenant.tenant_lease_end_date, tenant.tenant_renewal_period,
                       tenant.tenant_payment_terms
                FROM railway.tenant
                JOIN railway.prop ON prop.prop_id = tenant.prop_id
                WHERE tenant.tenant_current = 'Yes'
                ORDER BY prop.prop_country ASC, prop.prop_name ASC
            """)
            tenant_rows = my_cursor.fetchall()
            
            # Get properties with current tenants (just names)
            my_cursor.execute("""
                SELECT prop.prop_name
                FROM railway.tenant
                JOIN railway.prop ON prop.prop_id = tenant.prop_id
                WHERE tenant.tenant_current = 'Yes'
            """)
            prop_active_tenant = [row[0] for row in my_cursor.fetchall()]
            
            # Get all active properties available for rent with details
            my_cursor.execute("""
                SELECT prop.prop_name, prop.prop_country
                FROM railway.prop
                WHERE prop.prop_status = 'Active'
                AND prop.prop_available_for_rent = 'Yes'
                ORDER BY prop.prop_country ASC, prop.prop_name ASC
            """)
            active_properties_data = my_cursor.fetchall()
            
            # Find expiring leases with details
            expiring_leases = []
            for row in tenant_rows:
                prop_name = row[0]
                prop_country = row[1]
                tenant_name = row[2]
                lease_end_date = row[3]
                renewal_period = int(row[4])
                
                renewal_date = lease_end_date - timedelta(days=renewal_period)
                warning_date = renewal_date - timedelta(days=30)
                
                if today >= warning_date:
                    expiring_leases.append({
                        'prop_name': prop_name,
                        'prop_country': prop_country,
                        'tenant_name': tenant_name,
                        'lease_end_date': lease_end_date.strftime('%Y-%m-%d'),
                        'renewal_date': renewal_date.strftime('%Y-%m-%d')
                    })
            
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
            overdue_invoices = self.get_outstanding_invoices(my_cursor, today)
            
            return vacant_properties, expiring_leases, overdue_invoices
            
        finally:
            if mydb.is_connected():
                my_cursor.close()
                mydb.close()
    
    def get_outstanding_invoices(self, cursor, today):
        """Get properties with overdue invoices only"""
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
    
    def run_notification_function(self, vacant_properties, expiring_leases, overdue_invoices, created_invoices_count):
        """Send email notification for lease renewals, vacant properties, overdue invoices, and invoice creation"""
        import smtplib
        import logging
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        logger = logging.getLogger(__name__)
        smtp_object = None
        
        vacant_count = len(vacant_properties)
        expiring_count = len(expiring_leases)
        overdue_count = len(overdue_invoices)
        
        try:
            self.stdout.write('=== SENDING PROPERTY MANAGEMENT NOTIFICATION ===')
            
            # Get email settings from environment variables
            email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
            email_port = int(os.environ.get('EMAIL_PORT', '587'))
            email_user = os.environ.get('EMAIL_USER', 'demetrimanias@gmail.com')
            email_password = os.environ.get('EMAIL_PASSWORD')
            email_to = os.environ.get('EMAIL_TO', 'demetrimanias@gmail.com')
            
            if not email_password:
                self.stdout.write('❌ EMAIL_PASSWORD environment variable not set')
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = email_user
            msg['To'] = email_to
            msg['Subject'] = "Property Management Alert - Invoice Creation, Lease Renewals, Vacant Properties & Overdue Invoices"
            
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
                <p>Property management alert from Alivente Property Management System:</p>
                <br>
                <p><b><u>REPORT SUMMARY:</u></b><br>"""
            
            # Only show lines with counts > 0
            if created_invoices_count > 0:
                html_body += f"• New Invoices Created: {created_invoices_count}<br>"
            if vacant_count > 0:
                html_body += f"• Vacant Properties: {vacant_count}<br>"
            if expiring_count > 0:
                html_body += f"• Expiring Leases: {expiring_count}<br>"
            if overdue_count > 0:
                html_body += f"• Tenants with Overdue Invoices: {overdue_count}<br>"
            
            html_body += "</p><br>"
            
            # Add invoice creation summary if any were created
            if created_invoices_count > 0:
                today = date.today()
                months = ('','January','February','March','April','May','June',
                         'July','August','September','October','November','December')
                current_month = months[today.month]
                html_body += f"""<p><b><u>INVOICE CREATION SUMMARY:</u></b><br>
                {created_invoices_count} new invoices were automatically created today for {current_month} {today.year}.</p><br>"""
            
            # Add detailed vacant properties list
            if vacant_count > 0:
                html_body += f"""<p><b><u>VACANT PROPERTIES ({vacant_count}):</u></b><br>
                These properties are active and available for rent but currently have no tenants. Contact estate agents ASAP.</p><ul>"""
                for prop in vacant_properties:
                    html_body += f"<li><b>{prop['prop_name']} ({prop['prop_country']})</b></li>"
                html_body += """</ul><br>"""
            
            # Add detailed expiring leases list
            if expiring_count > 0:
                html_body += f"""<p><b><u>EXPIRING LEASES ({expiring_count}):</u></b><br>
                These tenants have leases expiring soon and need renewal discussions. Contact tenants ASAP.</p><ul>"""
                for lease in expiring_leases:
                    html_body += f"<li><b>{lease['prop_name']} ({lease['prop_country']})</b> - Tenant: {lease['tenant_name']}<br>"
                    html_body += f"(Lease ends: {lease['lease_end_date']} | Renewal due by: {lease['renewal_date']})</li>"
                html_body += """</ul><br>"""
            
            # Add detailed overdue invoices list
            if overdue_count > 0:
                html_body += f"""<p><b><u>OVERDUE INVOICES ({overdue_count}):</u></b><br>
                These tenants have overdue invoices that require immediate attention. Contact tenants ASAP.</p><ul>"""
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

Property management alert from Alivente Property Management System:

REPORT SUMMARY:"""
            
            # Only show lines with counts > 0
            if created_invoices_count > 0:
                text_body += f"\n • New Invoices Created: {created_invoices_count}"
            if vacant_count > 0:
                text_body += f"\n • Vacant Properties: {vacant_count}"
            if expiring_count > 0:
                text_body += f"\n • Expiring Leases: {expiring_count}"
            if overdue_count > 0:
                text_body += f"\n • Tenants with Overdue Invoices: {overdue_count}"
            
            text_body += "\n\n"
            
            # Add invoice creation summary if any were created
            if created_invoices_count > 0:
                today = date.today()
                months = ('','January','February','March','April','May','June',
                         'July','August','September','October','November','December')
                current_month = months[today.month]
                text_body += f"""INVOICE CREATION SUMMARY:
{created_invoices_count} new invoices were automatically created today for {current_month} {today.year}.

"""
            
            # Add plain text vacant properties
            if vacant_count > 0:
                text_body += f"""VACANT PROPERTIES ({vacant_count}):
These properties are active and available for rent but currently have no tenants. Contact estate agents ASAP."""
                for prop in vacant_properties:
                    text_body += f"\n • {prop['prop_name']} ({prop['prop_country']})"
                text_body += f"\n\n"
            
            # Add plain text expiring leases
            if expiring_count > 0:
                text_body += f"""EXPIRING LEASES ({expiring_count}):
These tenants have leases expiring soon and need renewal discussions. Contact tenants ASAP."""
                for lease in expiring_leases:
                    text_body += f"\n • {lease['prop_name']} ({lease['prop_country']}) - Tenant: {lease['tenant_name']}"
                    text_body += f"\n   (Lease ends: {lease['lease_end_date']} | Renewal due by: {lease['renewal_date']})"
                text_body += f"\n\n"
            
            # Add plain text overdue invoices
            if overdue_count > 0:
                text_body += f"""OVERDUE INVOICES ({overdue_count}):
These tenants have overdue invoices that require immediate attention. Contact tenants ASAP."""
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
            
            # SMTP setup with detailed error handling
            smtp_object = smtplib.SMTP(email_host, email_port)
            smtp_object.ehlo()
            smtp_object.starttls()
            
            smtp_object.login(email_user, email_password)
            
            # Send email
            text = msg.as_string()
            smtp_object.sendmail(email_user, email_to, text)
            
            self.stdout.write('✅ Property management notification email sent successfully!')
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
            logger.error(f"Error sending property management email: {e}")
            self.stdout.write(f'❌ Error sending email: {e}')
            return False
        finally:
            if smtp_object:
                try:
                    smtp_object.quit()
                except:
                    pass