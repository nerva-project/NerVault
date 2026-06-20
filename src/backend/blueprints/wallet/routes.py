from typing import Any

import json
import base64
import string
from io import BytesIO
from asyncio import sleep
from decimal import Decimal, InvalidOperation
from pathlib import Path
from secrets import token_hex
from datetime import UTC, datetime, timedelta

from PIL import Image
from quart import Response, jsonify, request
from quart_auth import (
    current_user as _current_user,
    login_required,
)
from qrcode.main import QRCode
from qrcode.constants import ERROR_CORRECT_H
from redis.exceptions import LockError
from quart_rate_limiter import rate_limit
from redis.asyncio.lock import Lock

from backend import config
from backend.factory import cache, bcrypt, daemon, docker
from backend.library.rpc import Wallet
from backend.utils.models import User
from backend.library.utils import client_ip, to_atomic, sort_transactions
from backend.library.helpers import (
    capture_event,
    verify_step_up,
    verify_2fa_code,
)
from backend.utils.decorators import check_confirmed
from backend.library.validation import validate_seed

from . import wallet_bp

current_user: User = _current_user  # type: ignore[assignment]

QR_LOGO_PATH = Path(__file__).resolve().parents[2] / "assets" / "nerva-qr.png"

SENSITIVE_IP_LIMIT = 10
SENSITIVE_IP_PERIOD = timedelta(minutes=1)
SENSITIVE_ACCOUNT_LIMIT = 5
SENSITIVE_ACCOUNT_PERIOD = timedelta(minutes=15)

# Sweep estimates build (but don't relay) a transaction, so they are cheaper
# than a real transfer and may be re-run as the user edits the address.
ESTIMATE_IP_LIMIT = 20
ESTIMATE_IP_PERIOD = timedelta(minutes=1)
ESTIMATE_ACCOUNT_LIMIT = 30
ESTIMATE_ACCOUNT_PERIOD = timedelta(minutes=1)

# Blocks an output stays locked after its block before it becomes spendable.
SPENDABLE_AGE = 10


async def _account_rate_limit_key() -> str:
    """Rate-limit key based on the authenticated account, for abuse protection."""
    if current_user.auth_id:
        return str(current_user.auth_id).strip().lower()

    return client_ip()


async def _acquire_wallet_lock(username: str) -> Lock | None:
    """Acquire a per-user lock serializing wallet lifecycle operations.

    Returns the lock if acquired, or None if another operation already holds it.
    """
    lock = cache.redis.lock(f"wallet-lock:{username}", timeout=60, blocking=False)
    return lock if await lock.acquire() else None


async def _release_wallet_lock(lock: Lock) -> None:
    """Release a wallet lock, tolerating an already-expired lock."""
    try:
        await lock.release()
    except LockError:
        pass


def _wallet_rpc(timeout: int | None = None) -> Wallet:
    """Builds a Wallet RPC client for the current user's running container."""
    kwargs: dict[str, Any] = {
        "host": docker.rpc_host(current_user.username),
        "port": current_user.wallet_port,
        "ssl": False,
        "username": current_user.username,
        "password": current_user.wallet_password,
    }
    if timeout is not None:
        kwargs["timeout"] = timeout
    return Wallet(**kwargs)


def _branded_qr(data: str) -> bytes:
    """Renders a PNG QR code for the given data with the Nerva logo centred."""
    qr = QRCode(version=1, error_correction=ERROR_CORRECT_H)
    qr.add_data(data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")  # type: ignore[union-attr]

    logo_size = 256
    logo = Image.open(QR_LOGO_PATH).convert("RGBA").resize((logo_size, logo_size))
    qr_width, qr_height = qr_img.size
    qr_img.paste(
        logo,
        ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2),
        mask=logo,
    )

    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    return buffer.getvalue()


