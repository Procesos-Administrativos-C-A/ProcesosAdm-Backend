import datetime
from pydantic import BaseModel

class Preoperativo(BaseModel):
    fecha: datetime.date
    encargado: str
    turno: str
    lugar: str