from typing import Any, Dict

from time import time
from decimal import Decimal

from quart import request

from backend import config

PICO_XNV = Decimal("0.000000000001")

# wallet2 marks a pending tx "failed" when two consecutive pool polls miss it,
# which false-positives when the tx is mined before the wallet scans its block
# (nerva-project/nerva wallet2.cpp update_pool_state). Show young failures as
# pending until they outlive the race window.
FAILED_GRACE_SECONDS = 300


def client_ip() -> str:
    """
    Returns the originating client IP for rate limiting. Behind a trusted proxy
    (TRUST_PROXY_IP_HEADER, default True) the proxy-set CF-Connecting-IP header
    is used; otherwise the unspoofable socket peer is used, so the header cannot
    be forged to dodge rate limits when the origin is directly reachable.
    """
    if getattr(config, "TRUST_PROXY_IP_HEADER", True):
        forwarded = request.headers.get("CF-Connecting-IP")
        if forwarded:
            return forwarded

    return request.remote_addr or "unknown"


def to_atomic(amount: Decimal) -> int:
    """
    Converts a given amount (in Decimal) to atomic units.

    Args:
        amount (Decimal): The amount to convert to atomic units.

    Returns:
        int: The amount in atomic units (as an integer).

    Raises:
        ValueError: If the provided amount is not of a numeric type (Decimal, int, or float).
    """
    if not isinstance(amount, (Decimal, float, int)):
        raise ValueError(
            f"Amount '{amount}' doesn't have numeric type. Only Decimal, int, long and "
            "float (not recommended) are accepted as amounts."
        )

    if isinstance(amount, Decimal) and not amount.is_finite():
        raise ValueError("Amount must be a finite number.")

    return int(amount * 10**12)


def from_atomic(amount: int) -> Decimal:
    """
    Converts an atomic unit amount (integer) back to its Decimal representation.

    Args:
        amount (int): The atomic amount to convert.

    Returns:
        Decimal: The amount in Decimal form.
    """
    return (Decimal(amount) * PICO_XNV).quantize(PICO_XNV)


def sort_transactions(transactions: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Sorts transactions by timestamp and computes the running total of amounts,
    distinguishing between incoming and outgoing transactions.

    Args:
        transactions (dict): A dictionary where the keys are transaction types ('in' or 'out')
                              and the values are lists of transaction data dictionaries.

    Returns:
        dict: A sorted dictionary of transactions with running totals. Each entry contains
              transaction details along with the cumulative total at that point in time.
    """
    total = 0
    txs: Dict[str, Dict[str, Any]] = {}
    sorted_txs: Dict[str, Dict[str, Any]] = {}

    now = time()
    live_txids = {
        t["txid"]
        for tx_type, entries in transactions.items()
        if tx_type != "failed"
        for t in entries
    }

    for tx_type in transactions:
        for t in transactions[tx_type]:
            entry_type = tx_type
            if tx_type == "failed":
                # A "failed" tx that also lives in another bucket (or is still
                # inside the grace window) is the wallet2 race, not a failure.
                if t["txid"] in live_txids:
                    continue
                if now - t["timestamp"] < FAILED_GRACE_SECONDS:
                    entry_type = "pending"
            # Key by txid AND type: one txid can appear in multiple buckets
            # (e.g. a self-send in both "in" and "out"); a bare-txid key would
            # silently drop one leg from the history.
            txs[f"{t['txid']}:{entry_type}"] = {
                "txid": t["txid"],
                "type": entry_type,
                "amount": t["amount"],
                "timestamp": t["timestamp"],
                "fee": t["fee"],
            }

    for tx_id, tx_data in sorted(
        txs.items(), key=lambda x: (x[1]["timestamp"], x[0])
    ):
        if tx_data["type"] == "in":
            total += tx_data["amount"]
        elif tx_data["type"] == "out":
            total -= tx_data["amount"]
            total -= tx_data["fee"]

        sorted_txs[tx_id] = {
            "txid": tx_data["txid"],
            "type": tx_data["type"],
            "amount": str(tx_data["amount"]),
            "timestamp": tx_data["timestamp"],
            "total": str(total),
        }

    return sorted_txs