@wallet_bp.route("/status", methods=["GET"])
@login_required
@check_confirmed
async def _status() -> tuple[Response, int]:
    """
    Returns the current state of the user's wallet (created/connected/ready).
    """
    user_vol = docker.get_user_volume(current_user.username)
    initializing = await docker.container_exists(
        f"init_wallet_{current_user.username}"
    )
    progress = (
        await docker.restore_progress(current_user.username)
        if initializing
        else None
    )

    if current_user.wallet_created and current_user.wallet_connected:
        wallet_ready = await _wallet_rpc().connected
    else:
        wallet_ready = False

    return jsonify(
        {
            "status": "success",
            "result": {
                "created": current_user.wallet_created,
                "connected": current_user.wallet_connected,
                "port": current_user.wallet_port,
                "container": current_user.wallet_container,
                "volume": await docker.volume_exists(user_vol),
                "initializing": initializing,
                "progress": progress,
                "ready": wallet_ready,
            },
        }
    ), 200


@wallet_bp.route("/setup", methods=["POST"])
@login_required
@check_confirmed
async def _setup() -> tuple[Response, int]:
    """
    Creates or restores the user's wallet and starts initialization.
    """
    if current_user.wallet_created:
        return jsonify({"status": "error", "error": "Wallet already exists."}), 400

    data = await request.get_json(silent=True) or {}
    mode = str(data.get("mode") or "create").strip().lower()

    seed: str | None
    if mode == "restore":
        try:
            seed = validate_seed(str(data.get("seed") or "").lower())
        except ValueError:
            return jsonify(
                {
                    "status": "error",
                    "error": "Invalid seed phrase provided; must be a standard "
                    "25-word Nerva mnemonic seed phrase.",
                }
            ), 400
        event = "restore_wallet"

    elif mode == "create":
        seed = None
        event = "create_wallet"

    else:
        return jsonify({"status": "error", "error": "Invalid setup mode."}), 400

    lock = await _acquire_wallet_lock(current_user.username)
    if lock is None:
        return jsonify(
            {
                "status": "error",
                "error": "A wallet operation is already in progress.",
                "code": "in_progress",
            }
        ), 409

    try:
        await current_user.load()
        if current_user.wallet_created:
            return jsonify(
                {"status": "error", "error": "Wallet already exists."}
            ), 400

        await docker.create_wallet(current_user.username, seed)
        await capture_event(current_user.username, event)

        current_user.wallet_created = True
        await current_user.save(["wallet_created"])
    finally:
        await _release_wallet_lock(lock)

    return jsonify(
        {"status": "success", "message": "Wallet setup has started."}
    ), 201


@wallet_bp.route("/connect", methods=["POST"])
@login_required
@check_confirmed
async def _connect() -> tuple[Response, int]:
    """
    Starts the wallet RPC container and assigns it to the user.
    """
    if not current_user.wallet_created:
        return jsonify({"status": "error", "error": "Wallet not yet created."}), 400

    if current_user.wallet_connected:
        return jsonify(
            {"status": "error", "error": "Wallet is already connected."}
        ), 400

    lock = await _acquire_wallet_lock(current_user.username)
    if lock is None:
        return jsonify(
            {
                "status": "error",
                "error": "A wallet operation is already in progress.",
                "code": "in_progress",
            }
        ), 409

    try:
        await current_user.load()
        if not current_user.wallet_created:
            return jsonify(
                {"status": "error", "error": "Wallet not yet created."}
            ), 400
        if current_user.wallet_connected:
            return jsonify(
                {"status": "error", "error": "Wallet is already connected."}
            ), 400

        container = await docker.start_wallet(current_user.username)

        try:
            port = await docker.rpc_port(container)
        except TypeError:
            return jsonify(
                {"status": "error", "error": "Failed to connect wallet."}
            ), 500

        current_user.wallet_connected = await docker.container_exists(container)
        current_user.wallet_port = port
        current_user.wallet_container = container
        current_user.wallet_started_at = datetime.now(UTC)
        await current_user.save(
            [
                "wallet_connected",
                "wallet_port",
                "wallet_container",
                "wallet_started_at",
            ]
        )

        await capture_event(current_user.username, "start_wallet")
    finally:
        await _release_wallet_lock(lock)

    return jsonify(
        {"status": "success", "message": "Wallet has been connected."}
    ), 200


