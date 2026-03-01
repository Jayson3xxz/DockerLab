FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Добавьте проверку инициализации БД
RUN python -c "from app import init_db; init_db()" || echo "DB init failed (expected if DB not running)"

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--access-logfile=-", "--error-logfile=-", "app:app"]