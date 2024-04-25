from pydantic import BaseModel

class EmpleadoPreoperativo(BaseModel):
    cedula: int
    nombre: str
    horas_diarias: int
    horas_adicionales: int
    estacion: str