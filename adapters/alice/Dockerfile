FROM python:3.12-alpine

ENV HOST=0.0.0.0 \
    PORT=8080 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup -S botnest && adduser -S -G botnest botnest

COPY adapters/alice/handler.py adapters/alice/runtime.json adapters/alice/server.py ./
RUN chown -R botnest:botnest /app && chmod 0444 handler.py runtime.json && chmod 0555 server.py

USER botnest
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=3).read()"]

CMD ["python", "server.py"]
