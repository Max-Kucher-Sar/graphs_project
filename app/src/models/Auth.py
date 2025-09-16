from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Optional
from src.database.PSQLmodels import UserModel, User
from pydantic import BaseModel
import hashlib
import os
from dotenv import load_dotenv

class Token(BaseModel):
    access_token: str
    token_type: str

load_dotenv()


# Настройки
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="https://gubkin-technologies.ru/api/users/login")

def verify_password(plain_password, hashed_password):
    return hashlib.md5(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password):
    return hashlib.md5(password.encode()).hexdigest()

def authenticate_user(login: str, password: str):
    user_model = UserModel()
    user = user_model.get_user_by_login(login)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    
    # ПРОВЕРЯЕМ ЛИЦЕНЗИЮ ТОЛЬКО ПРИ ВХОДЕ
    if user.licence_date < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Срок действия вашей лицензии истек. Вход запрещен."
        )
    
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверные учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_model = UserModel()
    user = user_model.get_user_by_login(username)
    if user is None:
        raise credentials_exception
    
    # НЕ проверяем лицензию при каждом запросе - только при входе
    return user

async def get_current_admin_user(current_user = Depends(get_current_user)):
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав. Требуются права администратора."
        )
    return current_user

async def get_current_user_id(current_user = Depends(get_current_user)) -> int:
    """Возвращает ID текущего аутентифицированного пользователя"""
    return current_user.id