
from flask.blueprints import Blueprint

search_api_bp = Blueprint(
    'seacrh-api',
    __name__,
    url_prefix='/search'
)

from . import routes