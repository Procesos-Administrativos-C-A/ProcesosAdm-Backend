import sys
from typing import Generator,Union, Annotated

from schema.empleadoSchema import *
sys.path.append("..")
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext #para usar el algoritmo bcrypt de encriptamiento
from datetime import datetime, timedelta, timezone #para trabajar con los tiempos, esto para el token
from jose import jwt, JWTError #dependencia que extiende jwt
from utils.dbConection import conexion


login_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/ingresar", auto_error=False)
pwt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  #bcrypt sera el tipo de algoritmo para el encriptamiento o desencriptamiento de la password
secrectKey = '1ab911a1d38a65cf093c168d54f9615d60b464cd884aa3f15c940b9556f92cc6' # ESTO SE TIENE QUE CAMBIAR MAS ADELANTE

def verify_password(plane_password, hashed_password): #plane_password es la contraseña del formulario
    return pwt_context.verify(plane_password, hashed_password)

def authenticate_user( username, password):
    try:
        with conexion.cursor() as cursor:
            sql_empleados = "SELECT cedula, nombre, rol, contraseña FROM empleados WHERE cedula = %s"
            cursor.execute(sql_empleados, (username,))
            empleadoRes = cursor.fetchone()
            empleado = { 'cedula': empleadoRes['cedula'],
                          'nombre': empleadoRes['nombre'], 
                          'rol': empleadoRes['rol'], 
                          'contraseña': empleadoRes['contraseña']}
            
        if not empleado:
            raise HTTPException(status_code=401, detail="Usuario no encontrado", headers={"WWW-authenticate": "Bearer"})
        if not verify_password(password, empleado['contraseña']):
            raise HTTPException(status_code=401, detail="Contraseña incorrecta", headers={"WWW-authenticate": "Bearer"})
        
        return empleado

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener las credenciales del empleados: {str(e)}")
      

def create_token(data: dict, time_expire: Union[datetime, None] = None):
    data_copy = data.copy()
    if time_expire is None:
        expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    else:
        expires = datetime.now(timezone.utc) + time_expire
    data_copy.update({"exp": expires}) 
    token_jwt = jwt.encode(data_copy, key = secrectKey, algorithm="HS256")
    return token_jwt

#verificar que el usuario que envio el tokent existe
def get_user_current( token: str = Depends(oauth2_scheme)):
    try:
        token_decode = jwt.decode(token, key= secrectKey, algorithms="HS256")
        username = int(token_decode.get("sub"))

        # Verificar el tiempo restante del token
        tiempo = datetime.fromtimestamp(token_decode.get("exp"), tz=timezone.utc)
        tiempo_actual = datetime.now(timezone.utc)
        tiempo_restante = tiempo - tiempo_actual

        if tiempo_restante.total_seconds() <= 0:
            raise HTTPException(status_code=401, detail="El token ha expirado", headers={"WWW-authenticate": "Bearer"})

        if username == None:
            raise HTTPException(status_code=401, detail="Credenciales invalidas", headers={"WWW-authenticate": "Bearer"})
        with conexion.cursor() as cursor:
            sql_empleados = "SELECT cedula, nombre, rol, cargo, contraseña FROM empleados WHERE cedula = %s"
            cursor.execute(sql_empleados, (username,))
            empleadoRes = cursor.fetchone()
            empleado = { 'cedula': empleadoRes['cedula'],
                          'nombre': empleadoRes['nombre'], 
                          'rol': empleadoRes['rol'], 
                          'cargo': empleadoRes['cargo'], 
                          'contraseña': empleadoRes['contraseña']}
            
        if not empleado:
            raise HTTPException(status_code=401, detail="Usuario no encontrado", headers={"WWW-authenticate": "Bearer"})
        return empleado
    except JWTError:
        raise HTTPException(status_code=401, detail="Credenciales invalidas", headers={"WWW-authenticate": "Bearer"})
    
    

#cuando se verifique el usuario siga siendo valido
def get_user_disabled_current(user: Empleado = Depends(get_user_current)):
    if not user.activo:
        raise HTTPException(status_code=400, detail="Inactive User")
    return user



@login_router.post("/CrearEmpleado", response_model=Empleado)
async def create_empleado(empleado_data: Empleado):
    """
    Creates a new employee in the database.

    **Permissions:** Requires a valid user with active status.

    **Parameters:**
        - empleado_data (EmpleadoInDB): A Pydantic model containing employee details.

    **Returns:**
        The newly created employee object (Empleado).

    **Raises:**
        - HTTPException 400: If invalid employee data is provided.
        - HTTPException 403: If the user is unauthorized or inactive.
        - HTTPException 409: If an employee with the same cedula already exists.
        - HTTPException 500: If an internal server error occurs.
    """

    try:
        # Validate employee data
        if not empleado_data.cedula or not empleado_data.contraseña or not empleado_data.rol:
            raise HTTPException(status_code=400, detail="Employee name and role are required.")

        # Hash the password before storing it
        empleado_data.contraseña = pwt_context.hash(empleado_data.contraseña)

        with conexion.cursor() as cursor:
            # Check for existing employee with the same cedula
            sql_check_exist = "SELECT cedula FROM empleados WHERE cedula = %s"
            cursor.execute(sql_check_exist, (empleado_data.cedula,))
            existing_user = cursor.fetchone()

            if existing_user:
                raise HTTPException(status_code=409, detail="Employee with this cedula already exists.")

            # Insert new employee into the database
            sql_insert = "INSERT INTO empleados (cedula, nombre, rol, cargo, email, contraseña) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql_insert, (empleado_data.cedula, empleado_data.nombre, empleado_data.rol, empleado_data.cargo, empleado_data.email, empleado_data.contraseña))
            conexion.commit()

            # Retrieve the newly created employee for response
            sql_get_created = "SELECT cedula, nombre, rol, cargo, email, contraseña FROM empleados WHERE cedula = %s"
            cursor.execute(sql_get_created, (empleado_data.cedula,))
            created_empleado = cursor.fetchone()

            if created_empleado:
                return Empleado(**created_empleado)
            else:
                raise HTTPException(status_code=500, detail="Employee creation failed (no record found).")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating employee: {str(e)}")

@login_router.get("/user/me")
def user(user: Empleado = Depends(get_user_current)):
    return user

@login_router.post("/ingresar")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user( form_data.username, form_data.password)
    access_token_expires = timedelta(minutes=30)  #timpo de token
    access_token_jwt = create_token({"sub": str(user['cedula'])}, access_token_expires)
    return {
        "access_token": access_token_jwt,
        "token_type": "bearer"
    }