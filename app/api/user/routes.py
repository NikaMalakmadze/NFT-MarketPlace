
from datetime import datetime, timezone
from flask import g, jsonify, request
from pydantic import ValidationError
from decimal import Decimal

from sqlalchemy import func

from app.api.user.schemas import UserProfileFilters, UserProfileUpdate
from app.nft.models import NFT, Like, NFTView, Offer
from app.api.user.utils import validate_user_id
from app.jwt.decorators import jwt_required
from app.api.utils import update_old_image
from app.api.user import user_api_bp
from app.user.models import User
from app.extensions import db
from config import settings

@user_api_bp.route('/<int:user_id>/update', methods=['POST'])
@jwt_required
def update_profile(user_id):
    user_jwt_payload: dict = g.get('jwt_payload', None)
    if not user_jwt_payload:
        return jsonify({'status': 'error', 'errors': ['Invalid Token']}), 400
    
    if user_jwt_payload.get('user_id') != user_id:
        return jsonify({'status': 'error', 'errors': ['Unauthorized']}), 401
    
    user: User = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'status': 'error', 'errors': ['No such User']}), 404

    form_data: dict = request.form.to_dict()
    bg_file = request.files.get('profile_background')
    avatar_file = request.files.get('profile_avatar')

    if bg_file:
        user.profile_background = update_old_image(
            file=bg_file,
            old_filename=user.profile_background,
            upload_dir=settings.db.UPLOAD_FOLDER / 'user-bg',
            default_filename='defaultAvatar.png'
        )

    if avatar_file:
        user.profile_avatar = update_old_image(
            file=avatar_file,
            old_filename=user.profile_avatar,
            upload_dir=settings.db.UPLOAD_FOLDER / 'user-logo',
            default_filename='defaultBg.png'
        )
            
    try:
        data: UserProfileUpdate = UserProfileUpdate(**form_data)
    except ValidationError as e:
        errors = e.errors()
        error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in errors]
        return jsonify({'status': 'error', 'errors': error_messages}), 400
    
    if User.query.filter(User.email == data.email, User.id != user_id).first():
        return jsonify({'status': 'error', 'errors': ['Email already in use']}), 409

    user.display_name = data.display_name
    user.email = data.email
    user.bio = data.bio
    user.updated_at = datetime.now(timezone.utc)

    db.session.commit()

    return jsonify({'status': 'success', 'message': 'updated'}), 200

@user_api_bp.route('/<int:user_id>', methods=['POST'])
def get_user_created_nfts(user_id: int):
    validated_user = validate_user_id(user_id)
    if isinstance(validated_user, tuple): 
        return validated_user
    
    try:
        filters: UserProfileFilters = UserProfileFilters(**request.get_json())
    except ValidationError as e:
        errors = e.errors()
        error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in errors]
        return jsonify({'status': 'error', 'errors': error_messages}), 400

    query = NFT.query

    if filters.currentTab == 1:
        query = query.filter(NFT.owner_id == validated_user.id)

    elif filters.currentTab == 2:
        query = query.filter(NFT.creator_id == validated_user.id)

    if filters.search:
        search_term = f"%{filters.search.strip().lower()}%"
        query = query.filter(func.lower(NFT.name).like(search_term))

    if filters.sortBy == 1:
        query = (
            query.outerjoin(Offer)
            .group_by(NFT.id)
            .order_by(func.count(Offer.id).desc())
    )
    elif filters.sortBy == 2:
        query = query.order_by(NFT.price.asc())
    elif filters.sortBy == 3:
        query = query.order_by(NFT.price.desc())
    elif filters.sortBy == 4:
        query = query.order_by(NFT.created_at.asc())
    elif filters.sortBy == 5:
        query = query.order_by(NFT.created_at.desc())
    elif filters.sortBy == 6:
        query = (
            query.outerjoin(NFTView)
            .group_by(NFT.id)
            .order_by(func.count(NFTView.id).desc())
        )
    elif filters.sortBy == 7:
        query = (
            query.outerjoin(Like)
            .group_by(NFT.id)
            .order_by(func.count(Like.id).desc())
        )

    nfts = query.all()

    user_nfts_dicts = [nft.info() for nft in nfts]

    return jsonify(
        {'status': 'success', 'data': user_nfts_dicts}
    ), 200

