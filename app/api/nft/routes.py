
from datetime import datetime, timezone
from decimal import Decimal
from flask import abort
from werkzeug.datastructures.file_storage import FileStorage
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload 
from pydantic import ValidationError
from flask.globals import request, g
from requests import Response, get
from flask.json import jsonify
from sqlalchemy import func
from uuid import uuid4

from app.api.nft.schemas import NFTCreate, NFTCreateResponse, NFTFilterSchema, OfferCreate
from app.nft.models import NFT, Category, Like, Offer, NFTView
from app.collection.models import NFTCollection
from app.jwt.decorators import jwt_required
from app.utils import allowed_image_type
from app.api.nft import nft_api_bp
from app.user.models import User
from app.extensions import db
from config import settings

@nft_api_bp.route('/create', methods=['POST'])
@jwt_required
def create_nft(): 

    if 'image_url' not in request.files:
        return jsonify({'errors': ['No image file in request']}), 400
    
    file: FileStorage = request.files['image_url']

    if file.filename == '':
        return jsonify({'errors': ['No file selected']}), 400
        
    if file and allowed_image_type(file.filename):
        filename: str = f'{uuid4().hex}-{secure_filename(file.filename)}'
        file.save(settings.db.UPLOAD_FOLDER / 'nft-images' / filename)
    else:
        return jsonify({'errors': ['Invalid file type']}), 400

    form_data = request.form.to_dict()

    form_data['image_url'] = file.filename

    if len(form_data.keys()) != 6:
        return jsonify({'errors': ['Not Enough Data']})
    
    try:
        data: NFTCreate = NFTCreate(**form_data)
    except ValidationError as e:
        errors = e.errors()
        error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in errors]
        return jsonify({'status': 'error', 'errors': error_messages}), 400
    
    user_jwt_payload: dict = g.get('jwt_payload', None)
    if not user_jwt_payload:
        return jsonify({'status': 'error', 'errors': ['Invalid Token']}), 400

    nft = NFT(
        token_id=str(uuid4()),
        name=data.name.strip(),
        description=data.description.strip(),
        image_file=filename,
        price=data.price,
        category_id=data.category_id,
        creator_id=user_jwt_payload.get('user_id'),
        owner_id=user_jwt_payload.get('user_id'),
    )

    if data.collection_id != 'NoCategory':

        collection = NFTCollection.query.get(data.collection_id)
        if not collection:
            return jsonify({'status': 'error', 'errors': ['Invalid collection ID']}), 400

        nft.collection_id = collection.id

    db.session.add(nft)
    db.session.commit()

    return jsonify(NFTCreateResponse.model_validate(nft.to_dict()).model_dump()), 200

@nft_api_bp.route('/get-category-nfts/<int:category_id>', methods=['GET'])
def get_nft_by_category(category_id):
    category: Category = Category.query.filter_by(id=category_id).first()
    if not category:
        return jsonify({'errors': ["Category with that id does't exists"]}), 400
    
    try:

        category_nfts: list[NFT] = (
            db.session.query(NFT)
            .outerjoin(NFT.likes)
            .options(joinedload(NFT.likes))
            .filter(NFT.category_id == category.id, NFT.is_blocked == False)
            .group_by(NFT.id)
            .order_by(func.count(Like.id).desc())
            .limit(5)
            .all()
        )
    
    except NotImplementedError:
        return jsonify(
        {'status': 'success', 'nfts': []}
    ), 200

    category_nfts_dicts: list[dict] = [nft.info() for nft in category_nfts]
    return jsonify(
        {'status': 'success', 'nfts': category_nfts_dicts}
    ), 200

