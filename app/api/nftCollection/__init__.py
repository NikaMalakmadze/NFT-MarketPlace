
from flask.blueprints import Blueprint

nft_collection_api_bp = Blueprint(
    'nft-collection-api',
    __name__,
    url_prefix='/nft-collection'
)

from . import routes