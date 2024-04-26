from pydantic import BaseModel
from typing import List

class Empleado(BaseModel):
    cedula: int
    nombre: str
    apellidos: str
    rol: int
    cargo: str
    email: str
    contraseña: str

class EmpleadosList(BaseModel):
    empleados: List[Empleado]