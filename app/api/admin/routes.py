
from datetime import datetime, timezone
from flask import g, jsonify

from app.api.admin.utils import serialize_collection, serialize_like, serialize_nft, serialize_offer, serialize_user, serialize_view
from app.jwt.decorators import admin_required, jwt_required
from app.nft.models import NFT, Like, NFTView, Offer
from app.collection.models import NFTCollection
from app.api.admin import admin_api_bp
from app.user.models import User
from app.extensions import db

@admin_api_bp.route('/users', methods=['GET'])
@jwt_required
@admin_required
def get_users():
    users: list[User] = User.query.all()

    users_dicts: list[dict] = [serialize_user(user) for user in users]

    return jsonify({'status': 'success', 'users': users_dicts}), 200

@admin_api_bp.route('/users/<int:user_id>/status', methods=['PATCH'])
@jwt_required
@admin_required
def toggle_user_status(user_id):
    user: User = User.query.filter_by(id=user_id).first_or_404()
    
    user_jwt_payload: dict = g.get('jwt_payload', None)
    if not user_jwt_payload:
        return jsonify({'status': 'error', 'errors': ['Invalid Token']}), 400

    if user_jwt_payload.get('user_id') == user_id:
        return jsonify('error'), 400

    current_status = user.is_blocked
    user.is_blocked = False if current_status else True
    db.session.commit()

    return jsonify({"status": 'blocked' if user.is_blocked else 'active'}), 200

@admin_api_bp.route('/nfts', methods=['GET'])
@jwt_required
@admin_required
def get_nfts():
    nfts: list[NFT] = NFT.query.all()

    nfts_dicts: list[dict] = [serialize_nft(nft) for nft in nfts]

    return jsonify({'status': 'success', 'nfts': nfts_dicts}), 200

@admin_api_bp.route('/nfts/<string:token_id>/status', methods=['PATCH'])
@jwt_required
@admin_required
def toggle_nft_status(token_id):
    nft: NFT = NFT.query.filter_by(token_id=token_id).first_or_404()

    current_status = nft.is_blocked
    nft.is_blocked = False if current_status else True
    db.session.commit()

    return jsonify({"status": 'blocked' if nft.is_blocked else 'active'}), 200

@admin_api_bp.route('/collections', methods=['GET'])
@jwt_required
@admin_required
def get_collections():
    collections: list[NFTCollection] = NFTCollection.query.all()

    collections_dicts: list[dict] = [serialize_collection(nft) for nft in collections]

    return jsonify({'status': 'success', 'collections': collections_dicts}), 200

@admin_api_bp.route('/offers', methods=['GET'])
@jwt_required
@admin_required
def get_offers():
    offers: list[Offer] = Offer.query.all()

    offers_dicts: list[dict] = [serialize_offer(offer) for offer in offers]

    return jsonify({'status': 'success', 'offers': offers_dicts}), 200

@admin_api_bp.route("/offers/<int:offer_id>/cancel", methods=["PATCH"])
@jwt_required
@admin_required
def admin_cancel_offer(offer_id):
    offer: Offer = Offer.query.get(offer_id)
    if not offer:
        return jsonify({"status": "error", "message": "Offer not found"}), 404

    if offer.is_cancelled:
        return jsonify({"status": "info", 'data': 'cancelled', "message": "Offer is already Expired."}), 200
    
    if offer.is_accepted:
        return jsonify({"status": "info", 'data': 'accepted', "message": "Offer is already accepted."}), 200

    offer.is_cancelled = True
    db.session.commit()

    return jsonify({"status": "success", 'data': 'cancelled', "message": "Offer successfully canceled."}), 200

@admin_api_bp.route('/analytics', methods=['GET'])
@jwt_required
@admin_required
def get_activity():
    likes: list[Like] = Like.query.all()
    views: list[NFTView] = NFTView.query.all()

    activity_dicts: list[dict] = [serialize_view(view) for view in views] + [serialize_like(like) for like in likes]

    return jsonify({'status': 'success', 'activity': activity_dicts}), 200