# syntax=docker/dockerfile:1
# Multi-stage: build a relocatable `.venv` with uv, ship only that + app code in a slim runtime.

FROM python:3.13-slim-bookworm AS builder

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /src

# Dependency layer (invalidates only when lockfiles change).
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

# Application + migrations; install project into `.venv` (non-editable by default in this layer).
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN uv sync --frozen --no-dev

# --- Runtime: no compiler, no uv, no root user ---
FROM python:3.13-slim-bookworm AS runner

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin app

COPY --from=builder /src/.venv /app/.venv
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

RUN chown -R app:app /app

USER app

EXPOSE 8000

# First boot may run Alembic migrations — allow extra time before marking unhealthy.
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/docs', timeout=4)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
