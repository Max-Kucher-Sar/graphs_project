from sqlalchemy import create_engine, Column, Integer, Text, Boolean, String, DateTime, Numeric, JSON, MetaData, Table, ForeignKey, desc, func, Date, or_, and_, over
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
from datetime import datetime
import hashlib
import os
from dotenv import load_dotenv
import math

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
    spider = Column(Boolean, default=False)
    rpl = Column(JSONB, default=dict)
    rsum = Column(Boolean, default=False)

    user = relationship("User", back_populates="wells")

    data = relationship('Data', back_populates='well', cascade="all, delete-orphan", passive_deletes=True)
    
    well_tech_data = relationship('WellTechData', back_populates='well', cascade="all, delete-orphan", passive_deletes=True)
    user_tech_data = relationship('UserTechData', back_populates='well', cascade="all, delete-orphan", passive_deletes=True)

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
    well_id = Column(Integer, ForeignKey('wells.id', ondelete='CASCADE'), nullable=True)
    pressure = Column(String, nullable=True)
    debit = Column(String, nullable=True)
    thickness = Column(String, nullable=True)
    viscosity = Column(String, nullable=True)
    permeability = Column(String, nullable=True)
    porosity = Column(String, nullable=True)
    radius = Column(String, nullable=True)
    compressibility = Column(String, nullable=True)
    volume_factor = Column(String, nullable=True)

    user = relationship("User", back_populates="user_tech_data")
    well = relationship("Well", back_populates="user_tech_data")

class WellTechData(Base):
    __tablename__ = 'welltechdata'
    id = Column(Integer, primary_key=True)
    well_id = Column(Integer, ForeignKey('wells.id', ondelete='CASCADE'), nullable=False)
    pressure = Column(Numeric(40, 25), nullable=True)
    thickness = Column(Numeric(40, 25), nullable=True)
    viscosity = Column(Numeric(40, 25), nullable=True)
    permeability = Column(Numeric(40, 25), nullable=True)
    porosity = Column(Numeric(40, 25), nullable=True)
    radius = Column(Numeric(40, 25), nullable=True)
    compressibility = Column(Numeric(40, 25), nullable=True)
    volume_factor = Column(Numeric(40, 25), nullable=True)

    well = relationship("Well", back_populates="well_tech_data")


engine = create_engine(f'postgresql+psycopg2://{user}:{pswd}@postgres/pdb', pool_size=50, max_overflow=0)

Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autoflush=True, bind=engine)
db = SessionLocal()

# def convert_to_si(debit_info: Optional[dict()] = None, values: Optional[dict()] = None, measures: Optional[dict()] = None, press_info: Optional[dict()] = None):
#         pressure = {"тех.атм": 98066.5, "psi": 6894.76, "МПа": 1000000, "физ.атм": 101325, "kПа-1": 1000} # умножить чтобы перевести в СИ
#         thickness = {"ft": 3.28084} # разделить чтобы перевести в СИ
#         viscosity = {"сП": 0.001, "cp": 0.001} # умножить чтобы перевести в СИ
#         permeability = {"мД": 9.86923e-16, "md": 9.86923e-16, "Дарси": 9.86923e-13} # умножить чтобы перевести в СИ
#         porosity = {"%": 0.01} # умножить чтобы перевести в СИ
#         radius = {"ft": 3.28084} # разделить чтобы перевести в СИ
#         compressibility = {"psi-1": 0.0014505, "МПа-1": 0.000001, "физ.атм-1": 0.0000098694, "кПа-1": 0.001, "кг/см2": 0.00000000101972} # умножить чтобы перевести в СИ
#         debit = {"м3/сут": 0.0000115740740740741, "bbl/d": 0.00000184} # умножить чтобы перевести в СИ
#         param_list_str = ['pressure', 'thickness', 'viscosity', 'permeability', 'porosity', 'radius', 'compressibility']
#         param_list = [pressure, thickness, viscosity, permeability, porosity, radius, compressibility]

        

#         try:
#             if values and measures:
#                 result = dict()
#             """
#             из measures по ключу param получаем название параметра, потом это название используем как ключ параметра и достаем числовое значение
#             это числовое значение нужно либо умножить, либо разделить на число, которое содержится в self.data по ключу param.
#             В заключении переопределить в self.data по ключу param полученное значение
#             """
#                 for i in range(len(param_list)):
#                     user_param_name = measures[param_list_str[i]]
#                     coef_for_param = param_list[i][user_param_name]
#                     value_param = values[param_list_str[i]]
#                     if param_list_str[i] == 'radius' or param_list_str[i] == 'thickness':
#                         result[param_list_str[i]] = value_param / coef_for_param
#                     else:
#                         result[param_list_str[i]] = value_param * coef_for_param
#                 return result
#             elif debit_info:
#                 for user_unit, user_value in debit_info.items():
#                     result_value = user_value * debit[user_unit]
#                 return result_value
#             elif press_info:
#                 for user_unit, user_value in press_info.items():
#                     result_value = user_value * pressure[user_unit]
#                 return result_value
#         except Exception as e:
#             return {"err_msg": f"Ошибка при конвертировании параметра в удобные нам единицы: {e}"}

