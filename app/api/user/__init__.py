
from flask.blueprints import Blueprint

user_api_bp = Blueprint('user-api', __name__, url_prefix='/user')

from . import routes