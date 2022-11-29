import mysql.connector as sql
from mysql.connector import errorcode

connect = sql.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')

connect.close()
