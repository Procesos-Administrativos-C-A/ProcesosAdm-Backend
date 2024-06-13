import pymysql

#conexion a la base de datos alojada en MySql 
conexion = pymysql.connect(
    host='localhost',
    user='root',
    password='1234',  
    database='cable_aereo',
    cursorclass=pymysql.cursors.DictCursor
)

''''
password:
    Alberth: alberth
    Camilo: 1234
    Jhonthan: Admin12345

'''