@wallet_bp.route("/keepalive", methods=["POST"])
@login_required
@check_confirmed
async def _keepalive() -> tuple[Response, int]:
    """
    Resets the wallet session timer so the container is not reaped yet.
    """
    if (
        not current_user.wallet_connected
        or not current_user.wallet_container
        or not await docker.container_exists(current_user.wallet_container)
    ):
        return jsonify(
            {
                "status": "error",
                "error": "Wallet not connected.",
                "code": "not_connected",
            }
        ), 409

    current_user.wallet_started_at = datetime.now(UTC)
    await current_user.save(["wallet_started_at"])

    expires_at = (
        current_user.wallet_started_at
        + timedelta(seconds=config.PERMANENT_SESSION_LIFETIME)
    ).isoformat()

    return jsonify(
        {
            "status": "success",
            "message": "Wallet session extended.",
            "result": {"expires_at": expires_at},
        }
    ), 200


@wallet_bp.route("", methods=["GET"])
@login_required
@check_confirmed
async def _overview() -> tuple[Response, int]:
    """
    Returns the wallet dashboard data: address, balances, and transfers.
    """
    if not current_user.wallet_created:
        return jsonify(
            {
                "status": "error",
                "error": "Wallet not created.",
                "code": "not_created",
            }
        ), 409

    if not current_user.wallet_container or not await docker.container_exists(
        current_user.wallet_container
    ):
        await current_user.clear_wallet_data()
        return jsonify(
            {
                "status": "error",
                "error": "Wallet not connected.",
                "code": "not_connected",
            }
        ), 409

    wallet = _wallet_rpc()

    if not await wallet.connected:
        return jsonify(
            {
                "status": "error",
                "error": "Wallet RPC interface is unavailable.",
                "code": "not_ready",
            }
        ), 409

    address = await wallet.get_address()
    transfers = await wallet.get_transfers()
    transactions = [tx for t in transfers.values() for tx in t]
    balance, unlocked_balance = await wallet.get_balances()

    coin = await cache.get_coin_info()
    wallet_height = int((await wallet.height())["result"]["height"])
    try:
        network_height = int((await daemon.get_info())["height"])
    except Exception:
        network_height = wallet_height

    started = current_user.wallet_started_at
    expires_at = None
    if started is not None:
        if started.tzinfo is None:
            started = started.replace(tzinfo=UTC)
        expires_at = (
            started + timedelta(seconds=config.PERMANENT_SESSION_LIFETIME)
        ).isoformat()

    blocks_to_unlock = 0
    if balance > unlocked_balance:
        for tx in transactions:
            # Any still-locked output (a received tx, or the change from a sent
            # one) unlocks SPENDABLE_AGE blocks after its block, unless a longer
            # custom unlock height is set. Unconfirmed (pool) txs have no height
            # yet, so estimate the lock from the current tip.
            if not tx.get("locked"):
                continue
            height = int(tx.get("height") or 0) or wallet_height
            unlock_height = height + SPENDABLE_AGE
            unlock_time = int(tx.get("unlock_time") or 0)
            if 0 < unlock_time < 500_000_000:
                unlock_height = max(unlock_height, unlock_time)
            blocks_to_unlock = max(blocks_to_unlock, unlock_height - wallet_height)
        # Locked balance with nothing pinning a future unlock height yet (e.g. a
        # just-sent change tx still unconfirmed) — show a full lock rather than 0.
        if blocks_to_unlock <= 0:
            blocks_to_unlock = SPENDABLE_AGE

    await capture_event(current_user.username, "load_dashboard")

    return jsonify(
        {
            "status": "success",
            "result": {
                "address": address,
                "email": current_user.email,
                "balance": str(balance),
                "unlocked_balance": str(unlocked_balance),
                "transfers": transactions,
                "sorted_transactions": sort_transactions(transfers),
                "price": coin.get("current_price", 0),
                "wallet_height": wallet_height,
                "network_height": network_height,
                "blocks_to_unlock": blocks_to_unlock,
                "expires_at": expires_at,
            },
        }
    ), 200


