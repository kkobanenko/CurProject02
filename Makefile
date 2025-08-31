.PHONY: up down logs lint test format precommit

up:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

lint:
	ruff check .
	black --check .
	isort --check-only .

format:
	black .
	isort .

test:
	pytest -q

precommit:
	pre-commit install
