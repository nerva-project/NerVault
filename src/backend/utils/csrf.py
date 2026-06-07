from typing import Optional

from secrets import token_urlsafe, compare_digest

from quart import Quart, Response, jsonify, request
from quart.typing import ResponseReturnValue

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def init_csrf(app: Quart) -> None:
    """
    Registers double-submit CSRF protection.

    A readable CSRF cookie is issued on responses that lack one; the SPA echoes
    its value in the X-CSRF-Token header on every state-changing request, which
    the server compares against the cookie.

    Args:
        app (Quart): The Quart application instance.
    """
    secure: bool = app.config.get("QUART_AUTH_COOKIE_SECURE", True)
    samesite: str = app.config.get("QUART_AUTH_COOKIE_SAMESITE", "Lax")

    @app.before_request
    async def _validate_csrf() -> Optional[ResponseReturnValue]:
        if request.method in SAFE_METHODS:
            return None

        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)

        if (
            not cookie_token
            or not header_token
            or not compare_digest(cookie_token, header_token)
        ):
            return jsonify(
                {"status": "error", "error": "CSRF validation failed"}
            ), 403

        return None

    @app.after_request
    async def _set_csrf_cookie(response: Response) -> Response:
        if not request.cookies.get(CSRF_COOKIE_NAME):
            response.set_cookie(
                CSRF_COOKIE_NAME,
                token_urlsafe(32),
                secure=secure,
                httponly=False,
                samesite=samesite,
            )

        return response