@nft_api_bp.route('<token_id>/like-nft', methods=['GET'])
@jwt_required
def like_nft(token_id):

    nft: NFT = NFT.query.filter_by(token_id=token_id).first()

    if not nft:
        return jsonify({'status': 'not found'}), 404
    
    if nft.is_blocked:
        return abort(403)
    
    user_jwt_payload: dict = g.get('jwt_payload', None)
    if not user_jwt_payload:
        return jsonify({'status': 'error', 'errors': ['Invalid Token']}), 400
    
    nft_liked: Like = Like.query.filter_by(
        user_id=user_jwt_payload.get('user_id'), 
        token_id=nft.token_id
    ).first()

    if not nft_liked:

        nft_like = Like(
            nft_id=nft.id,
            token_id=nft.token_id,
            user_id=user_jwt_payload.get('user_id')
        )
        db.session.add(nft_like)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'liked', 'user': nft_like.to_dict()}), 200

    else:
        db.session.delete(nft_liked)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'unLiked'}), 200
    
@nft_api_bp.route('/price/<token_id>')
def get_rate(token_id):
    response: Response = get("https://api.coinbase.com/v2/exchange-rates?currency=ETH")

    if not response or response.status_code != 200:
        return jsonify({'status': 'not found', 'errors': ['not found']}), 404
    
    value = round(float(response.json()['data']['rates']['USD']), 2)

    nft: NFT = NFT.query.filter_by(token_id=token_id).first()

    if not nft:
        return jsonify({'status': 'not found'}), 404
    
    if nft.is_blocked:
        return abort(403)
    
    in_usd = round(float(nft.price) * value, 2)

    return jsonify({'status': 'success', 'price': in_usd})

@nft_api_bp.route('<string:token_id>/offer', methods=['POST'])
@jwt_required
def make_offer(token_id):
    nft: NFT = NFT.query.filter_by(token_id=token_id).first()
    if not nft:
        return jsonify({'errors': ['Not Found']}), 404

    if nft.is_blocked or nft.owner.is_blocked:
        return abort(403)

    user_jwt_payload: dict = g.get('jwt_payload', None)
    if not user_jwt_payload:
        return jsonify({'status': 'error', 'errors': ['Invalid Token']}), 400
    
    user_id: int = user_jwt_payload.get('user_id')

    if int(user_id) == nft.creator_id and int(user_id) == nft.owner_id:
        return jsonify({'status': 'error', 'errors': ['Can not make offer to owned nft']}), 400
    
    user: User = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'errors': ['Not Found']}), 404

    data = request.get_json()

    try:
        validated = OfferCreate(**data)
    except ValidationError as e:
        errors = e.errors()
        error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in errors]
        return jsonify({'status': 'error', 'errors': error_messages}), 400

    if validated.amount > user.balance:
        return jsonify({'status': 'error', 'errors': ['Not Enough Balance']}), 400
    
    if validated.amount <= 0:
        return jsonify({'status': 'error', 'errors': ['Invalid Amount']}), 400
    
    existing_offer: Offer = Offer.query.filter(
        Offer.nft_id == nft.id,
        Offer.owner_id == nft.owner_id,
        Offer.buyer_id == user_id,
        Offer.is_accepted == False,
        Offer.is_cancelled == False,
        Offer.expires_at > datetime.now(timezone.utc)
    ).first()

    if existing_offer:
        return jsonify({'status': 'error', 'errors': ['You already have an active offer for this NFT']}), 400

    expires_at: datetime = datetime.now(timezone.utc) + validated.expires_delta

    offer = Offer(
        nft_id=nft.id,
        buyer_id=user_id,
        owner_id=nft.owner_id,
        amount=validated.amount,
        expires_at=expires_at,
        price_at_offer=nft.price
    )

    db.session.add(offer)
    db.session.commit()

    return jsonify({'message': 'Offer submitted successfully'}), 200

@nft_api_bp.route('/<token_id>/unlist', methods=['POST'])
@jwt_required
def unlist_nft(token_id):
    nft: NFT = NFT.query.filter_by(token_id=token_id).first()
    if not nft:
        return jsonify({'errors': ['Not Found']}), 404

    if nft.is_blocked:
        return abort(403)

    user_jwt_payload: dict = g.get('jwt_payload', None)
    if not user_jwt_payload:
        return jsonify({'status': 'error', 'errors': ['Invalid Token']}), 400
    
    user_id: int = user_jwt_payload.get('user_id')

    if int(user_id) not in (nft.creator_id, nft.owner_id):
        return jsonify({'status': 'error', 'errors': ['Can not unlist item if you does not own it']}), 400
    
    nft.is_listed = False

    db.session.commit()

    return jsonify({'message': 'unlisted successfully'}), 200

