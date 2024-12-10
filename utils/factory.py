from __future__ import annotations

from typing import TYPE_CHECKING

import sys
import asyncio
from datetime import datetime
from urllib.parse import quote_plus

import click
import motor.motor_asyncio
from quart import Quart, flash, request, url_for, redirect
from quart_wtf import CSRFProtect
from aiosmtplib import SMTP, SMTPException
from quart_auth import QuartAuth, Unauthorized, current_user
from nerva.daemon import DaemonLegacy
from quart_bcrypt import Bcrypt
from dateutil.parser import parse
from password_validator import PasswordValidator

if TYPE_CHECKING:
    from library.cache import Cache
    from library.docker import Docker

# Global variables to hold instances of external components
bcrypt: Bcrypt
cache: Cache
csrf: CSRFProtect
daemon: DaemonLegacy
db: motor.motor_asyncio.AsyncIOMotorDatabase
docker: Docker
schema: PasswordValidator


async def create_app() -> Quart:
    """
    Create and configure the Quart application with various services, such as
    database, SMTP, authentication, and Docker.

    Returns:
        Quart: The configured Quart application instance.

    This function initializes all components required for the application,
    such as:
    - Quart application setup
    - Configuration from environment or config file
    - Password hashing and validation (bcrypt, schema)
    - Cache service (Valkey)
    - CSRF protection
    - Daemon connection (Nerva)
    - MongoDB connection
    - SMTP server connection
    - User authentication (QuartAuth)
    - Several CLI commands for container and maintenance management
    """
    app: Quart = Quart(
        __name__,
        static_url_path="/assets",
        static_folder="../assets",
        template_folder="../templates",
    )

    try:
        app.config.from_envvar("QUART_SECRETS")
    except RuntimeError:
        app.config.from_pyfile("../config.py")

    global bcrypt, cache, csrf, daemon, db, docker, schema

    # Initialize bcrypt for password hashing
    bcrypt = Bcrypt(app)

    # Initialize cache (Valkey)
    from library.cache import Cache

    cache = Cache()

    # Initialize CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)

    # Set up Daemon connection (Nerva)
    daemon = DaemonLegacy(
        host=app.config["DAEMON_HOST"],
        port=app.config["DAEMON_PORT"],
    )

    # Connect to MongoDB using Motor async driver
    db = motor.motor_asyncio.AsyncIOMotorClient(
        f"mongodb://{quote_plus(app.config['MONGO_USERNAME'])}:{quote_plus(app.config['MONGO_PASSWORD'])}@"
        f"{app.config['MONGO_HOST']}:{app.config['MONGO_PORT']}"
    )[app.config["MONGO_DB"]]

    # Initialize Docker client
    from library.docker import Docker

    docker = Docker()

    # Set up password validation schema
    schema = PasswordValidator()
    schema.min(8).max(
        100
    ).has().uppercase().has().lowercase().has().digits().has().symbols().has().no().spaces()

    # Initialize authentication manager
    auth_manager = QuartAuth(app)

    # Set up SMTP server connection
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
        del smtp
    except SMTPException:
        print("Failed to connect to SMTP server. Exiting...")
        sys.exit(1)

    # App context for user-related operations and filters
    async with app.app_context():
        from utils.models import User

        auth_manager.user_class = User

        # Template filters
        @app.template_filter("datestamp")
        def _datestamp(dt: int) -> str:
            """
            Converts a timestamp to a human-readable date string.

            Args:
                dt (int): Unix timestamp.

            Returns:
                str: Formatted date string (e.g., "2024-11-27 14:00:00").
            """
            return datetime.fromtimestamp(dt).strftime("%Y-%m-%d %H:%M:%S")

        @app.template_filter("timeparse")
        def _timeparse(dt: str) -> str:
            """
            Parses and converts a date string into a formatted date string.

            Args:
                dt (str): Date string to parse.

            Returns:
                str: Formatted date string.
            """
            return datetime.fromtimestamp(parse(dt).timestamp()).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        @app.template_filter("from_atomic")
        def from_atomic(a: int) -> str:
            """
            Converts atomic units to the standard format.

            Args:
                a (int): Amount in atomic units.

            Returns:
                str: Formatted amount with up to 10 decimal places.
            """
            from library.utils import from_atomic

            amount = from_atomic(a)
            return (
                0 if amount == 0 else format(amount, ".10f").rstrip("0").rstrip(".")
            )

        # Before request hooks
        @app.before_request
        async def _load_user_data():
            """
            Loads the current user data if available before each request.
            """
            try:
                await current_user.load()
            except ValueError:
                pass

        @app.before_request
        async def _check_maintenance():
            """
            Checks if the app is in maintenance mode before processing a request.
            Redirects to maintenance page if the app is in maintenance mode.
            """
            from library.helpers import on_maintenance

            if request.endpoint in ["meta._maintenance", "static"]:
                return

            if await on_maintenance():
                return redirect(url_for("meta._maintenance"))

        # CLI commands
        @app.cli.command("clean_containers")
        def _clean_containers() -> None:
            """Cleans up Docker containers."""

            async def __clean_containers() -> None:
                await docker.cleanup()
                print("[INFO] Cleaned up expired wallet containers")

            asyncio.get_event_loop().run_until_complete(__clean_containers())

        @app.cli.command("reset_wallet")
        @click.argument("username")
        def _reset_wallet(username: str) -> None:
            """
            Resets the wallet data for a given user.

            Args:
                username (str): The username whose wallet data is to be cleared.
            """

            async def __reset_wallet() -> None:
                from models import User

                user = User(username=username)
                await user.clear_wallet_data()
                print(f"Wallet data cleared for user {user.username}")

            asyncio.get_event_loop().run_until_complete(__reset_wallet())

        @app.cli.command("maintenance")
        @click.argument("mode")
        def _maintenance(mode: str) -> None:
            """
            Enables or disables maintenance mode.

            Args:
                mode (str): "enable" or "disable" to set the maintenance mode.
            """

            async def __maintenance() -> None:
                from library.helpers import on_maintenance, set_maintenance

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

            asyncio.get_event_loop().run_until_complete(__maintenance())

        # Error handling
        @app.errorhandler(Unauthorized)
        async def _redirect_to_login(*_):
            """Redirects the user to the login page in case of Unauthorized access."""
            await flash("You need to log in to access this page", "warning")
            return redirect(url_for("auth._login"))

        # Register blueprints
        from blueprints.auth import auth_bp
        from blueprints.meta import meta_bp
        from blueprints.wallet import wallet_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(meta_bp)
        app.register_blueprint(wallet_bp)

        return app
