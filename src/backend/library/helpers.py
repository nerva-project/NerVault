from __future__ import annotations

from typing import TYPE_CHECKING

import hmac

from backend.factory import cache
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
    authenticator code, an unused backup code, or the emailed step-up code for
    their method. A consumed backup code triggers the same notification as a
    backup-code login.

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

        if pyotp.TOTP(user.totp_secret).verify(code, valid_window=1):
            return True

        from backend.utils.twofa import verify_and_consume

        matched, remaining = verify_and_consume(code, user.backup_codes)
        if not matched:
            return False

        user.backup_codes = remaining
        await user.save()

        from quart import render_template

        from backend.utils.mail import send_email

        html = await render_template(
            "email/backup_code_used.html", remaining=len(user.backup_codes)
        )
        await send_email(user.email, "Backup Code Used", html)
        await capture_event(user.username, "backup_code_used")
        return True

    if method == "email":
        stored = await cache.get_data(f"2fa:stepup:{user.username}")
        if stored and hmac.compare_digest(stored, code):
            await cache.redis.delete(f"2fa:stepup:{user.username}")
            return True

    return False
