.DEFAULT_GOAL := help
UV := uv run

.PHONY: help run run-api run-fe db dev-postgres format lint migrate upgrade install

help:
	@echo "Targets:"
	@echo "  make run-api       - Start backend API"
	@echo "  make run-fe        - Start frontend UI"
	@echo "  make dev-postgres  - Start DB and local API"
	@echo "  make format        - Format code (Ruff)"
	@echo "  make lint          - Check code (Ruff + Mypy)"
	@echo "  make migrate       - Generate database migration (MSG='description')"
	@echo "  make upgrade       - Execute database migration"

run-api:
	$(UV) uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-fe:
	$(UV) streamlit run frontend/app.py

db:
	docker compose up -d db

dev-postgres: db run-api

format:
	$(UV) ruff format .
	$(UV) ruff check --fix .

lint:
	$(UV) ruff check .
	$(UV) mypy

# Usage: make migrate MSG="add users table"
MSG ?= auto
migrate:
	$(UV) alembic revision --autogenerate -m "$(MSG)"

upgrade:
	$(UV) alembic upgrade head

install:
	uv sync
