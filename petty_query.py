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

# CONNECT TO DATBASE (FIRST HAVE TO LEAVE database line off until have created database)
mydb = mysql.connector.connect(
	host = "localhost",
	user = "root",
	password = "Smiles123$",
	database = "alivente",
	auth_plugin = "mysql_native_password",
	)

def add_new_petty(transdatev, transdescv, transamountv, transdrcrv):
	my_cursor = mydb.cursor()
	sqlStuff = "INSERT INTO petty_cash (petty_cash_date, petty_cash_description, petty_cash_amount, petty_cash_dr_cr) VALUES (%s, %s, %s, %s)"
	records = [(transdatev,transdescv,transamountv,transdrcrv)]
	my_cursor.executemany(sqlStuff, records)
	mydb.commit()
