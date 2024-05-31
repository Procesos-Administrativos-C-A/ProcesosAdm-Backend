import json
import sys
from typing import Any, Dict
from datetime import datetime
from schema.empleadoSchema import *
sys.path.append("..")
from fastapi import APIRouter, HTTPException
from utils.dbConection import conexion
from datetime import datetime, timedelta
import time
#Conexión con la api de FortiCliend
import requests

#PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from fastapi.responses import FileResponse
import os

from typing import List

notificacion_fin_contrato_routes = APIRouter()

# Función para limpiar la respuesta eliminando los caracteres especiales al inicio y al final
def limpiar_respuesta(respuesta: str) -> str:
    inicio = respuesta.find('{')
    fin = respuesta.rfind('}') + 1
    if inicio != -1 and fin != -1:
        return respuesta[inicio:fin]
    return respuesta

# Función para formatear las fechas que llegan desde la api
def formatear_fecha(fecha: str) -> str:
    return f"{fecha[:4]}-{fecha[4:6]}-{fecha[6:]}"

# Función para formatear el sueldo
def formatear_sueldo(sueldo: str) -> str:
    return "{:,}".format(int(sueldo)).replace(",", ".")

# Función para validar y convertir una fecha en cadena a un objeto datetime
def validar_fecha(fecha_str: str) -> datetime:
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d")
    except ValueError:
        # Si la fecha no es válida, devuelve None
        return None

# Define el endpoint para obtener todas las cédulas de la tabla de empleados
@notificacion_fin_contrato_routes.get("/empleados/cedulas", response_model=List[str])
def obtener_cedulas_empleados():
    try:
        # Abre un cursor para ejecutar la consulta
        with conexion.cursor() as cursor:
            # Realiza la consulta SQL para obtener todas las cédulas de la tabla empleados
            sql = "SELECT CAST(cedula AS CHAR) AS cedula FROM empleados LIMIT 2"
            cursor.execute(sql)
            # Obtiene todas las filas del resultado
            result = cursor.fetchall()
            # Extrae las cédulas de las filas
            cedulas = [row['cedula'] for row in result]
            return cedulas
    except Exception as e:
        # Manejo de errores
        raise HTTPException(status_code=500, detail=str(e))


# coneccion y depuracion api
@notificacion_fin_contrato_routes.get("/coneccioApi/{cedula}")
def obtener_datos_api(cedula: str):
    try:
        # URL del API externo con la cédula proporcionada
        url = f"http://192.168.10.15/dsinomina/nom-app-consultaced.php?cedula={cedula}"
        
        # Realizar la solicitud GET al API externo
        response = requests.get(url)
        
        # Verificar si la solicitud fue exitosa (código de estado 200)
        if response.status_code == 200:
            # Limpiar la respuesta
            respuesta_limpia = limpiar_respuesta(response.text)
            
            # Intentar cargar la respuesta como JSON
            try:
                data = json.loads(respuesta_limpia)
            except json.JSONDecodeError as e:
                # Si no se puede cargar como JSON, lanzar una excepción con el mensaje de error
                raise HTTPException(status_code=500, detail=f"No se pudo analizar la respuesta como JSON: {str(e)}")
            
            # Verificar si hay datos de empleado en la respuesta
            if "EMPLEADO" in data and len(data["EMPLEADO"]) > 0:
                empleado = data["EMPLEADO"][0]  # Tomar el primer empleado encontrado
                
                # Formatear los datos del certificado laboral
                certificado_laboral = {
                    "codigo": empleado["CODIGO"].strip(),
                    "nombre": empleado["NOMBRE"].strip(),
                    "nombre2": empleado["NOMBRE2"].strip(),
                    "apellidos": empleado["APELLI"].strip(),
                    "apellidos2": empleado["APELLI2"].strip(),
                    "cedula": empleado["CEDULA"].strip(),
                    "cargo": empleado["CARGOS"].strip(),
                    "sueldo": formatear_sueldo(empleado["SUELDO"]),
                    "fecha_inicio_contrato": formatear_fecha(empleado["CONTRAINI"]),
                    "fecha_fin_contrato": formatear_fecha(empleado["CONTRAFIN"]),
                    "tipo_contrato": empleado["TIPOCONT"],
                    "nombre_contrato": empleado["NOMCONT"].strip()
                }
                
                return certificado_laboral
            else:
                # Si no se encontraron datos de empleado, lanzar una excepción
                raise HTTPException(status_code=404, detail="No se encontraron datos de empleado para la cédula proporcionada")
        else:
            # Si la solicitud no fue exitosa, lanzar una excepción con el código de estado
            raise HTTPException(status_code=response.status_code, detail=f"Error al consultar el API externo: {response.text}")
    
    except Exception as e:
        # Manejo de errores
        raise HTTPException(status_code=500, detail=str(e))


# Define el endpoint para obtener los empleados cuyo contrato vence en los próximos dos meses
@notificacion_fin_contrato_routes.get("/empleados/contratos_proximos", response_model=List[Dict[str, Any]])
def obtener_empleados_contrato_proximo():
    try:
        # Obtener todas las cédulas de la tabla empleados
        cedulas = obtener_cedulas_empleados()
        
        empleados_con_contrato_proximo = []
        fecha_actual = datetime.now()
        
        for cedula in cedulas:
            # Introduce un pequeño retraso entre cada solicitud
            #time.sleep(2)
            
            # Obtener el certificado laboral del empleado
            certificado_laboral = obtener_datos_api(cedula)
            
            # Convertir la fecha de fin de contrato a un objeto datetime
            fecha_fin_contrato_str = certificado_laboral.get("fecha_fin_contrato", "")
            fecha_fin_contrato = validar_fecha(fecha_fin_contrato_str)
            
            if fecha_fin_contrato:
                # Calcular la diferencia de tiempo entre la fecha actual y la fecha de fin de contrato
                diferencia = fecha_fin_contrato - fecha_actual
                
                # Si la diferencia es mayor o igual a 2 meses (aproximadamente 60 días), agregar el empleado a la lista
                if diferencia.days >= 60:
                    empleados_con_contrato_proximo.append(certificado_laboral)
        
        # Si no hay empleados próximos a terminar su contrato, devolver un mensaje
        if not empleados_con_contrato_proximo:
            return {"message": "No hay empleados próximos a terminar su contrato"}
        
        return empleados_con_contrato_proximo
    except Exception as e:
        # Manejo de errores
        raise HTTPException(status_code=500, detail=str(e))
