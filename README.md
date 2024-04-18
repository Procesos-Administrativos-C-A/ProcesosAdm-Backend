# ProcesosAdm-Backend

Necesitamos instalar

pip install pymysql
pip install fastapi
pip install "uvicorn[standard]"


Ejemplo de un post para probar en postman:

POST:
http://localhost:8000/preoperativos/preoperativos/

{
  "preoperativo": {
    "fecha": "2024-04-09",
    "encargado": "Juan Perez",
    "turno": "turno 1",
    "lugar": "Oficina central",
    "festivo": false,
		"horas_extra": true
  },
  "empleados_preoperativos": [
    {
      "cedula": 1053861263,
      "horas_diarias": 8,
      "horas_adicionales": 2,
      "estacion": "Estación 1"
    },
    {
      "cedula": 1058845573,
      "horas_diarias": 8,
      "horas_adicionales": 1,
      "estacion": "Estación 2"
    },
    {
      "cedula": 900315506,
      "horas_diarias": 7,
      "horas_adicionales": 3,
      "estacion": "Estación 3"
    }
  ]
}

///////////////////////////////////////////////////////////////////////////////////////////
///////////********************INSTALACIÓN********************/////////////////////////////
        python3 -m venv .env				//instalar el env para montar la el backend
        pip install -r requirements.txt			//instalar todas las dependencias  
        .env\Scripts\activate				//activar el ambiente 


///////////////////////////////////////////////////////////////////////////////////////////
///////////********************CORRER API********************/////////////////////////////
        uvicorn main:app --reload