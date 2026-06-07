from typing import Any, Callable

from functools import wraps

from quart import jsonify, current_app
from quart_auth import current_user as _current_user

from backend.utils.models import User

current_user: User = _current_user  # type: ignore[assignment]


def check_confirmed(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    A decorator that rejects requests from users who have not confirmed their
    account with a 403 response.

    Args:
        func (Callable[..., Any]): The view function to decorate.

    Returns:
        Callable[..., Any]: The wrapped function that checks confirmation status.
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if current_user.confirmed is False:
            return jsonify(
                {"status": "error", "error": "Please confirm your account first."}
            ), 403

        return await current_app.ensure_async(func)(*args, **kwargs)

    return wrapper
