FROM python:3.12-slim

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install -r cron-requirements.txt

# Set up cron job
RUN echo "0 9 * * * cd /app && python manage.py check_lease_renewals" | crontab -

# Start cron and keep container alive
CMD ["sh", "-c", "service cron start && tail -f /dev/null"]