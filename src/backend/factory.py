from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import asyncio
from datetime import timedelta

import click
from quart import Quart, Response, jsonify, request
from aiosmtplib import SMTP, SMTPException
from quart_auth import QuartAuth, Unauthorized, current_user
from nerva.daemon import DaemonHTTP
from quart_bcrypt import Bcrypt
from password_validator import PasswordValidator
from quart_rate_limiter import RateLimiter, limit_blueprint
from werkzeug.exceptions import HTTPException
from pymongo.asynchronous.database import AsyncDatabase
from quart_rate_limiter.redis_store import RedisStore
from pymongo.asynchronous.mongo_client import AsyncMongoClient

from backend.utils.csrf import init_csrf

if TYPE_CHECKING:
    from backend.library.cache import Cache
    from backend.library.docker import Docker

# Global variables to hold instances of external components
bcrypt: Bcrypt
cache: Cache
daemon: DaemonHTTP
db: AsyncDatabase[Any]
docker: Docker
schema: PasswordValidator


async def _rate_limit_key() -> str:
    return request.headers.get("CF-Connecting-IP") or request.access_route[0]


async def create_app() -> Quart:
    """
    Create and configure the API-only Quart application.

    Returns:
        Quart: The configured Quart application instance.

    This function initializes all components required for the application:
    - Quart application setup (API-only, no static serving)
    - Configuration from environment or config file
    - Password hashing and validation (bcrypt, schema)
    - Cache service (Redis)
    - Rate limiting and double-submit CSRF protection
    - Daemon connection (Nerva)
    - MongoDB connection
    - SMTP server connection
    - User authentication (QuartAuth)
    - Several CLI commands for container and maintenance management
    """
    app: Quart = Quart(__name__, static_folder=None)

    try:
        app.config.from_envvar("QUART_SECRETS")
    except RuntimeError:
        app.config.from_pyfile("config.py")

    if app.config.get("SECRET_KEY") in (None, "", "secret_key") or app.config.get(
        "PASSWORD_SALT"
    ) in (None, "", "password_salt"):
        raise RuntimeError(
            "SECRET_KEY and PASSWORD_SALT must be set to unique secret values "
            "(the config.example.py placeholders are not allowed)."
        )

    global bcrypt, cache, daemon, db, docker, schema

    # Initialize bcrypt for password hashing
    bcrypt = Bcrypt(app)

    # Initialize cache (Redis)
    from backend.library.cache import Cache

    cache = Cache()

    # Initialize rate limiting (per-client, keyed by originating IP);
    # backed by Redis so limits survive restarts and span multiple workers
    RateLimiter(
        app,
        key_function=_rate_limit_key,
        store=RedisStore(app.config["REDIS_URL"]),
    )

    # Initialize double-submit CSRF protection
    init_csrf(app)

    # Set up Daemon connection (Nerva)
    daemon = DaemonHTTP(
        host=app.config["DAEMON_HOST"],
        port=app.config["DAEMON_PORT"],
    )

    # Connect to MongoDB using pymongo async driver
    db = AsyncMongoClient(app.config["MONGO_URI"])[app.config["MONGO_DB"]]

    # Initialize Docker client
    from backend.library.docker import Docker

    docker = Docker()

    # Set up password validation schema
    schema = PasswordValidator()
    schema.min(8).max(
        72
    ).has().uppercase().has().lowercase().has().digits().has().symbols().has().no().spaces()

    # Cap the auth session lifetime (quart-auth defaults to 1 year)
    app.config.setdefault("QUART_AUTH_DURATION", 7 * 24 * 60 * 60)

    # Initialize authentication manager
    auth_manager = QuartAuth(app)

    async with app.app_context():
        from backend.utils.models import User

        auth_manager.user_class = User  # type: ignore[assignment]

        @app.before_request
        async def _load_user_data() -> None:
            """Loads the current user's data for authenticated, non-public requests."""
            if current_user.auth_id is None:
                return

            endpoint = request.endpoint or ""
            if ".meta." in endpoint or ".index." in endpoint:
                return

            try:
                await current_user.load()  # type: ignore[attr-defined]
            except ValueError:
                pass

        @app.before_request
        async def _check_maintenance() -> Optional[tuple[Response, int]]:
            """Returns a 503 for non-meta endpoints while in maintenance mode."""
            from backend.library.helpers import on_maintenance

            endpoint = request.endpoint or ""
            if ".meta." in endpoint or ".index." in endpoint:
                return None

            if await on_maintenance():
                return jsonify(
                    {"status": "error", "error": "Service is under maintenance"}
                ), 503

            return None

        # Background task: clean up stale/expired wallet containers every hour
        @app.before_serving
        async def _start_cleanup_loop() -> None:
            async def _cleanup_loop() -> None:
                while True:
                    await asyncio.sleep(3600)
                    try:
                        await docker.cleanup()
                        app.logger.info("Cleaned up expired wallet containers")
                    except Exception:
                        app.logger.exception("Failed to clean up wallet containers")

            app.add_background_task(_cleanup_loop)

        # Background task: probe the SMTP server without blocking startup.
        @app.before_serving
        async def _probe_smtp() -> None:
            async def _check() -> None:
                smtp = SMTP(
                    hostname=app.config["MAIL_HOST"],
                    port=app.config["MAIL_PORT"],
                    username=app.config["MAIL_USERNAME"],
                    password=app.config["MAIL_PASSWORD"],
                    use_tls=app.config["MAIL_USE_SSL"],
                    start_tls=app.config["MAIL_USE_TLS"],
                    validate_certs=app.config["MAIL_VALIDATE_CERTS"],
                )
                try:
                    await smtp.connect()
                    await smtp.quit()
                except SMTPException:
                    app.logger.warning("Could not connect to the SMTP server")

            app.add_background_task(_check)

        # Background task: warm the coin-info cache so the first page load is fast.
        @app.before_serving
        async def _warm_coin_cache() -> None:
            async def _warm() -> None:
                try:
                    await cache.get_coin_info()
                except Exception:
                    app.logger.warning("Could not warm the coin info cache")

            app.add_background_task(_warm)

        # CLI commands
        @app.cli.command("reset_wallet")
        @click.argument("username")
        def _reset_wallet(username: str) -> None:
            """
            Resets the wallet data for a given user.

            Args:
                username (str): The username whose wallet data is to be cleared.
            """

            async def __reset_wallet() -> None:
                from backend.utils.models import User

                user = User(username=username)
                await user.clear_wallet_data()
                print(f"Wallet data cleared for user {user.username}")

            asyncio.run(__reset_wallet())

        @app.cli.command("reset_2fa")
        @click.argument("username")
        def _reset_2fa(username: str) -> None:
            """
            Clears all two-factor authentication for a given user.

            Args:
                username (str): The username whose 2FA is to be reset.
            """

            async def __reset_2fa() -> None:
                from backend.utils.models import User

                user = User(username=username)
                try:
                    await user.load()
                except ValueError:
                    print(f"User {username} not found")
                    return

                user.email_2fa = False
                user.totp_secret = None
                user.totp_enabled = False
                user.backup_codes = []
                await user.save()
                print(f"Two-factor authentication reset for user {user.username}")

            asyncio.run(__reset_2fa())

        @app.cli.command("maintenance")
        @click.argument("mode")
        def _maintenance(mode: str) -> None:
            """
            Enables or disables maintenance mode.

            Args:
                mode (str): "enable" or "disable" to set the maintenance mode.
            """

            async def __maintenance() -> None:
                from backend.library.helpers import on_maintenance, set_maintenance

                if mode == "enable":
                    if await on_maintenance():
                        print("[WARNING] Application is already on maintenance mode")
                    else:
                        await set_maintenance(True)
                        print("[INFO] Maintenance mode enabled")

                elif mode == "disable":
                    if not await on_maintenance():
                        print("[WARNING] Application not on maintenance mode")
                    else:
                        await set_maintenance(False)
                        print("[INFO] Maintenance mode disabled")
                else:
                    print("[USAGE] quart maintenance enable/disable ")

            asyncio.run(__maintenance())

        # Error handling
        @app.errorhandler(Unauthorized)
        async def _handle_unauthorized(*_: Any) -> tuple[Response, int]:
            """Returns a 401 for unauthenticated access to protected endpoints."""
            return jsonify(
                {"status": "error", "error": "Authentication required"}
            ), 401

        @app.errorhandler(HTTPException)
        async def _handle_http_exception(
            error: HTTPException,
        ) -> tuple[Response, int]:
            """Returns a generic JSON response for HTTP errors."""
            return jsonify({"status": "error", "error": error.name}), (
                error.code or 500
            )

        @app.errorhandler(Exception)
        async def _handle_exception(_: Exception) -> tuple[Response, int]:
            """Logs unexpected errors server-side and returns a generic response."""
            app.logger.exception("Unhandled exception")
            return jsonify(
                {"status": "error", "error": "Internal server error"}
            ), 500

        # Register the API blueprint (mounts everything under /v1)
        from backend.blueprints import api_bp, auth_bp, meta_bp, wallet_bp

        count: int = app.config["RATE_LIMIT_COUNT"]
        period: timedelta = timedelta(seconds=app.config["RATE_LIMIT_PERIOD"])

        limit_blueprint(auth_bp, count, period)
        limit_blueprint(meta_bp, count, period)
        limit_blueprint(wallet_bp, count, period)

        app.register_blueprint(api_bp)

        return app
