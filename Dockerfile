FROM python:3.12-slim
# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*
# LibreOffice turns a generated lease into its e-signing PDF - GE-1, 28 Oct 2026.
# Writer only, no desktop; Inter stands in for the templates' Trebuchet MS
# (deploy/fonts), Liberation and DejaVu for everything else, Greek included.
RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-writer-nogui fonts-inter fonts-liberation fonts-dejavu-core fontconfig && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
COPY deploy/fonts/50-alivente-trebuchet.conf /etc/fonts/conf.d/50-alivente-trebuchet.conf
RUN fc-cache -f
RUN pip install -r mysite/cron-requirements.txt
# Keep it simple - just install dependencies and cron
CMD ["tail", "-f", "/dev/null"]