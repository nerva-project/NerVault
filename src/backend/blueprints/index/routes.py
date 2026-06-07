from importlib.metadata import (
    PackageNotFoundError,
    version as pkg_version,
)

from quart import Response, jsonify
from quart_rate_limiter import rate_exempt

from . import index_bp

try:
    APP_VERSION = pkg_version("NerVault")
except PackageNotFoundError:
    APP_VERSION = "0.0.0"


@index_bp.route("/", methods=["GET"])
@rate_exempt
async def _index() -> tuple[Response, int]:
    return jsonify(
        {
            "name": "NerVault",
            "version": APP_VERSION,
            "status": "ok",
        }
    ), 200
