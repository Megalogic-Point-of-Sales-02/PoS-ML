FROM python:3.10-slim

WORKDIR /app

# Define build-time arguments
ARG SUPABASE_URL
ARG SUPABASE_ANON_KEY
ARG DB_HOST
ARG DB_USER
ARG DB_PASSWORD
ARG DB_NAME

# Set environment variables from build arguments
ENV SUPABASE_URL=$SUPABASE_URL
ENV SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY
ENV DB_HOST=$DB_HOST
ENV DB_USER=$DB_USER
ENV DB_PASSWORD=$DB_PASSWORD
ENV DB_NAME=$DB_NAME

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# EXPOSE 8080

COPY . .

CMD ["sh", "-c", "fastapi run app.py --host 0.0.0.0 --port ${PORT}"]
