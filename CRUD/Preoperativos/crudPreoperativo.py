from typing import List
import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pymysql

# Establecer la conexión con la base de datos
conexion = pymysql.connect(
    host='localhost',
    user='root',
    password='alberth',
    database='cable_aereo',
    cursorclass=pymysql.cursors.DictCursor
)

# Modelo Pydantic para la tabla preopertativos
class Preoperativo(BaseModel):
    fecha: datetime.date
    encargado: str
    turno: str
    lugar: str

class EmpleadoPreoperativo(BaseModel):
    cedula: int
    horas_diarias: int
    horas_adicionales: int
    estacion: str


app = FastAPI()

# Función para crear un registro de preoperativo junto con los empleados preoperativos
@app.post("/preoperativos/", response_model=Preoperativo)
def crear_registro(preoperativo: Preoperativo, empleados_preoperativos: List[EmpleadoPreoperativo]):
    try:
        # Insertar en la tabla preoperativos
        with conexion.cursor() as cursor:
            sql_preopertativo = "INSERT INTO preopertativos (fecha, encargado, turno, lugar) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql_preopertativo, (preoperativo.fecha, preoperativo.encargado, preoperativo.turno, preoperativo.lugar))
            conexion.commit()
            # Obtener el ID del registro insertado en preoperativos
            id_preoperativo = cursor.lastrowid

        # Insertar en la tabla empleados_preoperativos
        with conexion.cursor() as cursor:
            for empleado in empleados_preoperativos:
                sql_empleado = "INSERT INTO empleados_preoperativos (id_preoperativo, cedula, horas_diarias, horas_adicionales, estacion) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql_empleado, (id_preoperativo, empleado.cedula, empleado.horas_diarias, empleado.horas_adicionales, empleado.estacion))
                conexion.commit()

        # Recuperar el registro insertado con su ID
        with conexion.cursor() as cursor:
            sql_get_preoperativo = "SELECT * FROM preopertativos WHERE id = %s"
            cursor.execute(sql_get_preoperativo, (id_preoperativo,))
            preoperativo_insertado = cursor.fetchone()

        return preoperativo_insertado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Función para obtener todos los registros de preoperativo junto con sus empleados preoperativos
@app.get("/preoperativos/", response_model=list[Preoperativo])
def obtener_registros():
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT * FROM preopertativos"
            cursor.execute(sql)
            resultados = cursor.fetchall()

            for resultado in resultados:
                sql_empleados = "SELECT * FROM empleados_preoperativos WHERE id_preoperativo = %s"
                cursor.execute(sql_empleados, (resultado['id'],))
                empleados = cursor.fetchall()
                resultado['empleados_preoperativos'] = empleados

            print(resultados)  # Imprime los resultados en la consola

            return resultados
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Función para obtener un registro de preoperatorio por su ID junto con sus empleados preoperativos
@app.get("/preoperativos/{id}", response_model=Preoperativo)
def obtener_registro_por_id(id: int):
    with conexion.cursor() as cursor:
        sql_preoperatorio = "SELECT * FROM preopertativos WHERE id = %s"
        cursor.execute(sql_preoperatorio, (id,))
        resultado = cursor.fetchone()
        if resultado is None:
            raise HTTPException(status_code=404, detail="Registro no encontrado")

        sql_empleados = "SELECT * FROM empleados_preoperativos WHERE id_preoperativo = %s"
        cursor.execute(sql_empleados, (id,))
        empleados = cursor.fetchall()
        resultado['empleados_preoperativos'] = empleados

        print(resultado)

        return resultado

# Función para actualizar un registro de preoperatorio por su ID junto con sus empleados preoperativos
@app.put("/preoperativos/{id}", response_model=Preoperativo)
def actualizar_registro(id: int, preoperatorio: Preoperativo, empleados_preoperativos: List[EmpleadoPreoperativo]):
    try:
        with conexion.cursor() as cursor:
            # Actualizar en la tabla preopertativos
            sql_preoperatorio = "UPDATE preopertativos SET fecha = %s, encargado = %s, turno = %s, lugar = %s WHERE id = %s"
            cursor.execute(sql_preoperatorio, (preoperatorio.fecha, preoperatorio.encargado, preoperatorio.turno, preoperatorio.lugar, id))
            conexion.commit()

            # Eliminar empleados preoperativos existentes para este registro
            sql_delete_empleados = "DELETE FROM empleados_preoperativos WHERE id_preoperativo = %s"
            cursor.execute(sql_delete_empleados, (id,))
            conexion.commit()

            # Insertar empleados preoperativos actualizados
            for empleado in empleados_preoperativos:
                sql_empleado = "INSERT INTO empleados_preoperativos (id_preoperativo, cedula, horas_diarias, horas_adicionales, estacion) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql_empleado, (id, empleado.cedula, empleado.horas_diarias, empleado.horas_adicionales, empleado.estacion))
                conexion.commit()

            return preoperatorio
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Función para eliminar un registro de preoperatorio por su ID junto con sus empleados preoperativos
@app.delete("/preoperativos/{id}", response_model=dict)
def eliminar_registro(id: int):
    try:
        with conexion.cursor() as cursor:
            # Eliminar empleados preoperativos asociados al registro
            sql_delete_empleados = "DELETE FROM empleados_preoperativos WHERE id_preoperativo = %s"
            cursor.execute(sql_delete_empleados, (id,))
            conexion.commit()

            # Eliminar el registro de preoperatorio
            sql_delete_preoperatorio = "DELETE FROM preopertativos WHERE id = %s"
            cursor.execute(sql_delete_preoperatorio, (id,))
            conexion.commit()

            return {"message": "Registro eliminado con éxito"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Montar servidor para probrar
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)