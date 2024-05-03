import datetime
from xmlrpc.client import Boolean
from pydantic import BaseModel

class Preoperativo(BaseModel):
    fecha: datetime.date
    encargado: str
    turno: str
    lugar: str
    festivo: Boolean
    horas_extra: Boolean