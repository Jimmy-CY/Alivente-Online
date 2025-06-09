FROM python:3.12-slim

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install -r cron-requirements.txt

# Simple startup with explicit logging
CMD ["sh", "-c", "echo 'CONTAINER STARTING' && service cron start && echo 'CRON SERVICE STARTED' && crontab -l && echo 'KEEPING CONTAINER ALIVE' && while true; do echo 'Container heartbeat:' $(date); sleep 300; done"]