def convert_to_si(
        debit_info: Optional[dict] = None,
        values: Optional[dict] = None, 
        measures: Optional[dict] = None, 
        press_info: Optional[dict] = None
    ):
    # Словари коэффициентов преобразования
    # pressure = {"тех.атм": 98066.5, "psi": 6894.76, "МПа": 1000000, "физ.атм": 101325, "kПа-1": 1000}
    pressure = {
        "тех.атм": 98066.5, 
        "psi": 6894.76, 
        "МПа": 1000000.0, 
        "физ.атм": 101325.0, 
        "кПа": 1000.0,
        "Па": 1.0
    }
    # thickness = {"ft": 3.28084, "m": 1.0}  # добавил метры
    thickness = {"ft": 3.28084, "m": 1.0}
    # viscosity = {"сП": 0.001, "cp": 0.001, "Па·с": 1.0}
    viscosity = {"сП": 0.001, "cp": 0.001, "Па*с": 1.0}
    # permeability = {"мД": 9.86923e-16, "md": 9.86923e-16, "Дарси": 9.86923e-13, "м²": 1.0}
    permeability = {
        "мД": 9.86923e-16, 
        "md": 9.86923e-16, 
        "Дарси": 9.86923e-13, 
        "m²": 1.0
    }
    # porosity = {"%": 0.01, "доли": 1.0}
    porosity = {"%": 0.01, "доли": 1.0}
    # radius = {"ft": 3.28084, "m": 1.0}
    radius = {"ft": 3.28084, "m": 1.0}
    # compressibility = {
    #     "psi-1": 0.0014505, "МПа-1": 0.000001, "физ.атм-1": 0.0000098694, 
    #     "кПа-1": 0.001, "кг/см2": 0.00000000101972, "Па⁻¹": 1.0
    # }
    compressibility = {
        "psi⁻¹": 0.0014505, 
        "МПа⁻¹": 1e-6, 
        "физ.атм⁻¹": 9.8694e-6, 
        "кПа⁻¹": 0.001, 
        "кг/см²": 1.01972e-9, 
        "Па⁻¹": 1.0
    }
    # volume_factor = {"%": 1.0, "fraction": 1.0}  # добавил словарь
    # debit = {"м³/сут": 0.0000115740740740741, "bbl/d": 0.00000184}
    volume_factor = {"%": 0.01, "доли": 1.0}  # добавил словарь
    debit = {
        "м³/сут": 1.157407e-5, 
        "bbl/d": 1.84e-6, 
        "м³/сек": 1.0
    }
    
    # Параметры, которые требуют деления (а не умножения)
    DIVISION_PARAMS = {'radius', 'thickness'}
    
    try:
        if values and measures:
            result = {}
            
            # Обрабатываем основные параметры
            for param_name in ['pressure', 'thickness', 'viscosity', 'permeability', 
                            'porosity', 'radius', 'compressibility', 'volume_factor']:
                
                if param_name not in measures or param_name not in values:
                    continue  # пропускаем отсутствующие параметры
                
                user_unit = measures[param_name]
                value = values[param_name]
                
                # Получаем соответствующий словарь коэффициентов
                coeff_dict = locals().get(param_name, {})
                
                if user_unit not in coeff_dict:
                    # Если единица измерения не найдена, используем исходное значение
                    result[param_name] = value
                    continue
                
                coefficient = coeff_dict[user_unit]
                
                # Применяем преобразование
                if param_name in DIVISION_PARAMS:
                    result[param_name] = value / coefficient
                else:
                    result[param_name] = value * coefficient
            
            return result
            
        elif debit_info:
            result = {}
            for user_unit, user_value in debit_info.items():
                if user_unit in debit:
                    result[user_unit] = user_value * debit[user_unit]
                else:
                    result[user_unit] = user_value  # неизвестная единица
            return result
            
        elif press_info:
            result = {}
            for user_unit, user_value in press_info.items():
                if user_unit in pressure:
                    result[user_unit] = user_value * pressure[user_unit]
                else:
                    result[user_unit] = user_value  # неизвестная единица
            return result
            
        else:
            return {"msg": "Не переданы данные для конвертации"}
            
    except Exception as e:
        return {"msg": f"Ошибка при конвертировании параметра в удобные нам единицы: {e}"}

