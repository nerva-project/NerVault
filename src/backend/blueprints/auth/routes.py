from typing import Any

import hmac
import base64
import asyncio
import secrets
import datetime
from io import BytesIO
from datetime import timedelta

import pyotp
import aiohttp
from quart import Response, jsonify, request, current_app, render_template
from quart_auth import (
    login_user,
    logout_user,
    current_user as _current_user,
    login_required,
)
from qrcode.main import QRCode
from email_validator import EmailNotValidError, validate_email
from qrcode.constants import ERROR_CORRECT_M
from quart_rate_limiter import rate_limit

from backend import config
from backend.factory import cache, bcrypt, docker, schema
from backend.utils.mail import send_email
from backend.utils.twofa import hash_codes, verify_and_consume, generate_backup_codes
from backend.utils.models import User
from backend.utils.tokens import (
    RESET_SALT,
    CONFIRM_SALT,
    LOGIN_2FA_SALT,
    EMAIL_CHANGE_SALT,
    generate_token,
    validate_token,
    password_fingerprint,
)
from backend.library.helpers import capture_event, verify_2fa_code
from backend.utils.decorators import check_confirmed
from backend.library.validation import is_valid_username

from . import auth_bp

current_user: User = _current_user  # type: ignore[assignment]

SENSITIVE_IP_LIMIT = 10
SENSITIVE_IP_PERIOD = timedelta(minutes=1)
SENSITIVE_ACCOUNT_LIMIT = 5
SENSITIVE_ACCOUNT_PERIOD = timedelta(minutes=15)

LOGIN_2FA_TTL_MINUTES = 10
LOGIN_2FA_TTL = LOGIN_2FA_TTL_MINUTES * 60
TOTP_VALID_WINDOW = 1
TOTP_ISSUER = "NerVault"

PASSWORD_POLICY = (
    "Password must be at least 8 characters long and contain at least one "
    "uppercase letter, one lowercase letter, one digit, and one symbol."
)

# A valid bcrypt hash compared against on unknown usernames so login timing does
# not reveal whether an account exists.
_DUMMY_PASSWORD_HASH = "$2b$12$RRy7tt6i02lRca/5bFoKO.3GCKBPyVWDGZ/76LNSWG8SSY8IeIkoq"


def _issue_session(username: str, session_version: int) -> None:
    """Log the user in with a cookie carrying their current session version, so a
    later password/email change can invalidate every other session."""
    login_user(User(f"{username}:{session_version}"))


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


async def _login_2fa_rate_limit_key() -> str:
    """Rate-limit the 2FA login step per targeted account (decoded from the token)."""
    data = await request.get_json(silent=True) or {}
    payload = validate_token(
        str(data.get("token") or ""), LOGIN_2FA_SALT, LOGIN_2FA_TTL
    )

    if isinstance(payload, list) and payload:
        return str(payload[0]).strip().lower()

    return request.headers.get("CF-Connecting-IP") or request.access_route[0]


def _user_dict(user: User) -> dict[str, Any]:
    """Returns the safe, client-facing representation of a user."""
    return {
        "username": user.username,
        "email": user.email,
        "confirmed": user.confirmed,
        "wallet_created": user.wallet_created,
        "wallet_connected": user.wallet_connected,
        "two_factor": {
            "email": user.email_2fa,
            "totp": user.totp_enabled,
            "method": user.two_factor_method,
        },
    }


def _totp_qr_data_uri(uri: str) -> str:
    """Renders an otpauth:// URI as a base64 PNG data URI for an <img> tag."""
    qr = QRCode(error_correction=ERROR_CORRECT_M)
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")  # type: ignore[union-attr]
    buffer = BytesIO()
    img.save(buffer, format="PNG")

    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


