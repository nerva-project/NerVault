from __future__ import annotations

from typing import Union

from itsdangerous import BadSignature, URLSafeTimedSerializer

import config


def generate_token(email_id: str) -> str:
    """
    Generates a time-sensitive token for the given email ID.

    Args:
        email_id (str): The email address for which the token will be generated.

    Returns:
        str: The generated token.
    """
    serializer = URLSafeTimedSerializer(config.SECRET_KEY)
    return serializer.dumps(email_id, salt=config.PASSWORD_SALT)


def validate_token(token: str, expiration: int = 3600) -> Union[bool, str]:
    """
    Validates the given token and returns the email ID if valid, otherwise returns False.

    Args:
        token (str): The token to be validated.
        expiration (int): The token expiration time in seconds (default is 3600 seconds).

    Returns:
        Optional[str]: The email ID if the token is valid, otherwise False.
    """
    serializer = URLSafeTimedSerializer(config.SECRET_KEY)

    try:
        email_id = serializer.loads(
            token, salt=config.PASSWORD_SALT, max_age=expiration
        )

    except BadSignature:
        return False

    return email_id
