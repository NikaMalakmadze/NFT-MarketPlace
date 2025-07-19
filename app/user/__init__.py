
from flask.blueprints import Blueprint

user_bp = Blueprint(
    'user', 
    __name__, 
    static_folder='static', 
    template_folder='templates', 
    static_url_path='/static/user',
    url_prefix='/user'
)

from . import routes