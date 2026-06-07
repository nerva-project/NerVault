# syntax=docker/dockerfile:1

# ---- build the SPA ----
FROM node:22-alpine AS frontend
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY pyproject.toml tsconfig.json tsconfig.app.json tsconfig.node.json vite.config.ts ./
COPY src/frontend ./src/frontend
RUN npm run build

# ---- nginx: serve the SPA, reverse-proxy /v1 to the API ----
FROM nginx:1.27-alpine AS web
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend /app/dist /usr/share/nginx/html

# ---- the API (hypercorn) ----
FROM python:3.13-slim AS api
COPY --from=ghcr.io/astral-sh/uv:0.9.28 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src/backend ./src/backend
RUN uv sync --frozen --no-dev --all-extras
EXPOSE 8080
CMD ["/app/.venv/bin/hypercorn", "backend.launcher:app", "--bind", "0.0.0.0:8080"]
