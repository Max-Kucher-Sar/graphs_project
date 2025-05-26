import datetime

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
                    well_data['pressure'][new_dt] = 0.0
            else:

                for missing_date in miss_time_in_debit:
                    new_dt = datetime.datetime.combine(missing_date, datetime.datetime.min.time())
                    well_data['debit'][new_dt] = 0.0

        return well_data

class SpiderData:
    def __init__(self, 
        folder_data, 
        height: int,
        viscosity: int,
        permeability: int,
        porosity: int,
        well_radius: int,
        betta_oil: int,
        betta_water: int,
        betta_rock: int,
        water_saturation: int,
        volume_factor: int,
        ):

        self.data = folder_data # session["spider"]["folder_name"]
        self.height = height # высота
        self.viscosity = viscosity # высота
        self.permeability = permeability # высота
        self.porosity = porosity # высота
        self.well_radius = well_radius # высота
        self.betta_oil = betta_oil # высота
        self.betta_water = betta_water # высота
        self.betta_rock = betta_rock # высота
        self.water_saturation = water_saturation # высота
        self.volume_factor = volume_factor # высота
        self.betta_all = 2 / 10 **9
        self.pyezoprovodnost = 0

    def reformat_time(self):
        update_well_data = {}
        for well, values in self.data.items():
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
        hours_dict = {} # новый словарь с часами вместо даты

        first_point = min(time_dict.keys()) # берем минимальное время

        for time, value in time_dict.items():
            delta = time - first_point # получаем разницу во времени
            hours = delta.total_seconds() / 3600 # переводим в часы
            hours_dict[hours] = value
        
        return hours_dict

    def convet_to_system_measure(self):
        pass

    """
    folder_name: str = Form(...),
    height: int = Form(...),
    viscosity: int = Form(...),
    permeability: int = Form(...),
    porosity: int = Form(...),
    well_radius: int = Form(...),
    betta_oil: int = Form(...),
    betta_water: int = Form(...),
    betta_rock: int = Form(...),
    water_saturation: int = Form(...),
    volume_factor: int = Form(...)
    """



