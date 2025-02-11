def db_create ():

	import mysql.connector
	import pdf_file_insert
	
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

	# CREATE DATABASE
	# my_cursor.execute ("CREATE DATABASE prop_mgmt")
	# my_cursor.execute ("SHOW DATABASES")
	# for db in my_cursor:
	#	  print (db[0])

	# DELETING OLD PROP TABLE
	my_sql = "DROP TABLE IF EXISTS prop"
	my_cursor.execute(my_sql)

	# CREATE NEW TABLE PROP
	my_cursor.execute("CREATE TABLE prop (prop_id INTEGER AUTO_INCREMENT PRIMARY KEY,prop_name VARCHAR (255),prop_address1 VARCHAR (255),prop_address2 VARCHAR (255),prop_suburb VARCHAR (255),prop_city VARCHAR (255),prop_province VARCHAR (255),prop_country VARCHAR (255),prop_pcode VARCHAR (255),prop_floor_area INTEGER (4),prop_year_built INTEGER (4),prop_status VARCHAR (255),prop_available_for_rent VARCHAR (255),prop_title_deed VARCHAR (255),prop_title_deed_status VARCHAR (255),prop_electricity VARCHAR(255),prop_water VARCHAR(255),prop_refuse VARCHAR(255),prop_property_tax VARCHAR(255), prop_sewerage VARCHAR(255),prop_insurance VARCHAR(255))")
	# my_cursor.execute ("SHOW TABLES")
	# for table in my_cursor:
	#	print (table[0])

	# INSERT MULTIPLE RECORDS INTO PROP TABLE
	sqlStuff = "INSERT INTO prop (prop_name,prop_address1,prop_address2,prop_suburb,prop_city,prop_province,prop_country,prop_pcode,prop_floor_area,prop_year_built,prop_status,prop_available_for_rent,prop_title_deed,prop_title_deed_status,prop_electricity,prop_water,prop_refuse,prop_property_tax,prop_sewerage,prop_insurance) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
	records = [
		('Palikaridi','Apartment 201','Evagora Palikaridi 3','Agios Dometios','Nicosia','Nicosia','Cyprus','2369',88,2010,'Active','Yes','Palikaridi - Title Deed.pdf','Yes','Meter: 962943','090 741 321 158 970','05 000 723 5','282 833 73','Not Applicable','699455'),
		('Foti Pitta','Apartment 204','Foti Pitta 13','Engomi','Nicosia','Nicosia','Cyprus','2408',90,2000,'Active','Yes','Foti Pitta - Title Deed.pdf','Yes','Not Available','0905964 2221946 0 ','283373/3/21','283373/3/21','Not Applicable','699456'),
		('Pindarou','Apartment 701, Vamiko/Tymvio Tower','Pindarou 23','','Nicosia','Nicosia','Cyprus','1060',165,1982,'Active','Yes','Pindarou - Title Deed.pdf','Yes','Not Available','0205184 2310020 5','251827/3/21','251827/3/21','Not Applicable','699452'),
		('Eleftheroupoleos','Flat 16, Oriana Court','Elftheroupoleos 6','Strovolos','Nicosia','Nicosia','Cyprus','2001',140,1973,'Active','Yes','Eleftheroupoleos - Title Deed.pdf','Yes','Meter: 211976','0101770 1827552 7','266521 ','266521 ','Not Available','699453'),
		('Apolloneon - Demetri','Office 103','Agias Annas 4','Strovolos','Nicosia','Nicosia','Cyprus','2054',77,2010,'Active','Yes','Apolloneon - Demetri - Title Deed.pdf','Yes','Not Available','Not Available','Not Available','Not Available','Not Available','Not Insured'),
		('Dikaiosynis','Dikaiosynis 13A','','Engomi','Nicosia','Nicosia','Cyprus','2412',367,2007,'Active','No','Dikaiosynis - Title Deed.pdf','Yes','295 910 696 29','170 796 721 187 079','309760/2/9','309760/2/9','241 476 700 012 00','699460'),
		('Ionion - Villa 24','Ionion Seafront Villas, Villa 24','Aristoteli Valaoriti 7','Agia Thekla','Sotira','Famagusta','Cyprus','5390',127,2007,'Active','No','Inonion - Villa 24 - Title Deed.pdf','No','384 193 123 01','99-009-0007-24-0554 or 283373','02-011-007-00-024-01A','99-009-0007-24-0554 or 283373','Not Applicable','699458'),
		('Ionion - Villa H4','Ionion Seafront Villas, Villa H4','Aristoteli Valaoriti 7','Agia Thekla','Sotira','Famagusta','Cyprus','5390',186,2014,'Active','No','Ionion - Villa H4 - Title Deed.pdf','No','689 707 644 91','99-009-0007-00-0H04 or 283373','02-011-007-00-0H4-01A','99-009-0007-00-0H04 or 283373','Not Applicable','699457'),
		('Athens - First Floor','First Floor Apartment','Afaias 15','Palaio Psychiko','Athens','Attiki','Greece','15452',121,1974,'Active','Yes','Athens - First Floor - Title Deed.pdf','Yes','Meter: 3138572','Meter: A97M44812','Not Available','Not Available','Not Available','361145'),
		('Athens - Second Floor','Second Floor Apartment','Afaias 15','Palaio Psychiko','Athens','Attiki','Greece','15452',121,1974,'Active','Yes','Athens - Second Floor - Title Deed.pdf','Yes','Meter: 3138573','Meter: A96E64201','Not Available','Not Available','Not Available','361145'),
		('Athens - Third Floor','Third Floor Apartment','Afaias 15','Palaio Psychiko','Athens','Attiki','Greece','15452',121,1974,'Active','Yes','Athens - Third Floor - Title Deed.pdf','Yes','Meter: 3138574','Meter: A97M44827','Not Available','Not Available','Not Available','361145'),
		('Spain - Eusebi Guell','Plaza Eusebi Guell 12','Bajos 1','Pedralbes','Barcelona','Barcelona','Spain','8034',81,1978,'Active','Yes','Spain - Eusebi Guell - Title Deed.pdf','Yes','Not Available','Not Available','Not Available','Not Available','Not Available','660056223'),
	]
	my_cursor.executemany(sqlStuff, records)
	mydb.commit()

	# # INSERT TITLE DEED PDFs INTO DATABASE AS BLOBs
	# file_path = "C:/Users/DemetrisManias/Desktop/mysql/Title Deeds/"
	# pdf_file_insert.db_title_insert (1,(file_path+"Pallikaridi - Title Deed.pdf"))
	# pdf_file_insert.db_title_insert (2,(file_path+"Pindarou - Title Deed.pdf"))
	# pdf_file_insert.db_title_insert (3,(file_path+"Eleftheroupoleos - Title Deed.pdf"))
	# pdf_file_insert.db_title_insert (4,(file_path+"Foti Pitta - Title Deed.pdf"))
	# pdf_file_insert.db_title_insert (5,(file_path+"Dummy - Title Deed.pdf"))
	# pdf_file_insert.db_title_insert (6,(file_path+"Dikaiosynis - Title Deed.pdf"))
	# pdf_file_insert.db_title_insert (9,(file_path+"Dummy - Title Deed.pdf"))
	# pdf_file_insert.db_title_insert (10,(file_path+"Dummy - Title Deed.pdf"))
	# pdf_file_insert.db_title_insert (11,(file_path+"Dummy - Title Deed.pdf"))
	# pdf_file_insert.db_title_insert (12,(file_path+"Dummy - Title Deed.pdf"))

	# DELETING OLD TENANT TABLE
	my_sql = "DROP TABLE IF EXISTS tenant"
	my_cursor.execute(my_sql)

	# CREATE NEW TABLE TENANT
	my_cursor.execute("CREATE TABLE tenant (tenant_id INTEGER AUTO_INCREMENT PRIMARY KEY,prop_id INTEGER,tenant_type VARCHAR (255),tenant_name VARCHAR (255),tenant_contact_person VARCHAR (255),tenant_contact_number VARCHAR (255),tenant_email VARCHAR (255),tenant_deposit INTEGER (10),tenant_lease_start_date DATE,tenant_lease_end_date DATE,tenant_rental_type VARCHAR (255),tenant_renewal VARCHAR (255),tenant_renewal_period INTEGER (3),tenant_rent INTEGER (5),tenant_levies INTEGER (4),tenant_payment_terms INTEGER (3),tenant_current VARCHAR (255),tenant_lease_agreement VARCHAR(255))")
	# my_cursor.execute ("SHOW TABLES")
	# for table in my_cursor:
	#	print (table[0])

	# INSERT MULTIPLE RECORDS INTO TENANT TABLE
	sqlStuff = "INSERT INTO tenant (prop_id,tenant_type,tenant_name,tenant_contact_person,tenant_contact_number,tenant_email,tenant_deposit,tenant_lease_start_date,tenant_lease_end_date,tenant_rental_type,tenant_renewal,tenant_renewal_period,tenant_rent,tenant_levies,tenant_payment_terms,tenant_current,tenant_lease_agreement) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
	records = [
		(1,'Individual','Sacha Mamou and James Luc-Sebaoun','Sacha Mamou and James Luc-Sebaoun','+33651200465 and +33769672329','sacha.mamou2@gmail.com and james.ls@icloud.com',930,'2024-09-01','2025-08-31','Monthly','Yes',60,945,30,0,'Yes',''),
		(3,'Company','Capacitor Partners Limited','Michael Tyrimos','+35799660928','michael.tyrimos@capacitorpartners.com',1250,'2023-07-01','2026-06-30','Monthly','Yes',60,1250,45,0,'Yes',''),
		(4,'Company','Assetworth Limited','Andreas Evangelou','+35799343298','andreas.evangelou@assetworth.com.cy',1064,'2024-09-01','2025-11-30','Monthly','Yes',60,1064,35,60,'Yes',''),
		(2,'Individual','Elisavet Solomonidou','Elisavet Solomonidou','+306948881091','solomonidou.elisabeth@yahoo.com',850,'2024-05-01','2026-06-30','Monthly','Yes',60,850,30,0,'Yes',''),
		(5,'Individual','Chrystalla Katelari and Antigoni Andreou','Chrystalla Katelari and Antigoni Andreou','+35799266001 and +35796272030','katelari_chrystalla@hotmail.com and antigoni_andreou@outlook.com',750,'2024-10-01','2026-09-30','Monthly','Yes',60,750,30,0,'Yes',''),
		(9,'Individual','Anastasia Spiropoulou and Constantinos Souvatzoglou','Anastasia Spiropoulou and Constantinos Souvatzoglou','+30 99 999999','nastaziaspy@googlemail.com and k.souvatzoglou@gmail.com',875,'2025-03-01','2027-02-28','Monthly','Yes',60,925,0,0,'Yes',''),
		(10,'Individual','Tenant - Athens 2','XXX','+30 99 999999','XXX@XXX.com',999,'2024-09-01','2027-08-31','Monthly','Yes',60,999,99,0,'Yes',''),
		(11,'Individual','Tenant - Athens 3','XXX','+30 99 999999','XXX@XXX.com',999,'2024-09-01','2027-08-31','Monthly','Yes',60,999,99,0,'Yes',''),
		(12,'Individual','Tenant - Spain - Test 1 (Non)','XXX','+34 99 999999','XXX@XXX.com',999,'2024-09-01','2024-08-31','Monthly','Yes',60,999,99,0,'No',''),
		(12,'Individual','Tenant - Spain - Test 2 (Active)','XXX','+34 99 999999','XXX@XXX.com',999,'2024-09-01','2024-08-31','Monthly','Yes',60,999,99,0,'No',''),
	]
	my_cursor.executemany(sqlStuff, records)
	mydb.commit()

	# INSERT LEASE AGREEMENT PDFs INTO DATABASE AS BLOBs
	# file_path = "C:/Users/DemetrisManias/Desktop/mysql/"
	# pdf_file_insert.db_lease_insert (1,(file_path+"Integrations.pdf"))
	# pdf_file_insert.db_lease_insert (2,(file_path+"Integrations.pdf"))
	# pdf_file_insert.db_lease_insert (3,(file_path+"Integrations.pdf"))
	# pdf_file_insert.db_lease_insert (4,(file_path+"Integrations.pdf"))
	# pdf_file_insert.db_lease_insert (5,(file_path+"Integrations.pdf"))
	# pdf_file_insert.db_lease_insert (9,(file_path+"Integrations.pdf"))
	# pdf_file_insert.db_lease_insert (10,(file_path+"Integrations.pdf"))
	# pdf_file_insert.db_lease_insert (11,(file_path+"Integrations.pdf"))
	# pdf_file_insert.db_lease_insert (12,(file_path+"Integrations.pdf"))

	# DELETING OLD INVOICE TABLE
	my_sql = "DROP TABLE IF EXISTS invoice"
	my_cursor.execute(my_sql)

	# CREATE NEW TABLE INVOICE
	my_cursor.execute("CREATE TABLE invoice (invoice_id INTEGER AUTO_INCREMENT PRIMARY KEY,tenant_id INTEGER,invoice_date DATE,invoice_paid VARCHAR (10))")
	# my_cursor.execute ("SHOW TABLES")
	# for table in my_cursor:
	#	print (table[0])

	# INSERT MULTIPLE RECORDS INTO INVOICE TABLE
	sqlStuff = "INSERT INTO invoice (tenant_id,invoice_date,invoice_paid) VALUES (%s, %s, %s)"
	records = [
		(1,'2024-12-01','No'),
		(2,'2024-12-01','Yes'),
		(3,'2024-12-01','No'),
		(3,'2024-11-01','No'),
		(3,'2024-10-01','No'),
		(3,'2024-09-01','No'),
		(3,'2024-08-01','Yes'),
		(4,'2024-12-01','No'),
		(5,'2025-01-01','No'),
		(9,'2024-11-01','No'),
		(9,'2024-10-01','No'),
		(10,'2024-08-01','No'),
		(10,'2024-09-01','No'),
	]
	
	my_cursor.executemany(sqlStuff, records)
	mydb.commit()

	# DELETING OLD PETTY CASH TABLE
	my_sql = "DROP TABLE IF EXISTS petty_cash"
	my_cursor.execute(my_sql)

	# CREATE NEW PETTY CASH INVOICE
	my_cursor.execute("CREATE TABLE petty_cash (petty_cash_id INTEGER AUTO_INCREMENT PRIMARY KEY,petty_cash_date VARCHAR (255),petty_cash_description VARCHAR (60),petty_cash_amount DECIMAL (5,2), petty_cash_dr_cr VARCHAR (2))")
	# my_cursor.execute ("SHOW TABLES")
	# for table in my_cursor:
	#	print (table[0])

	# INSERT MULTIPLE RECORDS INTO PETTY CASH TABLE
	sqlStuff = "INSERT INTO petty_cash (petty_cash_date, petty_cash_description, petty_cash_amount, petty_cash_dr_cr) VALUES (%s, %s, %s, %s)"
	records = [
		('2024-07-01','Opening Balance',51.29,'DR'),
		('2024-07-03','Apollonio: labour for carrying washing machine up the stairs',30.00,'CR'),
		('2024-07-10','Alivente: Top Up',100.00,'DR'),		
		('2024-08-16','Sklaveniti 2 x anti mould sprays for Lykavitto storeroom',10.94,'CR'),
		('2024-08-17','Princess Lykavitto cleaned storeroom',15.00,'CR'),
		('2024-08-17','Bought rubbish bags for Lykavitto @ Green Tree',1.29,'CR'),
	]
	my_cursor.executemany(sqlStuff, records)
	mydb.commit()

	# DELETING OLD ISSUES TABLE
	my_sql = "DROP TABLE IF EXISTS issues"
	my_cursor.execute(my_sql)

	# CREATE NEW TABLE ISSUES
	my_cursor.execute("CREATE TABLE issues (issues_id INTEGER AUTO_INCREMENT PRIMARY KEY,prop_id INTEGER,issues_heading VARCHAR (255),issues_description VARCHAR (255), issues_date_logged DATE, issues_status VARCHAR (255), issues_resolution_date DATE, issues_resolving_user VARCHAR (255))")
	# my_cursor.execute ("SHOW TABLES")
	# for table in my_cursor:
	#	print (table[0])

	# INSERT MULTIPLE RECORDS INTO ISSUES TABLE
	sqlStuff = "INSERT INTO issues (prop_id,issues_heading,issues_description,issues_date_logged,issues_status,issues_resolution_date,issues_resolving_user) VALUES (%s, %s, %s, %s, %s, %s, %s)"
	records = [
		(1,'Painting of Reception','Have to repaint the whole of reception due to water damage.','2024-11-24','Unresolved','1900-01-01',''),
		(4,'Tiling of Balcony','Have to retile the entire baclony to avoid water going through the slab','2024-12-09','Unresolved','1900-01-01',''),
		(2,'Replace Airconditioner','Need to replace the airconditioner in the Boardroom','2024-10-15','Resolved','2024-12-23','DM'),
		(2,'Clean Reception','Need to take Princess to clean the reception','2024-11-16','Resolved','2024-12-24','DM'),
		(1,'Sealing of Door','Have to seal door so that water does not come through','2024-11-20','Unresolved','1900-01-01',''),
		(5,'Mould on Ceiling','Humidity in Bedroom','2024-06-20','Issue','1900-01-01',''),
	]
	my_cursor.executemany(sqlStuff, records)
	mydb.commit()

	# DELETING OLD ISSUES_DETAILS TABLE
	my_sql = "DROP TABLE IF EXISTS issues_details"
	my_cursor.execute(my_sql)

	# CREATE NEW TABLE ISSUES_DETAILS
	my_cursor.execute("CREATE TABLE issues_details (isues_details_id INTEGER AUTO_INCREMENT PRIMARY KEY,issues_id INTEGER,issues_details_comment VARCHAR (255),issues_details_user VARCHAR (255), issues_details_date DATE)")
	# my_cursor.execute ("SHOW TABLES")
	# for table in my_cursor:
	#	print (table[0])

	# INSERT MULTIPLE RECORDS INTO ISSUES_DETAILS TABLE
	sqlStuff = "INSERT INTO issues_details (issues_id,issues_details_comment,issues_details_user,issues_details_date) VALUES (%s, %s, %s, %s)"
	records = [
		(1,'OK.  Perfect.  Confirm a date for next month for him to come and complete.','DM','2024-12-04'),
		(1,'Spoke to Marko, he will send someone to address this right away.','DM','2024-12-01'),
		(1,'Marko confirmed that Vasilli would come today, but Vasilli did not come.  Will  call Marko again.','SS','2024-12-01'),
		(1,'This is urgent, please ensure that we resolve this ASAP.','DM','2024-12-02'),
		(1,'I spoke to Marko.  He went past.  He says that we need to wait for the slab to dry out first.','SS','2024-12-03'),
		(3,'We need to replace the airconditioner with a 24,000 BTU Bosch unit.','SS','2024-11-18'),
		(4,'Princess completed the cleaning','SS','2024-12-23'),
		(2,'We will need to uplift all of the old tiles on the balcony','SS','2024-12-09'),
		(2,'What is the toatl cost for this work?','DM','2024-12-10'),
		(5,'I will speak to Mathew to get a quote','SS','2024-12-04'),
		(6,'Running de-humidifiers','SS','2024-11-05'),
	]
	my_cursor.executemany(sqlStuff, records)
	mydb.commit()

	if mydb.is_connected():
		my_cursor.close()
		mydb.close()
