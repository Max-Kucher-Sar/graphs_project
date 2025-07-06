from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from typing import Dict
import re
from starlette.responses import RedirectResponse
import secrets
from funcs.data_processing import TransformDate, SpiderData

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import HTMLResponse
import plotly.graph_objects as go
from plotly.io import to_html

import sys
sys.setrecursionlimit(10000)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Глобальное хранилище сессий (ключ: session_id, значение: данные сессии)
session_storage: Dict[str, Dict] = {}

# Время жизни сессии в часах
SESSION_EXPIRE_HOURS = 8

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://31.31.196.98",
        "https://optiwell.gubkin-technologys.ru"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware для обработки сессий
@app.middleware("http")
async def session_middleware(request: Request, call_next):
    # Получаем session_id из cookies
    session_id = request.cookies.get("session_id")

    # Если сессии нет - создаем новую
    if not session_id or session_id not in session_storage:
        session_id = secrets.token_hex(16)
        session_storage[session_id] = {
            "created_at": datetime.now(),  # Время создания сессии
            "data_storage": {},  # Данные скважин
            "saved_flags": {},  # Флаги сохранения
            "column_formats": {}  # Форматы данных
        }

    # Привязываем сессию к запросу
    request.state.session = session_storage[session_id]
    request.state.session_id = session_id

    # Продолжаем обработку запроса
    response = await call_next(request)

    # Устанавливаем cookie с session_id
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=SESSION_EXPIRE_HOURS * 3600,
        samesite="lax"
    )

    return response


# @app.get("/")
# async def read_root(request: Request):
#     session = request.state.session

#     has_spider = any(well.get('type') == 'spider' for well in session["data_storage"].values())

#     # Генерируем пустые графики при первом открытии
#     plots_html = {}
#     for well_name, well_data in session["data_storage"].items():
#         well_plots = {}

#         if well_data.get("pressure"):
#             fig = go.Figure()
#             fig.add_trace(go.Scatter(
#                 x=list(well_data["pressure"].keys()),
#                 y=list(well_data["pressure"].values()),
#                 line=dict(color="blue")
#             ))
#             fig.update_layout(
#                 title=f"{well_name} - Давление",
#                 width=1000,
#                 height=300,
#                 margin=dict(t=30, l=40, r=40, b=40),
#                 showlegend=False
#             )
#             well_plots["pressure"] = to_html(fig, full_html=False, config={'staticPlot': True})

#         if well_data.get("debit"):
#             fig = go.Figure()
#             fig.add_trace(go.Scatter(
#                 x=list(well_data["debit"].keys()),
#                 y=list(well_data["debit"].values()),
#                 line=dict(color="red")
#             ))
#             fig.update_layout(
#                 title=f"{well_name} - Дебит",
#                 width=1000,
#                 height=300,
#                 margin=dict(t=30, l=40, r=40, b=40),
#                 showlegend=False
#             )
#             well_plots["debit"] = to_html(fig, full_html=False, config={'staticPlot': True})

#         plots_html[well_name] = well_plots

#     return templates.TemplateResponse("index.html", {
#         "request": request,
#         "folders": list(session["data_storage"].keys()),
#         "saved_flags": session["saved_flags"],
#         "data_storage": session["data_storage"],
#         "plots_html": plots_html,
#         "message": request.query_params.get("message", ""),
#         "has_spider": has_spider
#     })