@wallet_bp.route("/address", methods=["GET"])
@login_required
@check_confirmed
async def _address() -> tuple[Response, int]:
    """
    Returns the user's primary wallet address.
    """
    wallet = _wallet_rpc()

    if not await wallet.connected:
        return jsonify(
            {"status": "error", "error": "Wallet RPC interface is unavailable."}
        ), 503

    return jsonify(
        {"status": "success", "result": {"address": await wallet.get_address()}}
    ), 200


@wallet_bp.route("/transfers", methods=["GET"])
@login_required
@check_confirmed
async def _transfers() -> tuple[Response, int]:
    """
    Returns the user's transfers, both raw and with running balances.
    """
    wallet = _wallet_rpc()

    if not await wallet.connected:
        return jsonify(
            {"status": "error", "error": "Wallet RPC interface is unavailable."}
        ), 503

    transfers = await wallet.get_transfers()
    transactions = [tx for t in transfers.values() for tx in t]

    return jsonify(
        {
            "status": "success",
            "result": {
                "transfers": transactions,
                "sorted_transactions": sort_transactions(transfers),
            },
        }
    ), 200


@wallet_bp.route("/qr", methods=["GET"])
@login_required
@check_confirmed
async def _qr() -> Response:
    """
    Returns a branded PNG QR code encoding the user's wallet address.
    """
    wallet = _wallet_rpc()

    if not current_user.wallet_container or not await docker.container_exists(
        current_user.wallet_container
    ):
        return Response(status=409)

    if not await wallet.connected:
        return Response(status=409)

    address = await wallet.get_address()

    return Response(_branded_qr(f"nerva:{address}"), mimetype="image/png")


@wallet_bp.route("/integrated-address", methods=["POST"])
@login_required
@check_confirmed
async def _integrated_address() -> tuple[Response, int]:
    """
    Builds an integrated address (wallet address + payment ID) for receiving,
    returning the address, the payment ID, and a branded QR for it.
    """
    data = await request.get_json(silent=True) or {}
    payment_id = str(data.get("payment_id") or "").strip().lower()

    if payment_id and (
        len(payment_id) != 16 or not all(c in string.hexdigits for c in payment_id)
    ):
        return jsonify(
            {
                "status": "error",
                "error": "Payment ID must be 16 hexadecimal characters.",
            }
        ), 400

    wallet = _wallet_rpc()

    if not await wallet.connected:
        return jsonify(
            {
                "status": "error",
                "error": "Wallet RPC interface is unavailable.",
                "code": "not_connected",
            }
        ), 409

    result = await wallet.make_integrated_address(payment_id)
    qr = base64.b64encode(
        _branded_qr(f"nerva:{result['integrated_address']}")
    ).decode()

    return jsonify(
        {
            "status": "success",
            "result": {
                "integrated_address": result["integrated_address"],
                "payment_id": result["payment_id"],
                "qr": f"data:image/png;base64,{qr}",
            },
        }
    ), 200


