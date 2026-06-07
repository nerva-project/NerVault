from typing import Any

import string
from io import BytesIO
from asyncio import sleep
from decimal import Decimal, InvalidOperation
from pathlib import Path
from datetime import UTC, datetime

from PIL import Image
from quart import Response, jsonify, request
from quart_auth import (
    current_user as _current_user,
    login_required,
)
from qrcode.main import QRCode
from qrcode.constants import ERROR_CORRECT_H

from backend.factory import cache, bcrypt, docker
from backend.library.rpc import Wallet
from backend.utils.models import User
from backend.library.utils import to_atomic, sort_transactions
from backend.library.helpers import capture_event
from backend.utils.decorators import check_confirmed
from backend.library.validation import validate_seed

from . import wallet_bp

current_user: User = _current_user  # type: ignore[assignment]

QR_LOGO_PATH = Path(__file__).resolve().parents[2] / "assets" / "nerva-qr.png"


def _wallet_rpc() -> Wallet:
    """Builds a Wallet RPC client for the current user's running container."""
    return Wallet(
        host="127.0.0.1",
        port=current_user.wallet_port,
        ssl=False,
        username=current_user.username,
        password=current_user.wallet_password,
    )


@wallet_bp.route("/status", methods=["GET"])
@login_required
@check_confirmed
async def _status() -> tuple[Response, int]:
    """
    Returns the current state of the user's wallet (created/connected/ready).
    """
    user_vol = docker.get_user_volume(current_user.username)
    create_container = await cache.get_data(f"init_wallet_{current_user.username}")

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
                "volume": docker.volume_exists(user_vol),
                "initializing": docker.container_exists(create_container)
                if create_container
                else False,
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

        container = await docker.create_wallet(current_user.username, seed)
        event = "restore_wallet"

    elif mode == "create":
        container = await docker.create_wallet(current_user.username)
        event = "create_wallet"

    else:
        return jsonify({"status": "error", "error": "Invalid setup mode."}), 400

    await cache.store_data(f"init_wallet_{current_user.username}", 30, container)
    await capture_event(current_user.username, event)

    await current_user.load()
    current_user.wallet_created = True
    await current_user.save()

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

    container = await docker.start_wallet(current_user.username)

    try:
        port = docker.get_port(container)
    except TypeError:
        return jsonify(
            {"status": "error", "error": "Failed to connect wallet."}
        ), 500

    current_user.wallet_connected = docker.container_exists(container)
    current_user.wallet_port = port
    current_user.wallet_container = container
    current_user.wallet_started_at = datetime.now(UTC)
    await current_user.save()

    await capture_event(current_user.username, "start_wallet")

    return jsonify(
        {"status": "success", "message": "Wallet has been connected."}
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

    if not current_user.wallet_container or not docker.container_exists(
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

    await capture_event(current_user.username, "load_dashboard")

    return jsonify(
        {
            "status": "success",
            "result": {
                "address": address,
                "email": current_user.email,
                "balance": balance,
                "unlocked_balance": unlocked_balance,
                "transfers": transactions,
                "sorted_transactions": sort_transactions(transfers),
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

    if not current_user.wallet_container or not docker.container_exists(
        current_user.wallet_container
    ):
        return Response(status=409)

    if not await wallet.connected:
        return Response(status=409)

    address = await wallet.get_address()
    uri = f"nerva:{address}?tx_description={current_user.email}"

    qr = QRCode(version=1, error_correction=ERROR_CORRECT_H)
    qr.add_data(uri)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")  # type: ignore[union-attr]

    logo_size = 256
    logo = Image.open(QR_LOGO_PATH).convert("RGBA").resize((logo_size, logo_size))
    qr_width, qr_height = qr_img.size
    logo_position = (
        (qr_width - logo_size) // 2,
        (qr_height - logo_size) // 2,
    )
    qr_img.paste(logo, logo_position, mask=logo)

    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")

    return Response(buffer.getvalue(), mimetype="image/png")


@wallet_bp.route("/transfer", methods=["POST"])
@login_required
@check_confirmed
async def _transfer() -> tuple[Response, int]:
    """
    Sends funds from the user's wallet, or sweeps the full balance.
    """
    data = await request.get_json(silent=True) or {}
    address = str(data.get("address") or "").strip()
    amount_raw = str(data.get("amount") or "").strip()
    payment_id = str(data.get("payment_id") or "").strip() or None

    wallet = Wallet(
        host="127.0.0.1",
        port=current_user.wallet_port,
        ssl=False,
        username=current_user.username,
        password=current_user.wallet_password,
        timeout=30,
    )

    if not await wallet.connected:
        await capture_event(current_user.username, "tx_fail_rpc_unavailable")
        return jsonify(
            {
                "status": "error",
                "error": "Wallet RPC interface is unavailable. "
                "Please log out and log in again.",
            }
        ), 503

    if not await wallet.validate_address(address):
        await capture_event(current_user.username, "tx_fail_address_invalid")
        return jsonify(
            {"status": "error", "error": "Invalid Nerva address provided."}
        ), 400

    if amount_raw == "all":
        tx = await wallet.transfer(address, None, "sweep_all")

    else:
        try:
            decimal_amount = Decimal(amount_raw)
            if not decimal_amount.is_finite() or decimal_amount <= 0:
                raise InvalidOperation
            amount = to_atomic(decimal_amount)
            if amount <= 0:
                raise InvalidOperation

        except (InvalidOperation, ValueError):
            await capture_event(current_user.username, "tx_fail_amount_invalid")
            return jsonify(
                {"status": "error", "error": "Invalid Nerva amount specified."}
            ), 400

        if payment_id and (
            len(payment_id) not in [16, 32]
            or not all(c in string.hexdigits for c in payment_id)
        ):
            return jsonify(
                {"status": "error", "error": "Invalid payment ID specified."}
            ), 400

        tx = await wallet.transfer(address, amount, payment_id=payment_id)

    if "message" in tx:
        msg_lower = tx["message"].replace(" ", "_").lower()
        await capture_event(current_user.username, f"tx_fail_{msg_lower}")
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


@wallet_bp.route("/secrets", methods=["POST"])
@login_required
@check_confirmed
async def _secrets() -> tuple[Response, int]:
    """
    Returns the wallet's secret keys after verifying the account password.
    """
    data = await request.get_json(silent=True) or {}
    password = str(data.get("password") or "")

    if not bcrypt.check_password_hash(current_user.password, password):
        return jsonify({"status": "error", "error": "Invalid password."}), 401

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

    docker.stop_container(current_user.wallet_container)
    await capture_event(current_user.username, "stop_container")

    await sleep(2)

    docker.delete_wallet_data(current_user.username)
    await capture_event(current_user.username, "delete_wallet")

    await current_user.clear_wallet_data(reset_password=True, reset_wallet=True)

    return jsonify(
        {"status": "success", "message": "Successfully deleted wallet data."}
    ), 200