@app.get("/")
async def read_root(request: Request):
    session = request.state.session

    # Инициализируем структуру для хранения графиков
    plots_html = {
        'wells': {},    # Обычные скважины: {'well_name': {'pressure': html, 'debit': html}}
        'spiders': {}   # Spider графики: {'spider_name': html}
    }

    # Обрабатываем обычные скважины
    for well_name, well_data in session["data_storage"].items():
        if well_data.get('type') == 'well':
            well_plots = {}
            
            # Давление
            if well_data.get("pressure"):
                res = []
                try:
                    res = SpiderData(folder_data=session).create_sum()
                except:
                    pass

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=list(well_data["pressure"].keys()),
                    y=list(well_data["pressure"].values()),
                    mode='markers',
                    name='P скважины',
                    marker=dict(size=6),
                    line=dict(color="blue")
                ))
                """
                #добавляем часы на ось Х
                if 'spider' in session.keys() and well_name in session["spider"]:
                    fig.add_trace(go.Scatter(
                        x=list(session["spider"][well_name]["data"].keys()),
                        y=list(well_data["pressure"].values()),
                        mode='markers',
                        name='P скважины',
                        marker=dict(size=6),
                        line=dict(color="blue")
                    ))
                """
                if len(res) > 0:
                    first_well = list(session["data_storage"]['spider']['wells'].keys())
                    if well_name == first_well[0]:
                        fig.add_trace(go.Scatter(
                            x=list(well_data["pressure"].keys()),
                            y=res,
                            mode='markers',
                            name='P суммы',
                            marker=dict(size=6),
                            line=dict(color="red")
                        ))

                else:
                    pass

                min_x = min(well_data["pressure"].keys())
                max_x = max(well_data["pressure"].keys())
                fig.update_layout(
                    title=f"{well_name} - Давление",
                    width=1000,
                    height=300,
                    margin=dict(t=30, l=40, r=40, b=40),
                    showlegend=True,
                    xaxis_range=[min_x, max_x] if min_x and max_x else None
                )
                well_plots["pressure"] = to_html(fig, full_html=False, config={'staticPlot': True})

            # Дебит
            if well_data.get("debit"):
                fig = go.Figure()
                """
                #добавляем часы на ось Х
                if 'spider' in session.keys() and well_name in session["spider"]:
                    # Основной график (ось X — часы)
                    fig.add_trace(go.Scatter(
                        x=list(well_data["debit"].keys()),
                        y=list(well_data["debit"].values()),
                        mode='lines',
                        line_shape='hv',
                        line=dict(color="red", width=2, dash='solid'),
                        name="Дебит"
                    ))

                    # Настройка осей X
                    fig.update_layout(
                        title=f"{well_name} - Дебит",
                        width=1000,
                        height=300,
                        margin=dict(t=30, l=40, r=40, b=40),
                        showlegend=False,
                        xaxis=dict(
                            title="Даты",
                            tickmode='array',
                            tickvals=list(well_data["debit"].keys()),  # Позиции подписей (часы)
                            #ticktext=[f"{h} ч" for h in list(well_data["debit"].keys())],  # Подписи снизу (числа)
                            range=[min(list(well_data["debit"].keys())), max(list(well_data["debit"].keys()))] if list(well_data["debit"].keys()) else None
                        ),
                        xaxis2=dict(
                            title="Дата",
                            overlaying="x",  # Накладываем на основную ось X
                            side="top",
                            tickmode='array',     # Размещаем сверху
                            tickvals=list(well_data["debit"].keys()),  # Позиции подписей (те же, что и у чисел)
                            ticktext=list(session["spider"][well_name]["data"].keys()),  # Подписи сверху (даты)
                            tickangle=-45,  # Наклон для удобства
                        )
                    )
                else:
                """
                fig.add_trace(go.Scatter(
                    x=list(well_data["debit"].keys()),
                    y=list(well_data["debit"].values()),
                    mode='lines',
                    line_shape='hv',
                    line=dict(color="red", width=2, dash='solid')
                ))

                min_x = min(well_data["debit"].keys())
                max_x = max(well_data["debit"].keys())
                fig.update_layout(
                    title=f"{well_name} - Дебит",
                    width=1000,
                    height=300,
                    margin=dict(t=30, l=40, r=40, b=40),
                    showlegend=False,
                    xaxis_range=[min_x, max_x] if min_x and max_x else None
                )

                well_plots["debit"] = to_html(fig, full_html=False, config={'staticPlot': True})
            
            plots_html['wells'][well_name] = well_plots

    # Обрабатываем spider графики
    if 'spider' in session:
        # Создаем один график для всех spider данных
        fig = go.Figure()
        
        # Собираем все spider данные
        for spider_name, spider_data in session['spider'].items():
            if not spider_data.get('data'):
                continue
            else:
                if session["saved_flags"]["spider"]["wells"][spider_name]:
                    # Добавляем spider данные на график
                    x_values = []
                    y_values = []
                    for time, value in spider_data['data'].items():
                        x_values.append(float(time))
                        y_values.append(value)
                    
                    fig.add_trace(go.Scatter(
                        x=x_values,
                        y=y_values,
                        name=spider_name,
                        mode='markers',
                        marker=dict(size=8)#, symbol='circle-open')
                    ))
                else:
                    pass
        
        if len(fig.data) > 0:
            fig.update_layout(
                title="Spider Data",
                width=1000,
                height=400,
                margin=dict(t=30, l=40, r=40, b=40),
                # yaxis=dict(tickfont=dict(size=10)),  # Уменьшаем размер шрифта для оси Y),
                showlegend=True,
                legend=dict(orientation="v", yanchor="top", xanchor="right", x=1.2, y=1)
            )
            plots_html['spiders']['all_spiders'] = to_html(fig, full_html=False, config={'staticPlot': True})

    # Проверяем наличие spider'ов для отображения панели управления
    has_spider = any(well.get('type') == 'spider' for well in session["data_storage"].values())

    return templates.TemplateResponse("index.html", {
        "request": request,
        "folders": list(session["data_storage"].keys()),
        "saved_flags": session["saved_flags"],
        "data_storage": session["data_storage"],
        "plots_html": plots_html,
        "message": request.query_params.get("message", ""),
        "has_spider": has_spider
    })

