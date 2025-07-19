
from flask.blueprints import Blueprint

admin_api_bp = Blueprint(
    'admin-api',
    __name__,
    url_prefix='/admin'
)

from . import routes