@nft_api_bp.route('/<token_id>/list', methods=['POST'])
@jwt_required
def list_nft(token_id):
    nft: NFT = NFT.query.filter_by(token_id=token_id).first()
    if not nft:
        return jsonify({'errors': ['Not Found']}), 404

    if nft.is_blocked:
        return abort(403)

    user_jwt_payload: dict = g.get('jwt_payload', None)
    if not user_jwt_payload:
        return jsonify({'status': 'error', 'errors': ['Invalid Token']}), 400
    
    user_id: int = user_jwt_payload.get('user_id')

    if int(user_id) not in (nft.creator_id, nft.owner_id):
        return jsonify({'status': 'error', 'errors': ['Can not list item if you does not own it']}), 400
    
    nft.is_listed = True

    db.session.commit()

    return jsonify({'message': 'Offer submitted successfully'}), 200

@nft_api_bp.route('/<token_id>/buy', methods=['POST'])
@jwt_required
def buy_nft(token_id):
    nft: NFT = NFT.query.filter_by(token_id=token_id).first()
    if not nft:
        return jsonify({'errors': ['Not Found']}), 404

    if nft.is_blocked or nft.owner.is_blocked:
        return abort(403)

    user_jwt_payload: dict = g.get('jwt_payload', None)
    if not user_jwt_payload:
        return jsonify({'status': 'error', 'errors': ['Invalid Token']}), 400
    
    user_id: int = user_jwt_payload.get('user_id')

    if int(user_id) == nft.owner_id:
        return jsonify({'status': 'error', 'errors': ['Can not buy item if you already own it']}), 400
    
    user: User = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'errors': ['Not Found']}), 404
    
    if user.balance < nft.price:
        return jsonify({'status': 'error', 'errors': ['Not Enough Balance']}), 400
    
    user.balance -= nft.price
    previous_owner: User = User.query.get(nft.owner_id)

    royalty = Decimal("0")
    collection_owner: User = None

    if nft.collection:
        collection_owner = User.query.get(nft.collection.user_id)
        royalty = nft.price * (nft.collection.royalty / 100)

    if previous_owner:
        if collection_owner and previous_owner.id == collection_owner.id:
            previous_owner.balance += nft.price
        else:
            if collection_owner:
                collection_owner.balance += royalty
            previous_owner.balance += nft.price - royalty

    nft.owner_id = user.id
    nft.is_listed = False

    db.session.commit()

    return jsonify({'message': 'Offer submitted successfully'}), 200

@nft_api_bp.route('/filter', methods=['POST'])
def drops_filter():
    try:
        filters: NFTFilterSchema = NFTFilterSchema(**request.get_json())
    except ValidationError as e:
        errors = e.errors()
        error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in errors]
        return jsonify({'status': 'error', 'errors': error_messages}), 400

    query = NFT.query.filter(NFT.is_blocked == False)

    if filters.categoryInputs:
        query = query.filter(NFT.category_id.in_(filters.categoryInputs))

    query = query.filter(NFT.price >= filters.minValue)

    if filters.maxValue != -1:
        query = query.filter(NFT.price <= filters.maxValue)

    if filters.isListedInputs:
        if 1 in filters.isListedInputs and 2 in filters.isListedInputs: 
            pass
        elif 1 in filters.isListedInputs:
            query = query.filter(NFT.is_listed.is_(True))
        elif 2 in filters.isListedInputs:
            query = query.filter(NFT.is_listed.is_(False))

    if filters.search:
        search_term = f"%{filters.search.strip().lower()}%"
        query = query.filter(func.lower(NFT.name).like(search_term))

    if filters.sortBy == 1:
        query = (
            query.outerjoin(Offer)
            .group_by(NFT.id)
            .order_by(func.count(Offer.id).desc()
        )
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

    if filters.fileTypeInputs:
        nfts: list[NFT] = [nft for nft in nfts if nft.extension_id in filters.fileTypeInputs]

    return jsonify({'nfts': [nft.info() for nft in nfts]}), 200