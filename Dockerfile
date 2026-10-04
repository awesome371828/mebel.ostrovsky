FROM python:3.11-slim

WORKDIR /app

# Pillow нужен для настоящего favicon (ICO/PNG)
RUN pip install --no-cache-dir pillow

COPY mebel.py content.json ./
RUN mkdir -p uploads

ENV PORT=8080 \
    DOMAIN=https://кухниостровский.рф \
    ADMIN_LOGIN=кухнироманост \
    ADMIN_PASSWORD=kuhroman

EXPOSE 8080

CMD ["python", "mebel.py"]