async def _send_email_login_code(user: User) -> None:
    """Generates, caches, and emails a one-time login code for email 2FA."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    await cache.store_data(f"2fa:login:{user.username}", LOGIN_2FA_TTL_MINUTES, code)

    html = await render_template(
        "email/two_factor_code.html", code=code, ttl_minutes=LOGIN_2FA_TTL_MINUTES
    )
    await send_email(user.email, "Your NerVault Login Code", html)


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

    token = generate_token(user.email, CONFIRM_SALT)
    confirm_url = f"{config.FRONTEND_URL}/confirm/{token}"
    template = await render_template("email/activate.html", confirm_url=confirm_url)
    await send_email(user.email, "Account Activation", template)

    await capture_event(user.username, "register")
    _issue_session(user.username, user.session_version)

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
    email = validate_token(token, CONFIRM_SALT)

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
    await user.save(["confirmed", "confirmed_at"])

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

    token = generate_token(current_user.email, CONFIRM_SALT)
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
        # Equalise timing with the valid-user path so a fast response does not
        # reveal that the username is unregistered.
        bcrypt.check_password_hash(_DUMMY_PASSWORD_HASH, password)
        return jsonify(
            {"status": "error", "error": "Invalid username or password."}
        ), 401

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify(
            {"status": "error", "error": "Invalid username or password."}
        ), 401

    method = user.two_factor_method
    if method is not None:
        # Defer the session until the second factor is verified; bind the
        # challenge to the password so it dies if the password later changes.
        if method == "email":
            await _send_email_login_code(user)

        token = generate_token(
            [user.username, password_fingerprint(user.password)], LOGIN_2FA_SALT
        )
        await capture_event(user.username, "login_2fa_challenge")

        return jsonify(
            {
                "status": "success",
                "result": {"two_factor": True, "method": method, "token": token},
            }
        ), 200

    await capture_event(user.username, "login")
    _issue_session(user.username, user.session_version)

    return jsonify({"status": "success", "result": _user_dict(user)}), 200


@auth_bp.route("/logout", methods=["POST"])
@login_required
async def _logout() -> tuple[Response, int]:
    """
    Logs the user out, stops their wallet container, and clears wallet data.
    """
    await docker.stop_container(current_user.wallet_container)
    await capture_event(current_user.username, "stop_container")
    await current_user.clear_wallet_data(
        expected_container=current_user.wallet_container
    )
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

    token = generate_token(
        [user.email, password_fingerprint(user.password)], RESET_SALT
    )
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
    payload = validate_token(token, RESET_SALT)

    invalid = jsonify(
        {
            "status": "error",
            "error": "The reset link is either invalid or has expired.",
        }
    )

    if not isinstance(payload, list) or len(payload) != 2:
        return invalid, 400

    email, fingerprint = payload

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
        return invalid, 400

    if password_fingerprint(user.password) != fingerprint:
        return invalid, 400

    user.password = bcrypt.generate_password_hash(password).decode("utf8")
    user.session_version += 1
    await user.save(["password", "session_version"])

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
    code = str(data.get("code") or "")

    if not bcrypt.check_password_hash(current_user.password, current_password):
        return jsonify(
            {"status": "error", "error": "Current password is incorrect."}
        ), 400

    if not await verify_2fa_code(current_user, code):
        return jsonify(
            {"status": "error", "error": "Invalid or missing two-factor code."}
        ), 400

    if password != confirm:
        return jsonify(
            {"status": "error", "error": "The passwords do not match."}
        ), 400

    if not schema.validate(password):
        return jsonify({"status": "error", "error": PASSWORD_POLICY}), 400

    current_user.password = bcrypt.generate_password_hash(password).decode("utf8")
    current_user.session_version += 1
    await current_user.save(["password", "session_version"])
    _issue_session(current_user.username, current_user.session_version)

    await capture_event(current_user.username, "password_change")

    return jsonify(
        {
            "status": "success",
            "message": "Your password has been changed successfully.",
        }
    ), 200


@auth_bp.route("/login/2fa", methods=["POST"])
@rate_limit(
    SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD, skip_function=_skip_safe_methods
)
@rate_limit(
    SENSITIVE_ACCOUNT_LIMIT,
    SENSITIVE_ACCOUNT_PERIOD,
    key_function=_login_2fa_rate_limit_key,
    skip_function=_skip_safe_methods,
)
async def _login_2fa() -> tuple[Response, int]:
    """
    Completes a login by verifying the second factor and starting the session.
    """
    if await current_user.is_authenticated:
        return jsonify(
            {"status": "success", "result": _user_dict(current_user)}
        ), 200

    data = await request.get_json(silent=True) or {}
    token = str(data.get("token") or "")
    code = str(data.get("code") or "").strip()

    payload = validate_token(token, LOGIN_2FA_SALT, LOGIN_2FA_TTL)

    expired = jsonify(
        {
            "status": "error",
            "error": "Your login session has expired. Please sign in again.",
        }
    )

    if not isinstance(payload, list) or len(payload) != 2:
        return expired, 400

    username, fingerprint = payload
    user = User(username=str(username))

    try:
        await user.load()
    except ValueError:
        return expired, 400

    if password_fingerprint(user.password) != fingerprint:
        return expired, 400

    method = user.two_factor_method
    verified = method is None
    used_backup = False

    if method == "totp" and user.totp_secret:
        if pyotp.TOTP(user.totp_secret).verify(code, valid_window=TOTP_VALID_WINDOW):
            verified = True
        else:
            matched, remaining = verify_and_consume(code, user.backup_codes)
            if matched:
                verified = True
                used_backup = True
                user.backup_codes = remaining
                await user.save(["backup_codes"])
    elif method == "email":
        stored = await cache.get_data(f"2fa:login:{user.username}")
        if stored and hmac.compare_digest(stored, code):
            verified = True
            await cache.redis.delete(f"2fa:login:{user.username}")

    if not verified:
        return jsonify(
            {"status": "error", "error": "The code is incorrect or has expired."}
        ), 401

    await capture_event(user.username, "login")
    _issue_session(user.username, user.session_version)

    if used_backup:
        await capture_event(user.username, "login_2fa_backup_used")
        html = await render_template(
            "email/backup_code_used.html", remaining=len(user.backup_codes)
        )
        await send_email(user.email, "Backup Code Used", html)

    return jsonify({"status": "success", "result": _user_dict(user)}), 200


@auth_bp.route("/login/2fa/resend", methods=["POST"])
@rate_limit(
    SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD, skip_function=_skip_safe_methods
)
@rate_limit(
    SENSITIVE_ACCOUNT_LIMIT,
    SENSITIVE_ACCOUNT_PERIOD,
    key_function=_login_2fa_rate_limit_key,
    skip_function=_skip_safe_methods,
)
async def _login_2fa_resend() -> tuple[Response, int]:
    """
    Re-sends the email login code for an in-progress email-2FA challenge.
    """
    data = await request.get_json(silent=True) or {}
    token = str(data.get("token") or "")

    payload = validate_token(token, LOGIN_2FA_SALT, LOGIN_2FA_TTL)

    expired = jsonify(
        {
            "status": "error",
            "error": "Your login session has expired. Please sign in again.",
        }
    )

    if not isinstance(payload, list) or len(payload) != 2:
        return expired, 400

    username, fingerprint = payload
    user = User(username=str(username))

    try:
        await user.load()
    except ValueError:
        return expired, 400

    if (
        password_fingerprint(user.password) != fingerprint
        or user.two_factor_method != "email"
    ):
        return expired, 400

    await _send_email_login_code(user)

    return jsonify(
        {"status": "success", "message": "A new code has been sent."}
    ), 200


@auth_bp.route("/change-email", methods=["POST"])
@rate_limit(
    SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD, skip_function=_skip_safe_methods
)
@rate_limit(
    SENSITIVE_ACCOUNT_LIMIT,
    SENSITIVE_ACCOUNT_PERIOD,
    key_function=_account_rate_limit_key,
    skip_function=_skip_safe_methods,
)
@login_required
@check_confirmed
async def _change_email() -> tuple[Response, int]:
    """
    Begins an email change: emails a confirmation link to the new address and a
    notice to the old one. The address only changes once the link is confirmed.
    """
    data = await request.get_json(silent=True) or {}
    password = str(data.get("password") or "")
    new_email = str(data.get("new_email") or "").strip()
    code = str(data.get("code") or "")

    if not bcrypt.check_password_hash(current_user.password, password):
        return jsonify(
            {"status": "error", "error": "Current password is incorrect."}
        ), 400

    if not await verify_2fa_code(current_user, code):
        return jsonify(
            {"status": "error", "error": "Invalid or missing two-factor code."}
        ), 400

    try:
        validate_email(new_email, check_deliverability=False)
    except EmailNotValidError:
        return jsonify(
            {"status": "error", "error": "A valid email address is required."}
        ), 400

    if new_email.lower() == current_user.email.lower():
        return jsonify(
            {"status": "error", "error": "That is already your email address."}
        ), 400

    try:
        await User.get_by_email(new_email)
        return jsonify(
            {"status": "error", "error": "That email address is already in use."}
        ), 409
    except ValueError:
        pass

    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        ) as session:
            async with session.get(
                f"https://block-temporary-email.com/check/email/{new_email}",
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
                            "error": "Temporary disposable emails are not allowed.",
                        }
                    ), 400
    except (aiohttp.ClientError, asyncio.TimeoutError):
        pass

    token = generate_token(
        [
            current_user.username,
            new_email,
            password_fingerprint(current_user.password),
        ],
        EMAIL_CHANGE_SALT,
    )
    confirm_url = f"{config.FRONTEND_URL}/profile/email/{token}"

    html = await render_template("email/change_email.html", confirm_url=confirm_url)
    await send_email(new_email, "Confirm Your New Email", html)

    notice = await render_template("email/email_changed.html", new_email=new_email)
    await send_email(current_user.email, "Email Change Requested", notice)

    await capture_event(current_user.username, "email_change_requested")

    return jsonify(
        {
            "status": "success",
            "message": "A confirmation link has been sent to your new email "
            "address. Please check Junk/Spam folders.",
        }
    ), 200


@auth_bp.route("/change-email/<token>", methods=["POST"])
@rate_limit(
    SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD, skip_function=_skip_safe_methods
)
@login_required
@check_confirmed
async def _change_email_confirm(token: str) -> tuple[Response, int]:
    """
    Applies a pending email change using a valid confirmation token.
    """
    payload = validate_token(token, EMAIL_CHANGE_SALT)

    invalid = jsonify(
        {
            "status": "error",
            "error": "The email change link is either invalid or has expired.",
        }
    )

    if not isinstance(payload, list) or len(payload) != 3:
        return invalid, 400

    username, new_email, fingerprint = payload

    if (
        current_user.username != username
        or password_fingerprint(current_user.password) != fingerprint
    ):
        return invalid, 400

    try:
        existing = await User.get_by_email(new_email)
        if existing.username != current_user.username:
            return jsonify(
                {"status": "error", "error": "That email address is already in use."}
            ), 409
    except ValueError:
        pass

    old_email = current_user.email
    current_user.email = new_email
    current_user.session_version += 1
    await current_user.save(["email", "session_version"])
    _issue_session(current_user.username, current_user.session_version)

    notice = await render_template("email/email_updated.html", new_email=new_email)
    await send_email(old_email, "Email Address Changed", notice)

    await capture_event(current_user.username, "email_changed")

    return jsonify(
        {
            "status": "success",
            "message": "Your email address has been updated.",
            "result": _user_dict(current_user),
        }
    ), 200


@auth_bp.route("/2fa/email/enable", methods=["POST"])
@rate_limit(
    SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD, skip_function=_skip_safe_methods
)
@login_required
@check_confirmed
async def _2fa_email_enable() -> tuple[Response, int]:
    """
    Enables email-based two-factor authentication after verifying the password.
    """
    data = await request.get_json(silent=True) or {}
    password = str(data.get("password") or "")

    if not bcrypt.check_password_hash(current_user.password, password):
        return jsonify(
            {"status": "error", "error": "Current password is incorrect."}
        ), 400

    if current_user.totp_enabled:
        return jsonify(
            {
                "status": "error",
                "error": "Disable the authenticator app before using email codes.",
            }
        ), 400

    current_user.email_2fa = True
    await current_user.save(["email_2fa"])

    await capture_event(current_user.username, "2fa_email_enabled")

    return jsonify(
        {
            "status": "success",
            "message": "Email two-factor authentication is now enabled.",
            "result": _user_dict(current_user),
        }
    ), 200


@auth_bp.route("/2fa/email/disable", methods=["POST"])
@rate_limit(
    SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD, skip_function=_skip_safe_methods
)
@login_required
@check_confirmed
async def _2fa_email_disable() -> tuple[Response, int]:
    """
    Disables email-based two-factor authentication after verifying the password
    and a current step-up code, so the second factor cannot be stripped with the
    password alone.
    """
    data = await request.get_json(silent=True) or {}
    password = str(data.get("password") or "")
    code = str(data.get("code") or "")

    if not bcrypt.check_password_hash(current_user.password, password):
        return jsonify(
            {"status": "error", "error": "Current password is incorrect."}
        ), 400

    if not await verify_2fa_code(current_user, code):
        return jsonify(
            {"status": "error", "error": "Invalid or missing two-factor code."}
        ), 401

    current_user.email_2fa = False
    await current_user.save(["email_2fa"])

    await capture_event(current_user.username, "2fa_email_disabled")

    return jsonify(
        {
            "status": "success",
            "message": "Email two-factor authentication is now disabled.",
            "result": _user_dict(current_user),
        }
    ), 200


@auth_bp.route("/2fa/totp/setup", methods=["POST"])
@rate_limit(
    SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD, skip_function=_skip_safe_methods
)
@login_required
@check_confirmed
async def _2fa_totp_setup() -> tuple[Response, int]:
    """
    Starts authenticator-app setup: stores a fresh secret and returns its QR.
    """
    data = await request.get_json(silent=True) or {}
    password = str(data.get("password") or "")

    if not bcrypt.check_password_hash(current_user.password, password):
        return jsonify(
            {"status": "error", "error": "Current password is incorrect."}
        ), 400

    if current_user.totp_enabled:
        return jsonify(
            {"status": "error", "error": "The authenticator app is already enabled."}
        ), 400

    secret = pyotp.random_base32()
    current_user.totp_secret = secret
    await current_user.save(["totp_secret"])

    uri = pyotp.TOTP(secret).provisioning_uri(
        name=current_user.email, issuer_name=TOTP_ISSUER
    )

    return jsonify(
        {
            "status": "success",
            "result": {
                "secret": secret,
                "otpauth_uri": uri,
                "qr": _totp_qr_data_uri(uri),
            },
        }
    ), 200


@auth_bp.route("/2fa/totp/verify", methods=["POST"])
@rate_limit(
    SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD, skip_function=_skip_safe_methods
)
@login_required
@check_confirmed
async def _2fa_totp_verify() -> tuple[Response, int]:
    """
    Confirms authenticator setup with a code, enables TOTP, and issues backup codes.
    """
    data = await request.get_json(silent=True) or {}
    code = str(data.get("code") or "").strip()

    if not current_user.totp_secret:
        return jsonify(
            {"status": "error", "error": "Start the authenticator setup first."}
        ), 400

    if current_user.totp_enabled:
        return jsonify(
            {"status": "error", "error": "The authenticator app is already enabled."}
        ), 400

    if not pyotp.TOTP(current_user.totp_secret).verify(
        code, valid_window=TOTP_VALID_WINDOW
    ):
        return jsonify(
            {"status": "error", "error": "That code is incorrect. Please try again."}
        ), 400

    codes = generate_backup_codes()
    current_user.backup_codes = hash_codes(codes)
    current_user.totp_enabled = True
    current_user.email_2fa = False  # the authenticator app supersedes email
    await current_user.save(["backup_codes", "totp_enabled", "email_2fa"])

    await capture_event(current_user.username, "2fa_totp_enabled")

    return jsonify(
        {
            "status": "success",
            "message": "The authenticator app is now enabled.",
            "result": {"backup_codes": codes, "user": _user_dict(current_user)},
        }
    ), 200


@auth_bp.route("/2fa/totp/disable", methods=["POST"])
@rate_limit(
    SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD, skip_function=_skip_safe_methods
)
@login_required
@check_confirmed
async def _2fa_totp_disable() -> tuple[Response, int]:
    """
    Disables the authenticator app after verifying the password and a current code.
    """
    data = await request.get_json(silent=True) or {}
    password = str(data.get("password") or "")
    code = str(data.get("code") or "").strip()

    if not bcrypt.check_password_hash(current_user.password, password):
        return jsonify(
            {"status": "error", "error": "Current password is incorrect."}
        ), 400

    if not current_user.totp_enabled:
        return jsonify(
            {"status": "error", "error": "The authenticator app is not enabled."}
        ), 400

    valid = bool(
        current_user.totp_secret
        and pyotp.TOTP(current_user.totp_secret).verify(
            code, valid_window=TOTP_VALID_WINDOW
        )
    )
    if not valid:
        valid, remaining = verify_and_consume(code, current_user.backup_codes)
        current_user.backup_codes = remaining

    if not valid:
        return jsonify(
            {"status": "error", "error": "That code is incorrect. Please try again."}
        ), 400

    current_user.totp_enabled = False
    current_user.totp_secret = None
    current_user.backup_codes = []
    await current_user.save(["totp_enabled", "totp_secret", "backup_codes"])

    await capture_event(current_user.username, "2fa_totp_disabled")

    return jsonify(
        {
            "status": "success",
            "message": "The authenticator app is now disabled.",
            "result": _user_dict(current_user),
        }
    ), 200


@auth_bp.route("/2fa/backup/regenerate", methods=["POST"])
@rate_limit(
    SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD, skip_function=_skip_safe_methods
)
@login_required
@check_confirmed
async def _2fa_backup_regenerate() -> tuple[Response, int]:
    """
    Replaces the user's backup codes after verifying the password and a TOTP code.
    """
    data = await request.get_json(silent=True) or {}
    password = str(data.get("password") or "")
    code = str(data.get("code") or "").strip()

    if not bcrypt.check_password_hash(current_user.password, password):
        return jsonify(
            {"status": "error", "error": "Current password is incorrect."}
        ), 400

    if not current_user.totp_enabled or not current_user.totp_secret:
        return jsonify(
            {"status": "error", "error": "The authenticator app is not enabled."}
        ), 400

    if not pyotp.TOTP(current_user.totp_secret).verify(
        code, valid_window=TOTP_VALID_WINDOW
    ):
        return jsonify(
            {"status": "error", "error": "That code is incorrect. Please try again."}
        ), 400

    codes = generate_backup_codes()
    current_user.backup_codes = hash_codes(codes)
    await current_user.save(["backup_codes"])

    await capture_event(current_user.username, "2fa_backup_regenerated")

    return jsonify(
        {
            "status": "success",
            "message": "New backup codes have been generated.",
            "result": {"backup_codes": codes},
        }
    ), 200


@auth_bp.route("/2fa/step-up/send", methods=["POST"])
@rate_limit(
    SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD, skip_function=_skip_safe_methods
)
@login_required
@check_confirmed
async def _2fa_step_up_send() -> tuple[Response, int]:
    """
    Emails a one-time code to confirm a sensitive action (email 2FA method only).
    """
    if current_user.two_factor_method != "email":
        return jsonify(
            {"status": "error", "error": "No email code is required."}
        ), 400

    code = f"{secrets.randbelow(1_000_000):06d}"
    await cache.store_data(
        f"2fa:stepup:{current_user.username}", LOGIN_2FA_TTL_MINUTES, code
    )

    html = await render_template(
        "email/step_up_code.html", code=code, ttl_minutes=LOGIN_2FA_TTL_MINUTES
    )
    await send_email(current_user.email, "Your NerVault Confirmation Code", html)

    return jsonify(
        {"status": "success", "message": "A code has been sent to your email."}
    ), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
async def _me() -> tuple[Response, int]:
    """
    Returns the currently authenticated user.
    """
    return jsonify({"status": "success", "result": _user_dict(current_user)}), 200
