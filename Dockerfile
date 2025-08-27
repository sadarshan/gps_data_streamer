FROM python:3.11-slim

# Install system dependencies for SSL and MongoDB
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE $PORT

CMD uvicorn main:app --host 0.0.0.0 --port $PORT