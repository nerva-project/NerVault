from typing import Any

import asyncio
import datetime
from datetime import timedelta

import aiohttp
from quart import Response, jsonify, request, current_app, render_template
from quart_auth import (
    login_user,
    logout_user,
    current_user as _current_user,
    login_required,
)
from email_validator import EmailNotValidError, validate_email
from quart_rate_limiter import rate_limit

from backend import config
from backend.factory import bcrypt, docker, schema
from backend.utils.mail import send_email
from backend.utils.models import User
from backend.utils.tokens import generate_token, validate_token
from backend.library.helpers import capture_event
from backend.library.validation import is_valid_username

from . import auth_bp

current_user: User = _current_user  # type: ignore[assignment]

SENSITIVE_IP_LIMIT = 10
SENSITIVE_IP_PERIOD = timedelta(minutes=1)
SENSITIVE_ACCOUNT_LIMIT = 5
SENSITIVE_ACCOUNT_PERIOD = timedelta(minutes=15)

PASSWORD_POLICY = (
    "Password must be at least 8 characters long and contain at least one "
    "uppercase letter, one lowercase letter, one digit, and one symbol."
)


async def _account_rate_limit_key() -> str:
    """Rate-limit key based on the targeted account, for brute-force protection."""
    data = await request.get_json(silent=True) or {}
    identifier = (
        data.get("username")
        or data.get("email")
        or (request.view_args or {}).get("token")
    )

    if identifier:
        return str(identifier).strip().lower()

    return request.headers.get("CF-Connecting-IP") or request.access_route[0]


async def _skip_safe_methods() -> bool:
    """Skip rate limiting for non-mutating requests."""
    return request.method in ("GET", "HEAD", "OPTIONS")


def _user_dict(user: User) -> dict[str, Any]:
    """Returns the safe, client-facing representation of a user."""
    return {
        "username": user.username,
        "email": user.email,
        "confirmed": user.confirmed,
        "wallet_created": user.wallet_created,
        "wallet_connected": user.wallet_connected,
    }


@auth_bp.route("/register", methods=["POST"])
@rate_limit(
    SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD, skip_function=_skip_safe_methods
)
@rate_limit(
    SENSITIVE_ACCOUNT_LIMIT,
    SENSITIVE_ACCOUNT_PERIOD,
    key_function=_account_rate_limit_key,
    skip_function=_skip_safe_methods,
)
async def _register() -> tuple[Response, int]:
    """
    Registers a new user, sends a confirmation email, and starts a session.
    """
    if await current_user.is_authenticated:
        return jsonify({"status": "error", "error": "Already authenticated."}), 400

    data = await request.get_json(silent=True) or {}
    username = str(data.get("username") or "").strip().lower()
    email = str(data.get("email") or "").strip()
    password = str(data.get("password") or "")

    if not is_valid_username(username):
        return jsonify(
            {
                "status": "error",
                "error": "Username must be 3-32 characters long and contain only "
                "lowercase letters, digits, or underscores.",
            }
        ), 400

    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return jsonify(
            {"status": "error", "error": "A valid email address is required."}
        ), 400

    existing = User(username=username)
    try:
        await existing.load()
        return jsonify(
            {"status": "error", "error": "This username is already registered."}
        ), 409
    except ValueError:
        pass

    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        ) as session:
            async with session.get(
                f"https://block-temporary-email.com/check/email/{email}",
                headers={
                    "x-api-key": str(
                        current_app.config.get("TEMP_MAIL_BLOCK_API_KEY", "")
                    )
                },
            ) as res:
                if res.status == 200 and (await res.json()).get("temporary"):
                    return jsonify(
                        {
                            "status": "error",
                            "error": "Registrations with temporary disposable "
                            "emails are not allowed.",
                        }
                    ), 400
    except (aiohttp.ClientError, asyncio.TimeoutError):
        pass

    if not schema.validate(password):
        return jsonify({"status": "error", "error": PASSWORD_POLICY}), 400

    user = User(username=username)
    user.email = email
    user.password = bcrypt.generate_password_hash(password).decode("utf8")
    await user.save()

    token = generate_token(user.email)
    confirm_url = f"{config.FRONTEND_URL}/confirm/{token}"
    template = await render_template("email/activate.html", confirm_url=confirm_url)
    await send_email(user.email, "Account Activation", template)

    await capture_event(user.username, "register")
    login_user(user)

    return jsonify(
        {
            "status": "success",
            "message": "A confirmation email has been sent. "
            "Please check Junk/Spam folders.",
            "result": _user_dict(user),
        }
    ), 201


@auth_bp.route("/confirm/<token>", methods=["GET"])
@rate_limit(SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD)
@rate_limit(
    SENSITIVE_ACCOUNT_LIMIT,
    SENSITIVE_ACCOUNT_PERIOD,
    key_function=_account_rate_limit_key,
)
async def _confirm(token: str) -> tuple[Response, int]:
    """
    Confirms a user's account using the provided token.
    """
    email = validate_token(token)

    try:
        if not email:
            raise ValueError
        user = await User.get_by_email(email)
    except ValueError:
        return jsonify(
            {
                "status": "error",
                "error": "The confirmation link is either invalid or has expired.",
            }
        ), 400

    if user.confirmed:
        return jsonify(
            {"status": "success", "message": "Account already confirmed."}
        ), 200

    user.confirmed = True
    user.confirmed_at = datetime.datetime.now(datetime.UTC)
    await user.save()

    await capture_event(user.username, "confirmed")

    return jsonify(
        {
            "status": "success",
            "message": "You have successfully confirmed your account.",
        }
    ), 200


