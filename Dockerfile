FROM python:3.10-slim

WORKDIR /app

# Define build-time arguments
ARG SUPABASE_URL
ARG SUPABASE_ANON_KEY

# Set environment variables from build arguments
ENV SUPABASE_URL=$SUPABASE_URL
ENV SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# EXPOSE 8080

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
