FROM python:3.9-alpine

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3-dev \
        build-essential \
        libblas-dev \
        liblapack-dev \
        gfortran && \
    rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 -r /app/requirements.txt
# COPY ../code /data/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]