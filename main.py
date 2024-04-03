from os import name
from typing import Union
from fastapi import FastAPI, APIRouter

from router.preoperativo import preoperativos
from services.login import login_router

app = FastAPI()

app.include_router(preoperativos, prefix='/preoperativos')
app.include_router(login_router, prefix='/login')

@app.get("/")
def hello_world():
    return {"message": "Servidor ejecutandose"}

if name == "main":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)