@wallet_bp.route("/transfer", methods=["POST"])
@rate_limit(SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD)
@rate_limit(
    SENSITIVE_ACCOUNT_LIMIT,
    SENSITIVE_ACCOUNT_PERIOD,
    key_function=_account_rate_limit_key,
)
@login_required
@check_confirmed
async def _transfer() -> tuple[Response, int]:
    """
    Relays the transaction the user reviewed via /transfer/prepare.
    """
    data = await request.get_json(silent=True) or {}
    code = str(data.get("code") or "")
    password = str(data.get("password") or "")
    prepare_id = str(data.get("prepare_id") or "")

    wallet = _wallet_rpc(timeout=30)

    if not await wallet.connected:
        await capture_event(current_user.username, "tx_fail_rpc_unavailable")
        return jsonify(
            {
                "status": "error",
                "error": "Wallet RPC interface is unavailable. "
                "Please log out and log in again.",
            }
        ), 503

    cache_key = f"tx_prepared_{current_user.username}"
    raw = await cache.get_data(cache_key)
    if not raw:
        return jsonify(
            {
                "status": "error",
                "error": "Your transaction preview expired. Please review again.",
                "code": "expired",
            }
        ), 409

    cached = json.loads(raw)
    if not prepare_id or prepare_id != cached.get("id"):
        return jsonify(
            {
                "status": "error",
                "error": "Your transaction preview changed. Please review again.",
                "code": "expired",
            }
        ), 409

    if not await verify_step_up(current_user, code, password):
        return jsonify(
            {
                "status": "error",
                "error": "Verification failed. Re-enter your two-factor code "
                "or password.",
            }
        ), 401

    try:
        hashes = await wallet.relay(cached["metadata"])
    except Exception:
        await cache.redis.delete(cache_key)
        await capture_event(current_user.username, "tx_fail_relay")
        return jsonify(
            {
                "status": "error",
                "error": "There was a problem sending the transaction. "
                "Please review again.",
                "code": "expired",
            }
        ), 400

    await cache.redis.delete(cache_key)

    if not hashes:
        await capture_event(current_user.username, "tx_fail_relay")
        return jsonify(
            {
                "status": "error",
                "error": "There was a problem sending the transaction.",
            }
        ), 400

    await capture_event(current_user.username, "tx_success")

    return jsonify(
        {"status": "success", "message": "The transaction has been sent."}
    ), 200


@wallet_bp.route("/transfer/prepare", methods=["POST"])
@rate_limit(ESTIMATE_IP_LIMIT, ESTIMATE_IP_PERIOD)
@rate_limit(
    ESTIMATE_ACCOUNT_LIMIT,
    ESTIMATE_ACCOUNT_PERIOD,
    key_function=_account_rate_limit_key,
)
@login_required
@check_confirmed
async def _transfer_prepare() -> tuple[Response, int]:
    """
    Builds (without relaying) the transfer or sweep the user is about to send,
    returning the amount and network fee to confirm, and stashing the signed
    transaction so /transfer can relay it.
    """
    data = await request.get_json(silent=True) or {}
    address = str(data.get("address") or "").strip()
    sweep = data.get("sweep") is True
    amount_raw = str(data.get("amount") or "").strip()
    payment_id = str(data.get("payment_id") or "").strip() or None

    wallet = _wallet_rpc(timeout=30)

    if not await wallet.connected:
        return jsonify(
            {
                "status": "error",
                "error": "Wallet RPC interface is unavailable.",
                "code": "not_connected",
            }
        ), 503

    if not await wallet.validate_address(address):
        return jsonify(
            {"status": "error", "error": "Invalid Nerva address provided."}
        ), 400

    if payment_id is not None:
        if len(payment_id) != 16 or not all(
            c in string.hexdigits for c in payment_id
        ):
            return jsonify(
                {
                    "status": "error",
                    "error": "Payment ID must be 16 hexadecimal characters.",
                }
            ), 400

        if await wallet.is_integrated(address):
            return jsonify(
                {
                    "status": "error",
                    "error": "This address already includes a payment ID; "
                    "remove the payment ID field.",
                }
            ), 400

    amount: int | None = None
    if not sweep:
        try:
            decimal_amount = Decimal(amount_raw)
            if not decimal_amount.is_finite() or decimal_amount <= 0:
                raise InvalidOperation

        except (InvalidOperation, ValueError):
            return jsonify(
                {"status": "error", "error": "Invalid Nerva amount specified."}
            ), 400

        exponent = decimal_amount.normalize().as_tuple().exponent
        if isinstance(exponent, int) and -exponent > 12:
            return jsonify(
                {
                    "status": "error",
                    "error": "Amount has more than 12 decimal places "
                    "(pico precision).",
                }
            ), 400

        try:
            amount = to_atomic(decimal_amount)
            if amount <= 0:
                raise InvalidOperation

        except (InvalidOperation, ValueError):
            return jsonify(
                {"status": "error", "error": "Invalid Nerva amount specified."}
            ), 400

    try:
        prepared = await wallet.prepare(
            address, atomic_amount=amount, sweep=sweep, payment_id=payment_id
        )
    except Exception:
        return jsonify(
            {
                "status": "error",
                "error": "Could not prepare the transaction. You may not have "
                "enough unlocked balance.",
            }
        ), 400

    if prepared["amount"] <= 0 or not prepared["metadata"]:
        return jsonify(
            {
                "status": "error",
                "error": "Could not prepare the transaction. You may not have "
                "enough unlocked balance.",
            }
        ), 400

    prepare_id = token_hex(16)
    await cache.store_data(
        f"tx_prepared_{current_user.username}",
        5,
        json.dumps(
            {
                "id": prepare_id,
                "metadata": prepared["metadata"],
                "address": address,
                "amount": prepared["amount"],
                "fee": prepared["fee"],
            }
        ),
    )

    return jsonify(
        {
            "status": "success",
            "result": {
                "prepare_id": prepare_id,
                "amount": str(prepared["amount"]),
                "fee": str(prepared["fee"]),
            },
        }
    ), 200


