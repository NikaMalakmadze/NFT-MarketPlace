
from flask.blueprints import Blueprint

allowed_wallets_bp = Blueprint('allowed_wallets', __name__, url_prefix='/allowed-wallets')

from . import routes