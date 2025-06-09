FROM python:3.12-slim

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install -r cron-requirements.txt

# Create a test cron job that runs every minute for testing
RUN echo "* * * * * echo 'Cron is working at' \$(date) >> /app/cron-test.log 2>&1" | crontab -
# Add your actual lease renewal job
RUN echo "0 9 * * * cd /app && python manage.py check_lease_renewals >> /app/lease-renewals.log 2>&1" | crontab -

# Start cron and keep container alive  
CMD ["sh", "-c", "service cron start && tail -f /dev/null"]