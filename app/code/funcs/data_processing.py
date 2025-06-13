import datetime
import math

class TransformDate:
    def __init__(self):
        self.max_time = []

    

    def get_unique_dates(self, data_dict):
        return {dt.date() for dt in data_dict.keys()}

    def upgrade_data(self, well_data):
        pressure_dates = self.get_unique_dates(well_data['pressure'])
        debit_dates = self.get_unique_dates(well_data['debit'])

        miss_time_in_debit = sorted(pressure_dates - debit_dates)
        mess_time_in_press = sorted(debit_dates - pressure_dates)

        if len(miss_time_in_debit) == 0 and len(mess_time_in_press) == 0:
            pass
        else:
            if len(miss_time_in_debit) == 0:

                for missing_date in mess_time_in_press:
                    new_dt = datetime.datetime.combine(missing_date, datetime.datetime.min.time())
                    well_data['pressure'][new_dt] = None
            else:

                for missing_date in miss_time_in_debit:
                    new_dt = datetime.datetime.combine(missing_date, datetime.datetime.min.time())
                    well_data['debit'][new_dt] = None

        return well_data

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
        self.well_radius = well_radius / 100 # радиус скважины
        self.betta_oil = betta_oil / 10 ** 9# бетта нефть
        self.betta_water = betta_water / 10 ** 9 # бетта вода
        self.betta_rock = betta_rock / 10 ** 9 # бетта порода
        self.water_saturation = water_saturation # насыщение водой
        self.pressure = pressure * 0.098
        self.volume_factor = volume_factor # объемный коэф
        self.betta_all = 2.0 / 10 ** 9
        self.pyezoprovodnost = self.permeability / (self.viscosity * self.betta_all) / self.porosity # вопрос правильности !
       

    def reformat_time(self):
        update_well_data = {}
        for well, values in self.data['data_storage'].items():
            update_value_data = {}
            # well - название скважины
            values_press = values['pressure'] # достали словарь с временем и значениями для давления
            values_deb = values['debit'] # достали словарь с временем и значениями для дебита

            update_time_press = self.get_hours(values_press) # вызываем функцию для перевода из даты в часы по давлению
            update_time_deb = self.get_hours(values_deb)# вызываем функцию для перевода из даты в часы по дебиту

            update_value_data['pressure'] = update_time_press # добавляем измененные данные по давлению
            update_value_data['debit'] = update_time_deb# добавляем измененные данные по дебиту
            update_well_data[well] = update_value_data
        return update_well_data

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
        
        data = self.data["spider"][self.folder_name]['debit']

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
        self.data['spider'][self.folder_name]['values'] = args_dict
        print(args_dict)
        return self.data

    def convert_func(self):
        debit_table = self.create_table_time_debit()
        debit_table_times = [k for k, v in debit_table.items()]
        press_table = self.data['spider'][self.folder_name]['pressure']
        self.save_const()
        press_flag = 0
        result = {}
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
                    continue
                elif time_press < next_time_deb:
                    if time_press not in result.keys():
                        prev_press = press_flag if press_flag != 0 else new_prev_press
                        press_flag = 0
                        current_press = value_press
                        x = (self.well_radius ** 2) / (4 * self.pyezoprovodnost * ((time_press - current_time_deb) * 3600))
                        E = math.log(1/x) - 0.5772 + x - (x**2/4) + (x**3/18) - (x**4/96) + (x**5/600)
                        DP1 = ((debit_table[current_time_deb] * self.volume_factor / 86400) * self.viscosity / (4 * math.pi * self.permeability * self.height)) * E / 1000000 / 0.098
                        DP_kappa = prev_press - current_press
                        print(f'Результаты: X={x}, E={E}, DP1={DP1}, DP_kappa={DP_kappa}')
                        res_press = abs(DP_kappa - DP1) / DP_kappa * 100
                        result[time_press] = res_press
                        new_prev_press = current_press
                    else:
                        pass
                else:
                    break

        print(result)
        return result



