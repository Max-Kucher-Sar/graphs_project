FROM python:3.13.2

WORKDIR /app

COPY ./requirments.txt /app/requirments.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirments.txt

# COPY ../code /data/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]