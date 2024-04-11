import sys
from typing import Dict

from schema.empleadoSchema import *
sys.path.append("..")
from fastapi import APIRouter, HTTPException
from utils.dbConection import conexion


empleados = APIRouter()

#devolver los empleados por cargo por orden alfabético  
@empleados.get("/getEmpleados/{cargo}", response_model=List[dict])
def obtener_nombres_empleados_por_cargo(cargo: str):
    try:
        cargos_validos = ["Jefe Sistemas", "Jefe Talento Humano", "Supervisor", "Operador", "Auxiliar de T & A", "Ingeniero MTTO", "Tecnico MTTO"]
        if cargo not in cargos_validos:
            raise HTTPException(status_code=400, detail="Cargo inválido")

        with conexion.cursor() as cursor:
            sql_empleados = "SELECT nombre, cedula FROM empleados WHERE cargo = %s ORDER BY nombre" 
            cursor.execute(sql_empleados, (cargo,))
            resultados_empleados = cursor.fetchall()
            empleados = [{'nombre': empleado['nombre'], 'cedula': empleado['cedula']} for empleado in resultados_empleados]
            return empleados

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los nombres de empleados: {str(e)}")
    

@empleados.get("/getEmpleados", response_model=EmpleadosList)
def obtener_todos_empleados():
    try:
        with conexion.cursor() as cursor:
            sql_empleados = "SELECT cedula, nombre, rol, cargo, email FROM empleados"
            cursor.execute(sql_empleados)
            resultados_empleados = cursor.fetchall()

            empleados_lista = [
                Empleado(
                    cedula=empleado["cedula"],
                    nombre=empleado["nombre"],
                    rol=empleado["rol"],
                    cargo=empleado["cargo"],
                    email=empleado["email"],
                )
                for empleado in resultados_empleados
            ]

            empleados_respuesta = EmpleadosList(empleados=empleados_lista)
            return empleados_respuesta

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al obtener todos los empleados: {str(e)}"
        )