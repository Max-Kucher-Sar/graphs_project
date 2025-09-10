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

    wells = relationship('Well', back_populates='user', cascade="all, delete-orphan", passive_deletes=True)

class Well(Base):
    __tablename__ = 'wells'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=True)
    is_press = Column(Boolean, nullable=True)
    is_debit = Column(Boolean, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    user = relationship("User", back_populates="wells")

    data = relationship('Data', back_populates='well', cascade="all, delete-orphan", passive_deletes=True)

class Data(Base):
    __tablename__ = 'data'
    id = Column(Integer, primary_key=True)
    well_id = Column(Integer, ForeignKey('wells.id', ondelete='CASCADE'), nullable=False)
    debit_data = Column(JSONB, default=dict)
    press_data = Column(JSONB, default=dict)
    debit_table = Column(JSONB, default=dict)
    dpi = Column(JSONB, default=dict)
    spider_graph = Column(JSONB, default=dict)

    well = relationship("Well", back_populates="data")


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

class WellModel:
    def __init__(self, id: int = 0, name: str = '', is_press=False, is_debit=False, user_id: int = 0):
        self.session = db
        self.id = id
        self.name = name
        self.is_press = is_press
        self.is_debit = is_debit
        self.user_id = user_id

    def create_well(self):
        existing_well = self.session.query(Well).filter(Well.name == self.name, Well.user_id == self.user_id).first()
        if existing_well:
            return {"msg": "Скважина уже существует"}
        new_well = Well(
            name=self.name,
            is_press=self.is_press,
            is_debit=self.is_debit,
            user_id=self.user_id
        )
        self.session.add(new_well)
        self.session.commit()
        return {"msg": "Скважина создана"}
    
    def delete_well(self):
        existing_well = self.session.query(Well).filter(Well.id == self.id, Well.user_id == self.user_id).first()
        if existing_well:
            self.session.delete(existing_well)
            self.session.commit()
            return {"msg": "Скважина удалена"}
        return {"msg": "Скважина не существует"}
    
    def get_all_wells(self):
        return self.session.scalars(self.session.query(Well).filter(Well.user_id == self.user_id)).all()

class DataModel:
    def __init__(self, id: int = 0, well_id: int = 0, user_id: int = 0):
        self.session = db
        self.id = id
        self.well_id = well_id
        self.user_id = user_id

    
    