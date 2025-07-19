
from flask.blueprints import Blueprint

jwt_bp = Blueprint('jwt', __name__, url_prefix='/jwt')

from app.jwt import routes