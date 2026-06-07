from quart import Blueprint

meta_bp: Blueprint = Blueprint("meta", __name__, url_prefix="/meta")

from . import routes as routes  # noqa: E402
