# FROM python:3.13-alpine

# WORKDIR /app

# # COPY ./requirements.txt /app/requirements.txt
# COPY . .

# RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
# # COPY ../code /data/app

# #CMD ["uvicorn", "main:app", "--host", "80.78.243.208", "--port", "8000"]

# # CMD ["fastapi", "run", "main.py", "--port", "8000"]
# # Указываем правильный путь к main.py
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
FROM python:3.13-alpine

WORKDIR /app

# Сначала копируем зависимости
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Затем копируем весь код
COPY ../src /data/app

# Используем uvicorn напрямую
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]