# def convert_to_user_si(debit_info: Optional[dict()] = None, values: Optional[dict()] = None, measures: Optional[dict()] = None, press_info: Optional[dict()] = None):
#         pressure = {"тех.атм": 98066.5, "psi": 0.000145038, "МПа": 1000000, "физ.атм": 0.00000986923, "kПа-1": 1000} # разделить чтобы перевести в СИ
#         thickness = {"ft": 3.28084} # умножить чтобы перевести в СИ
#         viscosity = {"сП": 0.001, "cp": 0.001} # разделить чтобы перевести в СИ
#         permeability = {"мД": 9.86923e-16, "md": 9.86923e-16, "Дарси": 9.86923e-13} # разделить чтобы перевести в СИ
#         porosity = {"%": 0.01} # разделить чтобы перевести в СИ
#         radius = {"ft": 3.28084} # умножить чтобы перевести в СИ
#         compressibility = {"psi-1": 0.0014505, "МПа-1": 0.000001, "физ.атм-1": 0.0000098694, "кПа-1": 0.001, "кг/см2": 0.00000000101972} # разделить чтобы перевести в СИ
#         debit = {"м3/сут": 0.0000115740740740741, "bbl/d": 1.8399999999999998e-6} # разделить чтобы перевести в СИ
#         param_list_str = ['pressure', 'thickness', 'viscosity', 'permeability', 'porosity', 'radius', 'compressibility']
#         param_list = [pressure, thickness, viscosity, permeability, porosity, radius, compressibility]

    
#         try:
#             if values and measures:
#                 result = dict()
#             """
#             из measures по ключу param получаем название параметра, потом это название используем как ключ параметра и достаем числовое значение
#             это числовое значение нужно либо умножить, либо разделить на число, которое содержится в self.data по ключу param.
#             В заключении переопределить в self.data по ключу param полученное значение
#             """
#                 for i in range(len(param_list)):
#                     user_param_name = measures[param_list_str[i]]
#                     coef_for_param = param_list[i][user_param_name]
#                     value_param = values[param_list_str[i]]
#                     if param_list_str[i] == 'radius' or param_list_str[i] == 'thickness':
#                         result[param_list_str[i]] = value_param * coef_for_param
#                     else:
#                         result[param_list_str[i]] = value_param / coef_for_param
#                 return result
#             elif debit_info:
#                 for user_unit, user_value in debit_info.items():
#                     result_value = user_value / debit[user_unit]
#                     return result_value
#             elif press_info:
#                 for user_unit, user_value in press_info.items():
#                     result_value = user_value / pressure[user_unit]
#                     return result_value
#         except Exception as e:
#             return {"err_msg": f"Ошибка при конвертировании параметра в удобные нам единицы: {e}"}

