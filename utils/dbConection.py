import pymysql


conexion = pymysql.connect(
    host='localhost',
    user='root',
    password='Admin12345',  
    database='cable_aereo',
    cursorclass=pymysql.cursors.DictCursor
)

''''
password:
    Alberth: alberth
    Camilo: 1234
    Jhonthan: Admin12345

'''