# En backend/services/auth_service.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pymongo.database import Database
from typing import Optional

from database.database import get_db_nosql
from utils import security
from schemas import user_schemas

bearer_scheme = HTTPBearer()
optional_bearer_scheme = HTTPBearer(auto_error=False)  # No lanza error si no hay token

async def get_current_user(authorization: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Database = Depends(get_db_nosql)) -> user_schemas.UserOut:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = authorization.credentials
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.users.find_one({"email": email})
    if user is None:
        raise credentials_exception
    # Convert ObjectId to string for Pydantic validation
    if "_id" in user:
        user["_id"] = str(user["_id"])

    return user_schemas.UserOut(**user)

async def get_current_user_optional(
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer_scheme), 
    db: Database = Depends(get_db_nosql)
) -> Optional[user_schemas.UserOut]:
    """
    Obtiene el usuario actual si está autenticado, o None si no lo está.
    Esta función NO lanza excepción si no hay token, permitiendo acceso anónimo.
    """
    if not authorization:
        return None
    
    try:
        token = authorization.credentials
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None

    user = await db.users.find_one({"email": email})
    if user is None:
        return None
    
    # Convert ObjectId to string for Pydantic validation
    if "_id" in user:
        user["_id"] = str(user["_id"])

    return user_schemas.UserOut(**user)

async def get_current_admin_user(current_user: user_schemas.UserOut = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges"
        )
    return current_user