# Common dev tasks (requires https://docs.astral.sh/uv/ on PATH).
.DEFAULT_GOAL := help

UV := uv run

.PHONY: help run run-api run-fe dev format lint lint-ruff lint-mypy migrate upgrade install pre-commit

help:
	@echo "Targets:"
	@echo "  make run / run-api - Uvicorn :8000 (Alembic on startup)"
	@echo "  make run-fe        - Streamlit UI :8501"
	@echo "  make dev           - API + Streamlit (:8000 + :8501); Ctrl+C stops both"
	@echo "  make format           - Ruff formatter"
	@echo "  make lint             - Ruff check + Mypy"
	@echo "  make migrate          - Alembic autogenerate (set MSG='your message')"
	@echo "  make upgrade          - Alembic upgrade head (same as app startup migration)"
	@echo "  make install          - uv sync (runtime + dev deps)"
	@echo "  make pre-commit       - pre-commit on all files"

run: run-api

run-api:
	$(UV) uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-fe:
	$(UV) streamlit run frontend/app.py

# Needs bash. Starts API in background, Streamlit in foreground; TERM/INT or normal UI exit kills API.
dev:
	@echo "API http://localhost:8000  |  UI http://localhost:8501"
	@bash -c 'set -e; \
		$(UV) uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload & \
		API_PID=$$!; \
		trap "kill $$API_PID 2>/dev/null" INT TERM; \
		$(UV) streamlit run frontend/app.py; \
		st=$$?; kill $$API_PID 2>/dev/null || true; exit $$st'

format:
	$(UV) ruff format app main.py frontend alembic

lint: lint-ruff lint-mypy

# Example: make migrate MSG=add_comments_table
MSG ?= auto

migrate:
	$(UV) alembic revision --autogenerate -m "$(MSG)"

upgrade:
	$(UV) alembic upgrade head

install:
	uv sync

pre-commit:
	pre-commit run --all-files
