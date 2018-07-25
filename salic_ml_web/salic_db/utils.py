import MySQLdb
import os

SALIC_CREDENTIALS = {
    'USER': os.environ.get('SALIC_DB_USER', ''),
    'PASSWORD': os.environ.get('SALIC_DB_PASSWORD', ''),
    'DATABASE': os.environ.get('SALIC_DB_NAME', ''),
}

def testConnection():
    db = MySQLdb.connect(
        host="salic_db",
        user="minc_lappis_edson",
        passwd="1qazxsw2",
        #db="",
        port=1435
    )
    cursor = db.cursor()
    cursor.execute("SHOW DATABASES;")
    data = cursor.fetchone()
    db.close()
    return data
