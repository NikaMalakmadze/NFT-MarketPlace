
from flask.blueprints import Blueprint

nft_api_bp = Blueprint('nft-api', __name__, url_prefix='/nft')

from . import routes