# ProcesosAdm-Backend

Necesitamos instalar

pip install pymysql
pip install fastapi
pip install "uvicorn[standard]"


Ejemplo de un post para probar en postman:

POST:
http://localhost:8000/preoperativos/

{
    "preoperativo": {
        "fecha": "2024-03-19",
        "encargado": "Alejandro Posada",
        "turno": "Mañana",
        "lugar": "Estación A"
    },
    "empleados_preoperativos": [
        {
            "cedula": 75066500,
            "horas_diarias": 8,
            "horas_adicionales": 2,
            "estacion": "Estación A"
        },
        {
            "cedula": 1053783963,
            "horas_diarias": 7,
            "horas_adicionales": 1,
            "estacion": "Estación B"
        }
    ]
}


