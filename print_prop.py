def prop_report (property, rep_output, email, fname):

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
	pdf.cell(w=0,h=8, txt="PROPERTY DETAILS REPORT - (" + str(today) + ")", align="C")
	pdf.ln()
	pdf.ln()

	pdf.set_font("Arial", size=14)
	pdf.set_left_margin (10)
	my_cursor.execute("SELECT prop.prop_name, prop.prop_address1, prop.prop_address2, prop.prop_suburb, prop.prop_city, prop.prop_province, prop.prop_country, prop.prop_pcode, prop.prop_floor_area, prop.prop_year_built, prop.prop_status, prop.prop_available_for_rent, prop.prop_title_deed, prop.prop_title_deed_status, prop.prop_electricity, prop.prop_water, prop.prop_refuse, prop.prop_property_tax, prop.prop_sewerage, prop.prop_insurance FROM alivente.prop ORDER BY prop.prop_country ASC, prop.prop_name ASC")
#	my_cursor.execute("SELECT * FROM prop ORDER BY prop.prop_country ASC, prop.prop_name ASC")
	result = my_cursor.fetchall()
	print(result)
	
	page_break = 0

	for row in result:
		if property == "All":
			if page_break == 2:
				pdf.add_page()
				page_break = 0
			page_break = page_break + 1
			pdf.set_font("Arial", "BU", size=14)
			pdf.set_left_margin (10)
			pdf.write (5,f"Property Name: {row[0]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			# pdf.set_left_margin (15)
			pdf.write (5,f"    Address: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[1]}")
			pdf.ln()
			# pdf.set_left_margin (33)
			if row[2] != "":
				pdf.write (5,f"                    {row[2]}")
				pdf.ln()
			if row[3] != "":
				pdf.write (5,f"                    {row[3]}")
				pdf.ln()
			pdf.write (5,f"                    {row[4]}")
			pdf.ln()
			pdf.write (5,f"                    {row[5]}")
			pdf.ln()
			pdf.write (5,f"                    {row[6]}")
			pdf.ln()
			pdf.write (5,f"                    {row[7]}")
			# pdf.ln()
			# pdf.set_left_margin (15)
			# pdf.set_left_margin (15)
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"    Square Meters: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[8]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Year Built: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[9]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Electricty Account No.: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[14]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Water Account No.: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[15]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Municipality (Refuse) Account No.: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[16]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Municipality (Annual Property Tax) Account No.: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[17]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Sewerage Account No.: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[18]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Insurance Policy Number: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[19]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Status: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[10]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Available for Rent: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[11]}")
			pdf.ln()
			pdf.ln()
			# pdf.set_left_margin (10)
		elif property == row [0]:
			if page_break == 2:
				pdf.add_page()
				page_break = 0
			page_break = page_break + 1
			pdf.set_font("Arial", "BU", size=14)
			pdf.set_left_margin (10)
			pdf.write (5,f"Property Name: {row[0]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			# pdf.set_left_margin (15)
			pdf.write (5,f"    Address: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[1]}")
			pdf.ln()
			# pdf.set_left_margin (33)
			if row[2] != "":
				pdf.write (5,f"                    {row[2]}")
				pdf.ln()
			if row[3] != "":
				pdf.write (5,f"                    {row[3]}")
				pdf.ln()
			pdf.write (5,f"                    {row[4]}")
			pdf.ln()
			pdf.write (5,f"                    {row[5]}")
			pdf.ln()
			pdf.write (5,f"                    {row[6]}")
			pdf.ln()
			pdf.write (5,f"                    {row[7]}")
			# pdf.ln()
			# pdf.set_left_margin (15)
			# pdf.set_left_margin (15)
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"    Square Meters: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[8]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Year Built: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[9]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Electricty Account No.: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[14]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Water Account No.: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[15]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Municipality (Refuse) Account No.: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[16]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Municipality (Annual Property Tax) Account No.: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[17]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Sewerage Account No.: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[18]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Insurance Policy Number: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[19]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Status: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[10]}")
			pdf.ln()
			pdf.set_font("Arial", "B", size=12)
			pdf.write (5,f"	   Available for Rent: ")
			pdf.set_font("Arial", size=12)
			pdf.write (5,f"{row[11]}")
			pdf.ln()
			pdf.ln()
			# pdf.set_left_margin (10)
		
	file_path = "C:/Users/DemetrisManias/Desktop/code/djangoproject/static/reports/"
	report_name = file_path+"Property Details Report ("+str(today)+").pdf"
	pdf.output (report_name)

	# send email to (email address, email subject, report name and "file path and name") - fixed body text for email
	if rep_output == "Email":
		send_email.send_email(email,"Property Details Report ("+str(today)+")","Property Details Report",report_name,fname)

	# display pdf file in new window - send file_name
	if rep_output == "Display":
		pdf_display.pdf_display(report_name)

	if mydb.is_connected():
		my_cursor.close()
		mydb.close()
