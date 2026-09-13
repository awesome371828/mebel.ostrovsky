# Сайт «Кухни Островский» + серверный ИИ-чат
FROM python:3.11-slim

WORKDIR /app

# Копируем сервер
COPY mebel.py /app/mebel.py

# Порт, на котором слушает приложение (совпадает с PORT в mebel.py)
EXPOSE 8080

# Запуск сервера. Ключи читаются из переменных окружения
# (FOLDER_ID, YANDEX_API_KEY, GIGACHAT_AUTH_KEY), которые задаются
# в настройках деплоя, а НЕ хранятся в коде.
CMD ["python", "mebel.py"]
