import sys

from schema.empleadoPreoperativoSchema import EmpleadoPreoperativo
sys.path.append("..")
from fastapi import APIRouter, HTTPException, Query
from utils.dbConection import conexion

from typing import List
# Función para crear un registro de preoperativo junto con los empleados preoperativos
from schema.preoperativoSchema import Preoperativo
from typing import List


preoperativos = APIRouter()

'''Tareas pendiente '''
#retornar aparte de (fecha, encargado, turno, lugar, festivo)que es de Preoperativos, y falta traer todos los empledos que estan relacionados a ese preoperativo(nombre, cargo, cedula, estacion, horas extra)
#le falta horas extra, toca modificar la base de datos, en la tabla
@preoperativos.post("/preoperativos/", response_model=Preoperativo)
def crear_registro(preoperativo: Preoperativo, empleados_preoperativos: List[EmpleadoPreoperativo]):
    try:
        # Insertar en la tabla preoperativos
        with conexion.cursor() as cursor:
            sql_preopertativo = "INSERT INTO preoperativos (fecha, encargado, turno, lugar, festivo) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql_preopertativo, (preoperativo.fecha, preoperativo.encargado, preoperativo.turno, preoperativo.lugar, preoperativo.festivo))
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
            sql_get_preoperativo = "SELECT * FROM preoperativos WHERE id = %s"
            cursor.execute(sql_get_preoperativo, (id_preoperativo,))
            preoperativo_insertado = cursor.fetchone()

        return preoperativo_insertado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Función para obtener los preoperativos por fecha
@preoperativos.get("/preoperativos_por_fecha/", response_model=List[dict])
def obtener_preoperativos_por_fecha(fecha: str = Query(...)): #Query(...) es usada para especificar que el parámetro fecha es requerido en la consulta y no puede ser omitido.
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT * FROM preoperativos WHERE fecha = %s"
            cursor.execute(sql, (fecha,))
            preoperativos = cursor.fetchall()

            registros = []

            for preoperativo in preoperativos:
                sql_empleados = "SELECT * FROM empleados_preoperativos WHERE id_preoperativo = %s"
                cursor.execute(sql_empleados, (preoperativo['id'],))
                empleados = cursor.fetchall()
                
                preoperativo_dict = dict(preoperativo)
                preoperativo_dict['empleados_preoperativos'] = empleados
                registros.append(preoperativo_dict)

            return registros
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Función para obtener todos los registros de preoperativo junto con sus empleados preoperativos
@preoperativos.get("/getPreoperativos/", response_model=List[dict])
def obtener_registros():
    try:
        with conexion.cursor() as cursor:
            sql_preoperativos = "SELECT * FROM preoperativos"
            cursor.execute(sql_preoperativos)
            resultados_preoperativos = cursor.fetchall()

            registros = []

            for preoperativo in resultados_preoperativos:
                sql_empleados = "SELECT * FROM empleados_preoperativos WHERE id_preoperativo = %s"
                cursor.execute(sql_empleados, (preoperativo['id'],))
                empleados = cursor.fetchall()
                
                preoperativo_dict = dict(preoperativo)
                preoperativo_dict['empleados_preoperativos'] = empleados
                registros.append(preoperativo_dict)

            print(registros)  # Imprime los resultados en la consola

            return registros
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Función para obtener un registro de preoperativo por su ID junto con sus empleados preoperativos
@preoperativos.get("/idPreoperativos/{id}", response_model=Preoperativo)
def obtener_registro_por_id(id: int):
    with conexion.cursor() as cursor:
        sql_preoperativo = "SELECT * FROM preoperativos WHERE id = %s"
        cursor.execute(sql_preoperativo, (id,))
        resultado = cursor.fetchone()
        if resultado is None:
            raise HTTPException(status_code=404, detail="Registro no encontrado")

        sql_empleados = "SELECT * FROM empleados_preoperativos WHERE id_preoperativo = %s"
        cursor.execute(sql_empleados, (id,))
        empleados = cursor.fetchall()
        resultado['empleados_preoperativos'] = empleados

        print(resultado)

        return resultado

# Función para actualizar un registro de preoperativo por su ID junto con sus empleados preoperativos
@preoperativos.put("/putPreoperativos/{id}", response_model=Preoperativo)
def actualizar_registro(id: int, preoperativo: Preoperativo, empleados_preoperativos: List[EmpleadoPreoperativo]):
    try:
        with conexion.cursor() as cursor:
            # Actualizar en la tabla preoperativos
            sql_preoperativo = "UPDATE preoperativos SET fecha = %s, encargado = %s, turno = %s, lugar = %s, festivo = %s WHERE id = %s"
            cursor.execute(sql_preoperativo, (preoperativo.fecha, preoperativo.encargado, preoperativo.turno, preoperativo.lugar, preoperativo.festivo, id))
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

            return preoperativo
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Función para eliminar un registro de preoperativo por su ID junto con sus empleados preoperativos
@preoperativos.delete("/deletePreoperativos/{id}", response_model=dict)
def eliminar_registro(id: int):
    try:
        with conexion.cursor() as cursor:
            # Eliminar empleados preoperativos asociados al registro
            sql_delete_empleados = "DELETE FROM empleados_preoperativos WHERE id_preoperativo = %s"
            cursor.execute(sql_delete_empleados, (id,))
            conexion.commit()

            # Eliminar el registro de preoperativo
            sql_delete_preoperativo = "DELETE FROM preoperativos WHERE id = %s"
            cursor.execute(sql_delete_preoperativo, (id,))
            conexion.commit()

            return {"message": "Registro eliminado con éxito"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))