from blueprints.meta import meta_bp

from quart import jsonify, url_for, redirect, render_template
from quart.typing import ResponseReturnValue

from utils.factory import db, cache, daemon
from library.docker import Docker
from library.helpers import on_maintenance


@meta_bp.route("/", methods=["GET"])
async def _index() -> ResponseReturnValue:
    """
    Renders the homepage with information about the node and coin.

    Returns:
        ResponseReturnValue: The rendered template with node and coin info.
    """
    return await render_template(
        "meta/index.html",
        node=(await daemon.get_info()),
        info=(await cache.get_coin_info()),
    )


@meta_bp.route("/faq", methods=["GET"])
async def _faq() -> ResponseReturnValue:
    """
    Renders the FAQ page.

    Returns:
        ResponseReturnValue: The rendered FAQ template.
    """
    return await render_template("meta/faq.html")


@meta_bp.route("/terms", methods=["GET"])
async def _terms() -> ResponseReturnValue:
    """
    Renders the terms and conditions page.

    Returns:
        ResponseReturnValue: The rendered terms and conditions template.
    """
    return await render_template("meta/terms.html")


@meta_bp.route("/privacy", methods=["GET"])
async def _privacy() -> ResponseReturnValue:
    """
    Renders the privacy policy page.

    Returns:
        ResponseReturnValue: The rendered privacy policy template.
    """
    return await render_template("meta/privacy.html")


@meta_bp.route("/status", methods=["GET"])
async def _status() -> ResponseReturnValue:
    """
    Returns the system status, including the health of the valkey, MongoDB, and Docker.

    Returns:
        ResponseReturnValue: A JSON response with the status of valkey, MongoDB, and Docker.
    """
    return jsonify(
        {
            "valkey": (await cache.valkey.ping()),
            "mongodb": (await db.client.admin.command("ping")) == {"ok": 1.0},
            "docker": Docker().client.ping(),
        }
    ), 200


@meta_bp.route("/maintenance", methods=["GET"])
async def _maintenance() -> ResponseReturnValue:
    """
    Checks if the system is under maintenance and renders the appropriate page.

    If the system is under maintenance, it renders the maintenance page.
    Otherwise, it redirects to the homepage.

    Returns:
        ResponseReturnValue: A rendered maintenance page or a redirect to the homepage.
    """
    if await on_maintenance():
        return await render_template("meta/maintenance.html"), 503
    else:
        return redirect(url_for("meta._index"))