@user_api_bp.route('/my', methods=['POST'])
@jwt_required
def user_private_api():
    user_jwt_payload: dict = g.get('jwt_payload', None)
    if not user_jwt_payload:
        return jsonify({'status': 'error', 'errors': ['Invalid Token']}), 400
    
    user_id = user_jwt_payload.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'errors': ['Invalid Token']}), 400

    validated_user = validate_user_id(user_id)
    if isinstance(validated_user, tuple): 
        return validated_user
    
    try:
        filters: UserProfileFilters = UserProfileFilters(**request.get_json())
    except ValidationError as e:
        errors = e.errors()
        error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in errors]
        return jsonify({'status': 'error', 'errors': error_messages}), 400

    if filters.currentTab == 5:
        query = (
            db.session.query(NFT)
            .join(Like, NFT.id == Like.nft_id)
            .filter(Like.user_id == validated_user.id)
            .group_by(NFT.id)
        )
    else:
        query = NFT.query
    
    if filters.search:
        search_term = f"%{filters.search.strip().lower()}%"
        query = query.filter(func.lower(NFT.name).like(search_term))
    
    if filters.sortBy == 1:
        query = (
            query.outerjoin(Offer)
            .group_by(NFT.id)
            .order_by(func.count(Offer.id).desc())
    )
    elif filters.sortBy == 2:
        query = query.order_by(NFT.price.asc())
    elif filters.sortBy == 3:
        query = query.order_by(NFT.price.desc())
    elif filters.sortBy == 4:
        query = query.order_by(NFT.created_at.asc())
    elif filters.sortBy == 5:
        query = query.order_by(NFT.created_at.desc())
    elif filters.sortBy == 6:
        query = (
            query.outerjoin(NFTView)
            .group_by(NFT.id)
            .order_by(func.count(NFTView.id).desc())
        )
    elif filters.sortBy == 7:
        query = (
            query.outerjoin(Like)
            .group_by(NFT.id)
            .order_by(func.count(Like.id).desc())
        )

    nfts = query.all()

    user_nfts_dicts: list[dict] = [nft.info() for nft in nfts]

    return jsonify(
        {'status': 'success', 'data': user_nfts_dicts}
    ), 200

@user_api_bp.route('/offers', methods=['GET'])
@jwt_required
def get_offers():
    user_jwt_payload: dict = g.get('jwt_payload', None)
    if not user_jwt_payload:
        return jsonify({'status': 'error', 'errors': ['Invalid Token']}), 400
    
    user_id = user_jwt_payload.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'errors': ['Invalid Token']}), 400

    validated_user = validate_user_id(user_id)
    if isinstance(validated_user, tuple): 
        return validated_user
    
    offers: list[Offer] = Offer.query.filter_by(owner_id=user_id).all()

    user_offers_dicts: list[dict] = [offer.info() for offer in offers if offer.is_active]

    return jsonify(
        {'status': 'success', 'data': user_offers_dicts}
    ), 200
    
@user_api_bp.route('/offers/<int:offer_id>/reject', methods=['POST'])
@jwt_required
def reject_offer(offer_id):
    user_jwt_payload: dict = g.get('jwt_payload')
    if not user_jwt_payload:
        return jsonify({'status': 'error', 'errors': ['Invalid token']}), 400

    user_id = user_jwt_payload.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'errors': ['Invalid token payload']}), 400

    offer: Offer = Offer.query.get(offer_id)
    if not offer:
        return jsonify({'status': 'error', 'errors': ['Offer not found']}), 404

    if int(user_id) != offer.owner_id:
        return jsonify({'status': 'error', 'errors': ['Not authorized to reject this offer']}), 403

    if offer.is_accepted:
        return jsonify({'status': 'error', 'errors': ['Offer already accepted']}), 400
    if offer.is_cancelled:
        return jsonify({'status': 'error', 'errors': ['Offer already cancelled/rejected']}), 400

    offer.is_cancelled = True
    db.session.commit()

    return jsonify({'message': 'Offer rejected successfully'}), 200

