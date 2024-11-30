from __future__ import annotations

from typing import Any, Dict

from decimal import Decimal

from six import integer_types

PICO_XNV = Decimal("0.000000000001")


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
    if not isinstance(amount, (Decimal, float) + integer_types):
        raise ValueError(
            f"Amount '{amount}' doesn't have numeric type. Only Decimal, int, long and "
            "float (not recommended) are accepted as amounts."
        )

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

    for tx_type in transactions:
        for t in transactions[tx_type]:
            txs[t["txid"]] = {
                "type": tx_type,
                "amount": t["amount"],
                "timestamp": t["timestamp"],
                "fee": t["fee"],
            }

    for tx_id, tx_data in sorted(txs.items(), key=lambda x: x[1]["timestamp"]):
        if tx_data["type"] == "in":
            total += tx_data["amount"]
        elif tx_data["type"] == "out":
            total -= tx_data["amount"]
            total -= tx_data["fee"]

        sorted_txs[tx_id] = {
            "type": tx_data["type"],
            "amount": tx_data["amount"],
            "timestamp": tx_data["timestamp"],
            "total": total,
        }

    return sorted_txs
