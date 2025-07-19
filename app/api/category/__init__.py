
from flask.blueprints import Blueprint

category_api_bp = Blueprint('category-api', __name__, url_prefix='/category')

from . import routes