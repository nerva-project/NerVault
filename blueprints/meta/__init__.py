from quart import Blueprint

# Blueprint for meta-related routes
meta_bp: Blueprint = Blueprint("meta", __name__)

# Import routes for the 'meta' blueprint
from . import routes as routes  # noqa: E402
