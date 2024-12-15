env:
	uv venv

rmenv:
	rm -rf .venv

activate:
	source .venv/bin/activate

install:
	uv sync --no-dev

install-dev:
	uv sync --all-extras

install-speed:
	uv sync --all-extras --no-dev

up:
	docker compose up -d

down:
	docker compose down

image:
	docker pull sn1f3rt/nerva:latest

dev:
	uv run launcher.py

prod:
	hypercorn --bind 0.0.0.0:17569 --certfile cert.pem --keyfile key.pem launcher:app

format:
	ruff check --select I --fix .
	ruff format .

.PHONY: env rmenv activate install install-dev up down image dev prod format
.DEFAULT_GOAL := dev
