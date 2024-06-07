from os import name
from typing import Union
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from router.preoperativo import preoperativos
#from services.login import login_router
from router.login import login_router
from router.empleado import empleados
from router.horas_empleados import horas_empleados_router
from router.certificados_laborales import certificados_laborales_routes
from router.notificacion_fin_contrato import notificacion_fin_contrato_routes

app = FastAPI()

origins = [
    "http://localhost:4200",  # Origen de tu aplicación Angular
    # Agrega más orígenes si es necesario
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(preoperativos, prefix='/preoperativos')
app.include_router(login_router, prefix='/login')
app.include_router(empleados, prefix="/empleados")
app.include_router(horas_empleados_router, prefix="/horas_empleados")
app.include_router(certificados_laborales_routes, prefix="/certificados_laborales")
app.include_router(notificacion_fin_contrato_routes, prefix="/notificacion_fin_contrato")


@app.get("/")
def hello_world():
    return {"message": "Servidor ejecutandose"}

if name == "main":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)