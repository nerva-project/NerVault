from typing import Any, Dict, Tuple, Optional

from json import JSONDecodeError

from httpx import HTTPError
from nerva import WalletRPC


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

        except (HTTPError, JSONDecodeError, KeyError):
            return False

    async def height(self) -> Dict[str, Any]:
        """
        Gets the current blockchain height.

        Returns:
            Dict[str, Any]: The height information from the wallet RPC.
        """
        return await self.rpc.get_height()  # type: ignore[no-any-return]

    async def public_spend_key(self) -> str:
        """
        Fetches the public spend key.

        Returns:
            str: The public spend key.
        """
        return (await self.rpc.query_key(key_type="public_spend_key"))["result"][  # type: ignore[no-any-return]
            "public_spend_key"
        ]

    async def secret_spend_key(self) -> str:
        """
        Fetches the secret spend key.

        Returns:
            str: The secret spend key.
        """
        return (await self.rpc.query_key(key_type="secret_spend_key"))["result"][  # type: ignore[no-any-return]
            "private_spend_key"
        ]

    async def public_view_key(self) -> str:
        """
        Fetches the public view key.

        Returns:
            str: The public view key.
        """
        return (await self.rpc.query_key(key_type="public_view_key"))["result"][  # type: ignore[no-any-return]
            "public_view_key"
        ]

    async def secret_view_key(self) -> str:
        """
        Fetches the secret view key.

        Returns:
            str: The secret view key.
        """
        return (await self.rpc.query_key(key_type="secret_view_key"))["result"][  # type: ignore[no-any-return]
            "private_view_key"
        ]

    async def seed(self) -> str:
        """
        Fetches the wallet mnemonic seed.

        Returns:
            str: The wallet mnemonic seed.
        """
        return (await self.rpc.query_key(key_type="mnemonic"))["result"]["mnemonic"]  # type: ignore[no-any-return]

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
        return (  # type: ignore[no-any-return]
            await self.rpc.make_integrated_address(
                payment_id=payment_id, standard_address=address
            )
        )["result"]["integrated_address"]

    async def make_integrated_address(self, payment_id: str = "") -> Dict[str, Any]:
        """
        Builds an integrated address for this wallet's own address.

        Args:
            payment_id (str): The 16-hex payment ID to embed. An empty string
                makes the wallet generate a random one.

        Returns:
            Dict[str, Any]: The result, including the integrated_address and the
            (possibly generated) payment_id.
        """
        return (  # type: ignore[no-any-return]
            await self.rpc.make_integrated_address(payment_id=payment_id)
        )["result"]

    async def validate_address(self, address: str) -> bool:
        """
        Validates a given address.

        Args:
            address (str): The address to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        return (await self.rpc.validate_address(address=address))["result"]["valid"]  # type: ignore[no-any-return]

    async def is_integrated(self, address: str) -> bool:
        """
        Checks if an address is an integrated address.

        Args:
            address (str): The address to check.

        Returns:
            bool: True if integrated, False otherwise.
        """
        return (await self.rpc.validate_address(address=address))["result"][  # type: ignore[no-any-return]
            "integrated"
        ]

    async def get_address(self, account_index: int = 0) -> str:
        """
        Gets the main address for an account index.

        Args:
            account_index (int, optional): The account index. Defaults to 0.

        Returns:
            str: The address.
        """
        return (await self.rpc.get_address(account_index=account_index))["result"][  # type: ignore[no-any-return]
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
        return (  # type: ignore[no-any-return]
            await self.rpc.get_transfers(
                account_index=account_index,
                incoming=True,
                outgoing=True,
                pending=True,
                failed=True,
                pool=True,
            )
        )["result"]

    async def prepare(
        self,
        dest_address: str,
        atomic_amount: Optional[int] = None,
        sweep: bool = False,
        account_index: int = 0,
        payment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Builds a transfer or full sweep without relaying it, returning the
        amount the destination will receive, the network fee, and the signed
        transaction metadata needed to relay it later.

        Args:
            dest_address (str): The destination address.
            atomic_amount (Optional[int], optional): The amount to transfer, in
                atomic units. Ignored when sweeping. Defaults to None.
            sweep (bool, optional): Whether to sweep the full balance.
            account_index (int, optional): The account index. Defaults to 0.
            payment_id (Optional[str], optional): The payment ID. Defaults to None.

        Returns:
            Dict[str, Any]: {"amount": int, "fee": int, "metadata": list[str]}.
        """
        if sweep:
            res = (
                await self.rpc.sweep_all(
                    address=dest_address,
                    subaddr_indices=[],
                    mixin=0,
                    below_amount=0,
                    get_tx_metadata=True,
                    account_index=account_index,
                    priority=0,
                    unlock_time=0,
                    get_tx_keys=False,
                    get_tx_hex=False,
                    do_not_relay=True,
                    ring_size=0,
                )
            )["result"]
            return {
                "amount": sum(res.get("amount_list") or []),
                "fee": sum(res.get("fee_list") or []),
                "metadata": res.get("tx_metadata_list") or [],
            }

        if payment_id and not await self.is_integrated(dest_address):
            dest_address = await self.integrated_address(dest_address, payment_id)

        res = (
            await self.rpc.transfer(
                destinations=[{"address": dest_address, "amount": atomic_amount}],
                subaddr_indices=[],
                mixin=0,
                get_tx_metadata=True,
                account_index=account_index,
                priority=0,
                unlock_time=0,
                get_tx_key=False,
                get_tx_hex=False,
                do_not_relay=True,
                ring_size=0,
            )
        )["result"]
        metadata = res.get("tx_metadata")
        return {
            "amount": res.get("amount", 0),
            "fee": res.get("fee", 0),
            "metadata": [metadata] if metadata else [],
        }

    async def relay(self, metadata: list[str]) -> list[str]:
        """
        Relays one or more transactions previously built with do_not_relay,
        returning their broadcast transaction hashes.

        Args:
            metadata (list[str]): The tx_metadata blobs to broadcast.

        Returns:
            list[str]: The broadcast transaction hashes.
        """
        hashes: list[str] = []
        for blob in metadata:
            res = (await self.rpc.relay_tx(tx_hex=blob))["result"]
            tx_hash = res.get("tx_hash")
            if tx_hash:
                hashes.append(tx_hash)
        return hashes
