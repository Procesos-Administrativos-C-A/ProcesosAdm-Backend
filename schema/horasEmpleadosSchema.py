import datetime
from xmlrpc.client import Boolean
from pydantic import BaseModel

class HorasEmpleados(BaseModel):
    cedula: int
    horas_diurnas_ord: int
    horas_diurnas_fest: int
    horas_nocturnas: int
    horas_nocturnas_fest: int
    horas_extras: int
    fecha: datetime.date