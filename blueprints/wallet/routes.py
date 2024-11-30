from blueprints.wallet import wallet_bp

import string
from io import BytesIO
from base64 import b64encode
from decimal import Decimal
from datetime import UTC, datetime

from PIL import Image
from quart import flash, jsonify, request, url_for, redirect, render_template
from quart_auth import current_user, login_required
from qrcode.main import QRCode
from quart.typing import ResponseReturnValue
from qrcode.constants import ERROR_CORRECT_H

from library.rpc import Wallet
from utils.forms import Send, Delete, Restore, Secrets
from utils.tokens import generate_token, validate_token
from library.utils import to_atomic, sort_transactions
from utils.factory import cache, bcrypt, docker
from library.helpers import capture_event
from utils.decorators import check_confirmed


@wallet_bp.route("/wallet/setup", methods=["GET", "POST"])
@login_required
@check_confirmed
async def _setup() -> ResponseReturnValue:
    """
    Handles the setup process of the wallet. If the wallet is already created,
    redirects to the dashboard. Otherwise, it presents the option to restore the wallet.

    Returns:
        ResponseReturnValue: The rendered setup page or a redirect to the loading page.
    """
    if current_user.wallet_created:
        return redirect(url_for("wallet._dashboard"))

    else:
        restore_form = await Restore().create_form()

        if await restore_form.validate_on_submit():
            c = await docker.create_wallet(
                current_user.username, restore_form.seed.data
            )
            await cache.store_data(f"init_wallet_{current_user.username}", 30, c)
            await capture_event(current_user.username, "restore_wallet")
            current_user.wallet_created = True
            await current_user.save()
            return redirect(url_for("wallet._loading"))

        else:
            return await render_template(
                "wallet/setup.html", restore_form=restore_form
            )


@wallet_bp.route("/wallet/loading", methods=["GET"])
@login_required
@check_confirmed
async def _loading() -> ResponseReturnValue:
    """
    Renders the loading page while the wallet is being initialized or connected.

    Returns:
        ResponseReturnValue: The rendered loading page or a redirect to the dashboard/setup page.
    """
    if current_user.wallet_created is False:
        return redirect(url_for("wallet._setup"))

    if current_user.wallet_connected and current_user.wallet_created:
        wallet = Wallet(
            host="localhost",
            port=current_user.wallet_port,
            ssl=False,
            username=current_user.username,
            password=current_user.wallet_password,
        )

        if await wallet.connected:
            return redirect(url_for("wallet._dashboard"))

    return await render_template("wallet/loading.html")


