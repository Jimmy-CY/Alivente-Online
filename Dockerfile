FROM python:3.12-slim

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install -r cron-requirements.txt

# Force immediate output and simpler startup
CMD ["sh", "-c", "echo 'STARTING CRON SERVICE' && service cron start && echo 'CRON STARTED' && echo 'Setting up cron job for lease renewals...' && echo '0 9 * * * cd /app && python manage.py check_lease_renewals' | crontab - && echo 'Cron job installed:' && crontab -l && echo 'Container is ready and waiting...' && exec tail -f /dev/null"]