def convert_to_user_si(
        debit_info: Optional[dict] = None,
        values: Optional[dict] = None, 
        measures: Optional[dict] = None, 
        press_info: Optional[dict] = None
    ):
    # Конвертируем все коэффициенты в float
    pressure = {
        "тех.атм": 98066.5, 
        "psi": 6894.76, 
        "МПа": 1000000.0, 
        "физ.атм": 101325.0, 
        "кПа": 1000.0,
        "Па": 1.0
    }
    thickness = {"ft": 3.28084, "m": 1.0}
    viscosity = {"сП": 0.001, "cp": 0.001, "Па*с": 1.0}
    permeability = {
        "мД": 9.86923e-16, 
        "md": 9.86923e-16, 
        "Дарси": 9.86923e-13, 
        "m²": 1.0
    }
    porosity = {"%": 0.01, "доли": 1.0}
    radius = {"ft": 3.28084, "m": 1.0}
    compressibility = {
        "psi⁻¹": 0.0014505, 
        "МПа⁻¹": 1e-6, 
        "физ.атм⁻¹": 9.8694e-6, 
        "кПа⁻¹": 0.001, 
        "кг/см²": 1.01972e-9, 
        "Па⁻¹": 1.0
    }
    volume_factor = {"%": 0.01, "доли": 1.0}  # добавил словарь
    debit = {
        "м³/сут": 1.157407e-5, 
        "bbl/d": 1.84e-6, 
        "м³/сек": 1.0
    }
    
    MULTIPLICATION_PARAMS = {'radius', 'thickness'}
    
    try:
        if values and measures:
            result = {"id": values['id'], "well_id": values['well_id']}
            
            # Конвертируем Decimal в float
            float_values = {k: float(v) if hasattr(v, '__float__') else v for k, v in values.items()}
            
            for param_name in ['pressure', 'thickness', 'viscosity', 'permeability', 
                             'porosity', 'radius', 'compressibility', 'volume_factor']:
                
                if param_name not in measures or param_name not in float_values:
                    continue
                
                user_unit = measures[param_name]
                value = float_values[param_name]
                
                coeff_dict = locals().get(param_name, {})
                
                if user_unit not in coeff_dict:
                    result[param_name] = value
                    continue
                
                coefficient = coeff_dict[user_unit]
                
                if param_name in MULTIPLICATION_PARAMS:
                    result[param_name] = value * coefficient
                else:
                    result[param_name] = value / coefficient
            
            return result
            
        elif debit_info:
            result = {}
            for user_unit, user_value in debit_info.items():
                if user_unit in debit:
                    # Конвертируем Decimal в float если нужно
                    value = float(user_value) if hasattr(user_value, '__float__') else user_value
                    result[user_unit] = value / debit[user_unit]
                else:
                    result[user_unit] = float(user_value) if hasattr(user_value, '__float__') else user_value
            return result
            
        elif press_info:
            result = {}
            for user_unit, user_value in press_info.items():
                if user_unit in pressure:
                    value = float(user_value) if hasattr(user_value, '__float__') else user_value
                    result[user_unit] = value / pressure[user_unit]
                else:
                    result[user_unit] = float(user_value) if hasattr(user_value, '__float__') else user_value
            return result
            
        else:
            return {"msg": "Не переданы данные для конвертации"}
            
    except Exception as e:
        return {"msg": f"Ошибка при конвертировании параметра в пользовательские единицы: {e}"}

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
                max_id = self.session.query(func.max(User.id)).scalar() or 0
                new_id = max_id + 1 
                new_user = User(
                    id=new_id,
                    login=data.login,
                    password=hashed_password,
                    licence_date=data.licence_date,
                    admin=data.admin
                )
                self.session.add(new_user)
                self.session.commit()
                return True
            return False
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
                return True
            return False
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
                return True
            return False
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
                return False
            max_id = self.session.query(func.max(Well.id)).scalar() or 0
            new_id = max_id + 1
            new_well = Well(
                id=new_id,
                name=self.name,
                is_press=self.is_press,
                is_debit=self.is_debit,
                user_id=self.user_id
            )
            self.session.add(new_well)
            self.session.commit()
            return True
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
                return True
            return False
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
                self.session.execute(update(Well).where(Well.id == self.well_id).values(is_debit = True))
                self.session.commit()
                return True
            else:
                max_id = self.session.query(func.max(Data.id)).scalar() or 0
                new_id = max_id + 1
                new_data = Data(
                    id = new_id,
                    well_id=self.well_id,
                    debit_data=self.data,
                    press_data={},
                    debit_table=debit_table,
                    dpi={},
                    spider_graph={}
                )
                self.session.add(new_data)
                self.session.execute(update(Well).where(Well.id == self.well_id).values(is_debit = True))
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
                flag_modified(existing_press_data, 'press_data')
                self.session.execute(update(Well).where(Well.id == self.well_id).values(is_press = True))
                self.session.commit()
                return True
            else:
                max_id = self.session.query(func.max(Data.id)).scalar() or 0
                new_id = max_id + 1
                new_data = Data(
                    id=new_id,
                    well_id=self.well_id,
                    debit_data={},
                    press_data=self.data,
                    debit_table={},
                    dpi={},
                    spider_graph={}
                )
                self.session.add(new_data)
                self.session.execute(update(Well).where(Well.id == self.well_id).values(is_press = True))
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

    def create_spider(self):
        self.data = WellTechDataModel(well_id=self.well_id).get_well_measures(user_id=self.user_id)
        debit_unit = self.session.query(UserTechData.debit).filter(UserTechData.user_id == self.user_id, UserTechData.well_id == None).scalar()
        # if self.data['pressure'] is None or self.data['thickness'] is None:
        #     return {"msg": "Отсутствуют переменные для расчета паука"}

        if any(value is None or value == 0.0 for value in self.data.values()):
            return {"msg": "Поле со значением 0 не валидно, введите правильное значение"}
        pressure = self.data['pressure']
        thickness = self.data['thickness']
        viscosity = self.data['viscosity']
        permeability = self.data['permeability']
        porosity = self.data['porosity']
        radius = self.data['radius']
        compressibility = self.data['compressibility']
        volume_factor = self.data['volume_factor']
        pyezoprovodnost = permeability / ((viscosity * compressibility) * porosity)

        # # Сохраняем изменения
        # WellTechDataModel(data=self.data, well_id=self.well_id).update_measures()

        try:
            # берем скважину где есть давление
            press_well_result = self.session.query(Well.id).filter(Well.is_press == True).first()
            press_well = press_well_result[0] if press_well_result else None
            data_for_processing = []
            if self.well_id == press_well:
                data_bd = self.session.query(Data.press_data, Data.debit_table).filter(Data.well_id == self.well_id).first() 
                press_data = self.get_hours(data_bd[0]) # переводим дату в часы
                data_for_processing = [press_data, data_bd[1]]
                
            else:
                press_data = self.session.query(Data.press_data).filter(Data.well_id == press_well).scalar()
                debit_table_data = self.session.query(Data.debit_table).filter(Data.well_id == self.well_id).scalar()
                press_data = self.get_hours(press_data) # переводим дату в часы
                data_for_processing = [press_data, debit_table_data]
            
            res_spider = {}
            dpi = []
            debit_table_times = [float(k) for k, v in data_for_processing[1].items()]

            for time_press, value_press in data_for_processing[0].items():
                time_press = float(time_press)
                # DPi = pressure 
                DPi = 0 
                for i in range(len(debit_table_times)):
                    to_str = str(debit_table_times[i])
                    if i == 0:
                        # deb_convert = {debit_unit: data_for_processing[1][to_str]}
                        # sys_deb = data_for_processing[1][to_str] # / 86400 # из м3/д в м3/сек
                        sys_deb = convert_to_si(debit_info={debit_unit: data_for_processing[1][to_str]})[debit_unit] # / 86400 # из м3/д в м3/сек
                    else:
                        to_str_2 = str(debit_table_times[i-1])
                        # sys_deb = (data_for_processing[1][to_str] - data_for_processing[1][to_str_2]) #/ 86400 # позже все будет в СИ ми убрать деление
                        sys_deb = (convert_to_si(debit_info={debit_unit: data_for_processing[1][to_str]})[debit_unit] - convert_to_si(debit_info={debit_unit: data_for_processing[1][to_str_2]})[debit_unit]) #/ 86400 # позже все будет в СИ ми убрать деление
                    
                    if time_press > debit_table_times[i]:
                        x = (radius ** 2) / (4 * pyezoprovodnost * ((time_press - debit_table_times[i]) * 3600))
               
                        E = self.ei(x)
                        
                        DPj = -((viscosity * sys_deb * volume_factor)/(permeability * thickness * 4 * math.pi)) * E
                        # DPj - используется для расчета суммы 
                        DPi += DPj

                    else:
                        continue

                res_spider[time_press] = DPi # / 101325 # из Па в физ.атм
                dpi.append(DPi) #  / 101325
            
            self.session.execute(update(Data).where(Data.well_id == self.well_id).values(dpi = dpi, spider_graph = res_spider))
            self.session.execute(update(Well).where(Well.id == self.well_id, Well.user_id == self.user_id).values(spider = True))
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            return {"msg": f"ошибка при расчете паука: {e}"}
        finally:
            self.session.close()

    def get_hours(self, time_dict):
        """
        Возвращает словарь, где дата переведена в часы
        """
        hours_dict = {} # новый словарь с часами вместо даты
        time_format = ''

        first_point = min(time_dict.keys()) # берем минимальное время
        if ":" in first_point[:-2]:
            time_format = "%d.%m.%Y %H:%M"
        else:
            time_format = "%d.%m.%Y"
        first_point =  datetime.strptime(first_point, time_format)
        for time, value in time_dict.items():
            time = datetime.strptime(time, time_format)
            delta = time - first_point # получаем разницу во времени
            hours = delta.total_seconds() / 3600 # переводим в часы
            hours_dict[hours] = value
        
        return hours_dict

    def ei(self, ARG):
        ARG2 = ARG*ARG
        ARG3 = ARG2*ARG
        ARG4 = ARG3*ARG

        if (ARG < 1):
            return -0.57721566+0.99999193*ARG-0.24991055*ARG2+0.05519968*ARG3-0.00976004*ARG4+0.00107857*ARG*ARG4-math.log(ARG)
        else:
            CHIS = 0.2677737343+8.6347608925*ARG+18.0590169730*ARG2+8.5733287401*ARG3 + ARG4
            ZNAM = 3.9584969228+21.0996530827*ARG+25.6329561486*ARG2+9.5733223454*ARG3 + ARG4

            if ARG == 0 or ZNAM == 0 : 
                return 0
            else: 
                return CHIS*math.exp(-ARG)/(ZNAM*ARG)

    def get_spider_data(self):
        # тут пересчитывать на те единицы, которые выбрал пользователь
        return self.session.query(Data.spider_graph).filter(Data.well_id == self.well_id).scalar()
    
    def get_press_sum(self):
        # по айди пользователя достать список айдишников его скважин, достать DPi из всех и рассчитать сумму и выдать ее
        # stmt = select(Well.id).where(Well.user_id == self.user_id)
        # user_wells = self.session.execute(stmt).scalars()
        # dpi_list = self.session.query(Data.dpi).join(Well).filter(Well.user_id == self.user_id, Data.dpi != {}).scalars()
        try:
            stmt = select(Data.dpi)\
                .select_from(Data)\
                .join(Well, Data.well_id == Well.id)\
                .where(Well.user_id == self.user_id, Data.dpi != {})
            
            dpi_result = self.session.execute(stmt).scalars().all()

            primary_sum = [
                sum(item for item in items if item is not None) 
                if any(item is not None for item in items) 
                else None 
                for items in zip(*dpi_result)
            ]
            stmt = select(WellTechData.pressure, Well.id)\
                .select_from(WellTechData)\
                .join(Well, WellTechData.well_id == Well.id)\
                .where(
                    Well.user_id == self.user_id, 
                    Well.is_press == True, 
                    Well.is_debit == True
                )
            
            main_well_info = self.session.execute(stmt).all()
            main_well_press = float(main_well_info[0][0])
            main_well_id = int(main_well_info[0][1])

            stmt = select(Data.press_data).where(Data.well_id == main_well_id)
            X_row = self.session.execute(stmt).scalar()
 
            result = {}
            for i, time in enumerate(X_row.keys()):
                if i < len(primary_sum):
                    result[time] = primary_sum[i] + main_well_press
                else:
                    result[time] = None
            # print(X_row)
            # для отображения на главной:
            self.session.execute(update(Well).where(Well.user_id == self.user_id).values(rsum = True))
            self.session.commit()
            return result
        except Exception as e:
            return {"msg": f"Ошибка при расчете суммы давлений: {e}"}

    def create_reservoir_press(self, step: float, interval: float):
        #собрать айди всех скважин для кого расчитывали паука
        """
        1)собрать айди всех скважин для кого расчитывали паука
        2)взять давление исследуемой скважины и завести переменную
        3)пойти по ним циклом и собрать список списков
        """
        try:
            
            # БЕРЕМ НАСТРОЙКУ ДЕБИТА ПОЛЬЗОВАТЕЛЯ
            debit_unit = self.session.query(UserTechData.debit).filter(UserTechData.user_id == self.user_id, UserTechData.well_id == None).scalar()
            # БЕРЕМ ДАВЛЕНИЕ И АЙДИ ИССЛЕДУЕМОЙ СКВАЖИНЫ
            stmt = select(WellTechData.pressure, WellTechData.well_id).select_from(WellTechData).join(Well, WellTechData.well_id == Well.id).where(Well.user_id == self.user_id, Well.is_press == True, Well.is_debit == True)
            main_info = self.session.execute(stmt).all()
            main_well_press_first = float(main_info[0][0])
            main_well_id = int(main_info[0][1])

            #СОХРАНЯЕМ ВВОДИМЫЕ ПАРАМЕТРЫ
            data = {"step": step, "interval": interval}
            self.session.execute(update(Well).where(Well.user_id == self.user_id, Well.id == main_well_id).values(rpl = True))

            # БЕРЕМ ДАННЫЕ ПО ДАВЛЕНИЮ В ВИДЕ СЛОВАРЯ ЧТОБЫ ПОЛУЧИТЬ ВРЕМЯ ПО ОСИ Х
            press_data_time = self.session.query(Data.press_data).filter(Data.well_id == main_well_id).scalar()
            press_data = self.get_hours(press_data_time)
            time_press = list(press_data.keys())
            

            #ПОЛУЧАЕМ СПИСОК ВСЕХ ТАБЛИЦ ДЕБИТОВ РАССЧИТАНЫХ ПОСЛЕ ПАУКА
            stmt = select(Data.debit_table)\
                    .select_from(Data)\
                    .join(Well, Data.well_id == Well.id)\
                    .where(Well.user_id == self.user_id, Data.debit_table != {})
                
            debit_table_results = self.session.execute(stmt).scalars().all()

            # ПОЛУЧАЕМ СПИСОК АЙДИШНИКОВ СКВ
            stmt = select(Data.well_id)\
                    .select_from(Data)\
                    .join(Well, Data.well_id == Well.id)\
                    .where(Well.user_id == self.user_id, Data.debit_table != {})
            wells_id = self.session.execute(stmt).scalars().all()

            res_list = []
            # ИДЕМ ПО ЦИКЛУ И РАССЧИТЫВАЕМ СПИСОК СПИСКОВ
            for i, well_debit_table in enumerate(debit_table_results):
                #НАХОДИМ ЗНАЧЕНИЯ ДЛ СКВАЖИН
                res = self.session.query(WellTechData).filter(WellTechData.well_id == wells_id[i]).first()
                self.data = res.__dict__
                if any(value is None or value == 0.0 for value in self.data.values()):
                    return {"msg": "Поле со значением 0 не валидно, введите правильное значение"}
                pressure = float(self.data['pressure'])
                thickness = float(self.data['thickness'])
                viscosity = float(self.data['viscosity'])
                permeability = float(self.data['permeability'])
                porosity = float(self.data['porosity'])
                radius = float(self.data['radius'])
                compressibility = float(self.data['compressibility'])
                volume_factor = float(self.data['volume_factor'])
                pyezoprovodnost = permeability / ((viscosity * compressibility) * porosity)


                # НАХОДИМ ВРЕМЯ ОКОНЧАНИЯ ИЗМЕРЕНИЯ
                time_finish = step + interval
                
                
                debit_table_times = [float(k) for k, v in well_debit_table.items()]
                
                DPi = 0
                well_P_points = [DPi]
                # НАХОДИМ НАЧАЛО
                time_start = time_press[0] + step # ИЗМЕНЯЕМАЯ ДЛЯ ЦИКЛА
                calculated_times_hours = [time_press[0]]
                debit_time = 0.0
                time_measure = time_press[0] + step # НЕ ИЗМЕНЯЕМАЯ ДЛЯ ИЗМЕРЕНИЯ ДЕБИТА
                for i in range(len(debit_table_times)): # ПОИСК ДЕБИТА ДО ОСТАНОВКИ
                    if time_start > debit_table_times[i]:
                        debit_time = debit_table_times[i]
                    else:
                        break
                
                to_str_2 = str(debit_time)
                sys_deb = (0 - convert_to_si(debit_info={debit_unit: well_debit_table[to_str_2]})[debit_unit])
                # ИДЕМ ЦИКЛОМ WHILE ПО ТОЧКАМ КОТОРЫЕ НАДО ИЗМЕРИТЬ ПОКА ВРЕМЯ МЕНЬШЕ КОНЦА
                while time_start < time_finish:
                    x = (radius ** 2) / (4 * pyezoprovodnost * ((time_start - debit_time) * 3600))

                    E = self.ei(x)
                    
                    DPj = -((viscosity * sys_deb * volume_factor)/(permeability * thickness * 4 * math.pi)) * E
                    # DPj - используется для расчета суммы 
                    DPi += DPj
                    
                    well_P_points.append(DPi)
                    calculated_times_hours.append(time_start)
                    time_start += step

                #  РАССЧИТЫВАЕМ КОНЕЧНУЮ ТОЧКУ
                to_str_2 = str(debit_table_times[-1])
                sys_deb = (0 - convert_to_si(debit_info={debit_unit: well_debit_table[to_str_2]})[debit_unit])
                if time_press[-1] < debit_table_times[-1]:                                                             # !!!!!!!!!!!!!ВРЕМЕНННОООО ПРОВЕРИТЬ ЧТОБЫ НЕ БЫЛО ЧТО ЧАСОВ У ДЕБИТА БОЛЬШЕ ЧЕМ У ДАВЛЕНИЯ
                    x = (radius ** 2) / (4 * pyezoprovodnost * ((time_press[-1] - debit_table_times[-2]) * 3600))   
                else:
                    x = (radius ** 2) / (4 * pyezoprovodnost * ((time_press[-1] - debit_table_times[-1]) * 3600))
                E = self.ei(x)
                
                DPj = -((viscosity * sys_deb * volume_factor)/(permeability * thickness * 4 * math.pi)) * E
                # DPj - используется для расчета суммы 
                DPi += DPj
                
                well_P_points.append(DPi)
                calculated_times_hours.append(time_press[-1])
                res_list.append(well_P_points)
                continue

            # РАССЧИТЫВАЕМ СУММУ ВСЕХ ПОЛУЧЕННЫХ ТОЧЕК
            primary_sum = [
                sum(item for item in items if item is not None) 
                if any(item is not None for item in items) 
                else None 
                for items in zip(*res_list)
            ]
            primary_sum = [item + main_well_press_first for item in primary_sum]
            # 2. Сопоставляем расчетные значения
            result_hours = self.map_calculated_values_with_hours(
                press_data, calculated_times_hours, primary_sum, step
            )
            # 3. Конвертируем обратно в нужный формат дат
            start_datetime = list(press_data_time.keys())[0]
            result_datetime = self.convert_hours_to_datetime_keys(result_hours, start_datetime)

            self.session.execute(update(Well).where(Well.user_id == self.user_id).values(rpl = True))
            self.session.commit()
            return result_datetime
        except Exception as e:
            return {"msg": f"ошибка при расчете Рпластового: {e}"}

    def parse_flexible_datetime(self, time_str):
        """
        Парсит дату-время в разных форматах.
        
        Args:
            time_str: строка с датой в формате '%d.%m.%Y %H:%M' или '%d.%m.%Y'
        
        Returns:
            datetime объект
        """
        from datetime import datetime
        
        # Пробуем разные форматы
        formats = [
            '%d.%m.%Y %H:%M',  # полный формат с временем
            '%d.%m.%Y',         # только дата
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        
        # Если ни один формат не подошел
        # raise ValueError(f"Неизвестный формат даты: {time_str}")
        raise {"msg": f"Неизвестный формат даты: {time_str}"}

    def map_calculated_values_with_hours(self, press_data, calculated_times_hours, primary_sum, step):
        result = {}
        
        # Сначала всем ставим None
        for hour in press_data.keys():
            result[hour] = None
        
        # Для каждой расчетной временной точки находим ближайший доступный час
        for i, target_hour in enumerate(calculated_times_hours):
            # Находим ближайший час из доступных
            closest_hour = min(press_data.keys(), key=lambda h: abs(h - target_hour))
            result[closest_hour] = primary_sum[i]
        
        return result

    def convert_hours_to_datetime_keys(self, hours_dict, start_datetime_str, output_format='%d.%m.%Y %H:%M'):
        """
        Конвертирует словарь с часами обратно в формат datetime ключей.
        
        Args:
            hours_dict: словарь {часы: значение}
            start_datetime_str: начальная дата в формате '01.01.2025 0:00' или '01.01.2025'
            output_format: желаемый формат выходных дат
        
        Returns:
            Словарь {дата_время: значение}
        """
        from datetime import datetime, timedelta
        
        try:
            start_time = self.parse_flexible_datetime(start_datetime_str)
        except ValueError as e:
            # raise ValueError(f"Неверный формат начальной даты '{start_datetime_str}': {e}")
            raise {"msg": f"Неверный формат начальной даты '{start_datetime_str}': {e}"}
        
        result = {}
        
        for hours, value in hours_dict.items():
            try:
                time_dt = start_time + timedelta(hours=float(hours))
                time_str = time_dt.strftime(output_format)
                result[time_str] = value
            except Exception as e:
                print(f"⚠️ Ошибка конвертации часов {hours}: {e}")
        
        return result

class UserTechDataModel:
    def __init__(self, data=[], user_id: int = 0):
        self.session = db
        self.data = data
        self.user_id = user_id

    def update_units(self):
        try:
            if self.data['well_id'] is None:
                result = self.session.execute(update(UserTechData).where(UserTechData.id == self.data['id'], UserTechData.user_id == self.user_id).values(**self.data))
                self.session.commit()
                if result:
                    return True
                else:
                    return False
            else:
                existing_note = self.session.query(UserTechData).filter(UserTechData.user_id == self.user_id, UserTechData.well_id == self.data['well_id']).first()
                if existing_note:
                    self.data['id'] = existing_note.id
                    result = self.session.execute(update(UserTechData).where(UserTechData.id == self.data['id'], UserTechData.user_id == self.user_id, UserTechData.well_id == self.data['well_id']).values(**self.data))
                    self.session.commit()
                    return True
                else:
                    max_id = self.session.query(func.max(UserTechData.id)).scalar() or 0
                    new_id = max_id + 1
                    self.data['id'] = new_id
                    self.data['user_id'] = self.user_id
                    new_well_units = UserTechData(**self.data)
                    self.session.add(new_well_units)
                    self.session.commit()
                    return True
        except Exception as e:
            self.session.rollback()
            return {"msg": f"ошибка при обновлении: {e}"}
        finally:
            self.session.close()

    def get_user_units(self, well_id):
        try:
            user_units = self.session.query(UserTechData).filter(UserTechData.user_id == self.user_id, UserTechData.well_id == well_id).first()
            if user_units:
                return user_units
            else:
                user_units = self.session.query(UserTechData).filter(UserTechData.user_id == self.user_id, UserTechData.well_id == None).first()
                if user_units:
                    return user_units
                else:
                    max_id = self.session.query(func.max(UserTechData.id)).scalar() or 0
                    new_id = max_id + 1
                    new_units = UserTechData(
                        id=new_id,
                        user_id=self.user_id,
                        well_id=None,
                        pressure=None,
                        debit=None,
                        thickness=None,
                        viscosity=None,
                        permeability=None,
                        porosity=None,
                        radius=None,
                        compressibility=None,
                        volume_factor=None
                    )
                    empty_units = {
                        'id':new_id,
                        'well_id':None,
                        'pressure':None,
                        'debit':None,
                        'thickness':None,
                        'viscosity':None,
                        'permeability':None,
                        'porosity':None,
                        'radius':None,
                        'compressibility':None,
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
    def __init__(self, data=[], well_id: int = 0, user_id: int = 0):
        self.session = db
        self.data = data
        self.well_id = well_id
        self.user_id = user_id

    
    def update_measures(self): # , measures: Optional[dict()] = None
        try:
            self.well_id = self.data.pop("well_id")
            # Берем СИ юзера
            # user_units = self.session.query(UserTechData).filter(UserTechData.user_id == self.user_id).first()
            user_units = UserTechDataModel(user_id=self.user_id).get_user_units(well_id=self.well_id)
            convert_result = convert_to_si(values=self.data, measures=user_units.__dict__)
            result = self.session.execute(update(WellTechData).where(WellTechData.well_id == self.well_id).values(**convert_result))
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

    def get_well_measures(self, user_id: Optional[int] = 0):
        try:
            well_measures = self.session.query(WellTechData).filter(WellTechData.well_id == self.well_id).first()
            
            
            if well_measures:
                if well_measures.pressure is None or well_measures.thickness is None:
                    return well_measures.__dict__
                # Берем СИ юзера
                user_units = UserTechDataModel(user_id=user_id).get_user_units(well_id=self.well_id)
                result = convert_to_user_si(values=well_measures.__dict__, measures=user_units.__dict__)
                return result
            else:
                max_id = self.session.query(func.max(WellTechData.id)).scalar() or 0
                new_id = max_id + 1
                new_measures = WellTechData(
                    id=new_id,
                    well_id=self.well_id,
                    pressure=None,
                    thickness=None,
                    viscosity=None,
                    permeability=None,
                    porosity=None,
                    radius=None,
                    compressibility=None,
                    volume_factor=None
                )
                empty_measures = {
                    'id':new_id,
                    'pressure':None,
                    'thickness':None,
                    'viscosity':None,
                    'permeability':None,
                    'porosity':None,
                    'radius':None,
                    'compressibility':None,
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
