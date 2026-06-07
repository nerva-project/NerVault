from quart import Blueprint

auth_bp: Blueprint = Blueprint("auth", __name__, url_prefix="/auth")

from . import routes as routes  # noqa: E402
