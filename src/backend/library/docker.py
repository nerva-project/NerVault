from typing import Optional, cast

import sys
import asyncio
from os.path import expanduser
from secrets import token_hex
from datetime import UTC, datetime, timedelta

from docker import APIClient, from_env
from docker.errors import APIError, NotFound, NullResource, DockerException
from docker.models.volumes import Volume
from docker.models.containers import Container

from backend import config
from backend.utils.models import User
from backend.library.validation import validate_seed, validate_username


class Docker:
    """
    A class to manage Docker operations for handling wallets and containers.
    """

    def __init__(self) -> None:
        """
        Initializes the Docker client and sets necessary configurations.
        """
        try:
            self.client = from_env()
        except DockerException:
            print("Failed to connect to Docker. Exiting...")
            sys.exit(1)

        self.nerva_docker_img: str = config.NERVA_DOCKER_IMAGE
        self.wallet_dir: str = expanduser(config.WALLET_DIR)
        self.listen_port: int = 8888

    async def create_wallet(self, username: str, seed: Optional[str] = None) -> str:
        """
        Creates a new wallet for a user.

        Args:
            username (str): The username of the user.
            seed (Optional[str], optional): The mnemonic seed for the wallet. Defaults to None.

        Returns:
            str: The short ID of the wallet initialization container.
        """
        from backend.factory import daemon

        username = validate_username(username)

        u = User(username=username)
        await u.load()
        volume_name = self.get_user_volume(u.username)
        wallet_password = token_hex(16)
        u.wallet_password = wallet_password
        await u.save()

        daemon_address = (
            f"{'https' if config.DAEMON_SSL else 'http'}://"
            f"{config.DAEMON_HOST}:{config.DAEMON_PORT}"
        )
        daemon_login = f"{config.DAEMON_USERNAME}:{config.DAEMON_PASSWORD}"

        entrypoint: list[str]
        if seed:
            seed = validate_seed(seed)
            script = (
                'yes "" | nerva-wallet-cli '
                "--restore-deterministic-wallet "
                '--generate-new-wallet "/wallet/$1.wallet" '
                "--restore-height 0 "
                '--password "$2" '
                f'--daemon-address "{daemon_address}" '
                f'--daemon-login "{daemon_login}" '
                "--trusted-daemon "
                '--electrum-seed "$3" '
                '--log-file "/wallet/$1-init.log" '
                "--command refresh"
            )
            entrypoint = [
                "sh",
                "-c",
                script,
                "sh",
                u.username,
                wallet_password,
                seed,
            ]
        else:
            entrypoint = [
                "nerva-wallet-cli",
                "--generate-new-wallet",
                f"/wallet/{u.username}.wallet",
                "--restore-height",
                str((await daemon.get_info())["height"]),
                "--password",
                wallet_password,
                "--mnemonic-language",
                "English",
                "--daemon-address",
                daemon_address,
                "--daemon-login",
                daemon_login,
                "--trusted-daemon",
                "--log-file",
                f"/wallet/{u.username}-init.log",
                "--command",
                "version",
            ]

        if not self.volume_exists(volume_name):
            self.client.volumes.create(name=volume_name, driver="local")
        container = self.client.containers.run(
            self.nerva_docker_img,
            entrypoint=entrypoint,
            auto_remove=True,
            name=f"init_wallet_{u.username}",
            remove=True,
            detach=True,
            volumes={volume_name: {"bind": "/wallet", "mode": "rw"}},
        )
        return container.short_id

    async def start_wallet(self, username: str) -> str:
        """
        Starts the wallet RPC container for a user.

        Args:
            username (str): The username of the user.

        Returns:
            str: The short ID of the wallet RPC container.
        """
        username = validate_username(username)

        u = User(username=username)
        await u.load()

        if not u.wallet_password:
            raise ValueError("Wallet password is not set for this user")

        wallet_password = u.wallet_password
        container_name = f"rpc_wallet_{u.username}"
        volume_name = self.get_user_volume(u.username)
        daemon_address = (
            f"{'https' if config.DAEMON_SSL else 'http'}://"
            f"{config.DAEMON_HOST}:{config.DAEMON_PORT}"
        )
        entrypoint: list[str] = [
            "nerva-wallet-rpc",
            "--non-interactive",
            "--rpc-bind-port",
            str(self.listen_port),
            "--rpc-bind-ip",
            "0.0.0.0",
            "--confirm-external-bind",
            "--wallet-file",
            f"/wallet/{u.username}.wallet",
            "--rpc-login",
            f"{u.username}:{wallet_password}",
            "--password",
            wallet_password,
            "--daemon-address",
            daemon_address,
            "--daemon-login",
            f"{config.DAEMON_USERNAME}:{config.DAEMON_PASSWORD}",
            "--trusted-daemon",
            "--log-file",
            f"/wallet/{u.username}-rpc.log",
        ]
        try:
            container = self.client.containers.run(
                self.nerva_docker_img,
                entrypoint=entrypoint,
                auto_remove=True,
                name=container_name,
                remove=True,
                detach=True,
                volumes={volume_name: {"bind": "/wallet", "mode": "rw"}},
                ports={
                    f"{self.listen_port}/tcp": cast(
                        "tuple[str, int]", ("127.0.0.1", None)
                    )
                },
            )
            return container.short_id

        except APIError as e:
            if str(e).startswith("409"):
                container = self.client.containers.get(container_name)
                return container.short_id
            raise

    def get_port(self, container_id: str) -> int:
        """
        Fetches the host port mapped to a given container.

        Args:
            container_id (str): The ID of the container.

        Returns:
            int: The mapped host port.
        """
        client = APIClient()
        port_data = client.port(container_id, self.listen_port)
        host_port = port_data[0]["HostPort"]
        return int(host_port)

    def container_exists(self, container_id: str) -> bool:
        """
        Checks if a container exists.

        Args:
            container_id (str): The ID of the container.

        Returns:
            bool: True if the container exists, False otherwise.
        """
        try:
            self.client.containers.get(container_id)
            return True
        except (NotFound, NullResource):
            return False

    def volume_exists(self, volume_id: str) -> bool:
        """
        Checks if a volume exists.

        Args:
            volume_id (str): The ID of the volume.

        Returns:
            bool: True if the volume exists, False otherwise.
        """
        try:
            self.client.volumes.get(volume_id)
            return True
        except (NotFound, NullResource):
            return False

    def stop_container(self, container_id: Optional[str]) -> None:
        """
        Stops a running container.

        Args:
            container_id (str): The ID of the container.
        """
        if container_id and self.container_exists(container_id):
            c: Container = self.client.containers.get(container_id)
            c.stop()

    def delete_wallet_data(self, user_id: str) -> bool:
        """
        Deletes wallet data associated with a user.

        Args:
            user_id (str): The user ID.

        Returns:
            bool: True if the operation is successful, False otherwise.
        """
        volume_name = self.get_user_volume(user_id)
        volume: Volume = self.client.volumes.get(volume_name)
        volume.remove()
        return True

    @staticmethod
    def get_user_volume(user_id: str) -> str:
        """
        Generates the volume name for a user.

        Args:
            user_id (str): The user ID.

        Returns:
            str: The volume name.
        """
        volume_name = f"user_{user_id}_wallet"
        return volume_name

    async def cleanup(self) -> None:
        """
        Cleans up expired wallet containers and stale data for all users.
        """
        users = await User.get_all()
        async for u in users:
            u = User(username=u["username"])
            await u.load()

            if u.wallet_started_at:
                session_lifetime: int = config.PERMANENT_SESSION_LIFETIME
                wallet_started: datetime = u.wallet_started_at
                if wallet_started.tzinfo is None:
                    wallet_started = wallet_started.replace(tzinfo=UTC)
                expiration_time: datetime = wallet_started + timedelta(
                    seconds=session_lifetime
                )
                now: datetime = datetime.now(UTC)
                time_diff: timedelta = expiration_time - now
                if time_diff.total_seconds() <= 0:
                    print(f"Found expired container for {u}. Killing...")
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.stop_container, u.wallet_container
                    )
                    await u.clear_wallet_data()
                    continue

            if u.wallet_container and not self.container_exists(u.wallet_container):
                print(f"Found stale data for {u}. Deleting...")
                await u.clear_wallet_data()
