def fsr_report(rep_type, rep_date, rep_output, email, fname):

	import mysql.connector
	from datetime import date, datetime, timedelta
	import send_email
	import pdf_display
	# from fpdf import FPDF

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
	my_cursor.execute("SELECT prop.prop_name, issues.issues_heading, issues.issues_description, issues.issues_status, issues_details.issues_details_comment, issues_details.issues_details_user, issues_details.issues_details_date, issues.issues_resolution_date FROM alivente.issues JOIN alivente.prop ON prop.prop_id = issues.prop_id JOIN alivente.issues_details ON issues_details.issues_id = issues.issues_id ORDER BY issues.issues_id ASC, issues_details.issues_details_id DESC")
	result = my_cursor.fetchall()
	my_cursor.execute("SELECT issues.issues_heading FROM alivente.issues ORDER BY issues.issues_date_logged ASC")
	result_issue_heading = my_cursor.fetchall()
	my_cursor.execute("SELECT issues.issues_description FROM alivente.issues ORDER BY issues.issues_date_logged DESC")
	result_issue_description = my_cursor.fetchall()
	my_cursor.execute("SELECT prop.prop_name FROM alivente.prop ORDER BY prop.prop_country ASC, prop.prop_name ASC")
	result_properties = my_cursor.fetchall()
	result_status = ['Resolved','Unresolved','Issue']
	my_cursor.execute("SELECT * FROM alivente.petty_cash ORDER BY petty_cash.petty_cash_date ASC")
	result_transactions = my_cursor.fetchall()

	import fpdf
	pdf = fpdf.FPDF(format='A4')
	pdf.add_page()
	pdf.set_font("Arial", "BU", size=20)
	pdf.cell(w=0,h=8, txt="FRIDAY STATUS REPORT - (" + str(today) + ")", align="C")
	# pdf.write (5,"Friday Status Report")
	# pdf.set_font("Arial", "B", size=16)
	# pdf.write (5,f" (Date: {today})")
	# pdf.ln()
	# pdf.ln()

	# pdf.set_fill_color(r=255, g=0, b=0)
	# pdf.set_text_color(r=60, g=219, b=192)
	# pdf.cell(w=0,h-5, txt="This is text", border=1, align="C", ln=1, fill =1)
	# pdf.multi_cell(w=100, h=5, border=1, txt="My name is Demetri and I don't know what I am doing")

	pdf.set_font("Arial", size=14)
	pdf.set_left_margin (0)

	for status in result_status:
		pdf.ln()
		pdf.set_font("Arial", "BU", size=16)
		pdf.set_left_margin (10)
		pdf.ln()
		pdf.write (5,f"STATUS: {status.upper()}")
		pdf.set_left_margin (0)
		pdf.ln()
		# pdf.ln()
		# circle through countries in country and property name order
		for prop in result_properties:
			count_prop= 0
			pdf.set_left_margin (0)
			# circle through issues in the order of the date the issue was logged
			for issue in result_issue_heading:
				count_issue = 0
				pdf.set_left_margin (0)
				# issue_number = 1
				# circle through issue descriptions in the order that the issue was logged
				for issue_detail in result_issue_description:
					count_issue_description = 0
					# 7 Days only included in the Resolved Status Section (see line below)
					cut_off_date = rep_date - timedelta(days=(7))
					count_issue_details = 1
					for row in result:
						resolved_issue_date = row[7]
#						datetime_obj = datetime.strptime(str(row[7]),'%Y-%m-%d %H:%M:%S')
#						resolved_issue_date = datetime_obj.date()
						# Only items resolved in 7 days from the function input date rep_date to be shown
						if status == 'Resolved' and resolved_issue_date >= cut_off_date:
							# check for a match for property name, status (e.g. Resolved, etc.), issue heading and issue description
							if row[0] == prop[0] and row[3] == status and row[1] == issue [0] and row[2] == issue_detail [0]:
								if count_prop == 0:
									pdf.ln()
									pdf.set_font("Arial", "B", size=14)
									pdf.set_left_margin (15)
									pdf.write (5,f"{prop[0].upper()}")
									pdf.ln()
									# pdf.ln()
									count_prop = count_prop + 1
								if count_issue == 0:
									pdf.set_font("Arial", "B", size=12)
									pdf.set_left_margin (20)
									pdf.write (5,f"- {issue[0]} ")
									# pdf.ln()
									count_issue = count_issue + 1
								if count_issue_description == 0:
									pdf.set_font("Arial", "", size=12)
									# pdf.set_left_margin (20)
									pdf.write (5,f"({issue_detail[0]})")
									pdf.ln()
									count_issue_description = count_issue_description + 1
								if count_issue_details <= 3:
									pdf.set_font("Arial", "B", size=11)
									pdf.set_left_margin (28)
									date1=row[6]
#									date1 = row[6].date()
									# pdf.cell(w=0,h=5, txt=str(date1)+" ("+str(row[5])+") - " + str(row[4]), border=1, align="L")
									pdf.write (5,f"{date1} ({row[5]})")
									pdf.set_font("Arial", "", size=11)
									pdf.write (5,f" - {row[4]}")
									count_issue_details = count_issue_details + 1
									pdf.set_left_margin (0)
									pdf.ln()
								elif count_issue_details > 3 and rep_type == 'Detailed':
									pdf.set_font("Arial", "B", size=11)
									pdf.set_left_margin (28)
									date1 = row[6]
#									date1 = row[6].date()
									# pdf.cell(w=0,h=5, txt=str(date1)+" ("+str(row[5])+") - " + str(row[4]), border=1, align="L")
									pdf.write (5,f"{date1} ({row[5]})")
									pdf.set_font("Arial", "", size=11)
									pdf.write (5,f" - {row[4]}")
									count_issue_details = count_issue_details + 1
									pdf.set_left_margin (0)
									pdf.ln()
						if status == 'Unresolved' or status == 'Issue':
							if row[0] == prop[0] and row[3] == status and row[1] == issue [0] and row[2] == issue_detail [0]:
								if count_prop == 0:
									pdf.ln()
									pdf.set_font("Arial", "B", size=14)
									pdf.set_left_margin (15)
									pdf.write (5,f"{prop[0].upper()}")
									pdf.ln()
									# pdf.ln()
									count_prop = count_prop + 1
								if count_issue == 0:
									pdf.set_font("Arial", "B", size=12)
									pdf.set_left_margin (20)
									pdf.write (5,f"- {issue[0]} ")
									# pdf.ln()
									count_issue = count_issue + 1
								if count_issue_description == 0:
									pdf.set_font("Arial", "", size=12)
									# pdf.set_left_margin (20)
									pdf.write (5,f"({issue_detail[0]})")
									pdf.ln()
									count_issue_description = count_issue_description + 1
								if count_issue_details <= 3:
									pdf.set_font("Arial", "B", size=11)
									pdf.set_left_margin (28)
									date1 = row[6]
#									date1 = row[6].date()
									# pdf.cell(w=0,h=5, txt=str(date1)+" ("+str(row[5])+") - " + str(row[4]), border=1, align="L")
									pdf.write (5,f"{date1} ({row[5]})")
									pdf.set_font("Arial", "", size=11)
									# pdf.write (5,f" - {row[4]}")
									pdf.write (5,f" - {row[4]}")
									count_issue_details = count_issue_details + 1
									pdf.set_left_margin (0)
									pdf.ln()
								elif count_issue_details > 3 and rep_type == 'Detailed':
									pdf.set_font("Arial", "B", size=11)
									pdf.set_left_margin (28)
									date1 = row [6]
#									date1 = row[6].date()
									# pdf.cell(w=0,h=5, txt=str(date1)+" ("+str(row[5])+") - " + str(row[4]), border=1, align="L")
									pdf.write (5,f"{date1} ({row[5]})")
									pdf.set_font("Arial", "", size=11)
									pdf.write (5,f" - {row[4]}")
									count_issue_details = count_issue_details + 1
									pdf.set_left_margin (0)
									pdf.ln()

				# issue_number = issue_number + 1

	pdf.ln()
	pdf.ln()
	pdf.ln()
	pdf.add_page()
	w = 210
	h = 297 
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
	report_name = file_path+"Friday Status Report ("+str(today)+").pdf"
	pdf.output (report_name)

	# send email to (email address, email subject, report name and "file path and name") - fixed body text for email
	if rep_output == "Email":
		send_email.send_email(email,"Friday Status Report ("+str(today)+")","Friday Status Report",report_name,fname)

	# display pdf file in new window - send file_name
	if rep_output == "Display":
		pdf_display.pdf_display(report_name)

	if mydb.is_connected():
		my_cursor.close()
		mydb.close()

	# Functionality to delete a file from a folder.....
	# import os 
	# try: 
	# 	os.remove (report_name)
	# except:
	# 	print("Couldn't remove the file")

