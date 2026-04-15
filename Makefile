PYTHON ?= python3

.PHONY: install run lint test compile migrate-up docker-up docker-down

install:
	$(PYTHON) -m pip install -e .[dev]

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	ruff check .

test:
	pytest

compile:
	$(PYTHON) -m compileall app

migrate-up:
	alembic upgrade head

docker-up:
	docker compose up --build

docker-down:
	docker compose down -v
