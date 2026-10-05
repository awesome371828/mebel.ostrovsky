FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

RUN pip install --no-cache-dir pillow supabase

COPY mebel.py ./
RUN mkdir -p uploads

EXPOSE 8080

CMD ["python", "-u", "mebel.py"]
