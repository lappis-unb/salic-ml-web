import pyodbc
import os

SALIC_CREDENTIALS = {
    'USER': os.environ.get('SALIC_DB_USER', ''),
    'PASSWORD': os.environ.get('SALIC_DB_PASSWORD', ''),
    'DATABASE': os.environ.get('SALIC_DB_NAME', ''),
}


def testConnection():
    db_parameters = 'DRIVER=FreeTDS;SERVER=salic_db;PORT=1435;DATABASE=;UID={0};PWD={1};TDS_Version=8.0;'.format(SALIC_CREDENTIALS['USER'], SALIC_CREDENTIALS['PASSWORD'])
    db = pyodbc.connect(db_parameters)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM BDCORPORATIVO.scSAC.tbItemCusto")
    data = cursor.fetchone()
    db.close()
    return data
