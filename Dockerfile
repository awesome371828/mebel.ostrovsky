FROM python:3.11-slim

WORKDIR /app

# Копируем только нужный файл
COPY mebel.py .

# Переменные окружения (можно переопределить в RelaxDev)
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "mebel.py"]
