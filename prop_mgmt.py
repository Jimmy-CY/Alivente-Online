import mysql.connector
from datetime import date, datetime, timedelta
import database_create
import print_prop
import fsr
import print_tenant
import print_title
import print_lease
import petty_cash
import lease_renewal
import open_invoices

# CONNECT TO DATBASE (FIRST HAVE TO LEAVE database line off until have created database)
mydb = mysql.connector.connect(
	host = "localhost",
	user = "root",
	password = "Smiles123$",
	database = "alivente",
	auth_plugin = "mysql_native_password",
	)

# CREATE CURSOR INSTANCE
my_cursor = mydb.cursor()

database_create.db_create ()

# EXTRACT ALL DATA RECORDS FROM PROP TABLE
# my_cursor.execute("SELECT * FROM prop")
# result = my_cursor.fetchall()
# for row in result:
#	 print (f"Property Name: {row[1]}")
#	 if row[2] == "":
#	 	print (f"Address: {row[3]}, {row[4]}, {row[5]}, {row[6]}, {row[7]}")
#	 else:
#	 	print (f"	Address: {row[2]}, {row[3]}, {row[4]}, {row[5]}, {row[6]}, {row[7]}")
#	 print (f"	Square Meters: {row[8]}")
#	 print (f"	Year Built: {row[9]}")
#	 print (f"	Status: {row[10]}")
#	 print (f"	Available for Rent: {row[11]}")

# # EXTRACT ALL DATA RECORDS FROM TENANT TABLE
# my_cursor.execute("SELECT * FROM tenant")
# result = my_cursor.fetchall()
# for row in result:
# 	 print (row [0]," | ",row[1]," | ",row[2]," | ",row[3],row [4]," | ",row[5]," | ",row[6]," | ",row[7],row [8]," | ",row[9]," | ",row[10]," | ",row[11]," | ",row[12],row [13]," | ",row[14]," | ",row[15]," | ",row[16])

# # EXTRACT ALL DATA RECORDS FROM INVOICE TABLE
# my_cursor.execute("SELECT * FROM invoice")
# result = my_cursor.fetchall()
# for row in result:
# 	 print (row [0]," | ",row[1]," | ",row[2]," | ",row[3])

# EXTRACT ALL DATA RECORDS FROM ISSUES TABLE
# |	 print (row [0]," | ",row[1]," | ",row[2]," | ",row[3]," | ",row [4]," | ",row[5]," | ",row[6])

# # EXTRACT ALL DATA RECORDS FROM ISSUES_DETAILS TABLE
# my_cursor.execute("SELECT * FROM issues_details")
# result = my_cursor.fetchall()
# for row in result:
	 # print (row [0]," | ",row[1]," | ",row[2]," | ",row[3]," | ",row [4])

# TABLE JOINS ON PRIMARY KEY (FOR PROP, TENANT AND INVOICE TABLES)
# my_cursor.execute("SELECT tenant.tenant_name, prop.prop_name, invoice.invoice_paid FROM prop_mgmt.prop JOIN prop_mgmt.tenant ON prop.prop_id = tenant.prop_id JOIN prop_mgmt.invoice ON tenant.tenant_id = invoice.tenant_id")
# result = my_cursor.fetchall()
# from datetime import date
# from datetime import datetime
# today = date.today()
# for row in result:
# 	date_object = datetime.strptime(row[3], '%Y-%m-%d').date()
# 	if date_object < today and row[4] == "No":
# 		print (row [0]," | ",row[1]," | ",row[2])

print ("*******************************************************")

# Setup a daily job that will run first thing every morning and will delete any of the old reports that are lying the Reports Folder
import os
import glob
file_path = "C:/Users/DemetrisManias/Desktop/code/djangoproject/static/reports/*.pdf"
files = glob.glob(file_path)
for f in files:
    os.remove(f)

rep_type = "Detailed"
rep_date = date.today()
rep_output = "Display"
# Generate Friday Status Report (or rep_type could be: Detailed or Summarised) and (rep_output could be: Display or Email)
fsr.fsr_report(rep_type, rep_date, rep_output)

property = "All"
rep_output = "Display"
# or property could be: All, Palikaridi, Foti Pitta, Pindarou, etc. and (rep_output could be: Display or Email)
print_prop.prop_report(property, rep_output)

property = "Dikaiosynis"
rep_output = "Display"
# Property could be: Dikaiosynis,Palikaridi,Foti Pitta,Pindarou,Eleftheroupoleos,Apolloneon - Demetri,Athens - First Floor,Athens - Second Floor,Athens - Third Floor,Spain - Eusebi Guell and (rep_output could be: Display or Email)
print_title.title_report(property, rep_output)

property = "Pindarou"
rep_output = "Display"
# or property could be: Palikaridi, Foti Pitta, Pindarou, etc. and (rep_output could be: Display or Email)
print_lease.lease_report(property, rep_output)

property = "All"
rep_output = "Display"
# or property could be: All, Palikaridi, Foti Pitta, Pindarou, etc. and (rep_output could be: Display or Email)
print_tenant.tenant_report(property, rep_output)

# Generate Petty Cash Report - rep_output could be: Display or Email
rep_output = "Display"
petty_cash.petty_cash(rep_output)

# Generate Lease Renewal Report - rep_output could be: Display or Email - check could be Yes or No to opt to send or display report only if values exist
# This must be set as a scheduled job as well.  It must run every morning and only if there are Lease Renewals, it must email out a copy of the report.
rep_output = "Display"
check = "Yes"
lease_renewal.lease_renewal(rep_output,check)

# Create Invoices - This must run once a month on the 1st of the Month - Will check that it is the first of the month.  Then will submit the current month and year and run.
today = date.today()
months = ('Month','January', 'February','March','April','May','June','July','August','September','October','November','December')
if today.day == 1:
	open_invoices.create_invoices(months[today.month],today.year)

# Generate Open Invoices Report - rep_output could be: Display or Email - check could be Yes or No to opt to send or display report only if values exist
# This must be set as a scheduled job as well.  It must run every morning and only if there are Open Invoices, it must email out a copy of the report.
rep_output = "Display"
check = "Yes"
open_invoices.open_invoices(rep_output, check)