@app.post("/create-folder")
async def create_folder(request: Request, folder_name: str = Form(...)):
    session = request.state.session
    spider_list = ['spider', 'паук']
    
    if folder_name in session["data_storage"]:
        raise HTTPException(status_code=400, detail="Уже существует")
    else:
        if folder_name.lower() in spider_list:
            # Инициализируем все необходимые структуры
            session["data_storage"][folder_name] = {
                "type": "spider",
                "wells": {
                    well: data 
                    for well, data in session["data_storage"].items() 
                    if data.get('type') == 'well'
                }
            }
            session["saved_flags"][folder_name] = {
                "wells": {
                    well: False 
                    for well in session["data_storage"] 
                    if session["data_storage"][well].get('type') == 'well'
                }
            }
            # Для spider'а column_formats не нужен
            
            return RedirectResponse(url="/?message=Паук+создан", status_code=303)
        else:
            # Обычная скважина
            session["data_storage"][folder_name] = {
                "pressure": {}, 
                "debit": {}, 
                "type": "well"
            }
            session["saved_flags"][folder_name] = {
                "pressure": False, 
                "debit": False
            }
            session["column_formats"][folder_name] = {
                "pressure": "", 
                "debit": ""
            }
            
            return RedirectResponse(url="/?message=Скважина+создана", status_code=303)

