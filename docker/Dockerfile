FROM python:3.11-slim-bullseye

# Chuyển hướng các nguồn repository cũ của Bullseye sang archive để tránh lỗi 404 Not Found
RUN echo "deb http://archive.debian.org/debian/ bullseye main" > /etc/apt/sources.list && \
    echo "deb http://archive.debian.org/debian-security/ bullseye-security main" >> /etc/apt/sources.list && \
    echo "Acquire::Check-Valid-Time \"false\";" > /etc/apt/apt.conf.d/99no-check-valid-time

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PYTHONPATH="/app"
EXPOSE 8000 8501