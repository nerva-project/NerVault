from __future__ import annotations

from typing import Optional

import sys
from time import sleep
from os.path import expanduser
from secrets import token_hex
from datetime import UTC, datetime, timedelta

from docker import APIClient, from_env
from docker.errors import APIError, NotFound, NullResource, DockerException
from docker.models.volumes import Volume
from docker.models.containers import Container

from utils.models import User

import config


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
        from utils.factory import daemon

        u = User(username=username)
        await u.load()
        volume_name = self.get_user_volume(u.username)
        u.wallet_password = token_hex(8)
        await u.save()

        if seed:
            command = f"""sh -c "yes '' | nerva-wallet-cli \
                    --restore-deterministic-wallet \
                    --generate-new-wallet /wallet/{u.username}.wallet \
                    --restore-height 0 \
                    --password {u.wallet_password} \
                    --daemon-address {'https' if config.DAEMON_SSL else 'http'}://{config.DAEMON_HOST}:{config.DAEMON_PORT} \
                    --daemon-login {config.DAEMON_USERNAME}:{config.DAEMON_PASSWORD} \
                    --trusted-daemon \
                    --electrum-seed '{seed}' \
                    --log-file /wallet/{u.username}-init.log \
                    --command refresh"
                    """
        else:
            command = f"""nerva-wallet-cli \
                    --generate-new-wallet /wallet/{u.username}.wallet \
                    --restore-height {(await daemon.get_info())["height"]} \
                    --password {u.wallet_password} \
                    --mnemonic-language English \
                    --daemon-address {'https' if config.DAEMON_SSL else 'http'}://{config.DAEMON_HOST}:{config.DAEMON_PORT} \
                    --daemon-login {config.DAEMON_USERNAME}:{config.DAEMON_PASSWORD} \
                    --trusted-daemon \
                    --log-file /wallet/{u.username}-init.log \
                    --command version
                    """

        if not self.volume_exists(volume_name):
            self.client.volumes.create(name=volume_name, driver="local")
        container = self.client.containers.run(
            self.nerva_docker_img,
            entrypoint=command,
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
        u = User(username=username)
        await u.load()

        container_name = f"rpc_wallet_{u.username}"
        volume_name = self.get_user_volume(u.username)
        command = f"""nerva-wallet-rpc \
        --non-interactive \
        --rpc-bind-port {self.listen_port} \
        --rpc-bind-ip 0.0.0.0 \
        --confirm-external-bind \
        --wallet-file /wallet/{u.username}.wallet \
        --rpc-login {u.username}:{u.wallet_password} \
        --password {u.wallet_password} \
        --daemon-address {'https' if config.DAEMON_SSL else 'http'}://{config.DAEMON_HOST}:{config.DAEMON_PORT} \
        --daemon-login {config.DAEMON_USERNAME}:{config.DAEMON_PASSWORD} \
        --trusted-daemon \
        --log-file /wallet/{u.username}-rpc.log
        """
        try:
            container = self.client.containers.run(
                self.nerva_docker_img,
                entrypoint=command,
                auto_remove=True,
                name=container_name,
                remove=True,
                detach=True,
                volumes={volume_name: {"bind": "/wallet", "mode": "rw"}},
                ports={f"{self.listen_port}/tcp": None},
            )
            return container.short_id

        except APIError as e:
            if str(e).startswith("409"):
                container = self.client.containers.get(container_name)
                return container.short_id

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

    def stop_container(self, container_id: str) -> None:
        """
        Stops a running container.

        Args:
            container_id (str): The ID of the container.
        """
        if self.container_exists(container_id):
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
        try:
            volume.remove()
            return True
        except Exception as e:
            raise e

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
                expiration_time: datetime = u.wallet_started_at + timedelta(
                    seconds=session_lifetime
                )
                now: datetime = datetime.now(UTC)
                time_diff: timedelta = expiration_time - now
                if time_diff.total_seconds() <= 0:
                    print(f"Found expired container for {u}. Killing...")
                    self.stop_container(u.wallet_container)
                    sleep(2)

            if u.wallet_container and not self.container_exists(u.wallet_container):
                print(f"Found stale data for {u}. Deleting...")
                await u.clear_wallet_data()
