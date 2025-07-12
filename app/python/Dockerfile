FROM python:3.13-alpine

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
# COPY ../code /data/app

CMD ["uvicorn", "main:app", "--host", "80.78.243.208", "--port", "8000"]