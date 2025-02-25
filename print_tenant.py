def tenant_report (property, rep_output, email, fname):

	import mysql.connector
	from datetime import date
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

	today=date.today()

	import fpdf
	pdf = fpdf.FPDF(format='letter')
	pdf.add_page()
	pdf.set_font("Arial", "BU", size=20)
	pdf.cell(w=0,h=8, txt="TENANT DETAILS REPORT - (" + str(today) + ")", align="C")
	# pdf.set_font("Arial", "BU", size=20)
	# pdf.write (5,"Property Details Report")
	# pdf.set_font("Arial", "B", size=16)
	# pdf.write (5,f" (Date: {today})")
	pdf.ln()
	pdf.ln()

	pdf.set_font("Arial", size=14)
	pdf.set_left_margin (10)

	my_cursor.execute("SELECT prop.prop_name, prop.prop_country, tenant.tenant_type, tenant.tenant_name, tenant.tenant_contact_person, tenant.tenant_contact_number, tenant.tenant_email, tenant.tenant_deposit, tenant.tenant_lease_start_date, tenant.tenant_lease_end_date, tenant.tenant_rental_type, tenant.tenant_renewal, tenant.tenant_renewal_period, tenant.tenant_rent, tenant.tenant_levies, tenant.tenant_payment_terms, tenant.tenant_current FROM alivente.tenant JOIN alivente.prop ON prop.prop_id = tenant.prop_id ORDER BY prop.prop_country ASC, prop.prop_name ASC")
	result = my_cursor.fetchall()
	my_cursor.execute("SELECT tenant.tenant_name FROM alivente.tenant WHERE tenant.tenant_current = 'Yes' ORDER BY tenant.tenant_name ASC")
	result_tenants = my_cursor.fetchall()
	my_cursor.execute("SELECT prop.prop_name FROM alivente.tenant JOIN alivente.prop ON prop.prop_id = tenant.prop_id WHERE tenant.tenant_current = 'Yes' ORDER BY prop.prop_country ASC, prop.prop_name ASC")
	prop_active_tenant = my_cursor.fetchall()
	my_cursor.execute("SELECT prop.prop_name FROM alivente.prop WHERE prop.prop_status = 'Active' and prop.prop_available_for_rent = 'Yes' ORDER BY prop.prop_country ASC, prop.prop_name ASC")
	active_prop = my_cursor.fetchall()
	
	page_break = 0
	single_property_print = 1

	for row in result:
		if property == "All":
			pdf.set_left_margin (0)
			if row[16] == "Yes":
				if page_break == 2:
					pdf.add_page()
					page_break = 0
				page_break = page_break + 1
				pdf.set_font("Arial", "BU", size=14)
				pdf.set_left_margin (10)
				pdf.write (5,f"Property Name: {row[0]}")
				pdf.ln()
				pdf.set_font("Arial", size=12)
				pdf.set_left_margin (15)
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Type: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[2]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Name: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[3]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Contact Person: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[4]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Contact Number: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[5]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Email: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[6]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Deposit Amount: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"Euro {row[7]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Lease Start Date: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[8]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Lease End Date: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[9]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Rental Type: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[10]}")
				pdf.ln()
				if row[11] == "Yes":
					pdf.set_font("Arial", "B", size=12)
					pdf.write (5,f"	Lease Renewal Clause: ")
					pdf.set_font("Arial", size=12)
					pdf.write (5,f"{row[11]}")
					pdf.ln()
					pdf.set_font("Arial", "B", size=12)
					pdf.write (5,f"	Lease Renewal Notice Period: ")
					pdf.set_font("Arial", size=12)
					pdf.write (5,f"{row[12]} days")
					pdf.ln()
				elif row[11] == "No":
					pdf.set_font("Arial", "B", size=12)
					pdf.write (5,f"	Lease Renewal Clause: ")
					pdf.set_font("Arial", size=12)
					pdf.write (5,f"{row[11]}")
					pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Rental Amount: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"Euro {row[13]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Levies Amount: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"Euro {row[14]}")
				pdf.ln()
				if row[15] == 0:
					pdf.set_font("Arial", "B", size=12)
					pdf.write (5,f"	Payment Terms: ")
					pdf.set_font("Arial", size=12)
					pdf.write (5,f"Immediate")
				else:
					pdf.set_font("Arial", "B", size=12)
					pdf.write (5,f"	Payment Terms: ")
					pdf.set_font("Arial", size=12)
					pdf.write (5,f"{row[15]} days")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Active: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[16]}")
				pdf.ln()
				pdf.set_left_margin (10)
				pdf.ln()
				pdf.set_left_margin (10)

		elif property == row [0]:
			single_property_print = 0
			pdf.set_left_margin (0)
			if row[16] == "Yes":
				single_property_print = single_property_print + 1
				pdf.set_font("Arial", "BU", size=14)
				pdf.set_left_margin (10)
				pdf.write (5,f"Property Name: {row[0]}")
				pdf.ln()
				pdf.set_font("Arial", size=12)
				pdf.set_left_margin (15)
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Type: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[2]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Name: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[3]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Contact Person: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[4]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Contact Number: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[5]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Email: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[6]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Deposit Amount: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"Euro {row[7]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Lease Start Date: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[8]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Lease End Date: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[9]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Rental Type: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[10]}")
				pdf.ln()
				if row[11] == "Yes":
					pdf.set_font("Arial", "B", size=12)
					pdf.write (5,f"	Lease Renewal Clause: ")
					pdf.set_font("Arial", size=12)
					pdf.write (5,f"{row[11]}")
					pdf.ln()
					pdf.set_font("Arial", "B", size=12)
					pdf.write (5,f"	Lease Renewal Notice Period: ")
					pdf.set_font("Arial", size=12)
					pdf.write (5,f"{row[12]} days")
					pdf.ln()
				elif row[11] == "No":
					pdf.set_font("Arial", "B", size=12)
					pdf.write (5,f"	Lease Renewal Clause: ")
					pdf.set_font("Arial", size=12)
					pdf.write (5,f"{row[11]}")
					pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Rental Amount: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"Euro {row[13]}")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Levies Amount: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"Euro {row[14]}")
				pdf.ln()
				if row[15] == 0:
					pdf.set_font("Arial", "B", size=12)
					pdf.write (5,f"	Payment Terms: ")
					pdf.set_font("Arial", size=12)
					pdf.write (5,f"Immediate")
				else:
					pdf.set_font("Arial", "B", size=12)
					pdf.write (5,f"	Payment Terms: ")
					pdf.set_font("Arial", size=12)
					pdf.write (5,f"{row[15]} days")
				pdf.ln()
				pdf.set_font("Arial", "B", size=12)
				pdf.write (5,f"	Active: ")
				pdf.set_font("Arial", size=12)
				pdf.write (5,f"{row[16]}")
				pdf.ln()
				pdf.set_left_margin (10)
				pdf.ln()
				pdf.set_left_margin (10)

	if property == "All":
		# for loop for properties that are both active and also available for rent (active-prop)
		for property in active_prop:
			# if property does not have an active tenant, i.e. tenant_current is not Yes 
			if property not in prop_active_tenant:
				pdf.add_page()
				pdf.set_font("Arial", "BU", size=14)
				pdf.set_left_margin (10)
				pdf.write (5,f"Property Name: {property[0]}")
				pdf.ln()
				pdf.set_font("Arial", size=12)
				pdf.set_left_margin (15)
				pdf.ln()
				pdf.write (5,f"	NO CURRENT TENANT")
				# pdf.set_font("Arial", "BU", size=14)
				# pdf.set_text_color(255,0,0)
				# pdf.write (5,f"NEED NEW TENANT")
				# pdf.set_text_color(0,0,0)
				pdf.ln()

	if single_property_print == 0:
		# for loop for properties that are both active and also available for rent (active-prop)
		for property in active_prop:
			# if property does not have an active tenant, i.e. tenant_current is not Yes 
			if property not in prop_active_tenant:
				pdf.set_font("Arial", "BU", size=14)
				pdf.set_left_margin (10)
				pdf.write (5,f"Property Name: {property[0]}")
				pdf.ln()
				pdf.set_font("Arial", size=12)
				pdf.set_left_margin (15)
				pdf.ln()
				pdf.write (5,f"	NO CURRENT TENANT")
				# pdf.set_font("Arial", "BU", size=14)
				# pdf.set_text_color(255,0,0)
				# pdf.write (5,f"NEED NEW TENANT")
				# pdf.set_text_color(0,0,0)
				pdf.ln()



	file_path = "C:/Users/DemetrisManias/Desktop/code/djangoproject/static/reports/"
	report_name = file_path+"Tenant Details Report ("+str(today)+").pdf"
	pdf.output (report_name)

	# send email to (email address, email subject, report name and "file path and name") - fixed body text for email
	if rep_output == "Email":
		send_email.send_email(email,"Tenant Details Report ("+str(today)+")","Tenant Details Report",report_name,fname)

	# display pdf file in new window - send file_name
	if rep_output == "Display":
		pdf_display.pdf_display(report_name)

	if mydb.is_connected():
		my_cursor.close()
		mydb.close()
