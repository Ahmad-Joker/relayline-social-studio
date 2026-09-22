FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY alembic.ini ./
COPY pyproject.toml ./
COPY alembic ./alembic
COPY app ./app
COPY tests ./tests

RUN useradd --create-home --uid 10001 relayline && mkdir -p /data && chown -R relayline:relayline /app /data
USER relayline

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
