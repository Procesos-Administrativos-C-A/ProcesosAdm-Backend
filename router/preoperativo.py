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
#from fastapi.responses import StreamingResponse
#from weasyprint import HTML, CSS
#from tempfile import NamedTemporaryFile


preoperativos = APIRouter()

'''Tareas pendiente '''
#retornar aparte de (fecha, encargado, turno, lugar, festivo)que es de Preoperativos, y falta traer todos los empledos que estan relacionados a ese preoperativo(nombre, cargo, cedula, estacion, horas extra)
#le falta horas extra, toca modificar la base de datos, en la tabla
@preoperativos.post("/preoperativos/", response_model=dict)
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

        preoperativo_dict = dict(preoperativo_insertado)
        return preoperativo_dict
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
    
#generar pdf por fecha
@preoperativos.get("/generar_pdf_preoperativos_fecha/")
def generar_pdf_preoperativos_fecha(fecha: str = Query(...)):
    try:
        # Llama a la función de obtener preoperativos por fecha para obtener los datos necesarios
        preoperativos = obtener_preoperativos_por_fecha(fecha)
        
        # Aquí comienzas a generar el archivo PDF utilizando los datos obtenidos
        pdf_canvas = canvas.Canvas("preoperativos_por_fecha.pdf")

        # Agrega los datos al PDF
        for preoperativo in preoperativos:
            pdf_canvas.drawString(100, 800, f"ID: {preoperativo['id']}")
            pdf_canvas.drawString(100, 780, f"Fecha: {preoperativo['fecha']}")
            pdf_canvas.drawString(100, 760, f"Encargado: {preoperativo['encargado']}")
            
        # Guarda el PDF
        pdf_canvas.save()
        
        # Crea la respuesta del archivo PDF
        pdf_name = "preoperativos_por_fecha.pdf" #cambiar el nombre despues 
        pdf_path = Path.cwd() / pdf_name
        headers = {"Content-Disposition": f"attachment; filename={pdf_name}"}
        
        # Devuelve la respuesta del archivo PDF
        return FileResponse(pdf_path, headers=headers, media_type="application/pdf")
    
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
            
            sql_empleados_preoperativos = " SELECT ep.cedula, ep.horas_adicionales, ep.estacion, e.nombre, e.cargo FROM empleados_preoperativos ep INNER JOIN empleados e ON ep.cedula = e.cedula WHERE ep.id_preoperativo = %s"
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