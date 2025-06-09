FROM python:3.12-slim

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install -r cron-requirements.txt

# Set up cron job - runs daily at 9 AM
RUN echo "0 9 * * * cd /app && python manage.py check_lease_renewals" | crontab -

# Start cron with logging and keep container alive
CMD ["sh", "-c", "echo 'Starting cron service...' && service cron start && echo 'Cron service status:' && service cron status && echo 'Current cron jobs:' && crontab -l && echo 'Container ready, waiting for cron jobs...' && tail -f /dev/null"]