from os import name
from typing import Union
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from router.preoperativo import preoperativos
from router.empleado import empleados

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
app.include_router(empleados, prefix="/empleados")



@app.get("/")
def hello_world():
    return {"message": "Servidor ejecutandose"}

if name == "main":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)