def lease_renewal(rep_output,check,email,fname):

	import mysql.connector
	from datetime import date, datetime, timedelta
	import send_email
	import pdf_display
	
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

	today = date.today()

	# EXTRACT INFO FROM TENANT TABLE
	my_cursor.execute("SELECT prop.prop_name, prop.prop_country, tenant.tenant_type, tenant.tenant_name, tenant.tenant_contact_person, tenant.tenant_contact_number, tenant.tenant_email, tenant.tenant_deposit, tenant.tenant_lease_start_date, tenant.tenant_lease_end_date, tenant.tenant_rental_type, tenant.tenant_renewal, tenant.tenant_renewal_period, tenant.tenant_rent, tenant.tenant_levies, tenant.tenant_payment_terms, tenant.tenant_current FROM alivente.tenant JOIN alivente.prop ON prop.prop_id = tenant.prop_id ORDER BY prop.prop_country ASC, prop.prop_name ASC")
	result = my_cursor.fetchall()
	my_cursor.execute("SELECT tenant.tenant_name FROM alivente.tenant WHERE tenant.tenant_current = 'Yes' ORDER BY tenant.tenant_name ASC")
	result_tenants = my_cursor.fetchall()
	my_cursor.execute("SELECT prop.prop_name FROM alivente.tenant JOIN alivente.prop ON prop.prop_id = tenant.prop_id WHERE tenant.tenant_current = 'Yes' ORDER BY prop.prop_country ASC, prop.prop_name ASC")
	prop_active_tenant = my_cursor.fetchall()
	my_cursor.execute("SELECT prop.prop_name FROM alivente.prop WHERE prop.prop_status = 'Active' and prop.prop_available_for_rent = 'Yes' ORDER BY prop.prop_country ASC, prop.prop_name ASC")
	active_prop = my_cursor.fetchall()
	
	import fpdf
	pdf = fpdf.FPDF(format='A4')
	pdf.add_page()
	pdf.set_font("Arial", "BU", size=20)
	pdf.cell(w=0,h=8, txt="LEASE RENEWAL REPORT - (" + str(today) + ")", align="C")

	pdf.set_font("Arial", size=14)
	pdf.set_left_margin (0)

	blank_report_check = 0

	for row in result:
		for tenant in result_tenants:
			lease_end_date = row[9]
			renewal_date = lease_end_date - timedelta(days=(int(row[12]))) # date - days
			warning_date = renewal_date - timedelta(days=(30))
			if tenant[0] == row[3] and today >= warning_date:
				pdf.ln()
				pdf.ln()
				pdf.set_font("Arial", "BU", size=16)
				pdf.set_left_margin (10)
				pdf.write (5,f"Property Name: {row[0]}")
				pdf.ln()
				pdf.set_font("Arial", size=12)
				pdf.set_left_margin (15)
				pdf.ln()
				pdf.write (5,f"	Type: {row[2]}")
				pdf.ln()
				pdf.write (5,f"	Name: {row[3]}")
				pdf.ln()
				pdf.write (5,f"	Contact Person: {row[4]}")
				pdf.ln()
				pdf.write (5,f"	Contact Number: {row[5]}")
				pdf.ln()
				pdf.write (5,f"	Email: {row[6]}")
				pdf.ln()
				pdf.write (5,f"	Lease Start Date: {row[8]}")
				pdf.ln()
				pdf.set_text_color(255,0,0)
				pdf.set_font("Arial", "B", size=14)
				pdf.write (5,f"	Lease End Date: {row[9]}")
				pdf.ln()
				pdf.set_text_color(0,0,0)
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"	Rental Type: {row[10]}")
				pdf.ln()
				pdf.write (5,f"	Lease Renewal Clause: {row[11]}")
				pdf.ln()
				pdf.write (5,f"	Lease Renewal Notice Period: {row[12]} days")
				pdf.ln()
				pdf.set_text_color(255,0,0)
				pdf.set_font("Arial", "B", size=14)
				pdf.write (5,f"	Tenant Contact Date: {renewal_date}")
				pdf.ln()
				pdf.set_text_color(0,0,0)
				pdf.set_font("Arial", size=12)
				pdf.set_left_margin (10)
				pdf.ln()
				pdf.set_left_margin (10)
				blank_report_check = blank_report_check + 1
	for property in active_prop:
		if property not in prop_active_tenant:
			pdf.ln()
			pdf.ln()
			pdf.set_font("Arial", "BU", size=16)
			pdf.set_left_margin (10)
			pdf.write (5,f"Property Name: {property[0]}")
			pdf.ln()
			pdf.set_font("Arial", size=16)
			pdf.set_left_margin (15)
			pdf.ln()
			pdf.write (5,f"	NO CURRENT TENANT - ")
			pdf.set_font("Arial", "BU", size=14)
			pdf.set_text_color(255,0,0)
			pdf.write (5,f"NEED NEW TENANT")
			pdf.set_text_color(0,0,0)
			pdf.ln()
		
				
	file_path = "C:/Users/DemetrisManias/Desktop/code/djangoproject/static/reports/"
	report_name = file_path+"Lease Renewal Report ("+str(today)+").pdf"
	pdf.output (report_name)

	# send email to (email address, email subject, report name and "file path and name") - fixed body text for email
	if rep_output == "Email" and check == "No":
		send_email.send_email(email,"Lease Renewal Report ("+str(today)+")","Lease Renewal Report",report_name, fname)
	elif rep_output == "Email" and check == "Yes" and blank_report_check > 0:
		send_email.send_email(email,"Lease Renewal Report ("+str(today)+")","Lease Renewal Report",report_name, fname)

	# display pdf file in new window - send file_name
	if rep_output == "Display" and check == "No":
		pdf_display.pdf_display(report_name)
	elif rep_output == "Display" and check == "Yes" and blank_report_check > 0:
		pdf_display.pdf_display(report_name)

	if mydb.is_connected():
		my_cursor.close()
		mydb.close()
