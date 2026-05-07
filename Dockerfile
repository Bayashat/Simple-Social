# syntax=docker/dockerfile:1
FROM python:3.13-slim-bookworm AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /src

# 1. Cache dependency layer
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2. Copy source code and build virtual environment
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN uv sync --frozen --no-dev

# --- Runtime ---
FROM python:3.13-slim-bookworm AS runner

ENV PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"
WORKDIR /app

# Create non-privileged user
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin app

# Copy compiled environment and code
COPY --from=builder /src/.venv /app/.venv
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

RUN chown -R app:app /app
USER app
EXPOSE 8000

# Health check (Best to add a /health interface in FastAPI later to replace /docs)
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/docs', timeout=4)"

# Critical fix: use exec to let uvicorn take over PID 1, implement graceful shutdown
CMD alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000
