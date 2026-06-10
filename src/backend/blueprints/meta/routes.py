from quart import Response, jsonify
from quart_rate_limiter import rate_exempt

from backend.factory import db, cache, daemon, docker
from backend.library.helpers import on_maintenance

from . import meta_bp


@meta_bp.route("/info", methods=["GET"])
async def _info() -> tuple[Response, int]:
    """
    Returns node information and cached coin market data for the home page.
    """
    try:
        node = await daemon.get_info()
    except Exception:
        node = {}

    return jsonify(
        {
            "status": "success",
            "result": {
                "node": node,
                "coin": (await cache.get_coin_info()),
            },
        }
    ), 200


@meta_bp.route("/status", methods=["GET"])
@rate_exempt
async def _status() -> tuple[Response, int]:
    """
    Returns the health of the application's backing services.
    """
    return jsonify(
        {
            "status": "success",
            "result": {
                "redis": (await cache.redis.ping()),  # type: ignore[misc]
                "mongodb": (await db.client.admin.command("ping")) == {"ok": 1.0},
                "docker": docker.client.ping(),
            },
        }
    ), 200


@meta_bp.route("/maintenance", methods=["GET"])
@rate_exempt
async def _maintenance() -> tuple[Response, int]:
    """
    Returns whether the application is currently in maintenance mode.
    """
    return jsonify(
        {
            "status": "success",
            "result": {"maintenance": await on_maintenance()},
        }
    ), 200
