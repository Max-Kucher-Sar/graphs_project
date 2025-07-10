FROM python:3.9-alpine

WORKDIR /app

RUN apk update && \
    apk add --no-cache \
        python3-dev \
        gcc \
        musl-dev \
        gfortran \
        lapack-dev \
        openblas-dev

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 -r /app/requirements.txt
# COPY ../code /data/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]