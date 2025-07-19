
from flask.blueprints import Blueprint

collection_bp = Blueprint(
    'collection',
    __name__,
    url_prefix='/collection',
    static_folder='static', 
    template_folder='templates', 
    static_url_path='/static/collection'
)

from . import routes