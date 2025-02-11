def send_email (email_address, subject, report_name, file_name, fname):

	import smtplib
	import getpass
	from email.mime.text import MIMEText
	from email.mime.multipart import MIMEMultipart
	from email.mime.base import MIMEBase
	from email import encoders

	
	smtp_object = smtplib.SMTP('smtp.gmail.com', 587)
	smtp_object.ehlo()
	smtp_object.starttls()

	# email = getpass.getpass("Email: ")
	email = "demetrimanias@gmail.com"
	# password = getpass.getpass("Password: ")
	# need to go to gmail and generate an App Password (Go to Gmail --> Settings --> See All Settings --> Accounts and Import --> Other Google Account Settings (in Change Account Settings) --> Security --> 2-Step Verification --> App Passwords)
	password = "nfvb been waqz wwks"
	smtp_object.login(email,password)

	from_address = email
	to_address = email_address
	
	# Alternative way to define body of email, but had problems with left justification on mobile

	# body = f"""
	# To Whom It May Concern,

	# Please find attached the {report_name} Report as requested.

	# Kind Regards,

	# Demetrios
	# """

	body = (f"Dear {fname},\n\nPlease find attached the {report_name}, as requested.\n\nKind Regards,\n\nAlivente Property Management System\n")

	msg=MIMEMultipart()
	msg["From"] = email
	msg["To"] = email_address
	msg["Subject"] = subject

	msg.attach(MIMEText(body, 'plain'))

	# prepare file for sending
	#open for read and for binary
	attachment = open (file_name,'rb')

	# encode in base 64
	attachment_package = MIMEBase('application', 'octet-stream')
	attachment_package.set_payload((attachment).read())
	encoders.encode_base64(attachment_package)
	attachment_package.add_header('Content-Disposition', "attachment; filename= " + report_name+".pdf")
	
	msg.attach(attachment_package)

	text = msg.as_string()

	smtp_object.sendmail(from_address,to_address,text)

	smtp_object.quit()