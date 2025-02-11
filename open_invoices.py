def open_invoices (rep_output,check,email,fname):

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

	today=date.today()

	import fpdf
	pdf = fpdf.FPDF(format='letter')
	pdf.add_page()
	pdf.set_font("Arial", "BU", size=20)
	pdf.cell(w=0,h=8, txt="OUTSTANDING INVOICES REPORT - (" + str(today) + ")", align="C")
	pdf.ln()
	pdf.ln()

	pdf.set_font("Arial", size=14)
	pdf.set_left_margin (10)

	# just before the ODER BY, paste this: WHERE tenant.tenant_current = 'Yes' 
	my_cursor.execute("SELECT prop.prop_name,prop.prop_country, tenant.tenant_id, tenant.tenant_name,tenant.tenant_contact_person,tenant.tenant_contact_number,tenant.tenant_email,tenant.tenant_rent,tenant.tenant_payment_terms,tenant.tenant_current FROM alivente.tenant JOIN alivente.prop ON prop.prop_id = tenant.prop_id ORDER BY prop.prop_country ASC, prop.prop_name ASC")
	result = my_cursor.fetchall()
	my_cursor.execute("SELECT  invoice.invoice_id, invoice.tenant_id, invoice.invoice_date, invoice.invoice_paid FROM alivente.invoice WHERE invoice.invoice_paid = 'No' ORDER BY invoice.invoice_date ASC")
	result_invoices = my_cursor.fetchall()
	
	today = date.today()
	blank_report_check = 0

	for row in result:
		prop_display = 1
		for inv in result_invoices:
			invoice_due_date = inv[2] + timedelta(days=(int(row[8]))) # date + days
			if row[2] == inv [1] and today >= invoice_due_date:
				# pdf.set_left_margin (0)
				if prop_display == 1:
					pdf.set_font("Arial", "BU", size=14)
					pdf.set_left_margin (10)
					pdf.write (5,f"Property Name: {row[0]}")
					pdf.ln()
					pdf.set_font("Arial", size=12)
					pdf.set_left_margin (20)
					pdf.ln()
					pdf.write (5,f"	  Name: {row[3]}")
					pdf.ln()
					pdf.write (5,f"	  Contact Person: {row[4]}")
					pdf.ln()
					pdf.write (5,f"	  Contact Number: {row[5]}")
					pdf.ln()
					pdf.write (5,f"	  Email: {row[6]}")
					pdf.ln()
					pdf.write (5,f"	  Rental Owing: Euro {row[7]}")
					pdf.ln()
					if row[8] == 0:
						pdf.write (5,f"	  Payment Terms: Immediate")
					else:
						pdf.write (5,f"	  Payment Terms: {row[8]} days")
					prop_display = prop_display + 1
					pdf.ln()
					pdf.write (5,f"	---------------------------------------------------------------------------------------------------------")
					pdf.ln()
				pdf.set_text_color(255,0,0)
				pdf.write (5,f"	     ~ Invoice Date: {inv[2]} with an Invoice Due Date: {invoice_due_date}")
				blank_report_check = blank_report_check + 1
				pdf.set_text_color(0,0,0)
				pdf.ln()
			pdf.set_left_margin (20)
		if prop_display > 1:
			pdf.ln()
			pdf.ln()
	

	file_path = "C:/Users/DemetrisManias/Desktop/code/djangoproject/static/reports/"
	report_name = file_path+"Open Invoices Report ("+str(today)+").pdf"
	pdf.output (report_name)

	# send email to (email address, email subject, report name and "file path and name") - fixed body text for email
	if rep_output == "Email" and check == "No":
		send_email.send_email(email,"Open Invoices Report ("+str(today)+")","Open Invoices Report",report_name,fname)
	elif rep_output == "Email" and check == "Yes" and blank_report_check > 0:
		send_email.send_email(email,"Open Invoices Report ("+str(today)+")","Open Invoices Report",report_name,fname)

	# display pdf file in new window - send file_name
	if rep_output == "Display" and check == "No":
		pdf_display.pdf_display(report_name)
	elif rep_output == "Display" and check == "Yes" and blank_report_check > 0:
		pdf_display.pdf_display(report_name)

	if mydb.is_connected():
		my_cursor.close()
		mydb.close()

def create_invoices(M,Y):

	import mysql.connector
	from datetime import date, datetime, timedelta

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

	my_cursor.execute("SELECT prop.prop_id, prop.prop_name, prop.prop_country, prop.prop_status, tenant.tenant_id FROM alivente.tenant JOIN alivente.prop ON prop.prop_id = tenant.prop_id WHERE tenant.tenant_current = 'Yes' and prop.prop_status = 'Active' ORDER BY tenant.tenant_id ASC")
	result = my_cursor.fetchall()

	months = (('January','01'),('February','02'),('March','03'),('April','04'),('May','05'),('June','06'),('July','07'),('August','08'),('September','09'),('October','10'),('November','11'),('December','12'))
	
	for num in months:
		if num [0] == M:
			temp_date = '01-'+num[1]+'-'+str(Y)
			new_invoice_date = datetime.strptime(temp_date, '%m-%d-%Y').date()
	
	# INSERT INDIVIDUAL INVOICES INTO INVOICE TABLE
	for row in result:
		sqlStuff = "INSERT INTO invoice (tenant_id,invoice_date,invoice_paid) VALUES (%s, %s, %s)"
		records = [
			(row[4],new_invoice_date,'No'),
		]
		my_cursor.executemany(sqlStuff, records)
		mydb.commit()

	if mydb.is_connected():
		my_cursor.close()
		mydb.close()

