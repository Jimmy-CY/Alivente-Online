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

def add_new_petty(transdatev, transdescv, transamountv, transdrcrv):
	my_cursor = mydb.cursor()
	sqlStuff = "INSERT INTO petty_cash (petty_cash_date, petty_cash_description, petty_cash_amount, petty_cash_dr_cr) VALUES (%s, %s, %s, %s)"
	records = [(transdatev,transdescv,transamountv,transdrcrv)]
	my_cursor.executemany(sqlStuff, records)
	mydb.commit()
