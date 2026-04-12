# Security
SECRET_KEY = "secret_key"
PASSWORD_SALT = "password_salt"

# MongoDB
from urllib.parse import quote_plus
MONGO_PASSWORD = "password"
MONGO_URI = f"mongodb+srv://user:{quote_plus(MONGO_PASSWORD)}@cluster.mongodb.net/?retryWrites=true&w=majority"
MONGO_DB = "database_name"

# Redis
REDIS_URL = "redis://:password@host:port/0"

# Docker
WALLET_DIR = "./data/wallets"
NERVA_DOCKER_IMAGE = "sn1f3rt/nerva:latest"
PERMANENT_SESSION_LIFETIME = 3600

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

# Development
DEBUG = False
TEMPLATES_AUTO_RELOAD = False
QUART_AUTH_COOKIE_SECURE = True
