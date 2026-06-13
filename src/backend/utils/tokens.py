from typing import Any, Optional

import hashlib

from itsdangerous import BadSignature, URLSafeTimedSerializer

from backend import config

CONFIRM_SALT = "email-confirmation"
RESET_SALT = "password-reset"
EMAIL_CHANGE_SALT = "email-change"
LOGIN_2FA_SALT = "login-2fa"


def generate_token(payload: Any, salt: str) -> str:
    """
    Generates a time-sensitive, namespaced token for the given payload.

    Args:
        payload (Any): The value to sign (e.g. an email, or [email, fingerprint]).
        salt (str): Namespace salt — confirmation and reset tokens use different
            salts so a token minted for one purpose cannot be used for the other.

    Returns:
        str: The generated token.
    """
    serializer = URLSafeTimedSerializer(config.SECRET_KEY)
    return serializer.dumps(payload, salt=f"{config.PASSWORD_SALT}:{salt}")


def validate_token(token: str, salt: str, expiration: int = 3600) -> Optional[Any]:
    """
    Validates a token and returns its payload, or None if invalid/expired.

    Args:
        token (str): The token to validate.
        salt (str): The namespace salt the token was generated with.
        expiration (int): Maximum token age in seconds (default 3600).

    Returns:
        Optional[Any]: The signed payload if valid, otherwise None.
    """
    serializer = URLSafeTimedSerializer(config.SECRET_KEY)

    try:
        return serializer.loads(
            token, salt=f"{config.PASSWORD_SALT}:{salt}", max_age=expiration
        )
    except BadSignature:
        return None


def password_fingerprint(password_hash: str) -> str:
    """
    Stable fingerprint of a password hash that changes whenever the password
    does. Binding a reset token to this makes the token single-use: once the
    password is changed the fingerprint no longer matches, so the spent (or any
    older) reset link is rejected.
    """
    digest = hashlib.sha256(f"{config.SECRET_KEY}:{password_hash}".encode())
    return digest.hexdigest()[:16]