@wallet_bp.route("/wallet/dashboard", methods=["GET"])
@login_required
@check_confirmed
async def _dashboard() -> ResponseReturnValue:
    """
    Renders the wallet dashboard, including transfers, balances, and QR code generation.
    Additionally, provides an option to view secrets if the correct token is provided.

    Returns:
        ResponseReturnValue: The rendered dashboard page.
    """
    wallet = Wallet(
        host="127.0.0.1",
        port=current_user.wallet_port,
        ssl=False,
        username=current_user.username,
        password=current_user.wallet_password,
    )

    if not docker.container_exists(current_user.wallet_container):
        await current_user.clear_wallet_data()
        return redirect(url_for("wallet._loading"))

    if not await wallet.connected:
        return redirect(url_for("wallet._loading"))

    send_form = await Send().create_form()
    delete_form = await Delete().create_form()

    address = await wallet.get_address()

    transfers = await wallet.get_transfers()
    transactions = [tx for t in transfers.values() for tx in t]

    balances = await wallet.get_balances()

    uri = f"nerva:{address}?tx_description={current_user.email}"
    qr = QRCode(
        version=1,
        error_correction=ERROR_CORRECT_H,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    logo = Image.open("assets/img/nerva-qr.png").convert("RGBA")
    logo_size = 256
    logo = logo.resize((logo_size, logo_size))
    qr_width, qr_height = qr_img.size
    logo_position = (
        (qr_width - logo_size) // 2,
        (qr_height - logo_size) // 2,
    )
    qr_img.paste(logo, logo_position, mask=logo)

    qr_data = BytesIO()
    qr_img.save(qr_data, format="PNG")
    qr_code = b64encode(qr_data.getvalue()).decode()

    await capture_event(current_user.username, "load_dashboard")

    show_secrets_flag = request.args.get("show_secrets", "false")
    secrets_token = request.args.get("token", None)

    if (
        show_secrets_flag == "true"
        and secrets_token
        and validate_token(secrets_token, 60) == current_user.email
    ):
        mnemonic_seed = await wallet.seed()
        public_spend_key = await wallet.public_spend_key()
        secret_spend_key = await wallet.secret_spend_key()
        public_view_key = await wallet.public_view_key()
        secret_view_key = await wallet.secret_view_key()

        return await render_template(
            "wallet/dashboard.html",
            transactions=transactions,
            sorted_transactions=sort_transactions(transfers),
            balances=balances,
            address=address,
            qr_code=qr_code,
            send_form=send_form,
            delete_form=delete_form,
            user=current_user,
            mnemonic_seed=mnemonic_seed,
            public_spend_key=public_spend_key,
            secret_spend_key=secret_spend_key,
            public_view_key=public_view_key,
            secret_view_key=secret_view_key,
        )

    else:
        secrets_form = await Secrets().create_form()

        return await render_template(
            "wallet/dashboard.html",
            transactions=transactions,
            sorted_transactions=sort_transactions(transfers),
            balances=balances,
            address=address,
            qr_code=qr_code,
            send_form=send_form,
            secrets_form=secrets_form,
            delete_form=delete_form,
            user=current_user,
        )


@wallet_bp.route("/wallet/connect", methods=["GET"])
@login_required
@check_confirmed
async def _connect() -> ResponseReturnValue:
    """
    Connects the user's wallet by starting the Docker container and assigning it to the user.

    Returns:
        ResponseReturnValue: A JSON response indicating success or failure.
    """
    if current_user.wallet_created is False:
        data = {"status": "error", "result": "Wallet not yet created"}
        return jsonify(data)

    if current_user.wallet_connected is False:
        wallet = await docker.start_wallet(current_user.username)

        try:
            port = docker.get_port(wallet)

        except TypeError:
            return jsonify({"status": "error", "result": "Failed to connect wallet"})

        current_user.wallet_connected = docker.container_exists(wallet)
        current_user.wallet_port = port
        current_user.wallet_container = wallet
        current_user.wallet_start = datetime.now(UTC)
        await current_user.save()

        await capture_event(current_user.username, "start_wallet")

        data = {"status": "success", "result": "Wallet has been connected"}

    else:
        data = {"status": "error", "result": "Wallet is already connected"}

    return jsonify(data)


@wallet_bp.route("/wallet/create", methods=["GET"])
@login_required
@check_confirmed
async def _create() -> ResponseReturnValue:
    """
    Creates a new wallet for the user and redirects them to the loading page.

    Returns:
        ResponseReturnValue: A redirect to the loading page.
    """
    if current_user.wallet_created is False:
        c = await docker.create_wallet(current_user.username)
        await cache.store_data(f"init_wallet_{current_user.username}", 30, c)
        await capture_event(current_user.username, "create_wallet")

        await current_user.load()
        current_user.wallet_created = True
        await current_user.save()

        return redirect(url_for("wallet._loading"))

    else:
        return redirect(url_for("wallet._dashboard"))


@wallet_bp.route("/wallet/status", methods=["GET"])
@login_required
@check_confirmed
async def _status() -> ResponseReturnValue:
    """
    Returns the current status of the user's wallet, including whether it is created and connected.

    Returns:
        ResponseReturnValue: A JSON response with the wallet status.
    """
    user_vol = docker.get_user_volume(current_user.username)
    create_container = await cache.get_data(f"init_wallet_{current_user.username}")

    if current_user.wallet_created and current_user.wallet_connected:
        wallet = Wallet(
            host="localhost",
            port=current_user.wallet_port,
            ssl=False,
            username=current_user.username,
            password=current_user.wallet_password,
        )
        wallet_ready = await wallet.connected

    else:
        wallet_ready = False

    return jsonify(
        {
            "created": current_user.wallet_created,
            "connected": current_user.wallet_connected,
            "port": current_user.wallet_port,
            "container": current_user.wallet_container,
            "volume": docker.volume_exists(user_vol),
            "initializing": docker.container_exists(create_container),
            "ready": wallet_ready,
        }
    )


@wallet_bp.route("/wallet/secrets", methods=["GET", "POST"])
@login_required
@check_confirmed
async def _secrets() -> ResponseReturnValue:
    """
    Allows the user to view wallet secrets if they provide the correct password.

    Returns:
        ResponseReturnValue: A redirect to the dashboard with the secrets token or errors.
    """
    secrets_form = await Secrets().create_form()

    if await secrets_form.validate_on_submit():
        password_matches = bcrypt.check_password_hash(
            current_user.password, secrets_form.password.data
        )

        if not password_matches:
            await flash("Invalid password.", "error")
            return redirect(url_for("wallet._dashboard") + "#secrets")

        else:
            _token = generate_token(current_user.email)
            return redirect(
                url_for("wallet._dashboard")
                + f"?show_secrets=true&token={_token}"
                + "#secrets"
            )


@wallet_bp.route("/wallet/send", methods=["GET", "POST"])
@login_required
@check_confirmed
async def _send() -> ResponseReturnValue:
    """
    Handles the process of sending funds from the user's wallet.

    Returns:
        ResponseReturnValue: A redirect to the dashboard with the result of the transaction.
    """
    send_form = await Send().create_form()

    redirect_url = url_for("wallet._dashboard") + "#send"

    wallet = Wallet(
        host="127.0.0.1",
        port=current_user.wallet_port,
        ssl=False,
        username=current_user.username,
        password=current_user.wallet_password,
        timeout=30,
    )

    if await send_form.validate_on_submit():
        address = str(send_form.address.data)
        payment_id = str(send_form.payment_id.data) or None

        if await wallet.connected is False:
            await flash(
                "Wallet RPC interface is unavailable at this time. Please logout and login again.",
                "warning",
            )
            await capture_event(current_user.username, "tx_fail_rpc_unavailable")
            return redirect(redirect_url)

        if not await wallet.validate_address(address):
            await flash("Invalid Nerva address provided.", "error")
            await capture_event(current_user.username, "tx_fail_address_invalid")
            return redirect(redirect_url)

        if send_form.amount.data == "all":
            tx = await wallet.transfer(address, None, "sweep_all")

        else:
            try:
                amount = to_atomic(Decimal(send_form.amount.data))

            except ValueError:
                await flash("Invalid Nerva amount specified.", "error")
                await capture_event(current_user.username, "tx_fail_amount_invalid")
                return redirect(redirect_url)

            if (
                payment_id
                and not len(payment_id) in [16, 32]
                and not all(c in string.hexdigits for c in payment_id)
            ):
                await flash("Invalid payment ID specified.", "error")
                return redirect(redirect_url)

            tx = await wallet.transfer(address, amount, payment_id=payment_id)

        if "message" in tx:
            msg_lower = tx["message"].replace(" ", "_").lower()
            await flash("There was a problem sending the transaction.", "error")
            await capture_event(current_user.username, f"tx_fail_{msg_lower}")
        else:
            await flash("The transaction has been sent.", "success")
            await capture_event(current_user.username, "tx_success")

        return redirect(redirect_url)

    else:
        for field, errors in send_form.errors.items():
            await flash(f"{send_form[field].label}: {', '.join(errors)}", "error")

        return redirect(redirect_url)
