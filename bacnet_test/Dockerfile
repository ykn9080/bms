FROM python:3.11-slim
RUN pip install --no-cache-dir bacpypes==0.18.6
WORKDIR /app
CMD ["sh", "-c", "while true; do python collector.py; sleep 5; done"]
