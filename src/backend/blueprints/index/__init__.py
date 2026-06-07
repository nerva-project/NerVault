from quart import Blueprint

index_bp: Blueprint = Blueprint("index", __name__)

from . import routes as routes  # noqa: E402
