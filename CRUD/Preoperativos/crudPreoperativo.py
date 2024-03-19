import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pymysql

# Establecer la conexión con la base de datos
conexion = pymysql.connect(
    host='localhost',
    user='root',
    password='alberth',
    database='cable_aereo',
    cursorclass=pymysql.cursors.DictCursor
)

# Modelo Pydantic para la tabla preopertativos
class Preoperatorio(BaseModel):
    fecha: datetime.date
    encargado: str
    turno: str
    lugar: str

app = FastAPI()

# Ruta para crear un registro
@app.post("/preopertativos/", response_model=Preoperatorio)
def crear_registro(preoperatorio: Preoperatorio):
    with conexion.cursor() as cursor:
        sql = "INSERT INTO preopertativos (fecha, encargado, turno, lugar) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (preoperatorio.fecha, preoperatorio.encargado, preoperatorio.turno, preoperatorio.lugar))
        conexion.commit()
        return preoperatorio

# Ruta para obtener todos los registros
@app.get("/preopertativos/", response_model=list[Preoperatorio])
def obtener_registros():
    with conexion.cursor() as cursor:
        sql = "SELECT * FROM preopertativos"
        cursor.execute(sql)
        resultados = cursor.fetchall()
        return resultados

# Ruta para obtener un registro por su ID
@app.get("/preopertativos/{id}", response_model=Preoperatorio)
def obtener_registro_por_id(id: int):
    with conexion.cursor() as cursor:
        sql = "SELECT * FROM preopertativos WHERE id = %s"
        cursor.execute(sql, (id,))
        resultado = cursor.fetchone()
        if resultado is None:
            raise HTTPException(status_code=404, detail="Registro no encontrado")
        return resultado

# Ruta para actualizar un registro por su ID
@app.put("/preopertativos/{id}", response_model=Preoperatorio)
def actualizar_registro(id: int, preoperatorio: Preoperatorio):
    with conexion.cursor() as cursor:
        sql = "UPDATE preopertativos SET fecha = %s, encargado = %s, turno = %s, lugar = %s WHERE id = %s"
        cursor.execute(sql, (preoperatorio.fecha, preoperatorio.encargado, preoperatorio.turno, preoperatorio.lugar, id))
        conexion.commit()
        return preoperatorio

# Ruta para eliminar un registro por su ID
@app.delete("/preopertativos/{id}", response_model=dict)
def eliminar_registro(id: int):
    with conexion.cursor() as cursor:
        sql = "DELETE FROM preopertativos WHERE id = %s"
        cursor.execute(sql, (id,))
        conexion.commit()
        return {"message": "Registro eliminado con éxito"}



# Montar servidor para probrar
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)