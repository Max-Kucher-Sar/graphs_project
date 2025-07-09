FROM python:3.13.2

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt \
    --index-url https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com
#RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
# COPY ../code /data/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]