# Security
SECRET_KEY = "secret_key"
PASSWORD_SALT = "password_salt"

# MongoDB
MONGO_URI = (
    "mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority"
)
MONGO_DB = "database_name"

# Redis
REDIS_URL = "redis://:password@host:port/0"

# Rate Limiting
RATE_LIMIT_COUNT = 120
RATE_LIMIT_PERIOD = 60

# Frontend
FRONTEND_URL = "http://localhost:3000"

# Docker
NERVA_DOCKER_IMAGE = "sn1f3rt/nerva:latest"
PERMANENT_SESSION_LIFETIME = 3600
# Empty for the run-on-host model (wallet RPC published to 127.0.0.1). In the
# containerized stack, set this to the shared Docker network name so the app
# reaches spawned wallet containers by name (e.g. "nervault").
WALLET_NETWORK = ""

# Daemon
DAEMON_HOST = "localhost"
DAEMON_PORT = 17566
DAEMON_SSL = False
DAEMON_USERNAME = "username"
DAEMON_PASSWORD = "password"

# Email
MAIL_HOST = "localhost"
MAIL_PORT = 25
MAIL_USE_SSL = False
MAIL_USE_TLS = False
MAIL_VALIDATE_CERTS = False
MAIL_USERNAME = "email@example.com"
MAIL_PASSWORD = "password"
MAIL_DEFAULT_SENDER = "NerVault <email@example.com>"

# COINGECKO
COINGECKO_API_KEY = "coingecko_api_key"

# TEMP MAIL BLOCK
TEMP_MAIL_BLOCK_API_KEY = "temp_mail_block_api_key"

# Networking
# Trust the proxy-set CF-Connecting-IP header for the client IP used in rate
# limiting. Keep this True only when the origin is reachable solely through the
# trusted proxy (e.g. firewall-locked to Cloudflare's IP ranges); otherwise a
# client could forge the header to bypass rate limits. Set False for a directly
# reachable origin to use the real socket peer instead.
TRUST_PROXY_IP_HEADER = True

# Development
DEBUG = False
TEMPLATES_AUTO_RELOAD = False
QUART_AUTH_COOKIE_SECURE = True
QUART_AUTH_COOKIE_SAMESITE = "Lax"
QUART_AUTH_DURATION = 604800  # Auth session lifetime in seconds (7 days)
