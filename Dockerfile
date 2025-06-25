FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DB_HOST=db
ENV DB_NAME=telegram_db
ENV DB_USER=telegram_user
ENV DB_PASSWORD=telegram_password
ENV APP_ENV=develop

CMD ["python", "main.py"]