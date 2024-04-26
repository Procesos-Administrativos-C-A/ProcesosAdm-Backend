from datetime import datetime
import sys

from schema.empleadoPreoperativoSchema import EmpleadoPreoperativo
sys.path.append("..")
from fastapi import APIRouter, HTTPException, Query, FastAPI
from utils.dbConection import conexion

from typing import List
# Función para crear un registro de preoperativo junto con los empleados preoperativos
from schema.preoperativoSchema import Preoperativo

#para el pdf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from fastapi.responses import FileResponse
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
#from fastapi.responses import StreamingResponse
#from weasyprint import HTML, CSS
#from tempfile import NamedTemporaryFile


preoperativos = APIRouter()


@preoperativos.post("/preoperativos/", response_model=dict)
def crear_registro(preoperativo: Preoperativo, empleados_preoperativos: List[EmpleadoPreoperativo]):
    try:
        # Insertar en la tabla preoperativos
        with conexion.cursor() as cursor:
            sql_preopertativo = "INSERT INTO preoperativos (fecha, encargado, turno, lugar, festivo, horas_extra) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql_preopertativo, (preoperativo.fecha, preoperativo.encargado, preoperativo.turno, preoperativo.lugar, preoperativo.festivo, preoperativo.horas_extra))
            conexion.commit()
            # Obtener el ID del registro insertado en preoperativos
            id_preoperativo = cursor.lastrowid

        # Insertar en la tabla empleados_preoperativos
        with conexion.cursor() as cursor:
            for empleado in empleados_preoperativos:
                sql_empleado = "INSERT INTO empleados_preoperativos (id_preoperativo, cedula, horas_diarias, horas_adicionales, estacion) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql_empleado, (id_preoperativo, empleado.cedula, empleado.horas_diarias, empleado.horas_adicionales, empleado.estacion))
                conexion.commit()

        # Crear un diccionario con los datos relevantes del preoperativo y empleados preoperativos
        datos_preoperativos = {
            "fecha": preoperativo.fecha,
            "empleados_preoperativos": [
                {
                    "cedula": empleado.cedula,
                    "horas_diarias": empleado.horas_diarias,
                    "horas_adicionales": empleado.horas_adicionales,
                    "estacion": empleado.estacion
                } for empleado in empleados_preoperativos
            ]
        }

        # Llamar a la función para insertar en la tabla horas_empleados
        insertar_horas_empleados(datos_preoperativos, preoperativo.festivo, preoperativo.turno)

        # Recuperar el registro insertado con su ID
        with conexion.cursor() as cursor:
            sql_get_preoperativo = "SELECT * FROM preoperativos WHERE id = %s"
            cursor.execute(sql_get_preoperativo, (id_preoperativo,))
            preoperativo_insertado = cursor.fetchone()

        preoperativo_dict = dict(preoperativo_insertado)
        return preoperativo_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#ingresar datos en tabla horas_empleados
