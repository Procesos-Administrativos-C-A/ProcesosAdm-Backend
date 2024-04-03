import sys
from typing import Dict

from schema.empleadoSchema import *
sys.path.append("..")
from fastapi import APIRouter, HTTPException
from utils.dbConection import conexion


empleados = APIRouter()

@empleados.get("/getEmpleados/{cargo}", response_model=List[str])
def obtener_nombres_empleados_por_cargo(cargo: str):
    try:
        cargos_validos = ["Jefe Sistemas", "Jefe Talento Humano", "Supervisor", "Operador", "Auxiliar de T & A", "Ingeniero MTTO", "Tecnico MTTO"]
        if cargo not in cargos_validos:
            raise HTTPException(status_code=400, detail="Cargo inválido")

        with conexion.cursor() as cursor:
            sql_empleados = "SELECT nombre FROM empleados WHERE cargo = %s"
            cursor.execute(sql_empleados, (cargo,))
            resultados_empleados = cursor.fetchall()
            nombres_empleados = [empleado['nombre'] for empleado in resultados_empleados]
            return nombres_empleados
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los nombres de empleados: {str(e)}")