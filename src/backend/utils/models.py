from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from datetime import UTC, datetime

from quart_auth import AuthUser

from backend.factory import db

if TYPE_CHECKING:
    from pymongo.asynchronous.cursor import AsyncCursor
    from pymongo.asynchronous.collection import AsyncCollection


class User(AuthUser):
    collection: AsyncCollection[Any] = db.get_collection("users")

    # The fields save() persists. A partial save(fields=[...]) writes only a
    # subset so a stale or separately-loaded instance can't overwrite fields it
    # does not own.
    PERSISTED_FIELDS: tuple[str, ...] = (
        "email",
        "password",
        "register_date",
        "confirmed",
        "confirmed_at",
        "email_2fa",
        "totp_secret",
        "totp_enabled",
        "backup_codes",
        "wallet_password",
        "wallet_created",
        "wallet_connected",
        "wallet_port",
        "wallet_container",
        "wallet_started_at",
    )

    def __init__(self, username: str) -> None:
        """
        Initializes a User instance with the given username.

        Args:
            username (str): The username of the user.
        """
        super().__init__(auth_id=username)

        self.username: str = username
        self.email: str = ""
        self.password: str = ""
        self.register_date: datetime = datetime.now(UTC)
        self.confirmed: bool = False
        self.confirmed_at: datetime = datetime.fromtimestamp(0, UTC)
        self.email_2fa: bool = False
        self.totp_secret: Optional[str] = None
        self.totp_enabled: bool = False
        self.backup_codes: list[str] = []
        self.wallet_password: Optional[str] = ""
        self.wallet_created: bool = False
        self.wallet_connected: bool = False
        self.wallet_port: Optional[int] = 0
        self.wallet_container: Optional[str] = None
        self.wallet_started_at: Optional[datetime] = datetime.fromtimestamp(0, UTC)

    def __repr__(self) -> str:
        """
        Returns the string representation of the User object (the username).

        Returns:
            str: The username of the user.
        """
        return self.username

    @property
    def is_active(self) -> bool:
        """
        Returns whether the user's account is active (confirmed).

        Returns:
            bool: True if the user is confirmed, else False.
        """
        return self.confirmed

    @property
    def two_factor_method(self) -> Optional[str]:
        """
        Returns the active two-factor method, or None if 2FA is disabled. The
        authenticator app (TOTP) supersedes the email method when both are set.

        Returns:
            Optional[str]: "totp", "email", or None.
        """
        if self.totp_enabled:
            return "totp"
        if self.email_2fa:
            return "email"
        return None

    async def save(self, fields: Optional[list[str]] = None) -> None:
        """
        Saves the user data to the database.

        Args:
            fields (Optional[list[str]]): When provided, only these fields are
                written (a partial update), so a stale or separately-loaded
                instance cannot overwrite fields it does not own. When None, the
                whole document is written, creating it if missing (upsert).
        """
        if fields is not None:
            unknown = set(fields) - set(self.PERSISTED_FIELDS)
            if unknown:
                raise ValueError(f"Unknown user fields: {sorted(unknown)}")

        names = list(self.PERSISTED_FIELDS) if fields is None else fields
        await User.collection.update_one(
            {"username": self.username},
            {"$set": {name: getattr(self, name) for name in names}},
            upsert=fields is None,
        )

    async def load(self) -> bool:
        """
        Loads the user data from the database.

        Returns:
            bool: True if user data is successfully loaded.

        Raises:
            ValueError: If the user is not found in the database.
        """
        user = await User.collection.find_one({"username": self.username})

        if not user:
            raise ValueError("User not found")

        self.email = user.get("email", "")
        self.password = user.get("password", "")
        self.register_date = user.get("register_date", self.register_date)
        self.confirmed = user.get("confirmed", False)
        self.confirmed_at = user.get("confirmed_at", self.confirmed_at)
        self.email_2fa = user.get("email_2fa", False)
        self.totp_secret = user.get("totp_secret")
        self.totp_enabled = user.get("totp_enabled", False)
        self.backup_codes = user.get("backup_codes", [])
        self.wallet_password = user.get("wallet_password", "")
        self.wallet_created = user.get("wallet_created", False)
        self.wallet_connected = user.get("wallet_connected", False)
        self.wallet_port = user.get("wallet_port", 0)
        self.wallet_container = user.get("wallet_container")
        self.wallet_started_at = user.get(
            "wallet_started_at", self.wallet_started_at
        )

        return True

    async def clear_wallet_data(
        self,
        reset_password: bool = False,
        reset_wallet: bool = False,
        expected_container: Optional[str] = None,
    ) -> None:
        """
        Clears the user's live wallet session. Only the fields actually being
        cleared are written, so unrelated data — including the wallet password
        unless reset_password is set — is never disturbed.

        Args:
            reset_password (bool): Also clear the stored wallet RPC password.
            reset_wallet (bool): Also mark the wallet as not yet created.
            expected_container (Optional[str]): When set, the update only applies
                if the stored wallet_container still matches it, so a concurrent
                writer (e.g. the reaper) can't wipe a session another request
                just re-established.
        """
        self.wallet_connected = False
        self.wallet_port = None
        self.wallet_container = None
        self.wallet_started_at = None
        update: dict[str, Any] = {
            "wallet_connected": False,
            "wallet_port": None,
            "wallet_container": None,
            "wallet_started_at": None,
        }
        if reset_password:
            self.wallet_password = None
            update["wallet_password"] = None
        if reset_wallet:
            self.wallet_created = False
            update["wallet_created"] = False

        query: dict[str, Any] = {"username": self.username}
        if expected_container is not None:
            query["wallet_container"] = expected_container

        await User.collection.update_one(query, {"$set": update})

    @staticmethod
    async def get_by_email(email: str) -> User:
        """
        Retrieves a User instance by email.

        Args:
            email (str): The email address of the user.

        Returns:
            User: A User instance.

        Raises:
            ValueError: If no user is found with the given email.
        """
        user = await User.collection.find_one({"email": email})

        if not user:
            raise ValueError("User not found")

        u = User(user["username"])
        await u.load()
        return u

    @staticmethod
    async def get_all() -> AsyncCursor[Any]:
        """
        Retrieves all users from the database.

        Returns:
            Any: The cursor for the users collection.
        """
        return User.collection.find()


class Event:
    collection: AsyncCollection[Any] = db.get_collection("events")

    def __init__(self, category: str, user: str) -> None:
        """
        Initializes an Event instance.

        Args:
            category (str): The event category.
            user (str): The user associated with the event.
        """
        self.category: str = category
        self.user: str = user
        self.date: datetime = datetime.now(UTC)

    async def save(self) -> None:
        """
        Saves the event data to the database.
        """
        await Event.collection.insert_one(
            {"category": self.category, "user": self.user, "date": self.date}
        )