@auth_bp.route("/resend-confirmation", methods=["POST"])
@rate_limit(SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD)
@login_required
async def _resend() -> tuple[Response, int]:
    """
    Resends the account confirmation email to the current user.
    """
    if current_user.confirmed:
        return jsonify(
            {"status": "error", "error": "Account already confirmed."}
        ), 400

    token = generate_token(current_user.email)
    confirm_url = f"{config.FRONTEND_URL}/confirm/{token}"
    html = await render_template("email/activate.html", confirm_url=confirm_url)
    await send_email(current_user.email, "Account Activation", html)

    await capture_event(current_user.username, "resend_confirm_email")

    return jsonify(
        {"status": "success", "message": "A new confirmation email has been sent."}
    ), 200


@auth_bp.route("/login", methods=["POST"])
@rate_limit(
    SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD, skip_function=_skip_safe_methods
)
@rate_limit(
    SENSITIVE_ACCOUNT_LIMIT,
    SENSITIVE_ACCOUNT_PERIOD,
    key_function=_account_rate_limit_key,
    skip_function=_skip_safe_methods,
)
async def _login() -> tuple[Response, int]:
    """
    Authenticates a user and starts a session.
    """
    if await current_user.is_authenticated:
        return jsonify(
            {"status": "success", "result": _user_dict(current_user)}
        ), 200

    data = await request.get_json(silent=True) or {}
    username = str(data.get("username") or "").strip().lower()
    password = str(data.get("password") or "")

    user = User(username=username)

    try:
        await user.load()
    except ValueError:
        return jsonify(
            {"status": "error", "error": "Invalid username or password."}
        ), 401

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify(
            {"status": "error", "error": "Invalid username or password."}
        ), 401

    await capture_event(user.username, "login")
    login_user(user)

    return jsonify({"status": "success", "result": _user_dict(user)}), 200


@auth_bp.route("/logout", methods=["POST"])
@login_required
async def _logout() -> tuple[Response, int]:
    """
    Logs the user out, stops their wallet container, and clears wallet data.
    """
    docker.stop_container(current_user.wallet_container)
    await capture_event(current_user.username, "stop_container")
    await current_user.clear_wallet_data()
    await capture_event(current_user.username, "logout")
    logout_user()

    return jsonify(
        {"status": "success", "message": "You have been logged out."}
    ), 200


@auth_bp.route("/reset", methods=["POST"])
@rate_limit(
    SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD, skip_function=_skip_safe_methods
)
@rate_limit(
    SENSITIVE_ACCOUNT_LIMIT,
    SENSITIVE_ACCOUNT_PERIOD,
    key_function=_account_rate_limit_key,
    skip_function=_skip_safe_methods,
)
async def _reset() -> tuple[Response, int]:
    """
    Sends a password reset link, without revealing whether the email exists.
    """
    data = await request.get_json(silent=True) or {}
    email = str(data.get("email") or "").strip()

    generic = jsonify(
        {
            "status": "success",
            "message": "If that email is registered and confirmed, a reset "
            "link has been sent. Please check Junk/Spam folders.",
        }
    )

    try:
        user = await User.get_by_email(email)
    except ValueError:
        return generic, 200

    if not user.confirmed:
        return generic, 200

    token = generate_token(user.email)
    reset_url = f"{config.FRONTEND_URL}/reset/{token}"
    html = await render_template("email/reset_password.html", reset_url=reset_url)
    await send_email(user.email, "Password Reset", html)

    await capture_event(user.username, "pwd_reset_email_sent")

    return generic, 200


@auth_bp.route("/reset/<token>", methods=["POST"])
@rate_limit(
    SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD, skip_function=_skip_safe_methods
)
async def _reset_token(token: str) -> tuple[Response, int]:
    """
    Sets a new password using a valid reset token.
    """
    email = validate_token(token)

    if not email:
        return jsonify(
            {
                "status": "error",
                "error": "The reset link is either invalid or has expired.",
            }
        ), 400

    data = await request.get_json(silent=True) or {}
    password = str(data.get("password") or "")
    confirm = str(data.get("confirm_password") or "")

    if password != confirm:
        return jsonify(
            {"status": "error", "error": "The passwords do not match."}
        ), 400

    if not schema.validate(password):
        return jsonify({"status": "error", "error": PASSWORD_POLICY}), 400

    try:
        user = await User.get_by_email(email)
    except ValueError:
        return jsonify(
            {
                "status": "error",
                "error": "The reset link is either invalid or has expired.",
            }
        ), 400

    user.password = bcrypt.generate_password_hash(password).decode("utf8")
    await user.save()

    await capture_event(user.username, "password_change")

    return jsonify(
        {
            "status": "success",
            "message": "Your password has been changed successfully.",
        }
    ), 200


@auth_bp.route("/change-password", methods=["POST"])
@login_required
async def _change_password() -> tuple[Response, int]:
    """
    Changes the authenticated user's password after verifying the current one.
    """
    data = await request.get_json(silent=True) or {}
    current_password = str(data.get("current_password") or "")
    password = str(data.get("password") or "")
    confirm = str(data.get("confirm_password") or "")

    if not bcrypt.check_password_hash(current_user.password, current_password):
        return jsonify(
            {"status": "error", "error": "Current password is incorrect."}
        ), 400

    if password != confirm:
        return jsonify(
            {"status": "error", "error": "The passwords do not match."}
        ), 400

    if not schema.validate(password):
        return jsonify({"status": "error", "error": PASSWORD_POLICY}), 400

    current_user.password = bcrypt.generate_password_hash(password).decode("utf8")
    await current_user.save()

    await capture_event(current_user.username, "password_change")

    return jsonify(
        {
            "status": "success",
            "message": "Your password has been changed successfully.",
        }
    ), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
async def _me() -> tuple[Response, int]:
    """
    Returns the currently authenticated user.
    """
    return jsonify({"status": "success", "result": _user_dict(current_user)}), 200
