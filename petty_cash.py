def petty_cash(rep_output, email, fname):

	import mysql.connector
	from datetime import date
	import fpdf
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

	# TABLE JOINS ON PRIMARY KEY (FOR PROP, ISSUES AND ISSUES_DETAILS TABLES)
	my_cursor.execute("SELECT * FROM alivente.petty_cash ORDER BY petty_cash.petty_cash_date ASC")
	result_transactions = my_cursor.fetchall()

	import fpdf
	pdf = fpdf.FPDF(format='A4')
	pdf.add_page()
	w = 210
	h = 297 

	pdf.ln()
	pdf.ln()
	pdf.ln()
	pdf.set_font("Arial", "BU", size=16)
	pdf.set_left_margin (10)
	pdf.ln()
	pdf.write (5,f"PETTY CASH")
	pdf.set_left_margin (0)
	pdf.ln()
	pdf.ln()
	pdf.set_font("Arial", "B", size=12)
	pdf.set_left_margin (20)
	pdf.set_fill_color (211,211,211)
	pdf.cell(w=30, h = 10, txt = 'Date', border = 1, ln = 0, align = 'C', fill = True, link = '')
	pdf.cell(w=120, h = 10, txt = 'Description', border = 1, ln = 0, align = 'C', fill = True, link = '')
	pdf.cell(w=20, h = 10, txt = 'Amount', border = 1, ln = 0, align = 'C', fill = True, link = '')
	pdf.ln()

	balance = 0
	for line in result_transactions:
		pdf.set_font("Arial", "", size=12)
		pdf.set_left_margin (20)
		# pdf.multi_cell(w=30, h = 8, txt = str(line[1]), border = 1, align = 'C', fill = False)
		pdf.cell(w=30, h = 8, txt = str(line[1]), border = 1, ln = 0, align = 'C', fill = False, link = '')
		descr = (line[2])[:60]
		# pdf.multi_cell(w=120, h = 8, txt = str(descr), border = 1, align = 'J', fill = False)
		pdf.cell(w=120, h = 8, txt = str(descr), border = 1, ln = 0, align = 'J', fill = False, link = '')
		if line[4] == "CR":
			neg = line [3] * -1
			pdf.cell(w=20, h = 8, txt = str(neg), border = 1, ln = 0, align = 'R', fill = False, link = '')
			balance = balance + neg
		elif line[4] == "DR":
			pdf.cell(w=20, h = 8, txt = str(line[3]), border = 1, ln = 0, align = 'R', fill = False, link = '')
			balance = balance + line[3]
		pdf.ln()

	pdf.set_font("Arial", "B", size=12)
	pdf.set_left_margin (20)
	pdf.set_fill_color (211,211,211)
	pdf.cell(w=30, h = 10, txt = str(today), border = 1, ln = 0, align = 'C', fill = True, link = '')
	pdf.cell(w=120, h = 10, txt = 'Closing Balance', border = 1, ln = 0, align = 'L', fill = True, link = '')
	pdf.cell(w=20, h = 10, txt = str(balance), border = 1, ln = 0, align = 'R', fill = True, link = '')
	pdf.ln()
		
	file_path = "C:/Users/DemetrisManias/Desktop/code/djangoproject/static/reports/"
	report_name = file_path+"Petty Cash ("+str(today)+").pdf"
	pdf.output (report_name)

	# send email to (email address, email subject, report name and "file path and name") - fixed body text for email
	if rep_output == "Email":
		send_email.send_email(email,"Petty Cash ("+str(today)+")","Petty Cash Report",report_name,fname)

	# display pdf file in new window - send file_name
	if rep_output == "Display":
		pdf_display.pdf_display(report_name)

	if mydb.is_connected():
		my_cursor.close()
		mydb.close()
