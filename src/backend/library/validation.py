from re import compile as re_compile

USERNAME_RE = re_compile(r"^[a-zA-Z0-9_]{3,32}$")

SEED_WORD_RE = re_compile(r"^[a-z]+$")
SEED_WORD_COUNT = 25


def is_valid_username(username: str) -> bool:
    """Return True if the username matches the allowed charset."""
    return isinstance(username, str) and bool(USERNAME_RE.match(username))


def validate_username(username: str) -> str:
    """
    Validate a username against the allowed charset.

    Args:
        username (str): The username to validate.

    Returns:
        str: The validated username, unchanged.

    Raises:
        ValueError: If the username is not a string or fails the charset check.
    """
    if not is_valid_username(username):
        raise ValueError("Invalid username")

    return username


def validate_seed(seed: str) -> str:
    """
    Validate a 25-word Nerva mnemonic seed phrase.

    Args:
        seed (str): The whitespace-separated mnemonic seed phrase.

    Returns:
        str: The seed normalised to single-space-separated words.

    Raises:
        ValueError: If the seed is not a string, has the wrong word count, or
            contains anything other than lowercase alphabetic words.
    """
    if not isinstance(seed, str):
        raise ValueError("Invalid seed phrase")

    words = seed.split()

    if len(words) != SEED_WORD_COUNT or not all(
        SEED_WORD_RE.match(word) for word in words
    ):
        raise ValueError("Invalid seed phrase")

    return " ".join(words)
