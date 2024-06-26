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
from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch


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
            "id_preoperativo": id_preoperativo,
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
                sql_horas_empleados = "INSERT INTO horas_empleados (id_preoperativo, cedula, horas_diurnas_ord, horas_diurnas_fest, horas_nocturnas, horas_nocturnas_fest, horas_extras, fecha) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql_horas_empleados, (datos_preoperativos['id_preoperativo'],empleado["cedula"], horas_diurnas_ord, horas_diurnas_fest, horas_nocturnas, horas_nocturnas_fest, horas_extras, fecha))
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

# Define el endpoint para generar el PDF de preoperativos por fecha
@preoperativos.get("/generar_pdf_preoperativos_fecha/")
def generar_pdf_preoperativos_fecha(fecha: str = Query(...)):
    try:
        # Llama a la función de obtener preoperativos por fecha para obtener los datos necesarios
        preoperativos = obtener_preoperativos_por_fecha(fecha)
        
        # Obtiene la fecha actual en el formato deseado para el nombre del archivo
        fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Inicializa el lienzo del PDF con un nombre único basado en la fecha
        pdf_name = f"preoperativos_{fecha_actual}.pdf"
        doc = SimpleDocTemplate(pdf_name, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Crea una lista de elementos para agregar al PDF
        pdf_elements = []

        # Título del documento
        titulo = f"Preoperativos de la fecha {fecha}"
        pdf_elements.append(Paragraph(titulo, styles['Title']))
        
        # Espacio después del título
        pdf_elements.append(Spacer(1, 12))
        
        # Itera sobre cada preoperativo y agrega sus detalles al PDF
        for preoperativo in preoperativos:
            # Agrega un salto de página antes de cada nuevo preoperativo (excepto para el primero)
            if preoperativos.index(preoperativo) != 0:
                pdf_elements.append(Spacer(1, 30))
            
            # Agrega los detalles del preoperativo al PDF
            pdf_elements.append(Paragraph(f"<b>Fecha:</b> {preoperativo['fecha']}", styles["Normal"]))
            pdf_elements.append(Paragraph(f"<b>Encargado:</b> {preoperativo['encargado']}", styles["Normal"]))
            pdf_elements.append(Paragraph(f"<b>Turno:</b> {preoperativo['turno']}", styles["Normal"]))
            pdf_elements.append(Paragraph(f"<b>Lugar:</b> {preoperativo['lugar']}", styles["Normal"]))
            
            # Ajusta la representación de "Festivo" a "Si" o "No"
            festivo = "Si" if preoperativo['festivo'] else "No"
            pdf_elements.append(Paragraph(f"<b>Festivo:</b> {festivo}", styles["Normal"]))
            
            # Agrega una tabla para los empleados preoperativos
            table_data = [["Nombre", "Cédula", "Horas Diarias", "Horas Adicionales", "Estación"]]
            for empleado in preoperativo['empleados_preoperativos']:
                # Obtiene el nombre del empleado desde el diccionario de empleados
                nombre_empleado = empleado.get('nombre', 'Nombre no disponible')
                table_data.append([
                    Paragraph(nombre_empleado, styles["Normal"]),  # Utiliza un Paragraph para permitir el ajuste automático del texto
                    str(empleado['cedula']),
                    str(empleado['horas_diarias']),
                    str(empleado['horas_adicionales']),
                    empleado['estacion']
                ])
            table = Table(table_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch, 2*inch])  # Ajusta el ancho de la columna del nombre
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ]))
            pdf_elements.append(table)
        
        # Agrega los elementos al documento PDF
        doc.build(pdf_elements)
        
        # Crea la respuesta del archivo PDF
        headers = {"Content-Disposition": f"attachment; filename={pdf_name}"}
        return FileResponse(pdf_name, headers=headers, media_type="application/pdf")
    
    except Exception as e:
        # Manejo de errores
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


