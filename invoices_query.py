import mysql.connector
from datetime import date, datetime, timedelta
import database_create
import print_prop
import fsr
import print_tenant
import print_title
import print_lease
import petty_cash
import lease_renewal
import open_invoices
from django.conf import settings

# CONNECT TO DATBASE (FIRST HAVE TO LEAVE database line off until have created database)
mydb = mysql.connector.connect(
	host = settings.DATABASES['default']['HOST'],
	port = settings.DATABASES['default']['PORT'],
	user = settings.DATABASES['default']['USER'],
	password = settings.DATABASES['default']['PASSWORD'],
	database = settings.DATABASES['default']['NAME'],
	auth_plugin = settings.DATABASES['default']['AUTH_PLUGIN'],
	)


def mark_paid_invoices(invid):
	my_cursor = mydb.cursor()
	print ('100',invid)
#	my_sql = "UPDATE invoice SET invoice_paid = 'Yes' WHERE invoice_id = 1"
#	my_cursor.execute(my_sql)
#	mydb.commit()
