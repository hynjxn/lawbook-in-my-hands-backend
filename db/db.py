import mysql.connector
from mysql.connector import Error, errorcode
from config.config import db


def get_mysql_connection():
    try:
        connection = mysql.connector.connect(**db)

        if connection.is_connected():
            print('connection ok!')
            return connection

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        connection.close()
        return
