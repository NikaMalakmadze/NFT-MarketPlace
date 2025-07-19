
from flask.blueprints import Blueprint

collection_category_api_bp = Blueprint(
    'collection-category-api',
    __name__, 
    url_prefix='/collection-category'
)

from . import routes