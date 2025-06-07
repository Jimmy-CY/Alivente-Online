FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r cron-requirements.txt
CMD ["tail", "-f", "/dev/null"]
