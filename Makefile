env:
	uv venv

install:
	uv sync --no-dev

install-dev:
	uv sync --all-extras

up:
	docker compose up -d

down:
	docker compose down

image:
	docker pull sn1f3rt/nerva:latest

run:
	uv run launcher.py

prod:
	uv run launcher.py --prod

format:
	ruff check --select I --fix .
	ruff format .

.PHONY: env install install-dev up down run prod format
.DEFAULT_GOAL := run