#Acceder al ultimo preoperativo que creo una persona 
@preoperativos.get("/ultimo_preoperativo/{cedula}", response_model=dict)
def obtener_ultimo_preoperativo(cedula: str):
    try:
        with conexion.cursor() as cursor:
            # Obtener el nombre de la persona asociada a la cédula
            sql_nombre_empleado = """
                SELECT nombre, apellidos
                FROM empleados
                WHERE cedula = %s
            """
            cursor.execute(sql_nombre_empleado, (cedula,))
            empleado = cursor.fetchone()

            if empleado is None:
                raise HTTPException(status_code=404, detail="No se encontró ningún empleado para la cédula proporcionada")

            nombre_completo = f"{empleado['nombre']} {empleado['apellidos']}"

            # Obtener el último preoperativo donde el encargado es la persona encontrada
            sql_ultimo_preoperativo = """
                SELECT p.* 
                FROM preoperativos p
                WHERE p.encargado = %s
                ORDER BY p.fecha DESC
                LIMIT 1
            """
            cursor.execute(sql_ultimo_preoperativo, (nombre_completo,))
            resultado_preoperativo = cursor.fetchone()

            if resultado_preoperativo is None:
                raise HTTPException(status_code=404, detail="No se encontró ningún preoperativo para el encargado proporcionado")

            preoperativo = dict(resultado_preoperativo)

            # Obtener los empleados asociados a este preoperativo
            sql_empleados = """
                SELECT ep.cedula, ep.horas_adicionales, ep.estacion, e.nombre, e.apellidos, e.cargo
                FROM empleados_preoperativos ep
                JOIN empleados e ON ep.cedula = e.cedula
                WHERE ep.id_preoperativo = %s
            """
            cursor.execute(sql_empleados, (preoperativo['id'],))
            empleados = cursor.fetchall()

            preoperativo["horas_extra"] = 0
            for empleado in empleados:
                if empleado["horas_adicionales"] > 0:
                    preoperativo["horas_extra"] = 1
                    break

            preoperativo['empleados_preoperativos'] = empleados

            return preoperativo
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
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            conexion.commit()

            # Eliminar registros de la tabla horas_empleados
            sql_delete_horas_empleados = "DELETE FROM horas_empleados WHERE id_preoperativo = %s"
            cursor.execute(sql_delete_horas_empleados, (id,))
            conexion.commit()
        
            # Eliminar empleados preoperativos existentes para este registro
            sql_delete_empleados = "DELETE FROM empleados_preoperativos WHERE id_preoperativo = %s"
            cursor.execute(sql_delete_empleados, (id,))
            conexion.commit()
            
            # Actualizar en la tabla preoperativos
            sql_preoperativo = "UPDATE preoperativos SET fecha = %s, encargado = %s, turno = %s, lugar = %s, festivo = %s, horas_extra = %s WHERE id = %s"
            cursor.execute(sql_preoperativo, (preoperativo.fecha, preoperativo.encargado, preoperativo.turno, preoperativo.lugar, preoperativo.festivo, preoperativo.horas_extra, id))
            conexion.commit()
            
            
            # Insertar empleados preoperativos actualizados
            for empleado in empleados_preoperativos:
                sql_empleado = "INSERT INTO empleados_preoperativos (id_preoperativo, cedula, horas_diarias, horas_adicionales, estacion) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql_empleado, (id, empleado.cedula, empleado.horas_diarias, empleado.horas_adicionales, empleado.estacion))
                conexion.commit()

            datos_preoperativos = {
                "fecha": preoperativo.fecha,
                "id_preoperativo": id,
                "empleados_preoperativos": [
                    {
                        "cedula": empleado.cedula,
                        "horas_diarias": empleado.horas_diarias,
                        "horas_adicionales": empleado.horas_adicionales,
                        "estacion": empleado.estacion
                    } for empleado in empleados_preoperativos
                ]
            }

            # Insertar nuevos registros en la tabla horas_empleados
            insertar_horas_empleados(datos_preoperativos, preoperativo.festivo, preoperativo.turno)

            # Volver a habilitar las restricciones de clave externa
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            conexion.commit()

            return preoperativo
    except Exception as e:
        # Volver a habilitar las restricciones de clave externa
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conexion.commit()
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