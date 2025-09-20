from src.database.PSQLmodels import DataModel, UserTechDataModel, WellTechDataModel
from fastapi import APIRouter, Body, Depends, HTTPException, status, Form
from src.models.Auth import get_current_user_id
from pydantic import BaseModel

import re
from datetime import datetime
data_router = APIRouter(prefix="/data", tags=["Данные"])

class UserUnitsCreate(BaseModel):
    id: int
    pressure: str
    flow: str
    thickness: str
    viscosity: str
    permeability: str
    porosity: str
    radius: str
    compressibility: str
    water_saturation: str
    volume_factor: str

class WellMeasuresCreate(BaseModel):
    id: int
    pressure: int
    flow: int
    thickness: int
    viscosity: int
    permeability: int
    porosity: int
    radius: int
    compressibility: int
    water_saturation: int
    volume_factor: int


class Data:
    def __init__(self, well_id: int = 0, user_id: int = 0, date_format: str = '', is_debit: bool = False, is_press: bool = False):
        self.well_id = well_id
        self.user_id = user_id
        self.is_debit = is_debit
        self.is_press = is_press
        self.date_format = date_format # datetime или date

    def confirm_data(self, data_debit, data_press): # data = {"well_id": int, "debit_data": str, "press_data": False (или str)}
        parsed_data = {} # для расчета таблицы дебитов
        original_dates = {} # для обычных графиков

        pattern = r'(\d{2}\.\d{2}\.\d{4}(?:\s\d{1,2}:\d{2})?)[\t,; ]+([\d,]+\.?\d*)'
        
        # matches = re.findall(pattern, data)
        if data_debit != '':
            parsed_data = {} # для расчета таблицы дебитов
            original_dates = {} # для обычных графиков
            matches = re.findall(pattern, data_debit)
            for time_str, value_str in matches:
                try:
                    value = float(value_str.replace(',', '.'))
                    if ':' in time_str:
                        self.date_format = "%d.%m.%Y %H:%M"
                    else:
                        self.date_format = "%d.%m.%Y"
                    dt_obj = datetime.strptime(time_str, self.date_format)
                    parsed_data[dt_obj] = value
                    original_dates[time_str] = value
                except ValueError:
                    continue
            hours_debit = self.get_hours(parsed_data)
            debit_table = self.create_table_time_debit(hours_debit)
            DataModel(data=original_dates, well_id=self.well_id).upload_primary_debit(debit_table) 
        else:
            pass
        if data_press != '':
            # parsed_data = {} # для расчета таблицы дебитов
            original_dates = {} # для обычных графиков
            matches = re.findall(pattern, data_press)
            for time_str, value_str in matches:
                try:
                    value = float(value_str.replace(',', '.'))
                    # if ':' in time_str:
                    #     self.date_format = "%d.%m.%Y %H:%M"
                    # else:
                    #     self.date_format = "%d.%m.%Y"
                    # dt_obj = datetime.strptime(time_str, self.date_format)
                    # parsed_data[dt_obj] = value
                    original_dates[time_str] = value
                except ValueError:
                    continue
            DataModel(data=original_dates, well_id=self.well_id).upload_primary_press()
        else:
            pass
        return True
    
    def get_hours(self, time_dict):
        """
        Возвращает словарь, где дата переведена в часы
        """
        hours_dict = {} # новый словарь с часами вместо даты

        first_point = min(time_dict.keys()) # берем минимальное время

        for time, value in time_dict.items():
            delta = time - first_point # получаем разницу во времени
            hours = delta.total_seconds() / 3600 # переводим в часы
            hours_dict[hours] = value
        
        return hours_dict
    
    def create_table_time_debit(self, data):
        """
        Возвращает словарь, где ключ - количество часов, а значене - дебит
        """
        well_operation = {}

        time_keys = [float(i) for i in data.keys()]

        current_value = float(data[time_keys[0]])
        start_time = time_keys[0]
        well_operation[start_time] = current_value
        for i in range(1, len(time_keys)):
            if data[time_keys[i]] != current_value:

                current_value = float(data[time_keys[i]])

                start_time = time_keys[i]

                well_operation[start_time] = current_value
                
        well_operation[time_keys[-1]] = current_value

        return well_operation
        
    def get_primary_data(self):
        return DataModel(well_id=self.well_id, is_debit=self.is_debit, is_press=self.is_press, user_id=self.user_id).get_primary_data()

    # настройки пользователя
    def update_units(self, data):
        return UserTechDataModel(data=data.__dict__, user_id=self.user_id).update_units()
    
    def get_user_units(self):
        return UserTechDataModel(user_id=self.user_id).get_user_units()
    
    # ВРЕМЕННО РУЧКА значения для паука
    def update_measures(self, data):
        return WellTechDataModel(data=data.__dict__, well_id=self.well_id).update_measures()
    
    def get_well_measures(self):
        return WellTechDataModel(well_id=self.well_id).get_well_measures()

@data_router.put("/upload_primary_data") 
async def upload_primary_data(well_id: int, data_debit: str = Form(...), data_press: str = Form(...),user_id: int = Depends(get_current_user_id)):
    return Data(well_id=well_id).confirm_data(data_debit=data_debit, data_press=data_press)

@data_router.get("/get_primary_data") 
async def get_primary_data(well_id: int, is_debit: bool = False, is_press: bool = False, user_id: int = Depends(get_current_user_id)):
    return Data(well_id=well_id, user_id=user_id, is_debit=is_debit, is_press=is_press).get_primary_data()

@data_router.post("/update_user_units")
async def update_user_units(data: UserUnitsCreate, user_id: int = Depends(get_current_user_id)):
    return Data(user_id=user_id).update_units(data=data)

@data_router.get("/get_user_units")
async def get_user_units(user_id: int = Depends(get_current_user_id)):
    return Data(user_id=user_id).get_user_units()

# ВРЕМЕННО
@data_router.post("/update_well_units/{well_id}")
async def update_well_units(data: WellMeasuresCreate, well_id: int):
    return Data(well_id=well_id).update_measures(data=data)

@data_router.get("/get_well_units/{well_id}")
async def get_well_units(well_id: int):
    return Data(well_id=well_id).get_well_measures()