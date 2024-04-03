from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext #para usar el algoritmo bcrypt de encriptamiento
from datetime import datetime, timedelta, timezone #para trabajar con los tiempos, esto para el token
from jose import jwt, JWTError #dependencia que extiende jwt

from typing import Union #especificar más de un solo tipo de datos para el user
from pydantic import BaseModel


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2a$10$ct8kTwou4/5PMBT/RMENy.oN49WqN4NYPOfzMAD.TS0oU64PMQA7e",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "$2a$12$pME1u69wjPTNADRxs0BQpeuv75z9odbWm1ZY56QPbLxmAowXCf2Fi",
        "disabled": True,
    },
}

login_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer("/login/token")

pwt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  #bcrypt sera el tipo de algoritmo para el encriptamiento o desencriptamiento de la password



#esquema usuarios generales
class User(BaseModel):
    username: str
    full_name: Union[str, None] = None
    email: Union[str, None] = None
    disabled: Union[bool, None] = None

#para los usuarios de la DB
class UserInDB(User): 
    hashed_password: str  #de acá sacamos el password del usuario por separado por seguridad




def get_user(db, username):
    if username in db:
        user_data = db[username]
        return UserInDB(**user_data) 
    return []

#verifica si la password es correcta y retorna (True o False)
def verify_password(plane_password, hashed_password): #plane_password es la contraseña del formulario
    return pwt_context.verify(plane_password, hashed_password)


#para autentificar el usuario y sus credenciales, retorna el usuario
def authenticate_user(db, username, password):
    user = get_user(db,username)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales invalidas", headers={"WWW-authenticate": "Bearer"})
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales invalidas", headers={"WWW-authenticate": "Bearer"})
    return user      

def create_token(data: dict, user:UserInDB, time_expire: Union[datetime, None] = None):
    data_copy = data.copy()
    if time_expire is None:
        expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    else:
        expires = datetime.now(timezone.utc) + time_expire
    data_copy.update({"exp": expires})
    token_jwt = jwt.encode(data_copy, user.hashed_password, algorithm="HS256")
    print (token_jwt)
    return token_jwt

@login_router.get("/user/me")
def user(token: str = Depends(oauth2_scheme)):
    return token

@login_router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    #user_copy = user.model_copy()
    access_token_expires = timedelta(minutes=30)  #timpo de token
    access_token_jwt = create_token({"sub": user.username}, user,access_token_expires)
    return {
        "access_token": access_token_jwt,
        "token_type": "bearer"
    }