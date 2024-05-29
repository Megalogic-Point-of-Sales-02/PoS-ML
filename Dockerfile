
FROM python:3.10-slim

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

COPY . .

CMD ["fastapi", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
