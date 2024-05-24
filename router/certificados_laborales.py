import json
import sys
from typing import Dict
from datetime import datetime
from schema.empleadoSchema import *
sys.path.append("..")
from fastapi import APIRouter, HTTPException
from utils.dbConection import conexion

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

certificados_laborales_routes = APIRouter()

import requests
from fastapi import HTTPException

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

# Ruta para obtener certificados laborales por cédula
@certificados_laborales_routes.get("/certificados_laborales/{cedula}")
def obtener_certificado_laboral(cedula: str):
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
                    "apellidos": empleado["APELLI"].strip(),
                    "cedula": empleado["CEDULA"].strip(),
                    "cargo": empleado["CARGOS"].strip(),
                    "sueldo": empleado["SUELDO"],
                    "fecha_inicio_contrato": formatear_fecha(empleado["CONTRAINI"]),
                    "fecha_fin_contrato": formatear_fecha(empleado["CONTRAFIN"])
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
    
#generar los certificados laborales de los empleados
@certificados_laborales_routes.get("/generar_certificado_laboral_pdf/{cedula}")
def generar_certificado_laboral(cedula: str):
    try:
        certificado_laboral = obtener_certificado_laboral(cedula)
        
        pdf_name = f"certificado_laboral_{cedula}.pdf"
        doc = SimpleDocTemplate(pdf_name, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Ruta absoluta de la imagen del logo
        logo_path = os.path.join(os.path.dirname(__file__), '../image/logo_cable_aereo_color_uno.png')
        
        if not os.path.isfile(logo_path):
            raise HTTPException(status_code=404, detail="Imagen del logo no encontrada")
        
        logo = Image(logo_path, width=2*inch, height=2*inch)
        logo.hAlign = 'LEFT'
        elements.append(logo)
        
        elements.append(Spacer(1, 0.25*inch))
        
        titulo = Paragraph("EL AREA DE RECURSOS HUMANOS DE LA ASOCIACION CABLE AEREO MANIZALES Nit. 900.315.506-2", 
                           ParagraphStyle(name="Titulo", fontSize=16, leading=20, alignment=TA_CENTER, spaceAfter=20, fontName="Helvetica-Bold"))
        elements.append(titulo)
        
        subtitulo = Paragraph("CERTIFICA", 
                              ParagraphStyle(name="Subtitulo", fontSize=14, leading=18, alignment=TA_CENTER, spaceAfter=20, fontName="Helvetica-Bold"))
        elements.append(subtitulo)
        
        texto_certificado = f"""Que, {certificado_laboral['nombre']} {certificado_laboral['apellidos']}, 
        con C.C. {certificado_laboral['cedula']}, labora en la Asociación Cable Aéreo Manizales, 
        iniciando vinculación laboral el {certificado_laboral['fecha_inicio_contrato']}. 
        Actualmente desempeña el cargo de {certificado_laboral['cargo']} y una asignación salarial de $ {certificado_laboral['sueldo']}. 
        """
        
        cuerpo = Paragraph(texto_certificado, ParagraphStyle(name="Cuerpo", fontSize=12, leading=15))
        elements.append(cuerpo)
        
        # Espacio después del cuerpo del texto
        elements.append(Spacer(1, 0.5*inch))
        
        # Texto final "Dado en Manizales – Caldas el {fecha actual}"
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        dado_en_texto = f"Dado en Manizales – Caldas el {fecha_actual}"
        dado_en_paragraph = Paragraph(dado_en_texto, ParagraphStyle(name="Derecha", fontSize=12, alignment=TA_RIGHT))
        elements.append(dado_en_paragraph)
        
        # Espacio antes de la firma
        elements.append(Spacer(1, 0.6*inch))
        
        # Ruta absoluta de la imagen de la firma
        firma_path = os.path.join(os.path.dirname(__file__), '../image/firma_talento_humano.png')
        
        if not os.path.isfile(firma_path):
            raise HTTPException(status_code=404, detail="Imagen de la firma no encontrada")
        
        firma = Image(firma_path, width=3*inch, height=1*inch)
        firma.hAlign = 'LEFT'
        elements.append(firma)
        
        # Texto de la firma
        texto_firma = """SANDRA MARIA LOPEZ<br/>
        Profesional Especializada Talento Humano<br/>
        Asociación Cable Aéreo Manizales<br/>
        Manizales
        """
        
        firma_paragraph = Paragraph(texto_firma, ParagraphStyle(name="Firma", fontSize=12, leading=15, alignment=TA_LEFT))
        elements.append(firma_paragraph)
        
        # Espacio después del cuerpo del texto
        elements.append(Spacer(1, 0.6*inch))

        # Agregar texto final centrado
        texto_final = """
        Página 1 de 1<br/>
        Calle 65 A Cra 42 Vía Panamericana <br/>
        Teléfono: (606)8931375<br/>
        talentohumano@cableaereomanizales.gov.co<br/>
        info@cableaereomanizales.gov.co<br/>
        """
        elements.append(Paragraph(texto_final.strip(), ParagraphStyle(name="TextoFinal", fontSize=12, alignment=TA_CENTER)))


        # Construir el documento PDF
        doc.build(elements)
        
        # Devolver el PDF como respuesta
        return FileResponse(pdf_name, filename=pdf_name, media_type='application/pdf')
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
