install: install-prod

install-dev:
	uv sync --all-extras

install-prod:
	uv sync --all-extras --no-dev

image:
	docker pull sn1f3rt/nerva:latest

dev:
	uv run hypercorn --reload --bind 127.0.0.1:8080 backend.launcher:app

serve:
	npm run serve

prod:
	uv run hypercorn --bind 0.0.0.0:17569 backend.launcher:app

maintenance-enable:
	QUART_APP=backend.launcher:app uv run quart maintenance enable

maintenance-disable:
	QUART_APP=backend.launcher:app uv run quart maintenance disable

reset-wallet:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then echo "Usage: make reset-wallet <username>"; exit 1; fi
	QUART_APP=backend.launcher:app uv run quart reset_wallet $(filter-out $@,$(MAKECMDGOALS))

lint:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy src/backend

.PHONY: install install-dev install-prod image dev serve prod maintenance-enable maintenance-disable reset-wallet lint typecheck
.DEFAULT_GOAL := dev

%:
	@:
