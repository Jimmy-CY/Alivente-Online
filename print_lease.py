def lease_report (property, rep_output, email, fname):

	import mysql.connector
	from datetime import date
	import pdf_display
	import send_email
	from django.conf import settings
	from django.templatetags.static import static

	# CONNECT TO DATBASE (FIRST HAVE TO LEAVE database line off until have created database)
	mydb = mysql.connector.connect(
		host = settings.DATABASES['default']['HOST'],
		port = settings.DATABASES['default']['PORT'],
		user = settings.DATABASES['default']['USER'],
		password = settings.DATABASES['default']['PASSWORD'],
		database = settings.DATABASES['default']['NAME'],
		auth_plugin = settings.DATABASES['default']['AUTH_PLUGIN'],
	)

	# CREATE CURSOR INSTANCE
	my_cursor = mydb.cursor()

	today=date.today()

#	file_path = "C:/Users/DemetrisManias/Desktop/code/djangoproject/static/lease_agreements/"
#	report_name = file_path+property+" - Lease Agreement.pdf"

	file_path = os.path.join(settings.STATIC_ROOT,property," - Lease Agreement.pdf")
	
	# send email to (email address, email subject, report name and "file path and name") - fixed body text for email
	if rep_output == "Email":
		send_email.send_email(email,property+" - Lease Agreement",property+" - Lease Agreement",report_name,fname)

	# display pdf file in new window - send file_name
	if rep_output == "Display":
		pdf_display.pdf_display(report_name)

	if mydb.is_connected():
		my_cursor.close()
		mydb.close()
