install: install-prod

install-dev:
	uv sync --all-extras

install-prod:
	uv sync --all-extras --no-dev

image:
	docker pull sn1f3rt/nerva:latest

dev:
	uv run launcher.py

prod:
	hypercorn --bind 0.0.0.0:17569 --certfile cert.pem --keyfile key.pem launcher:app

lint:
	uv run ruff check --select I --fix .
	uv run ruff format .

typecheck:
	uv run mypy .

.PHONY: install install-dev install-prod image dev prod lint typecheck
.DEFAULT_GOAL := dev
