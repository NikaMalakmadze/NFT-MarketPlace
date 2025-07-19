
from app.api.collectionCategory import collection_category_api_bp
from app.api.nftCollection import nft_collection_api_bp
from app.api.allowedwallets import allowed_wallets_bp
from app.api.category import category_api_bp
from app.api.search import search_api_bp
from app.api.admin import admin_api_bp
from app.api.user import user_api_bp
from app.api.nft import nft_api_bp
from app.api import api_bp

api_bp.register_blueprint(collection_category_api_bp)
api_bp.register_blueprint(nft_collection_api_bp)
api_bp.register_blueprint(allowed_wallets_bp)
api_bp.register_blueprint(category_api_bp)
api_bp.register_blueprint(search_api_bp)
api_bp.register_blueprint(admin_api_bp)
api_bp.register_blueprint(user_api_bp)
api_bp.register_blueprint(nft_api_bp)