@user_api_bp.route('/offers/<int:offer_id>/accept', methods=['POST'])
@jwt_required
def accept_offer(offer_id):
    user_jwt_payload: dict = g.get('jwt_payload')
    if not user_jwt_payload:
        return jsonify({'status': 'error', 'errors': ['Invalid token']}), 400

    user_id = user_jwt_payload.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'errors': ['Invalid token payload']}), 400

    offer: Offer = Offer.query.get(offer_id)
    if not offer:
        return jsonify({'status': 'error', 'errors': ['Offer not found']}), 404

    if int(user_id) != offer.owner_id:
        return jsonify({'status': 'error', 'errors': ['Not authorized to reject this offer']}), 403

    if offer.is_accepted:
        return jsonify({'status': 'error', 'errors': ['Offer already accepted']}), 400
    if offer.is_cancelled:
        return jsonify({'status': 'error', 'errors': ['Offer already cancelled/rejected']}), 400
    
    if not offer.is_active:
        return jsonify({"status": "error", "errors": ["Offer has expired"]}), 400
    
    nft: NFT = offer.nft
    if nft.owner_id != user_id:
        return jsonify({"status": "error", "errors": ["You are not the owner of this NFT"]}), 403
    
    seller: User = nft.owner
    buyer: User = offer.buyer

    if buyer.balance < offer.amount:
        return jsonify({"status": "error", "errors": ["Buyer has insufficient funds"]}), 400

    buyer.balance -= offer.amount
    seller.balance += offer.amount

    nft.owner_id = buyer.id
    nft.price = offer.amount
    offer.is_accepted = True

    other_offers: list[Offer] = Offer.query.filter(
        Offer.nft_id == nft.id,
        Offer.id != offer.id,
        Offer.is_accepted.is_(False),
        Offer.is_cancelled.is_(False)
    ).all()

    for other in other_offers:
        other.is_cancelled = True

    db.session.commit()

    return jsonify({"status": "success", "message": "Offer accepted, NFT transferred, other offers cancelled"}), 200

@user_api_bp.route('/offers/completed', methods=["GET"])
@jwt_required
def get_completed_offers():
    user_jwt_payload = g.get("jwt_payload", {})
    user_id = user_jwt_payload.get("user_id")

    if not user_id:
        return jsonify({"status": "error", "errors": ["Unauthorized"]}), 401

    sold_offers: list[Offer] = Offer.query.filter(
        Offer.is_accepted == True
    ).order_by(Offer.created_at.desc()).all()

    user_offers_dicts: list[dict] = [offer.info() for offer in sold_offers]

    return jsonify({'status': 'success', 'data': user_offers_dicts}), 200

@user_api_bp.route('/<int:user_id>/add-funds', methods=['POST'])
@jwt_required
def add_funds(user_id):
    user_jwt_payload: dict = g.get('jwt_payload', None)
    if not user_jwt_payload:
        return jsonify({'status': 'error', 'errors': ['Invalid Token']}), 400
    
    if user_jwt_payload.get('user_id', None) != user_id:
        return jsonify({'status': 'error', 'errors': ['Invalid Token']}), 401

    validated_user = validate_user_id(user_id)
    if isinstance(validated_user, tuple): 
        return validated_user
    
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'errors': ['No Data']}), 400
    
    try:
        amount = Decimal(str(data['amount']))
    except (TypeError, ValueError):
        return jsonify({'errors': ['Invalid amount format']}), 400

    validated_user.balance += amount

    db.session.commit()

    return jsonify({'status': 'success'}), 200

