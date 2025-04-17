def lease_report (property, rep_output, email, fname):

	import mysql.connector
	from datetime import date
	import pdf_display
	import send_email
	import os
	from django.conf import settings
	from django.templatetags.static import static

	def get_static_file_path(relative_path):
		if settings.DEBUG:
        	# Development - serve from STATICFILES_DIRS
			return os.path.join(settings.BASE_DIR, 'static', relative_path)
		else:
			# Production - serve from STATIC_ROOT
			return os.path.join(settings.STATIC_ROOT, relative_path)

	mydb = None
	try:
		# CONNECT TO DATABASE
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

		lease_agreements_dir = get_static_file_path("lease_agreements")
		print ("la_dir")
		print(lease_agreements_dir)

		lease_agreement_url = static ("lease_agreements/" + property + " - Lease Agreements.pdf")
		print ("URL")
		print (lease_agreement_url)

		report_name = os.path.join(settings.STATIC_ROOT, "lease_agreements/" + property + " - Lease Agreement.pdf")
		print("rn")
		print(report_name)
		
		# send email to (email address, email subject, report name and "file path and name") - fixed body text for email
		if rep_output == "Email":
			send_email.send_email(email, property + " - Lease Agreement", property + " - Lease Agreement", report_name, fname)

		# display pdf file in new window - send file_name
		if rep_output == "Display":
			pdf_display.pdf_display(report_name)

	finally:
		# Ensure resources are closed
		if mydb is not None and mydb.is_connected():
			my_cursor.close()
			mydb.close()
