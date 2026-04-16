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

maintenance-enable:
	QUART_APP=launcher:app uv run quart maintenance enable

maintenance-disable:
	QUART_APP=launcher:app uv run quart maintenance disable

reset-wallet:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then echo "Usage: make reset-wallet <username>"; exit 1; fi
	QUART_APP=launcher:app uv run quart reset_wallet $(filter-out $@,$(MAKECMDGOALS))

lint:
	uv run ruff check --select I --fix .
	uv run ruff format .

typecheck:
	uv run mypy .

.PHONY: install install-dev install-prod image dev prod maintenance-enable maintenance-disable reset-wallet lint typecheck
.DEFAULT_GOAL := dev

%:
	@:
