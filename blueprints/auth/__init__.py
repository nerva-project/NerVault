from __future__ import annotations

from quart import Blueprint

# Blueprint for authentication-related routes
auth_bp: Blueprint = Blueprint("auth", __name__)

# Import routes for the 'auth' blueprint
from . import routes
