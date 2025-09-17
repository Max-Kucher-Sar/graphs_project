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
from sqlalchemy.orm.attributes import flag_modified

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
    user_tech_data = relationship('UserTechData', back_populates='user', cascade="all, delete-orphan", passive_deletes=True)
    


class Well(Base):
    __tablename__ = 'wells'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=True)
    is_press = Column(Boolean, nullable=True)
    is_debit = Column(Boolean, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    user = relationship("User", back_populates="wells")

    data = relationship('Data', back_populates='well', cascade="all, delete-orphan", passive_deletes=True)
    
    well_tech_data = relationship('WellTechData', back_populates='well', cascade="all, delete-orphan", passive_deletes=True)

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


class UserTechData(Base):
    __tablename__ = 'usertechdata'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    pressure = Column(String, nullable=True)
    flow = Column(String, nullable=True)
    thickness = Column(String, nullable=True)
    viscosity = Column(String, nullable=True)
    permeability = Column(String, nullable=True)
    porosity = Column(String, nullable=True)
    radius = Column(String, nullable=True)
    compressibility = Column(String, nullable=True)
    water_saturation = Column(String, nullable=True)
    volume_factor = Column(String, nullable=True)

    user = relationship("User", back_populates="user_tech_data")

class WellTechData(Base):
    __tablename__ = 'welltechdata'
    id = Column(Integer, primary_key=True)
    well_id = Column(Integer, ForeignKey('wells.id', ondelete='CASCADE'), nullable=False)
    pressure = Column(Integer, nullable=True)
    flow = Column(Integer, nullable=True)
    thickness = Column(Integer, nullable=True)
    viscosity = Column(Integer, nullable=True)
    permeability = Column(Integer, nullable=True)
    porosity = Column(Integer, nullable=True)
    radius = Column(Integer, nullable=True)
    compressibility = Column(Integer, nullable=True)
    water_saturation = Column(Integer, nullable=True)
    volume_factor = Column(Integer, nullable=True)

    well = relationship("Well", back_populates="well_tech_data")



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
        try:        
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
        except Exception as e:
            self.session.rollback()
            return {"msg": f"ошибка при покупке: {e}"}
        finally:
            self.session.close()
    
    def all_users(self):
        result = self.session.query(User).all()
        return result
    
    def get_user_by_login(self, login: str):
        return self.session.query(User).filter(User.login == login).first()

    def update_user(self, data):
        try: 
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
        except Exception as e:
            self.session.rollback()
            return {"msg": f"ошибка при покупке: {e}"}
        finally:
            self.session.close()
    
    def delete_user(self):
        try:
            existing_user = self.session.query(User).filter(User.id == self.id).first()
            if existing_user:
                self.session.delete(existing_user)
                self.session.commit()
                return {"msg": "Пользователь удален"}
            return {"msg": "Пользователь отсутствует"}
        except Exception as e:
            self.session.rollback()
            return {"msg": f"ошибка при покупке: {e}"}
        finally:
            self.session.close()

class WellModel:
    def __init__(self, id: int = 0, name: str = '', is_press=False, is_debit=False, user_id: int = 0):
        self.session = db
        self.id = id
        self.name = name
        self.is_press = is_press
        self.is_debit = is_debit
        self.user_id = user_id

    def create_well(self):
        try:
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
        except Exception as e:
            self.session.rollback()
            return {"msg": f"ошибка при покупке: {e}"}
        finally:
            self.session.close()
    
    def delete_well(self):
        try:
            existing_well = self.session.query(Well).filter(Well.id == self.id, Well.user_id == self.user_id).first()
            if existing_well:
                self.session.delete(existing_well)
                self.session.commit()
                return {"msg": "Скважина удалена"}
            return {"msg": "Скважина не существует"}
        except Exception as e:
            self.session.rollback()
            return {"msg": f"ошибка при покупке: {e}"}
        finally:
            self.session.close()
    
    def get_all_wells(self):
        return self.session.scalars(self.session.query(Well).filter(Well.user_id == self.user_id)).all()

class DataModel:
    def __init__(self, data=[], id: int = 0, well_id: int = 0, user_id: int = 0, is_debit: bool = False, is_press: bool = False):
        self.session = db
        self.id = id
        self.well_id = well_id
        self.user_id = user_id
        self.is_debit = is_debit
        self.is_press = is_press
        self.data = data

    def upload_primary_debit(self, debit_table):
        try:
            existing_debit_data = self.session.query(Data).filter(Data.well_id == self.well_id).first()
            if existing_debit_data:
                existing_debit_data.debit_data = self.data
                existing_debit_data.debit_table = debit_table
                flag_modified(existing_debit_data, 'debit_data')
                flag_modified(existing_debit_data, 'debit_table')
                self.session.commit()
                return True
            else:
                new_data = Data(
                    well_id=self.well_id,
                    debit_data=self.data,
                    press_data={},
                    debit_table=debit_table,
                    dpi={},
                    spider_graph={}
                )
                self.session.add(new_data)
                self.session.commit()
                return True
        except Exception as e:
            self.session.rollback()
            return {"msg": f"ошибка при загрузке: {e}"}
        finally:
            self.session.close()

    def upload_primary_press(self):
        try:
            existing_press_data = self.session.query(Data).filter(Data.well_id == self.well_id).first()
            if existing_press_data:
                existing_press_data.press_data = self.data
                flag_modified(existing_debit_data, 'press_data')
                self.session.commit()
                return True
            else:
                new_data = Data(
                    well_id=self.well_id,
                    debit_data={},
                    press_data=self.data,
                    debit_table={},
                    dpi={},
                    spider_graph={}
                )
                self.session.add(new_data)
                self.session.commit()
                return True
        except Exception as e:
            self.session.rollback()
            return {"msg": f"ошибка при загрузке: {e}"}
        finally:
            self.session.close()
    
    def get_primary_data(self):
        if self.is_debit == True:
            result = self.session.query(Data.debit_data).join(Well, Data.well_id == Well.id).filter(Data.well_id == self.well_id).filter(Well.user_id == self.user_id).first()
            if result:
                return result[0]
            else:
                return None
        elif self.is_press == True:
            result = self.session.query(Data.press_data).join(Well, Data.well_id == Well.id).filter(Data.well_id == self.well_id).filter(Well.user_id == self.user_id).first()
            if result:
                return result[0]
            else:
                return None

class UserTechDataModel:
    def __init__(self, data=[], user_id: int = 0):
        self.session = db
        self.data = data
        self.user_id = user_id
            
    def update_units(self):
        try:
            result = self.session.execute(update(UserTechData).where(UserTechData.user_id == self.user_id).values(**self.data))
            self.session.commit()
            if result:
                return True
            else:
                return False
        except Exception as e:
            self.session.rollback()
            return {"msg": f"ошибка при обновлении: {e}"}
        finally:
            self.session.close()

    def get_user_units(self):
        try:
            user_units = self.session.query(UserTechData).filter(UserTechData.user_id == self.user_id).first()
            if user_units:
                return user_units
            else:
                max_id = self.session.query(func.max(UserTechData.id)).scalar() or 0
                new_units = UserTechData(
                    id=max_id,
                    user_id=self.user_id,
                    pressure=None,
                    flow=None,
                    thickness=None,
                    viscosity=None,
                    permeability=None,
                    porosity=None,
                    radius=None,
                    compressibility=None,
                    water_saturation=None,
                    volume_factor=None
                )
                empty_units = {
                    'id':max_id,
                    'pressure':None,
                    'flow':None,
                    'thickness':None,
                    'viscosity':None,
                    'permeability':None,
                    'porosity':None,
                    'radius':None,
                    'compressibility':None,
                    'water_saturation':None,
                    'volume_factor':None
                }
                self.session.add(new_units)
                self.session.commit()
                return empty_units
        except Exception as e:
            self.session.rollback()
            return {"msg": f"ошибка при загрузке: {e}"}
        finally:
            self.session.close()

class WellTechDataModel:
    def __init__(self, data=[], well_id: int = 0):
        self.session = db
        self.data = data
        self.well_id = well_id
            
    def update_measures(self):
        # print(self.data.__dict__)
        try:
            result = self.session.execute(update(WellTechData).where(WellTechData.well_id == self.well_id).values(**self.data))
            self.session.commit()
            if result:
                return True
            else:
                return False
        except Exception as e:
            self.session.rollback()
            return {"msg": f"ошибка при обновлении: {e}"}
        finally:
            self.session.close()

    def get_well_measures(self):
        try:
            well_measures = self.session.query(WellTechData).filter(WellTechData.well_id == self.well_id).first()
            if well_measures:
                return well_measures
            else:
                max_id = self.session.query(func.max(WellTechData.id)).scalar() or 0
                new_measures = WellTechData(
                    id=max_id,
                    well_id=self.well_id,
                    pressure=None,
                    flow=None,
                    thickness=None,
                    viscosity=None,
                    permeability=None,
                    porosity=None,
                    radius=None,
                    compressibility=None,
                    water_saturation=None,
                    volume_factor=None
                )
                empty_measures = {
                    'id':max_id,
                    'pressure':None,
                    'flow':None,
                    'thickness':None,
                    'viscosity':None,
                    'permeability':None,
                    'porosity':None,
                    'radius':None,
                    'compressibility':None,
                    'water_saturation':None,
                    'volume_factor':None
                }
                self.session.add(new_measures)
                self.session.commit()
                return empty_measures
        except Exception as e:
            self.session.rollback()
            return {"msg": f"ошибка при загрузке: {e}"}
        finally:
            self.session.close()
