# INSERT FILE INTO DATABASE

def db_lease_insert (tenant_identification, file_location):

	import mysql.connector

	mydb = mysql.connector.connect(
			host = "localhost",
			user = "root",
			password = "Smiles123$",
			database = "alivente",
			auth_plugin = "mysql_native_password",
			)

	my_cursor = mydb.cursor()

	def convertToBinaryData(file_url):
	    # Convert digital data to binary format
	    with open(file_url, 'rb') as file:
	        binaryData = file.read()
	    return binaryData

	def insertBLOB(tenant_no, upload_file):
	    try:
	        update_query = "UPDATE tenant SET tenant_lease_agreement = %s WHERE tenant_id = %s"

	        db_file = convertToBinaryData(upload_file)
	        values = (db_file, tenant_no)

	        my_cursor.execute(update_query,values)
	        mydb.commit()

	    except mysql.connector.Error as error:
	        print("Failed inserting BLOB data into MySQL table {}".format(error))

	    finally:
	        if mydb.is_connected():
	        	my_cursor.close()
	        	mydb.close()

	insertBLOB(tenant_identification,file_location)

def db_title_insert (property_identification, file_location):

	import mysql.connector

	mydb = mysql.connector.connect(
			host = "localhost",
			user = "root",
			password = "Smiles123$",
			database = "alivente",
			auth_plugin = "mysql_native_password",
			)

	my_cursor = mydb.cursor()

	def convertToBinaryData(file_url):
	    # Convert digital data to binary format
	    with open(file_url, 'rb') as file:
	        binaryData = file.read()
	    return binaryData

	def insertBLOB(property_no, upload_file):
	    try:
	        update_query = "UPDATE prop SET prop_title_deed = %s WHERE prop_id = %s"

	        db_file = convertToBinaryData(upload_file)
	        values = (db_file, property_no)

	        my_cursor.execute(update_query,values)
	        mydb.commit()

	    except mysql.connector.Error as error:
	        print("Failed inserting BLOB data into MySQL table {}".format(error))

	    finally:
	        if mydb.is_connected():
	        	my_cursor.close()
	        	mydb.close()

	insertBLOB(property_identification,file_location)