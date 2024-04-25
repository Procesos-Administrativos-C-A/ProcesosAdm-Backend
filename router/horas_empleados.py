import sys
from typing import Dict
from datetime import datetime
from schema.empleadoSchema import *
sys.path.append("..")
from fastapi import APIRouter, HTTPException
from utils.dbConection import conexion
from fastapi import Query

#PDF
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageBreak
from reportlab.lib import colors
from fastapi.responses import FileResponse


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
    
#generar pdf
@horas_empleados_router.get("/generar_pdf_consolidado_horas/")
async def generar_pdf_consolidado_horas(fecha_inicio: str = Query(...), fecha_fin: str = Query(...)):
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
            
            # Nombre del archivo PDF basado en la fecha actual
            pdf_name = f"consolidado_horas_{fecha_inicio}_{fecha_fin}.pdf"
            
            # Creación del PDF en orientación vertical
            doc = SimpleDocTemplate(pdf_name, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            elements = []
            
            # Cabecera de la tabla
            table_data = [
                ["Nombre", "Cedula", "Horas Diurnas Ord", "Horas Diurnas Fest", "Horas Nocturnas", "Horas Nocturnas Fest", "Horas Extras"]
            ]
            
            # Agregar datos a la tabla
            for empleado in consolidado_horas:
                table_data.append([
                    empleado['nombre'],
                    empleado['cedula'],
                    empleado['horas_diurnas_ord'],
                    empleado['horas_diurnas_fest'],
                    empleado['horas_nocturnas'],
                    empleado['horas_nocturnas_fest'],
                    empleado['horas_extras']
                ])
            
            # Creación de la tabla y estilo
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTSIZE', (0, 0), (-1, -1), 8),  # Tamaño de fuente reducido
                ('LEADING', (0, 0), (-1, -1), 6),    # Espaciado entre filas reducido
            ]))
            
            # Agregar la tabla al documento
            elements.append(table)
            
            # Agregar salto de página
            elements.append(PageBreak())
            
            # Generar el PDF
            doc.build(elements)
            
            # Devolver el PDF como respuesta
            return FileResponse(pdf_name, filename=pdf_name, media_type='application/pdf')
        
    except Exception as e:
        # Manejo de errores
        raise HTTPException(status_code=500, detail=str(e))