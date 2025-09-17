from src.database.PSQLmodels import UserModel
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import timedelta, datetime
from src.models.Auth import (
    Token, authenticate_user, 
    create_access_token, get_current_user, get_current_admin_user,
    get_current_user_id,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

users_router = APIRouter(prefix="/users", tags=["Пользователь"])

class UserCreate(BaseModel):
    login: str
    password: str
    licence_date: str 
    admin: bool = False

class User:
    def __init__(self, id: int = 0, login: str = '', password : str = '', licence_date: str = '', admin=False):
        self.id = id
        self.login = login
        self.password = password
        self.licence_date = licence_date
        self.admin = admin
    
    def add_new_user(self, data):
        return UserModel().create_user(data)
    
    def get_all_users(self):
        return UserModel().all_users()
    
    def update_user_info(self, data):
        return UserModel(id=self.id).update_user(data)
    
    def delete_user(self):
        return UserModel(id=self.id).delete_user()
    

@users_router.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Здесь происходит проверка лицензии при входе
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.login, "admin": user.admin},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

# @users_router.get("/users/me")
# async def read_users_me(current_user: User = Depends(get_current_user)):
#     """Информация о текущем пользователе"""
#     return {
#         "id": current_user.id,
#         "login": current_user.login,
#         "admin": current_user.admin,
#         "licence_date": current_user.licence_date
#     }

# @users_router.get("/users/my_id")
# async def get_my_user_id(user_id: int = Depends(get_current_user_id)):
#     """Получить только ID текущего пользователя"""
#     return {"user_id": user_id}

@users_router.put("/add_new_user")
async def add_new_user(
    data: UserCreate,
    current_user: User = Depends(get_current_admin_user)  # Только админы!
):
    """Создание нового пользователя - только для администраторов"""
    result = User().add_new_user(data)
    return result

@users_router.post("/update_user_info/{user_id}")
async def update_user_info(
    user_id: int,
    data: UserCreate,
    current_user: User = Depends(get_current_admin_user)  # Только админы!
):
    """Создание нового пользователя - только для администраторов"""
    result = User(id=user_id).update_user_info(data)
    return result

@users_router.delete("/delete_user/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user)  # Только админы!
):
    """Создание нового пользователя - только для администраторов"""
    result = User(id=user_id).delete_user()
    return result

@users_router.get("/all_users")
async def get_all_users(current_user: User = Depends(get_current_admin_user)):
    """Получение всех пользователей - только для администраторов"""
    result = User().get_all_users()
    return result
