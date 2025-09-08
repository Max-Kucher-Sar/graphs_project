from sqlalchemy import create_engine, Column, Integer, Text, Boolean, String, DateTime, JSON, MetaData, Table, ForeignKey, desc, func, Date, or_, and_, over
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import exists, select
from sqlalchemy.sql.expression import func
from sqlalchemy import inspect, text
from sqlalchemy import update, insert, delete
from typing import List, Optional, Dict, Tuple

import json
import datetime
import hashlib
import os
from dotenv import load_dotenv

from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

load_dotenv()

user = os.getenv('user')
pswd = os.getenv('pswd')

Base = declarative_base()
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    login = Column(String, nullable=True)
    password = Column(String, nullable=True)
    licence_date = Column(DateTime, nullable=True)
    admin = Column(Boolean, nullable=True)


engine = create_engine(f'postgresql+psycopg2://{user}:{pswd}@postgres/pdb', pool_size=50, max_overflow=0)

Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autoflush=True, bind=engine)
db = SessionLocal()


class UserModel:
    def __init__(self, id: int = 0, login: str = '', password : str = '', licence_date: str = '', admin=False):
        self.session = db
        self.id = id
        self.login = login
        self.password = password
        self.licence_date = licence_date
        self.admin = admin

    def create_user(self, data):        
        existing_user = self.session.query(User).filter(User.login == data.login).first()
        if not existing_user:
            # Хэшируем пароль
            hashed_password = hashlib.md5(data.password.encode()).hexdigest()
            
            new_user = User(
                login=data.login,
                password=hashed_password,
                licence_date=data.licence_date,
                admin=data.admin
            )
            self.session.add(new_user)
            self.session.commit()
            return {"msg": "Пользователь создан"}
        return {"msg": "Пользователь уже существует"}
    
    def all_users(self):
        result = self.session.query(User).all()
        return result
    
    def get_user_by_login(self, login: str):
        return self.session.query(User).filter(User.login == login).first()

    def update_user(self, data):
        existing_user = self.session.query(User).filter(User.id == self.id).first()
        if existing_user:
            hashed_password = hashlib.md5(data.password.encode()).hexdigest()

            existing_user.login = data.login
            existing_user.password = hashed_password
            existing_user.licence_date = data.licence_date
            existing_user.admin = data.admin

            self.session.commit()
            return {"msg": "Пользователь обновлен"}
        return {"msg": "Пользователь отсутствует"}
    
    def delete_user(self):
        existing_user = self.session.query(User).filter(User.id == self.id).first()
        if existing_user:
            self.session.delete(existing_user)
            self.session.commit()
            return {"msg": "Пользователь удален"}
        return {"msg": "Пользователь отсутствует"}