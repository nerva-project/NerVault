from __future__ import annotations

from typing import TYPE_CHECKING

import hmac

from backend.factory import cache, bcrypt
from backend.utils.models import Event

if TYPE_CHECKING:
    from backend.utils.models import User


async def capture_event(username: str, category: str) -> None:
    """
    Captures an event for a given username and category.
    """
    event: Event = Event(user=username, category=category)
    await event.save()


async def on_maintenance() -> bool:
    """
    Checks if the system is in maintenance mode.

    Returns:
        bool: True if in maintenance mode, False otherwise.
    """
    return bool(await cache.redis.exists("maintenance"))


async def set_maintenance(enable: bool = False) -> None:
    """
    Enables or disables maintenance mode.

    Args:
        enable (bool): Whether to enable maintenance mode. Default is False.
    """
    if enable:
        await cache.redis.set("maintenance", 1)
    else:
        await cache.redis.delete("maintenance")


async def verify_2fa_code(user: User, code: str) -> bool:
    """
    Verifies a step-up two-factor code for a sensitive action.

    Returns True if the user has no 2FA enabled, or the supplied code is a valid
    authenticator code (totp) or the emailed step-up code (email). Backup codes
    are deliberately NOT accepted here: they are a login-recovery mechanism, not
    a substitute factor for in-session sensitive actions.

    Args:
        user (User): The authenticated user performing the action.
        code (str): The code supplied by the client (ignored when 2FA is off).

    Returns:
        bool: True if the step-up check passes, else False.
    """
    method = user.two_factor_method
    if method is None:
        return True

    code = code.strip()
    if not code:
        return False

    if method == "totp" and user.totp_secret:
        import pyotp

        return pyotp.TOTP(user.totp_secret).verify(code, valid_window=1)

    if method == "email":
        stored = await cache.get_data(f"2fa:stepup:{user.username}")
        if stored and hmac.compare_digest(stored, code):
            await cache.redis.delete(f"2fa:stepup:{user.username}")
            return True

    return False


async def verify_step_up(user: User, code: str, password: str) -> bool:
    """
    Confirms a sensitive action. When the user has 2FA enabled a valid step-up
    code is required; otherwise the account password is required — so a user
    without 2FA still re-authenticates instead of acting on the session alone.

    Args:
        user (User): The authenticated user performing the action.
        code (str): The step-up code (used when 2FA is enabled).
        password (str): The account password (used when 2FA is disabled).

    Returns:
        bool: True if the step-up check passes, else False.
    """
    if user.two_factor_method is not None:
        return await verify_2fa_code(user, code)

    return bool(password) and bcrypt.check_password_hash(user.password, password)
