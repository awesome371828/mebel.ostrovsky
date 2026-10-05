FROM python:3.11-slim

WORKDIR /app

# Python без буферизации — чтобы логи сразу шли в RelaxDev
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Pillow — для favicon, supabase — для админки
RUN pip install --no-cache-dir pillow supabase

COPY mebel.py content.json ./
RUN mkdir -p uploads

EXPOSE 8080

CMD ["python", "mebel.py"]
