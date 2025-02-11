def supplier_report (supplier, rep_output, email, fname):

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
	pdf.cell(w=0,h=8, txt="SUPPLIER DETAILS REPORT - (" + str(today) + ")", align="C")
	# pdf.set_font("Arial", "BU", size=20)
	# pdf.write (5,"Property Details Report")
	# pdf.set_font("Arial", "B", size=16)
	# pdf.write (5,f" (Date: {today})")
	pdf.ln()
	pdf.ln()

	pdf.set_font("Arial", size=14)
	pdf.set_left_margin (10)

	my_cursor.execute("SELECT supplier.supplier_contact_person, supplier.supplier_contact_number, supplier.supplier_email, supplier.supplier_company_name, supplier.supplier_role, supplier.supplier_country FROM alivente.supplier ORDER BY supplier.supplier_contact_person ASC")
	result = my_cursor.fetchall()

	for row in result:
		if supplier == "All":
			pdf.set_left_margin (0)
			pdf.set_font("Arial", "BU", size=14)
			pdf.set_left_margin (10)
			pdf.write (5,f"Contact Person: {row[0]}")
			pdf.ln()
			pdf.set_font("Arial", size=12)
			pdf.set_left_margin (15)
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	Contact Number: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[1]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	Contact Email: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[2]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	Supplier Company: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[3]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	Supplier Role: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[4]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	Country: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[5]}")
			pdf.ln()
			pdf.ln()
			pdf.set_left_margin (10)
			pdf.ln()
			pdf.set_left_margin (10)
		elif supplier == row [0]:
			pdf.set_left_margin (0)
			pdf.set_font("Arial", "BU", size=14)
			pdf.set_left_margin (10)
			pdf.write (5,f"Contact Person: {row[0]}")
			pdf.ln()
			pdf.set_font("Arial", size=12)
			pdf.set_left_margin (15)
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	Contact Number: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[1]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	Contact Email: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[2]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	Supplier Company: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[3]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	Supplier Role: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[4]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	Country: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[5]}")
			pdf.ln()
			pdf.ln()
			pdf.set_left_margin (10)
			pdf.ln()
			pdf.set_left_margin (10)

	file_path = "C:/Users/DemetrisManias/Desktop/code/djangoproject/static/reports/"
	report_name = file_path+"Supplier Details Report ("+str(today)+").pdf"
	pdf.output (report_name)

	# send email to (email address, email subject, report name and "file path and name") - fixed body text for email
	if rep_output == "Email":
		send_email.send_email(email,"Supplier Details Report ("+str(today)+")","Supplier Details Report",report_name,fname)

	# display pdf file in new window - send file_name
	if rep_output == "Display":
		pdf_display.pdf_display(report_name)

	if mydb.is_connected():
		my_cursor.close()
		mydb.close()
