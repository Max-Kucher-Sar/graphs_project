import datetime
import math
from typing import Dict, Any

class TransformDate:
    def __init__(self):
        self.max_time = None

    def upgrade_data(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выравнивает временные шкалы всех скважин и их параметров по ДАТАМ (без учета времени),
        сохраняя все оригинальные значения и добавляя None для пропущенных дат.
        
        Args:
            session_data: Данные сессии (session["data_storage"])
            
        Returns:
            Обновленные данные сессии с выровненными временными шкалами по датам
        """
        # Собираем все уникальные ДАТЫ (без времени) из всех скважин и параметров
        all_dates = set()
        
        # Проходим по всем скважинам
        for well_name, well_data in session_data.items():
            if well_data.get("type") != "well":
                continue
                
            # Проходим по всем параметрам скважины
            for param_type in ["pressure", "debit"]:
                if param_type in well_data and well_data[param_type]:
                    # Извлекаем только дату (без времени) из каждого временного штампа
                    for timestamp in well_data[param_type].keys():
                        if timestamp:  # Игнорируем None или пустые значения
                            date_only = timestamp.date() if isinstance(timestamp, datetime.datetime) else datetime.datetime.fromisoformat(timestamp).date()
                            all_dates.add(date_only)
        
        if not all_dates:
            return session_data  # Нет данных для выравнивания
            
        # Преобразуем даты обратно в datetime с временем 00:00:00 для сравнения
        all_datetimes = {datetime.datetime.combine(date, datetime.time(0, 0)) for date in all_dates}
        self.max_time = max(all_datetimes)
        
        # Обновляем данные каждой скважины
        updated_data = {}
        for well_name, well_data in session_data.items():
            if well_data.get("type") != "well":
                updated_data[well_name] = well_data  # Копируем spider'ы без изменений
                continue
                
            updated_well = well_data.copy()
            
            # Выравниваем каждый параметр скважины
            for param_type in ["pressure", "debit"]:
                if param_type in well_data:
                    # Копируем оригинальные значения
                    param_data = well_data[param_type].copy()
                    
                    # Создаем набор дат для этого параметра
                    param_dates = set()
                    for timestamp in param_data.keys():
                        if timestamp:  # Игнорируем None или пустые значения
                            date_only = timestamp.date() if isinstance(timestamp, datetime.datetime) else datetime.datetime.fromisoformat(timestamp).date()
                            param_dates.add(date_only)
                    
                    # Добавляем None для отсутствующих ДАТ
                    for date in all_dates:
                        if date not in param_dates:
                            # Создаем datetime с временем 00:00:00 для этой даты
                            dt_key = datetime.datetime.combine(date, datetime.time(0, 0))
                            param_data[dt_key] = None
                    
                    updated_well[param_type] = param_data
            
            updated_data[well_name] = updated_well
        
        return updated_data

class SpiderData:
    def __init__(self, 
        folder_data,
        folder_name='str', 
        height=1,
        viscosity=1,
        permeability=1,
        porosity=1,
        well_radius=1,
        betta_oil=1,
        betta_water=1,
        betta_rock=1,
        water_saturation=1,
        pressure=1,
        volume_factor=1
        ):


        self.data = folder_data # session
        self.folder_name = folder_name # название скважины с которой работаем
        self.height = height # высота
        self.viscosity = viscosity / 1000 # вязкость
        self.permeability = permeability / 10 ** 15 # проницаемость
        self.porosity = porosity # пористоть
        self.well_radius = well_radius # радиус скважины в метрах
        self.betta_oil = betta_oil / 10 ** 9# бетта нефть
        self.betta_water = betta_water / 10 ** 9 # бетта вода
        self.betta_rock = betta_rock / 10 ** 9 # бетта порода
        self.water_saturation = water_saturation # насыщение водой
        self.pressure = pressure * 0.098
        self.volume_factor = volume_factor # объемный коэф
        self.betta_all = 2.0 / 10 ** 9
        self.pyezoprovodnost = self.permeability / ((self.viscosity * self.betta_all) * self.porosity) # вопрос правильности !
       

    def reformat_time(self, well_data):
        # update_well_data = {}
        # for well, values in well_data.items(): 
        update_value_data = {}
        # well - название скважины
        values_press = well_data['pressure'] # достали словарь с временем и значениями для давления
        values_deb = well_data['debit'] # достали словарь с временем и значениями для дебита
        
        update_time_press = {} if values_press == {} else self.get_hours(values_press) # вызываем функцию для перевода из даты в часы по давлению 
        update_time_deb = self.get_hours(values_deb)# вызываем функцию для перевода из даты в часы по дебиту

        update_value_data['pressure'] = update_time_press # добавляем измененные данные по давлению
        update_value_data['debit'] = update_time_deb# добавляем измененные данные по дебиту
        # update_well_data[well_name] = update_value_data
        return update_value_data

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

    def create_table_time_debit(self):
        """
        Возвращает словарь, где ключ - количество часов, а значене - дебит
        """
        well_operation = {}
        
        data = self.data["data_storage"]['spider']['wells'][self.folder_name]['debit']

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

    def save_const(self):
        """
        Функция сохраняет переданные аргументы под ключ 'values' блока 'spider'
        """
        const = vars(self)
        args_dict = {}
        for key, values in const.items():
            if key == 'data':
                pass
            elif key == 'folder_name':
                pass
            else:
                args_dict[key] = values
        
        print(args_dict)
        return args_dict

    def create_sum(self):
        # self.data["data_storage"]['spider']['wells'][self.folder_name]['dp1']
        dp_sum_list = []

        wells = list(self.data["data_storage"]['spider']['wells'].keys())
        dp1_lists = []

        for i in range(len(wells)):
            dp1_lists.append(self.data["data_storage"]['spider']['wells'][wells[i]]['dp1'])
        #print('считаем сумму')
        #res = [sum(items) for items in zip(*dp1_lists)]
        res = [
            sum(item for item in items if item is not None) 
            if any(item is not None for item in items) 
            else None 
            for items in zip(*dp1_lists)
        ]
        #print(res, 'итоговая сумма ')
        first_press = list(self.data["data_storage"][wells[0]]["pressure"].values())

        const_press = first_press[0]

        for value in res:
            dp_press = const_press - value
            dp_sum_list.append(dp_press)
        #print(dp_sum_list, 'итог')
        return dp_sum_list

        

    def convert_func(self):

        # для второстепенной скважины берем давление главной скважины:
        if self.data["data_storage"]['spider']['wells'][self.folder_name]['pressure'] == {}:

            first_well = list(self.data["data_storage"]['spider']['wells'].keys())

            well_data = self.data["data_storage"]['spider']['wells'][first_well[0]]
            
            first_time_key = next(iter(self.data["data_storage"]['spider']['wells'][self.folder_name]["debit"].keys()))
            if isinstance(first_time_key, (int, float)):
                pass
            else:
                time_to_reform = self.data["data_storage"]['spider']['wells'][self.folder_name]
                
                update_value_data = self.reformat_time(well_data=time_to_reform)
                
                self.data["data_storage"]['spider']['wells'][self.folder_name] = update_value_data
            
            
            press_table = self.data["data_storage"]['spider']['wells'][first_well[0]]['pressure']

        # для основной скважины и для скважин с давлением
        else:
            well_data = self.data["data_storage"]['spider']['wells'][self.folder_name]

            # Проверяем тип первого ключа в данных давления
            need_time_conversion = True
            if 'pressure' in well_data and well_data['pressure']:
                first_time_key = next(iter(well_data['pressure'].keys()))
                if isinstance(first_time_key, (int, float)):
                    need_time_conversion = False
            

            # Преобразуем дату в часы только если нужно
            if need_time_conversion:
                update_value_data = self.reformat_time(well_data=well_data)
                self.data["data_storage"]['spider']['wells'][self.folder_name] = update_value_data
            else:
                update_value_data = well_data

            press_table = self.data["data_storage"]['spider']['wells'][self.folder_name]['pressure']

      
        debit_table = self.create_table_time_debit()
      
        debit_table_times = [k for k, v in debit_table.items()]

        press_flag = 0
        result = {}
        dp1_lict = []
        for i in range(len(debit_table_times)):
            if i == len(debit_table_times) - 1:
                current_time_deb = debit_table_times[i]
                next_time_deb = debit_table_times[i]
            else:
                current_time_deb = debit_table_times[i]
                next_time_deb = debit_table_times[i + 1]
            for time_press, value_press in press_table.items():
                if time_press == 0:
                    press_flag = value_press
                    result[0.0] = 0
                    #dp1_dict[0.0] = 0
                    continue
                elif time_press <= next_time_deb:
                    if time_press not in result.keys():
                        # if time_press == 100.05:
                            #print(list(result.keys())[-1])

                        if (time_press -  current_time_deb) < 1:
                            DP1 = None
                            dp1_lict.append(DP1)
                            result[time_press] = None
                        else:
                            # prev_press = press_flag if press_flag != 0 else new_prev_press
                            # press_flag = 0
                            current_press = value_press
                            # if time_press == 100.05:
                            #     a = (time_press - current_time_deb) * 3600
                            #     b = 4 * self.pyezoprovodnost * a
                            #     c = self.well_radius ** 2
                            #     v = c / b
                            #     print(a, b, c, v, self.pyezoprovodnost)
                            x = (self.well_radius ** 2) / (4 * self.pyezoprovodnost * ((time_press - current_time_deb) * 3600))
                            E = (math.log(1/x) - 0.5772 + x - (x**2/4) + (x**3/18) - (x**4/96) + (x**5/600))
                            DP1 = (((debit_table[current_time_deb] * self.volume_factor / 86400) * self.viscosity / (4 * math.pi * self.permeability * self.height)) * E / 1000000 / 0.098)
                            DP_kappa = press_flag - current_press
                            #print(f'Результаты: X={x}, E={E}, DP1={DP1}, DP_kappa={DP_kappa}', self.folder_name)
                            #print(time_press, next_time_deb, current_time_deb)
                            res_press = abs(DP_kappa - DP1) / DP_kappa * 100
                            dp1_lict.append(DP1)
                            result[time_press] = res_press
                            #dp1_dict[time_press]
                        
                        # new_prev_press = current_press
                    else:
                        pass
                else:
                    break

        self.data["data_storage"]['spider']['wells'][self.folder_name]['dp1'] = dp1_lict
        
        return result #, dp1_list



