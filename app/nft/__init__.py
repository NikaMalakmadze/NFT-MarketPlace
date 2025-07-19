
from flask.blueprints import Blueprint

nft_bp = Blueprint(
    'nft', 
    __name__, 
    url_prefix='/nft',
    static_folder='static', 
    template_folder='templates', 
    static_url_path='/static/nft',
)

from . import routes
