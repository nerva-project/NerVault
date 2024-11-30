from __future__ import annotations

from typing import Any, Dict, Optional

import sys
import json
from datetime import timedelta

from aiohttp import ClientError, ClientSession
from valkey.asyncio import Valkey
from valkey.exceptions import ConnectionError

import config


class Cache:
    """
    A class for interacting with a caching service (Valkey) and retrieving
    coin-related information from an external API (CoinGecko).

    This class handles storing data in the cache, retrieving cached data, and
    fetching real-time coin information such as price, market cap, and volume.

    Attributes:
        valkey (Valkey): An instance of the Valkey client to interact with the cache.
    """

    def __init__(self) -> None:
        """
        Initializes the Cache instance by establishing a connection with the Valkey caching service.

        Raises:
            SystemExit: If the connection to the Valkey service fails.
        """
        try:
            from valkey import Valkey as Vlk

            client = Vlk.from_url(config.VALKEY_URL)
            client.ping()
            del client
            del Vlk

        except ConnectionError:
            print("Failed to connect to Valkey. Exiting...")
            sys.exit(1)

        self.valkey: Valkey = Valkey.from_url(config.VALKEY_URL)

    async def store_data(
        self, item_name: str, expiration_minutes: int, data: str
    ) -> None:
        """
        Stores the given data in the cache with a specified expiration time.

        Args:
            item_name (str): The name of the item to store in the cache.
            expiration_minutes (int): The expiration time for the cached data, in minutes.
            data (str): The data to store in the cache.
        """
        await self.valkey.setex(
            item_name, timedelta(minutes=expiration_minutes), value=data
        )

    async def get_data(self, item_name: str) -> Optional[str]:
        """
        Retrieves the cached data for a given item name.

        Args:
            item_name (str): The name of the item to retrieve from the cache.

        Returns:
            Optional[str]: The cached data as a string if it exists, or None if no data is found.
        """
        data = await self.valkey.get(item_name)
        if data:
            return data.decode()
        return None

    async def get_coin_info(self) -> Dict[str, Any]:
        """
        Retrieves coin information (e.g., price, market cap, volume) for Nerva from the CoinGecko API.
        If the information is not found in the cache, it will fetch the data from the CoinGecko API
        and store it in the cache for future use.

        Returns:
            Dict[str, Any]: A dictionary containing coin information such as price, market cap, etc.
        """
        info = await self.valkey.get("coin_info")

        if info:
            return json.loads(info)

        data = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false",
        }

        headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": config.COINGECKO_API_KEY,
        }
        url = "https://api.coingecko.com/api/v3/coins/nerva"

        try:
            async with ClientSession() as session:
                async with session.get(url, headers=headers, params=data) as res:
                    res_json = await res.json()

            info = {
                "genesis_date": res_json["genesis_date"],
                "market_cap_rank": res_json["market_cap_rank"],
                "current_price": res_json["market_data"]["current_price"]["usd"],
                "market_cap": res_json["market_data"]["market_cap"]["usd"],
                "total_volume": res_json["market_data"]["total_volume"]["usd"],
                "last_updated": res_json["last_updated"],
            }

            await self.store_data("coin_info", 15, json.dumps(info))

            return info

        except ClientError:
            return {}
