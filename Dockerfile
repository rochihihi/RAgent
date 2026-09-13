FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VERIPATCH_DATABASE_PATH=/app/runs/veripatch.sqlite3

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY examples ./examples
RUN pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 veripatch \
    && mkdir -p /app/runs \
    && chown -R veripatch:veripatch /app/runs

USER veripatch
EXPOSE 8000

CMD ["uvicorn", "veripatch.api:app", "--host", "0.0.0.0", "--port", "8000"]