@wallet_bp.route("/secrets", methods=["POST"])
@rate_limit(SENSITIVE_IP_LIMIT, SENSITIVE_IP_PERIOD)
@rate_limit(
    SENSITIVE_ACCOUNT_LIMIT,
    SENSITIVE_ACCOUNT_PERIOD,
    key_function=_account_rate_limit_key,
)
@login_required
@check_confirmed
async def _secrets() -> tuple[Response, int]:
    """
    Returns the wallet's secret keys after verifying the account password.
    """
    data = await request.get_json(silent=True) or {}
    password = str(data.get("password") or "")
    code = str(data.get("code") or "")

    if not bcrypt.check_password_hash(current_user.password, password):
        return jsonify({"status": "error", "error": "Invalid password."}), 401

    if not await verify_2fa_code(current_user, code):
        return jsonify(
            {"status": "error", "error": "Invalid or missing two-factor code."}
        ), 401

    wallet = _wallet_rpc()

    if not await wallet.connected:
        return jsonify(
            {"status": "error", "error": "Wallet RPC interface is unavailable."}
        ), 503

    return jsonify(
        {
            "status": "success",
            "result": {
                "mnemonic_seed": await wallet.seed(),
                "public_spend_key": await wallet.public_spend_key(),
                "secret_spend_key": await wallet.secret_spend_key(),
                "public_view_key": await wallet.public_view_key(),
                "secret_view_key": await wallet.secret_view_key(),
            },
        }
    ), 200


@wallet_bp.route("/delete", methods=["POST"])
@login_required
@check_confirmed
async def _delete() -> tuple[Response, int]:
    """
    Stops the wallet container and permanently deletes the user's wallet data.
    """
    data = await request.get_json(silent=True) or {}

    if data.get("confirm") is not True:
        return jsonify(
            {"status": "error", "error": "Please confirm deletion of the wallet."}
        ), 400

    lock = await _acquire_wallet_lock(current_user.username)
    if lock is None:
        return jsonify(
            {
                "status": "error",
                "error": "A wallet operation is already in progress.",
                "code": "in_progress",
            }
        ), 409

    try:
        await docker.stop_container(current_user.wallet_container)
        await capture_event(current_user.username, "stop_container")

        await sleep(2)

        await docker.delete_wallet_data(current_user.username)
        await capture_event(current_user.username, "delete_wallet")

        await current_user.clear_wallet_data(reset_password=True, reset_wallet=True)
    finally:
        await _release_wallet_lock(lock)

    return jsonify(
        {"status": "success", "message": "Successfully deleted wallet data."}
    ), 200
