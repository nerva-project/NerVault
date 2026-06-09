# NerVault

[![Lint](https://github.com/nerva-project/NerVault/actions/workflows/lint.yml/badge.svg)](https://github.com/nerva-project/NerVault/actions/workflows/lint.yml)
[![Type Check](https://github.com/nerva-project/NerVault/actions/workflows/typecheck.yml/badge.svg)](https://github.com/nerva-project/NerVault/actions/workflows/typecheck.yml)
[![Build](https://github.com/nerva-project/NerVault/actions/workflows/build.yml/badge.svg)](https://github.com/nerva-project/NerVault/actions/workflows/build.yml)

> A custodial web wallet for the Nerva (XNV) cryptocurrency.

## About

NerVault lets users create or restore a Nerva wallet and send/receive XNV from
the browser. It is a **custodial** wallet: the server holds the wallet files and
the secrets used to access them. Each user's wallet runs in its own
`nerva-wallet-rpc` Docker container that NerVault spawns, connects to, and tears
down on a schedule.

The application is split into two parts:

- **`src/backend`** — an API-only [Quart](https://quart.palletsprojects.com/)
  app that exposes JSON endpoints under `/v1` (auth, wallet, meta). It talks to
  MongoDB, Redis, a Nerva daemon, an SMTP server, and the Docker engine.
- **`src/frontend`** — a [Vue 3](https://vuejs.org/) + Tailwind v4 +
  [Vite](https://vite.dev/) single-page app (Vue Router + Pinia) that consumes
  the same-origin `/v1` API. Emails are the only thing still rendered by the
  backend.

## Architecture

```
            ┌─────────── HestiaCP / nginx (TLS at the edge) ───────────┐
 client ───▶│  https://vault.nerva.one  ──▶  127.0.0.1:17569 (web)      │
            └───────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴───────────────┐
                    │  web (nginx): serves the SPA  │
                    │  proxies /v1 ─▶ api:8080       │
                    └──────────────┬───────────────┘
                                   │
   ┌────────── docker network: nervault ──────────────────────────────┐
   │  api (hypercorn)  ──▶ redis (valkey)                              │
   │     │   │                                                         │
   │     │   └──▶ docker-socket-proxy ──▶ host docker (spawn wallets)  │
   │     │            (spawned rpc_wallet_<user> join `nervault`)      │
   │     └──▶ host.docker.internal ──▶ Nerva daemon (host) + Mongo/SMTP│
   └───────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- **Docker** (with the Compose plugin) on the host.
- A **Nerva daemon** (`nervad`) reachable from the containers — on the same host
  (reached via `host.docker.internal`) or remote.
- The **`sn1f3rt/nerva`** image pulled on the host (`make image`) — NerVault uses
  it for the spawned wallet containers.
- A **MongoDB** database (e.g. MongoDB Atlas) and an **SMTP** server.
- For local development: [uv](https://docs.astral.sh/uv/) and Node.js 22+.
- For production behind a domain: an nginx edge (this repo ships HestiaCP
  templates) and, recommended, Cloudflare in front (the rate limiter trusts
  `CF-Connecting-IP`).

## Installation

```bash
git clone https://github.com/nerva-project/NerVault.git
cd NerVault

# Backend dependencies
make install-dev          # uv sync --all-extras

# Frontend dependencies
npm install

# Configuration
cp src/backend/config.example.py src/backend/config.py
$EDITOR src/backend/config.py
```

## Configuration

All configuration lives in `src/backend/config.py` (gitignored; copy it from
`config.example.py`). Bootstrap values (`SECRET_KEY`, `MONGO_URI`, `REDIS_URL`)
must be present before anything else can load.

| Key | Description |
|---|---|
| `SECRET_KEY` | Secret used to sign session cookies and tokens. Use a long random value (`secrets.token_hex(32)`). |
| `PASSWORD_SALT` | Salt for email confirmation / password-reset tokens. |
| `MONGO_URI` / `MONGO_DB` | MongoDB connection string and database name. |
| `REDIS_URL` | Redis/Valkey URL (cache, maintenance flag). In the stack: `redis://redis:6379/0`. |
| `RATE_LIMIT_COUNT` / `RATE_LIMIT_PERIOD` | Default per-IP request budget (count per period seconds) for all blueprints. |
| `FRONTEND_URL` | Public base URL of the SPA; used to build email links. Prod: `https://vault.nerva.one`. |
| `NERVA_DOCKER_IMAGE` | Image used for the spawned wallet containers (`sn1f3rt/nerva:latest`). |
| `PERMANENT_SESSION_LIFETIME` | Wallet container lifetime in seconds before the cleanup loop reaps it. |
| `WALLET_NETWORK` | Empty for run-on-host (wallet RPC published to `127.0.0.1`). In the stack set to `nervault` so the app reaches wallet containers by name on the shared network. |
| `DAEMON_HOST` / `DAEMON_PORT` / `DAEMON_SSL` | Nerva daemon RPC location. In the stack, with the daemon on the host, set `DAEMON_HOST = "host.docker.internal"`. |
| `DAEMON_USERNAME` / `DAEMON_PASSWORD` | Daemon RPC credentials. |
| `MAIL_*` | SMTP host/port/credentials, TLS/SSL flags, and default sender. |
| `COINGECKO_API_KEY` | CoinGecko API key for market data on the home page. |
| `TEMP_MAIL_BLOCK_API_KEY` | API key for disposable-email detection at registration. |
| `DEBUG` | Quart debug mode. Keep `False` in production. |
| `TEMPLATES_AUTO_RELOAD` | Reload email templates on change (dev convenience). |
| `QUART_AUTH_COOKIE_SECURE` | `True` in production (HTTPS); `False` for local HTTP. |
| `QUART_AUTH_COOKIE_SAMESITE` | Session cookie SameSite policy (`Lax`). |

## Running (development)

```bash
make serve
```

This runs the backend (hypercorn with reload on `127.0.0.1:8080`) and the Vite
dev server (`127.0.0.1:3000`, proxying `/v1` to the backend) together. Open
<http://localhost:3000>.

Useful targets: `make dev` (backend only), `make lint`, `make typecheck`
(`mypy src/backend`; run `npm run typecheck` for backend mypy + frontend
`vue-tsc`), `make image` (pull the wallet image),
`make maintenance-enable` / `make maintenance-disable`,
`make reset-wallet <username>`. `make prod` runs the app directly on the host
(hypercorn, no Docker) — the Deployment section covers the containerised path.

## Deployment

NerVault orchestrates Docker, so the deployed stack runs the app in a container
alongside a **least-privilege `docker-socket-proxy`** that lets it spawn the
per-user wallet containers. TLS terminates at the HestiaCP/nginx edge, which
proxies to the published web container.

1. **Host prep.** Install Docker + Compose, run the Nerva daemon, and pull the
   wallet image: `make image`.
2. **DNS.** Point `vault.nerva.one` at the host (through Cloudflare,
   recommended). Consider a `vault-next.nerva.one` staging host first.
3. **Configure** `src/backend/config.py` for production:
   - `REDIS_URL = "redis://redis:6379/0"`
   - `WALLET_NETWORK = "nervault"`
   - `DAEMON_HOST = "host.docker.internal"` (daemon on the host)
   - `FRONTEND_URL = "https://vault.nerva.one"`
   - `QUART_AUTH_COOKIE_SECURE = True`, `DEBUG = False`
4. **Bring up the stack:**
   ```bash
   docker compose up -d --build
   ```
   This starts `api`, `web` (nginx, published on `127.0.0.1:17569`), `redis`,
   and `docker-socket-proxy` on the `nervault` network.
5. **Edge.** Install the HestiaCP proxy templates from `docker/hestia/`
   (`nervault.tpl`, `nervault.stpl`) — they terminate TLS and forward
   `X-Forwarded-For` to `127.0.0.1:17569`. Issue a Let's Encrypt certificate for
   `vault.nerva.one`.
6. **Firewall.** Restrict the daemon's RPC port (`17566`) so it is only
   reachable from the host and Docker networks. With `ufw`:
   ```bash
   ufw allow from 172.16.0.0/12 to any port 17566 proto tcp   # docker networks
   ufw allow from 127.0.0.1 to any port 17566 proto tcp
   ufw deny 17566
   ```

### Security notes

- **Custodial.** The server holds wallet files and secrets; this is convenient
  but riskier than a self-hosted wallet. The FAQ makes this clear to users.
- **docker-socket-proxy.** The proxy is scoped to only the endpoints NerVault
  needs (containers, images, networks, volumes, info, write), but container
  creation is inherently powerful — treat the `api` service as security-
  sensitive and keep it off the public internet (only `web` is published, to
  loopback, behind the edge).
- **Rate-limit IP.** The limiter keys on `CF-Connecting-IP`, falling back to the
  forwarded route. Put Cloudflare in front for a trustworthy client IP; a bare
  `X-Forwarded-For` can otherwise be spoofed.

## Funding

The application itself is free to use, but its development and hosting are not.
If you find the application useful, please consider donating:

- **Nerva (XNV):** `NV1PqtQwRik7FFeAJ5n7iKbHtve3nkeM99x3Q31wjBAm7twvRv6NYkbbP7vSG3n8N3fsUh2gpfZG2PRi4gYhxL4h2r2SnhUoX`
- **Monero (XMR):** `48SSQzEcvQPK7H69vUvwReFT7tCDESdRhPFGubTgJ8WeXUUPQRWjY8oZk3wHfLhsUnChJ1BYyYfoLKQh8epYsupAAWCnDKh`
- **Bitcoin (BTC):** `bc1qzg4jjtxq6cg22pmlaesyva64nrjzcaqud968vf`
- **Ethereum (ETH):** `0x97173e82df1d9Cc76946241D63A9f9231Dea1566`

or if you prefer, you can support using fiat currency via [GitHub Sponsors](https://github.com/sponsors/sn1f3rt), [Patreon](https://www.patreon.com/sn1f3rt), or [Buy Me A Coffee](https://www.buymeacoffee.com/sn1f3rt).

## License

[GNU General Public License v3.0](LICENSE)

Copyright &copy; 2024-present [Sayan "sn1f3rt" Bhattacharyya](https://sn1f3rt.dev), [The Nerva Project](https://nerva.one)
