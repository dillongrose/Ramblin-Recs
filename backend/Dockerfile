FROM python:3.11-slim

# System deps so lxml builds/works reliably
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libxml2-dev libxslt1-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# (compose supplies the uvicorn command; keeping CMD is optional)
