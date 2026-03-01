FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN python3 -m pip3 install -r requirements.txt

COPY app.py /app/app.py

EXPOSE 5000

RUN gunicorn --bind 0.0.0.0:5000 app:app
