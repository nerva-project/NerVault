from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from datetime import datetime

from quart_auth import AuthUser

from utils.factory import db

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorCursor, AsyncIOMotorCollection


class User(AuthUser):
    collection: AsyncIOMotorCollection = db.get_collection("users")

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
        self.register_date: datetime = datetime.now()
        self.confirmed: bool = False
        self.confirmed_at: datetime = datetime.fromtimestamp(0)
        self.wallet_password: str = ""
        self.wallet_created: bool = False
        self.wallet_connected: bool = False
        self.wallet_port: Optional[int] = 0
        self.wallet_container: str = ""
        self.wallet_started_at: datetime = datetime.fromtimestamp(0)

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

    async def save(self) -> None:
        """
        Saves the user data to the database. If the user does not exist, it is created.
        """
        await User.collection.update_one(
            {"username": self.username},
            {
                "$set": {
                    "email": self.email,
                    "password": self.password,
                    "register_date": self.register_date,
                    "confirmed": self.confirmed,
                    "confirmed_at": self.confirmed_at,
                    "wallet_password": self.wallet_password,
                    "wallet_created": self.wallet_created,
                    "wallet_connected": self.wallet_connected,
                    "wallet_port": self.wallet_port,
                    "wallet_container": self.wallet_container,
                    "wallet_started_at": self.wallet_started_at,
                }
            },
            upsert=True,
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

        self.email = user["email"]
        self.password = user["password"]
        self.register_date = user["register_date"]
        self.confirmed = user["confirmed"]
        self.confirmed_at = user["confirmed_at"]
        self.wallet_password = user["wallet_password"]
        self.wallet_created = user["wallet_created"]
        self.wallet_connected = user["wallet_connected"]
        self.wallet_port = user["wallet_port"]
        self.wallet_container = user["wallet_container"]
        self.wallet_started_at = user["wallet_started_at"]

        return True

    async def clear_wallet_data(
        self, reset_password: bool = False, reset_wallet: bool = False
    ) -> None:
        """
        Clears the wallet data of the user. Optionally resets the wallet password or wallet creation state.

        Args:
            reset_password (bool): If True, resets the wallet password.
            reset_wallet (bool): If True, resets the wallet creation state.
        """
        self.wallet_connected = False
        self.wallet_port = None
        self.wallet_container = None
        self.wallet_started_at = None
        if reset_password:
            self.wallet_password = None
        if reset_wallet:
            self.wallet_created = False

        await User.collection.update_one(
            {"username": self.username},
            {
                "$set": {
                    "wallet_connected": self.wallet_connected,
                    "wallet_port": self.wallet_port,
                    "wallet_container": self.wallet_container,
                    "wallet_started_at": self.wallet_started_at,
                    "wallet_password": self.wallet_password,
                    "wallet_created": self.wallet_created,
                }
            },
        )

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
    async def get_all() -> AsyncIOMotorCursor:
        """
        Retrieves all users from the database.

        Returns:
            Any: The cursor for the users collection.
        """
        return User.collection.find()


class Event:
    collection: AsyncIOMotorCollection = db.get_collection("events")

    def __init__(self, category: str, user: str) -> None:
        """
        Initializes an Event instance.

        Args:
            category (str): The event category.
            user (str): The user associated with the event.
        """
        self.category: str = category
        self.user: str = user
        self.date: datetime = datetime.today()

    async def save(self) -> None:
        """
        Saves the event data to the database.
        """
        await Event.collection.insert_one(
            {"category": self.category, "user": self.user, "date": self.date}
        )


class Config:
    collection: AsyncIOMotorCollection = db.get_collection("config")

    def __init__(self, key: str, value: Optional[bool] = None) -> None:
        """
        Initializes a Config instance.

        Args:
            key (str): The configuration key.
            value (Optional[bool]): The configuration value (default is None).
        """
        self.key: str = key
        self.value: Optional[bool] = value

    async def save(self) -> None:
        """
        Saves the configuration to the database.
        """
        await Config.collection.update_one(
            {"key": self.key}, {"key": self.key, "value": self.value}, upsert=True
        )

    async def delete(self) -> None:
        """
        Deletes the configuration from the database.
        """
        await Config.collection.delete_one({"key": self.key})

    async def load(self) -> None:
        """
        Loads the configuration from the database.

        Raises:
            AttributeError: If the config key is not found.
        """
        rec = await Config.collection.find_one({"key": self.key})

        if not rec:
            raise AttributeError(f"Config key '{self.key}' not found")

        self.value = rec["value"]
