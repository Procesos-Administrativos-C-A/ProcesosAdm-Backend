import sys
from typing import Dict
from datetime import datetime
from schema.empleadoSchema import *
sys.path.append("..")
from fastapi import APIRouter, HTTPException
from utils.dbConection import conexion
from fastapi import Query

horas_empleados_router = APIRouter()

class RangoFechas(BaseModel):
    fecha_inicio: datetime
    fecha_fin: datetime

@horas_empleados_router.get("/consolidado_horas/")
async def consolidado_horas(fecha_inicio: str = Query(...), fecha_fin: str = Query(...)):
    try:
        with conexion.cursor() as cursor:
            # Consulta SQL para obtener el consolidado de horas por empleado en el rango de fechas
            sql = """
                SELECT e.nombre, e.cedula,
                    SUM(he.horas_diurnas_ord) AS horas_diurnas_ord,
                    SUM(he.horas_diurnas_fest) AS horas_diurnas_fest,
                    SUM(he.horas_nocturnas) AS horas_nocturnas,
                    SUM(he.horas_nocturnas_fest) AS horas_nocturnas_fest,
                    SUM(he.horas_extras) AS horas_extras
                FROM empleados e
                INNER JOIN horas_empleados he ON e.cedula = he.cedula
                WHERE he.fecha BETWEEN %s AND %s
                GROUP BY e.cedula, e.nombre
            """
            cursor.execute(sql, (fecha_inicio, fecha_fin))
            consolidado_horas = cursor.fetchall()
            return consolidado_horas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))