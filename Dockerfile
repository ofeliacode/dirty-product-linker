FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000 \
    DPL_RUNTIME=lexical \
    DPL_CATALOG_PATH=/app/data/catalog/demo_catalog_v0_2.jsonl

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

COPY pyproject.toml README.md ./
COPY src ./src
COPY data/catalog/demo_catalog_v0_2.jsonl ./data/catalog/demo_catalog_v0_2.jsonl
RUN pip install --no-cache-dir ".[api]"

USER appuser
EXPOSE 10000

CMD ["sh", "-c", "uvicorn dirty_product_linker.api.app:app --host 0.0.0.0 --port ${PORT}"]