def insertar_horas_empleados(datos_preoperativos, festivo, turno):
    try:
        with conexion.cursor() as cursor:
            for empleado in datos_preoperativos["empleados_preoperativos"]:
                # Definir las horas de acuerdo con las condiciones especificadas
                if festivo:
                    if turno == "turno 1":
                        horas_diurnas_ord = 0
                        horas_diurnas_fest = empleado["horas_diarias"]
                        horas_nocturnas = 0
                        horas_nocturnas_fest = 0
                        horas_extras = empleado["horas_adicionales"]
                    elif turno == "turno 2":
                        horas_diurnas_ord = 0
                        horas_diurnas_fest = 7
                        horas_nocturnas = 0
                        horas_nocturnas_fest = 1
                        horas_extras = empleado["horas_adicionales"]
                    elif turno == "turno 3":
                        horas_diurnas_ord = 0
                        horas_diurnas_fest = 0
                        horas_nocturnas = 0
                        horas_nocturnas_fest = empleado["horas_diarias"]
                        horas_extras = empleado["horas_adicionales"]
                else:
                    if turno == "turno 1":
                        horas_diurnas_ord = empleado["horas_diarias"]
                        horas_diurnas_fest = 0
                        horas_nocturnas = 0
                        horas_nocturnas_fest = 0
                        horas_extras = empleado["horas_adicionales"]
                    elif turno == "turno 2":
                        horas_diurnas_ord = 7
                        horas_diurnas_fest = 0
                        horas_nocturnas = 1
                        horas_nocturnas_fest = 0
                        horas_extras = empleado["horas_adicionales"]
                    elif turno == "turno 3":
                        horas_diurnas_ord = 0
                        horas_diurnas_fest = 0
                        horas_nocturnas = empleado["horas_diarias"]
                        horas_nocturnas_fest = 0
                        horas_extras = empleado["horas_adicionales"]

                fecha = datos_preoperativos["fecha"]

                # Insertar en la tabla horas_empleados
                sql_horas_empleados = "INSERT INTO horas_empleados (cedula, horas_diurnas_ord, horas_diurnas_fest, horas_nocturnas, horas_nocturnas_fest, horas_extras, fecha) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql_horas_empleados, (empleado["cedula"], horas_diurnas_ord, horas_diurnas_fest, horas_nocturnas, horas_nocturnas_fest, horas_extras, fecha))
                conexion.commit()
    except Exception as e:
        print("Error al insertar en la tabla horas_empleados:", str(e))




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
                sql_empleados = """
                                SELECT ep.id, ep.id_preoperativo, ep.cedula, ep.horas_diarias, ep.horas_adicionales, ep.estacion, e.nombre, e.apellidos
                                FROM empleados_preoperativos ep
                                JOIN empleados e ON ep.cedula = e.cedula
                                WHERE ep.id_preoperativo = %s
                                """
                cursor.execute(sql_empleados, (preoperativo['id'],))
                empleados = cursor.fetchall()
                
                preoperativo_dict = dict(preoperativo)
                preoperativo_dict['empleados_preoperativos'] = empleados
                registros.append(preoperativo_dict)

            return registros
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#generar pdf por fecha
@preoperativos.get("/generar_pdf_preoperativos_fecha/")
def generar_pdf_preoperativos_fecha(fecha: str = Query(...)):
    try:
        # Llama a la función de obtener preoperativos por fecha para obtener los datos necesarios
        preoperativos = obtener_preoperativos_por_fecha(fecha)
        
        # Obtiene la fecha actual en el formato deseado para el nombre del archivo
        fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Inicializa el lienzo del PDF con un nombre único basado en la fecha, turno y lugar
        pdf_name = f"preoperativos_{fecha_actual}.pdf"
        pdf_canvas = canvas.Canvas(pdf_name)
        
        # Define el título del encabezado
        header_title = "Detalles de Preoperativos por Fecha"
        
        # Ajusta el tamaño de la fuente y la posición del título del encabezado
        pdf_canvas.setFont("Helvetica-Bold", 16)
        pdf_canvas.drawString(100, 850, header_title)
        
        # Dibuja una línea divisora debajo del título
        pdf_canvas.line(100, 840, 500, 840)
        
        # Define la posición inicial para escribir en el PDF después del encabezado y la línea divisora
        y_position = 800
        
        # Aumenta el espacio entre el título y la tabla
        y_position -= 60
        
        # Calcula la posición media de la página para colocar la tabla
        middle_position = y_position - 300
        
        # Itera sobre cada preoperativo y sus empleados
        for preoperativo in preoperativos:
            # Agrega los detalles del preoperativo al PDF
            pdf_canvas.drawString(100, y_position - 20, f"Fecha: {preoperativo['fecha']}")
            pdf_canvas.drawString(100, y_position - 40, f"Encargado: {preoperativo['encargado']}")
            pdf_canvas.drawString(100, y_position - 60, f"Turno: {preoperativo['turno']}")
            pdf_canvas.drawString(100, y_position - 80, f"Lugar: {preoperativo['lugar']}")
            pdf_canvas.drawString(100, y_position - 100, f"Festivo: {preoperativo['festivo']}")
            
            # Dibuja la tabla de empleados preoperativos
            table_data = [
                ["Cedula", "Horas Diarias", "Horas Adicionales", "Estacion"]
            ]
            for empleado in preoperativo['empleados_preoperativos']:
                table_data.append([
                    str(empleado['cedula']),
                    str(empleado['horas_diarias']),
                    str(empleado['horas_adicionales']),
                    empleado['estacion']
                ])
            
            # Dibuja la tabla en el PDF
            table = Table(table_data)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ]))
            
            # Ajusta la posición de la tabla para que quede en la mitad de la página
            table.wrapOn(pdf_canvas, 200, 400)
            table.drawOn(pdf_canvas, 100, middle_position)
            
            # Espacio entre preoperativos
            y_position -= 360
        
        # Guarda el PDF
        pdf_canvas.save()
        
        # Crea la respuesta del archivo PDF
        headers = {"Content-Disposition": f"attachment; filename={pdf_name}"}
        return FileResponse(pdf_name, headers=headers, media_type="application/pdf")
    
    except Exception as e:
        # Manejo de errores
        raise HTTPException(status_code=500, detail=str(e))


    # # Obtener datos de los preoperativos por fecha
    # preoperativos = obtener_preoperativos_por_fecha(fecha)

    # # Generar HTML para el PDF
    # html_content = "<h1>Preoperativos por Fecha</h1>"
    # for preoperativo in preoperativos:
    #     html_content += f"<h2>Fecha: {preoperativo['fecha']}</h2>"
    #     html_content += f"<p>Encargado: {preoperativo['encargado']}</p>"
    #     html_content += f"<p>Turno: {preoperativo['turno']}</p>"
    #     html_content += f"<p>Lugar: {preoperativo['lugar']}</p>"
    #     html_content += f"<p>Festivo: {preoperativo['festivo']}</p>"
    #     html_content += "<table border='1'><tr><th>Cédula</th><th>Horas Diarias</th><th>Horas Adicionales</th><th>Estación</th></tr>"
    #     for empleado in preoperativo['empleados_preoperativos']:
    #         html_content += f"<tr><td>{empleado['cedula']}</td><td>{empleado['horas_diarias']}</td><td>{empleado['horas_adicionales']}</td><td>{empleado['estacion']}</td></tr>"
    #     html_content += "</table>"

    # # Renderizar HTML a PDF
    # pdf_file = NamedTemporaryFile(delete=False)
    # HTML(string=html_content).write_pdf(pdf_file.name)
    # pdf_file.close()

    # # Preparar la respuesta del archivo PDF
    # headers = {
    #     "Content-Disposition": f"attachment; filename=preoperativos_{fecha}.pdf"
    # }

    # # Devolver el archivo PDF como una respuesta de transmisión
    # return StreamingResponse(open(pdf_file.name, "rb"), headers=headers, media_type="application/pdf")


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
@preoperativos.get("/preoperativos_por_id/{id}", response_model=dict)
def obtener_preoperativos_por_id(id: int):
    try:
        with conexion.cursor() as cursor:
            # Consulta SQL para obtener el preoperativo por su ID
            sql_preoperativo = "SELECT * FROM preoperativos WHERE id = %s"
            cursor.execute(sql_preoperativo, (id,))
            resultado_preoperativo = cursor.fetchone()
            
            # Si no se encuentra el preoperativo, lanzar una excepción 404
            if resultado_preoperativo is None:
                raise HTTPException(status_code=404, detail="Preoperativo no encontrado")

            # Consulta SQL para obtener los empleados preoperativos asociados al preoperativo por su ID
            
            sql_empleados_preoperativos = " SELECT ep.cedula, ep.horas_adicionales, ep.estacion, e.nombre, e.apellidos, e.cargo FROM empleados_preoperativos ep INNER JOIN empleados e ON ep.cedula = e.cedula WHERE ep.id_preoperativo = %s"
            cursor.execute(sql_empleados_preoperativos, (id,))
            empleados_preoperativos = cursor.fetchall()

            resultado_preoperativo["horas_extra"] = 0
            for empleado in empleados_preoperativos:
                if empleado["horas_adicionales"] > 0:
                    resultado_preoperativo["horas_extra"] = 1
                    break
                    

            # Construir el objeto de preoperativo con la lista de empleados preoperativos
            preoperativo = dict(resultado_preoperativo)
            preoperativo['empleados_preoperativos'] = empleados_preoperativos

            return preoperativo

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# Función para actualizar un registro de preoperativo por su ID junto con sus empleados preoperativos
@preoperativos.put("/putPreoperativos/{id}", response_model=Preoperativo)
def actualizar_registro(id: int, preoperativo: Preoperativo, empleados_preoperativos: List[EmpleadoPreoperativo]):
    try:
        with conexion.cursor() as cursor:
            # Actualizar en la tabla preoperativos
            sql_preoperativo = "UPDATE preoperativos SET fecha = %s, encargado = %s, turno = %s, lugar = %s, festivo = %s, horas_extra = %s WHERE id = %s"
            cursor.execute(sql_preoperativo, (preoperativo.fecha, preoperativo.encargado, preoperativo.turno, preoperativo.lugar, preoperativo.festivo, preoperativo.horas_extra, id))
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