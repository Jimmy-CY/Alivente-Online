def title_report (property, rep_output, email, fname):

	import mysql.connector
	from datetime import date
	import pdf_display
	import send_email

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
	pdf = fpdf.FPDF(format='A4')
	# pdf.add_page()
	# pdf.set_font("Arial", "BU", size=20)
	# pdf.cell(w=0,h=8, txt="TITLE DEED REPORT - (" + str(today) + ")", align="C")
	# pdf.set_font("Arial", "BU", size=20)
	# pdf.write (5,"Property Details Report")
	# pdf.set_font("Arial", "B", size=16)
	# pdf.write (5,f" (Date: {today})")
	# pdf.ln()
	# pdf.ln()

	pdf.set_font("Arial", size=14)
	pdf.set_left_margin (10)

	my_cursor.execute("SELECT * FROM prop ORDER BY prop.prop_country ASC, prop.prop_name ASC")
	result = my_cursor.fetchall()

	file_path = "C:/Users/DemetrisManias/Desktop/code/djangoproject/static/title_deeds/"

	report_name = file_path+property+" - Title Deed.pdf"
	
	# send email to (email address, email subject, report name and "file path and name") - fixed body text for email
	if rep_output == "Email":
		try:
			send_email.send_email(email,property+" - Title Deed",property+" - Title Deed",report_name,fname)
		except:
			pass

	# display pdf file in new window - send file_name
	if rep_output == "Display":
		try:
			pdf_display.pdf_display(report_name)
		except:
			pass

	if mydb.is_connected():
		my_cursor.close()
		mydb.close()
