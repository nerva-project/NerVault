import secrets

# Unambiguous alphabet (no 0/O/1/I) so backup codes are easy to read and type.
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_CODE_COUNT = 10
_GROUP = 4


def _one_code() -> str:
    raw = "".join(secrets.choice(_ALPHABET) for _ in range(_GROUP * 2))
    return f"{raw[:_GROUP]}-{raw[_GROUP:]}"


def generate_backup_codes(count: int = _CODE_COUNT) -> list[str]:
    """Generates a list of human-typeable one-time backup codes (e.g. AB3K-7QX9)."""
    return [_one_code() for _ in range(count)]


def normalize_code(code: str) -> str:
    """Strips separators/whitespace and upper-cases a user-entered code."""
    return code.strip().upper().replace(" ", "").replace("-", "")


def hash_codes(codes: list[str]) -> list[str]:
    """Returns bcrypt hashes of the given plaintext backup codes."""
    from backend.factory import bcrypt

    return [
        bcrypt.generate_password_hash(normalize_code(c)).decode("utf8")
        for c in codes
    ]


def verify_and_consume(code: str, hashes: list[str]) -> tuple[bool, list[str]]:
    """
    Checks a backup code against the stored hashes.

    Returns:
        tuple[bool, list[str]]: (matched, remaining_hashes). On a match the used
        hash is removed so each backup code works only once.
    """
    from backend.factory import bcrypt

    candidate = normalize_code(code)
    if not candidate:
        return False, hashes

    for h in hashes:
        if bcrypt.check_password_hash(h, candidate):
            return True, [x for x in hashes if x != h]

    return False, hashes
