from __future__ import annotations

from typing import Any, Dict, Tuple, Optional

from httpx import ReadError, ConnectError, RemoteProtocolError
from nerva.wallet import Wallet as WalletRPC


class Wallet:
    """
    A wrapper around the Nerva Wallet RPC client for managing wallet operations.

    This class provides a high-level interface to interact with the wallet,
    including retrieving keys, managing balances, transferring funds, and
    interacting with wallet-related blockchain operations.

    Attributes:
        rpc (WalletRPC): An instance of the WalletRPC client to communicate with the wallet.
    """

    def __init__(self, **kwargs: Any) -> None:
        self.rpc: WalletRPC = WalletRPC(**kwargs)

    @property
    async def connected(self) -> bool:
        """
        Checks if the wallet is connected.

        Returns:
            bool: True if connected, False otherwise.
        """
        try:
            if "height" in (await self.height())["result"]:
                return True
            return False

        except (ConnectError, ReadError, RemoteProtocolError):
            return False

    async def height(self) -> Dict[str, Any]:
        """
        Gets the current blockchain height.

        Returns:
            Dict[str, Any]: The height information from the wallet RPC.
        """
        return await self.rpc.get_height()

    async def public_spend_key(self) -> str:
        """
        Fetches the public spend key.

        Returns:
            str: The public spend key.
        """
        return (await self.rpc.query_key(key_type="public_spend_key"))["result"][
            "public_spend_key"
        ]

    async def secret_spend_key(self) -> str:
        """
        Fetches the secret spend key.

        Returns:
            str: The secret spend key.
        """
        return (await self.rpc.query_key(key_type="secret_spend_key"))["result"][
            "private_spend_key"
        ]

    async def public_view_key(self) -> str:
        """
        Fetches the public view key.

        Returns:
            str: The public view key.
        """
        return (await self.rpc.query_key(key_type="public_view_key"))["result"][
            "public_view_key"
        ]

    async def secret_view_key(self) -> str:
        """
        Fetches the secret view key.

        Returns:
            str: The secret view key.
        """
        return (await self.rpc.query_key(key_type="secret_view_key"))["result"][
            "private_view_key"
        ]

    async def seed(self) -> str:
        """
        Fetches the wallet mnemonic seed.

        Returns:
            str: The wallet mnemonic seed.
        """
        return (await self.rpc.query_key(key_type="mnemonic"))["result"]["mnemonic"]

    async def new_address(
        self, account_index: int = 0, label: Optional[str] = None
    ) -> Tuple[int, str]:
        """
        Creates a new address in the wallet.

        Args:
            account_index (int, optional): The account index. Defaults to 0.
            label (Optional[str], optional): The address label. Defaults to None.

        Returns:
            Tuple[int, str]: The address index and the new address.
        """
        res = (
            await self.rpc.create_address(account_index=account_index, label=label)
        )["result"]
        return res["address_index"], res["address"]

    async def integrated_address(self, address: str, payment_id: str) -> str:
        """
        Creates an integrated address using the provided payment ID.

        Args:
            address (str): The base address.
            payment_id (str): The payment ID.

        Returns:
            str: The integrated address.
        """
        return (await self.rpc.make_integrated_address(address, payment_id))[
            "result"
        ]["integrated_address"]

    async def validate_address(self, address: str) -> bool:
        """
        Validates a given address.

        Args:
            address (str): The address to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        return (await self.rpc.validate_address(address))["result"]["valid"]

    async def is_integrated(self, address: str) -> bool:
        """
        Checks if an address is an integrated address.

        Args:
            address (str): The address to check.

        Returns:
            bool: True if integrated, False otherwise.
        """
        return (await self.rpc.validate_address(address))["result"]["integrated"]

    async def get_address(self, account_index: int = 0) -> str:
        """
        Gets the main address for an account index.

        Args:
            account_index (int, optional): The account index. Defaults to 0.

        Returns:
            str: The address.
        """
        return (await self.rpc.get_address(account_index=account_index))["result"][
            "address"
        ]

    async def get_balances(self, account_index: int = 0) -> Tuple[int, int]:
        """
        Fetches the balance and unlocked balance for an account.

        Args:
            account_index (int, optional): The account index. Defaults to 0.

        Returns:
            Tuple[int, int]: The total balance and unlocked balance.
        """
        res = (await self.rpc.get_balance(account_index=account_index))["result"]
        return res["balance"], res["unlocked_balance"]

    async def get_transfers(self, account_index: int = 0) -> Dict[str, Any]:
        """
        Fetches all transfers for an account.

        Args:
            account_index (int, optional): The account index. Defaults to 0.

        Returns:
            Dict[str, Any]: The transfer details.
        """
        return (
            await self.rpc.get_transfers(
                account_index=account_index,
                incoming=True,
                outgoing=True,
                pending=True,
                failed=True,
                pool=True,
            )
        )["result"]

    async def transfer(
        self,
        dest_address: str,
        atomic_amount: Optional[float] = None,
        category: str = "transfer",
        account_index: int = 0,
        payment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Performs a transfer or a sweep operation.

        Args:
            dest_address (str): The destination address.
            atomic_amount (Optional[float], optional): The amount to transfer. Defaults to None.
            category (str, optional): The transfer category. Defaults to "transfer".
            account_index (int, optional): The account index. Defaults to 0.
            payment_id (Optional[str], optional): The payment ID. Defaults to None.

        Returns:
            Dict[str, Any]: The transfer result.
        """
        if category == "sweep_all":
            transfer = await self.rpc.sweep_all(
                address=dest_address,
                subaddr_indices=[],
                mixin=0,
                below_amount=0,
                get_tx_metadata=False,
                account_index=account_index,
                priority=0,
                unlock_time=0,
                get_tx_keys=False,
                get_tx_hex=False,
                do_not_relay=False,
                ring_size=0,
            )

        else:
            if payment_id and not await self.is_integrated(dest_address):
                dest_address = await self.integrated_address(
                    dest_address, payment_id
                )

            transfer = await self.rpc.transfer(
                destinations=[{"address": dest_address, "amount": atomic_amount}],
                subaddr_indices=[],
                mixin=0,
                get_tx_metadata=False,
                account_index=account_index,
                priority=0,
                unlock_time=0,
                get_tx_key=False,
                get_tx_hex=False,
                do_not_relay=False,
                ring_size=0,
            )

        return transfer["result"]
