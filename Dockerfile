FROM python:3.11-slim
WORKDIR /app
COPY mebel.py .
ENV PORT=8080
EXPOSE 8080
CMD ["python", "mebel.py"]
