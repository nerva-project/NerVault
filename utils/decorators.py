from __future__ import annotations

from typing import Any, Callable

from functools import wraps

from quart import flash, url_for, redirect, current_app
from quart_auth import current_user


def check_confirmed(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    A decorator that checks if the current user is confirmed. If the user is not confirmed,
    they are redirected to the unconfirmed page with a warning flash message.

    Args:
        func (Callable[..., Any]): The view function to decorate.

    Returns:
        Callable[..., Any]: The wrapped function that checks confirmation status.

    If the user is not confirmed, they will be redirected. If confirmed,
    the original function will be called.
    """

    @wraps(func)
    async def wrapper(*args: tuple, **kwargs: dict) -> Any:
        if current_user.confirmed is False:
            await flash("Please confirm your account first.", "warning")
            return redirect(url_for("auth._unconfirmed"))
        else:
            return await current_app.ensure_async(func)(*args, **kwargs)

    return wrapper
