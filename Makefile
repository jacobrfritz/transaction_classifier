.PHONY: install test test-watch test-cov lint format typecheck run

install:
	cd apps/api && uv sync

test:
	cd apps/api && uv run pytest

test-watch:
	cd apps/api && uv run ptw

test-cov:
	cd apps/api && uv run pytest --cov=src --cov-report=term-missing

lint:
	cd apps/api && uv run ruff check .

format:
	cd apps/api && uv run ruff format .

typecheck:
	cd apps/api && uv run mypy src
