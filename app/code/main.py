from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from typing import Dict
import re
from starlette.responses import RedirectResponse
import secrets
from funcs.data_processing import TransformDate, SpiderData

from fastapi.responses import HTMLResponse
import plotly.graph_objects as go
from plotly.io import to_html

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Глобальное хранилище сессий (ключ: session_id, значение: данные сессии)
session_storage: Dict[str, Dict] = {}

# Время жизни сессии в часах
SESSION_EXPIRE_HOURS = 8


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


@app.get("/")
async def read_root(request: Request):
    session = request.state.session

    # Генерируем пустые графики при первом открытии
    plots_html = {}
    for well_name, well_data in session["data_storage"].items():
        well_plots = {}

        if well_data.get("pressure"):
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(well_data["pressure"].keys()),
                y=list(well_data["pressure"].values()),
                line=dict(color="blue")
            ))
            fig.update_layout(
                title=f"{well_name} - Давление",
                width=1000,
                height=300,
                margin=dict(t=30, l=40, r=40, b=40),
                showlegend=False
            )
            well_plots["pressure"] = to_html(fig, full_html=False, config={'staticPlot': True})

        if well_data.get("debit"):
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(well_data["debit"].keys()),
                y=list(well_data["debit"].values()),
                line=dict(color="red")
            ))
            fig.update_layout(
                title=f"{well_name} - Дебит",
                width=1000,
                height=300,
                margin=dict(t=30, l=40, r=40, b=40),
                showlegend=False
            )
            well_plots["debit"] = to_html(fig, full_html=False, config={'staticPlot': True})

        plots_html[well_name] = well_plots

    return templates.TemplateResponse("index.html", {
        "request": request,
        "folders": list(session["data_storage"].keys()),
        "saved_flags": session["saved_flags"],
        "data_storage": session["data_storage"],
        "plots_html": plots_html,
        "message": request.query_params.get("message", "")
    })


@app.post("/create-folder")
async def create_folder(request: Request, folder_name: str = Form(...)):
    session = request.state.session
    spider_list = ['spider', 'паук'] # список возможных названий
    if folder_name in session["data_storage"]:
        raise HTTPException(status_code=400, detail="Скважина уже существует")
    else:
        if folder_name.lower() in spider_list:
            reformat_data = SpiderData(session["data_storage"]).reformat_time()
            session['spider'] = reformat_data

            return RedirectResponse(url="/?message=паук+создан", status_code=303)
        else:
            # Создаем новую скважину в данных текущей сессии
            session["data_storage"][folder_name] = {"pressure": {}, "debit": {}}
            session["saved_flags"][folder_name] = {"pressure": False, "debit": False}
            session["column_formats"][folder_name] = {"pressure": "", "debit": ""}

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

        flag = True # Флаг - True если дебит и давление присутствуют, False  - если одно из них отсутствует
        for key in session["data_storage"][folder_name].keys():
            if session["data_storage"][folder_name][key] == {}:
                flag = False
            else:
                pass
        if flag:
            session["data_storage"][folder_name] = TransformDate().upgrade_data(session["data_storage"][folder_name])
        else:
            pass

        return RedirectResponse(url=f"/?message=Данные+сохранены", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/create-well-spider")
async def create_well_spider(
    request: Request,
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
    ):
    session = request.state.session
    pass
    

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


@app.post("/delete-folder/{folder_name}")
async def delete_folder(request: Request, folder_name: str):
    session = request.state.session

    if folder_name in session["data_storage"]:
        # Удаляем данные только из текущей сессии
        del session["data_storage"][folder_name]
        del session["saved_flags"][folder_name]
        del session["column_formats"][folder_name]

        return {
            "status": "success",
            "message": f"Скважина {folder_name} удалена"
        }
    else:
        raise HTTPException(status_code=404, detail="Скважина не найдена")


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


