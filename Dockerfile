FROM python:3.12-slim
# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN pip install -r mysite/cron-requirements.txt
# Keep it simple - just install dependencies and cron
CMD ["tail", "-f", "/dev/null"]