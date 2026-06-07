from quart import Blueprint

from .auth import auth_bp
from .meta import meta_bp
from .index import index_bp
from .wallet import wallet_bp

__all__ = ["api_bp", "auth_bp", "index_bp", "meta_bp", "wallet_bp"]

api_bp: Blueprint = Blueprint("api", __name__, url_prefix="/v1")

api_bp.register_blueprint(index_bp)
api_bp.register_blueprint(auth_bp)
api_bp.register_blueprint(meta_bp)
api_bp.register_blueprint(wallet_bp)
