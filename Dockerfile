FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app/

ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade -r /app/requirements.txt

ENV PYTHONPATH=/app

CMD python main.py