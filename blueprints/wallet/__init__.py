from __future__ import annotations

from quart import Blueprint

# Blueprint for wallet-related routes
wallet_bp: Blueprint = Blueprint("wallet", __name__)

# Import routes for the 'wallet' blueprint
from . import routes