@app.post("/confirm-data")
async def confirm_data(
        request: Request,
        folder_name: str = Form(...),
        data_type: str = Form(...),
        date_format: str = Form(...),
        pasted_data: str = Form(...)
    ):
    session = request.state.session

    try:
        date_fmt = "%d.%m.%Y %H:%M" if date_format == "datetime" else "%d.%m.%Y"
        lines = [line.strip() for line in pasted_data.split('\n') if line.strip()]
        parsed_data = {}

        if date_format == 'date':
            for line in lines:
                parts = re.split(r'\t|,|;|\s+', line)
                if len(parts) >= 2:
                    try:
                        time = datetime.strptime(parts[0], date_fmt)
                        value = float(parts[1].replace(',', '.'))
                        parsed_data[time] = value
                    except ValueError:
                        continue
        elif date_format == 'datetime':
            for line in lines:
                line_modified = re.sub(r'(\d{2}\.\d{2}\.\d{4})\s(\d{2}:\d{2})', r'\1_\2', line)
                parts = re.split(r'\t|,|;|\s+', line_modified)
                parts = [p.replace('_', ' ') for p in parts]
                
                if len(parts) >= 2:
                    try:
                        time = datetime.strptime(parts[0], date_fmt)
                        value = float(parts[1].replace(',', '.'))
                        parsed_data[time] = value
                    except ValueError:
                        time_sum = parts[0] + ' ' + parts[1]
                        time = datetime.strptime(time_sum, date_fmt)
                        value = float(parts[2].replace(',', '.'))
                        parsed_data[time] = value

        # Сохраняем данные в текущей сессии
        session["data_storage"][folder_name][data_type] = parsed_data
        session["saved_flags"][folder_name][data_type] = True
        session["column_formats"][folder_name][data_type] = date_format

        # Проверяем наличие обоих параметров
        has_pressure = 'pressure' in session["data_storage"][folder_name] and session["data_storage"][folder_name]['pressure']
        has_debit = 'debit' in session["data_storage"][folder_name] and session["data_storage"][folder_name]['debit']

        # Если оба параметра присутствуют - выравниваем данные всех скважин
        if has_pressure and has_debit:
            session["data_storage"] = TransformDate().upgrade_data(session["data_storage"])

        return RedirectResponse(url=f"/?message=Данные+сохранены", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# @app.post("/confirm-data")
# async def confirm_data(
#         request: Request,
#         folder_name: str = Form(...),
#         data_type: str = Form(...),
#         date_format: str = Form(...),
#         pasted_data: str = Form(...)
#     ):
#     session = request.state.session

#     try:
#         date_fmt = "%d.%m.%Y %H:%M" if date_format == "datetime" else "%d.%m.%Y"
#         lines = [line.strip() for line in pasted_data.split('\n') if line.strip()]
#         parsed_data = {}

#         if date_format == 'date':
#             for line in lines:
#                 parts = re.split(r'\t|,|;|\s+', line)
#                 if len(parts) >= 2:
#                     try:
#                         time = datetime.strptime(parts[0], date_fmt)
#                         value = float(parts[1].replace(',', '.'))
#                         parsed_data[time] = value

#                     except ValueError:
#                         continue
#         elif date_format == 'datetime':
#             for line in lines:
#                 line_modified = re.sub(r'(\d{2}\.\d{2}\.\d{4})\s(\d{2}:\d{2})', r'\1_\2', line)
#                 parts = re.split(r'\t|,|;|\s+', line_modified)
#                 parts = [p.replace('_', ' ') for p in parts]
                
#                 if len(parts) >= 2:
#                     try:
#                         time = datetime.strptime(parts[0], date_fmt)

#                         value = float(parts[1].replace(',', '.'))
#                         parsed_data[time] = value

#                     except ValueError:
#                         time_sum = parts[0] + ' ' + parts[1]
#                         time = datetime.strptime(time_sum, date_fmt)
#                         value = float(parts[2].replace(',', '.'))
#                         parsed_data[time] = value
#         # Сохраняем данные в текущей сессии
#         session["data_storage"][folder_name][data_type] = parsed_data
#         session["saved_flags"][folder_name][data_type] = True
#         session["column_formats"][folder_name][data_type] = date_format

#         flag = True # Флаг - True если дебит и давление присутствуют, False  - если одно из них отсутствует
#         for key in session["data_storage"][folder_name].keys():
#             if session["data_storage"][folder_name][key] == {}:
#                 flag = False
#             else:
#                 pass
#         if flag:
#             session["data_storage"][folder_name] = TransformDate().upgrade_data(session["data_storage"][folder_name])
#         else:
#             pass

#         return RedirectResponse(url=f"/?message=Данные+сохранены", status_code=303)
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

@app.post("/create-well-spider")
async def create_well_spider(
        request: Request,
        folder_name: str = Form(...),
        height: float = Form(...),
        viscosity: float = Form(...),
        permeability: float = Form(...),
        porosity: float = Form(...),
        well_radius: float = Form(...),
        betta_oil: float = Form(...),
        betta_water: float = Form(...),
        betta_rock: float = Form(...),
        water_saturation: float = Form(...),
        pressure: float = Form(...),
        volume_factor: float = Form(...)
    ):
    session = request.state.session

    if 'spider_params' not in session:
        session['spider_params'] = {}
    
    session['spider_params'][folder_name] = {
        'height': height,
        'viscosity': viscosity,
        'permeability': permeability,
        'porosity': porosity,
        'well_radius': well_radius,
        'betta_oil': betta_oil,
        'betta_water': betta_water,
        'betta_rock': betta_rock,
        'water_saturation': water_saturation,
        'pressure': pressure,
        'volume_factor': volume_factor
    }
    
    try:
        
        processing = SpiderData(
            folder_data=session,
            folder_name=folder_name,
            height=height,
            viscosity=viscosity,
            permeability=permeability,
            porosity=porosity,
            well_radius=well_radius,
            betta_oil=betta_oil,
            betta_water=betta_water,
            betta_rock=betta_rock,
            water_saturation=water_saturation,
            pressure=pressure,
            volume_factor=volume_factor
        ).convert_func()
        
        if 'spider' not in session:
            session['spider'] = {}
        if folder_name not in session['spider']:
            session['spider'][folder_name] = {}
        
        session['spider'][folder_name]['data'] = processing
        
        
        return RedirectResponse(url="/?message=Паук+успешно+создан", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# @app.post("/create-well-spider")
# async def create_well_spider(
#     request: Request,
#     folder_name: str = Form(...),
#     height: float = Form(...),
#     viscosity: float = Form(...),
#     permeability: float = Form(...),
#     porosity: float = Form(...),
#     well_radius: float = Form(...),
#     betta_oil: float = Form(...),
#     betta_water: float = Form(...),
#     betta_rock: float = Form(...),
#     water_saturation: float = Form(...),
#     pressure: float = Form(...),
#     volume_factor: float = Form(...)
#     ):
#     session = request.state.session
#     processing = SpiderData(
#         folder_data=session,
#         folder_name=folder_name,
#         height=height,
#         viscosity=viscosity,
#         permeability=permeability,
#         porosity=porosity,
#         well_radius=well_radius,
#         betta_oil=betta_oil,
#         betta_water=betta_water,
#         betta_rock=betta_rock,
#         water_saturation=water_saturation,
#         pressure=pressure,
#         volume_factor=volume_factor
#     ).convert_func()
#     session['spider'][folder_name]['data'] = processing
#     return RedirectResponse(url="/?message=паук+создан", status_code=303)


@app.post("/api/toggle-param/{folder}/{param_type}")
async def toggle_parameter(request: Request, folder: str, param_type: str):
    session = request.state.session

    if folder not in session["saved_flags"] or param_type not in ["pressure", "debit"]:
        raise HTTPException(status_code=404, detail="Не найдено")

    # Переключаем флаг в данных сессии
    if session["data_storage"][folder][param_type]:

        session["saved_flags"][folder][param_type] = not session["saved_flags"][folder][param_type]
    else:
        session["saved_flags"][folder][param_type] = False

    return {"status": "success", "new_state": session["saved_flags"][folder][param_type]}

@app.post("/api/toggle-spider-well/{spider_name}/{well_name}")
async def toggle_spider_well(request: Request, spider_name: str, well_name: str):
    session = request.state.session
    
    if spider_name not in session["data_storage"] or session["data_storage"][spider_name]["type"] != "spider":
        raise HTTPException(status_code=404, detail="Spider не найден")
    
    if well_name not in session["saved_flags"][spider_name]["wells"]:
        session["saved_flags"][spider_name]["wells"][well_name] = False
    
    # Переключаем состояние
    session["saved_flags"][spider_name]["wells"][well_name] = not session["saved_flags"][spider_name]["wells"][well_name]
    
    return {"status": "success", "new_state": session["saved_flags"][spider_name]["wells"][well_name]}

@app.post("/delete-folder/{folder_name}")
async def delete_folder(request: Request, folder_name: str):
    session = request.state.session

    if folder_name.lower() == 'spider':
        if folder_name in session["data_storage"]:
            del session["data_storage"][folder_name]

        if folder_name in session["saved_flags"]:
            del session["saved_flags"][folder_name]

        del session['spider_params']
        del session['spider']

        return {
            "status": "success",
            "message": f"'{folder_name}' успешно удален"
        }

    if folder_name in session["data_storage"]:
        del session["data_storage"][folder_name]
        print('1')

        if folder_name in session["data_storage"]["spider"]["wells"]:
            del session["data_storage"]["spider"]["wells"][folder_name]
            print('2')
    
        if folder_name in session["saved_flags"]:
            del session["saved_flags"][folder_name]
            print('3')

        if folder_name in session["saved_flags"]["spider"]["wells"]:
            del session["saved_flags"]["spider"]["wells"][folder_name]
            print('4')

        if folder_name in session["column_formats"]:
            del session["column_formats"][folder_name]
            print('5')

        if folder_name in session['spider_params']:
            del session['spider_params'][folder_name]
            print('6')

        if folder_name in session['spider']:
            del session['spider'][folder_name]
            print('7')

    # if folder_name in session["data_storage"]:
    #     print('есть в session["data_storage"]')
    #     # Удаляем скважину из всех spider'ов (если это не сам spider)
    #     if session["data_storage"][folder_name].get('type') != 'spider':
    #         for spider_name, spider_data in session["data_storage"].items():
    #             if spider_data.get('type') == 'spider' and folder_name in spider_data.get('wells', {}):
    #                 del session["data_storage"][spider_name]["wells"][folder_name]
    #                 if folder_name in session["saved_flags"][spider_name]["wells"]:
    #                     del session["saved_flags"][spider_name]["wells"][folder_name]

    #     # Удаляем основные данные
    #     del session["data_storage"][folder_name]
    #     del session['spider_params'][folder_name]
    #     del session['spider'][folder_name]
        
    #     # Удаляем только если существует (для spider'а этого ключа нет)
    #     if folder_name in session["saved_flags"]:
    #         del session["saved_flags"][folder_name]
    #     if folder_name in session.get("column_formats", {}):
    #         del session["column_formats"][folder_name]

        return {
            "status": "success",
            "message": f"'{folder_name}' успешно удален"
        }
    else:
        raise HTTPException(status_code=404, detail="Не найдено")


# Новый эндпоинт для завершения сессии
@app.post("/end-session")
async def end_session(request: Request):
    session_id = request.state.session_id

    # Удаляем данные сессии
    if session_id in session_storage:
        del session_storage[session_id]

    # Создаем ответ и удаляем cookie
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_id")

    return response


@app.get("/debug-data")
async def debug_data(request: Request):
    # Для отладки - возвращаем данные текущей сессии
    return {
        "session_id": request.state.session_id,
        "session_data": request.state.session,
        "all_sessions": list(session_storage.keys())
    }


