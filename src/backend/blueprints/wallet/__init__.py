from quart import Blueprint

wallet_bp: Blueprint = Blueprint("wallet", __name__, url_prefix="/wallet")

from . import routes as routes  # noqa: E402
