FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Set environment variables (these will be overridden in production)
ENV DB_HOST=db
ENV DB_NAME=telegram_db
ENV DB_USER=telegram_user
ENV DB_PASSWORD=telegram_password

# Run the bot
CMD ["python", "main.py"]
