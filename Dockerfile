FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

COPY . .

CMD ["fastapi", "run", "app.py", "--host", "0.0.0.0", "--port", "8080"]
