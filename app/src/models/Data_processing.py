from src.database.PSQLmodels import DataModel
from fastapi import APIRouter, Body, Depends, HTTPException, status, Form
from src.models.Auth import get_current_user_id

import re
from datetime import datetime
data_router = APIRouter(prefix="/data", tags=["Данные"])



class Data:
    def __init__(self, well_id: int = 0, user_id: int = 0, date_format: str = '', is_debit: bool = False, is_press: bool = False):
        self.well_id = well_id
        self.user_id = user_id
        self.is_debit = is_debit
        self.is_press = is_press
        self.date_format = date_format # datetime или date

    def confirm_data(self, data):
        parsed_data = {} # для расчета таблицы дебитов
        original_dates = {} # для обычных графиков

        pattern = r'(\d{2}\.\d{2}\.\d{4}(?:\s\d{1,2}:\d{2})?)[\t,; ]+([\d,]+\.?\d*)'
        
        matches = re.findall(pattern, data)
        
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
        if self.is_debit == True:
            hours_debit = self.get_hours(parsed_data)
            debit_table = self.create_table_time_debit(hours_debit)
            return DataModel(data=original_dates, well_id=self.well_id).upload_primary_debit(debit_table)
        elif self.is_press == True:
            return DataModel(data=original_dates, well_id=self.well_id).upload_primary_press()
    
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


@data_router.put("/upload_primary_data") 
async def upload_primary_data(well_id: int, is_debit: bool = False, is_press: bool = False, user_id: int = Depends(get_current_user_id), data: str = Form(...)):
    return Data(well_id=well_id, user_id=user_id, is_debit=is_debit, is_press=is_press).confirm_data(data)

@data_router.get("/get_primary_data") 
async def get_primary_data(well_id: int, is_debit: bool = False, is_press: bool = False, user_id: int = Depends(get_current_user_id)):
    return Data(well_id=well_id, user_id=user_id, is_debit=is_debit, is_press=is_press).get_primary_data()