FROM python:3.12-slim

WORKDIR /app

# System deps (MySQL client libs for mysqlclient)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
  && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app

# Create logs dir
RUN mkdir -p /app/logs

ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "app:create_app()", "-b", "0.0.0.0:5000", "--config", "gunicorn.conf.py"]

