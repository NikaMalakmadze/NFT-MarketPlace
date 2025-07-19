
from decimal import ROUND_HALF_UP, Decimal
from pydantic import ValidationError
from flask.globals import request, g
from flask.json import jsonify
from sqlalchemy import func

from app.api.nftCollection.schemas import NFTCollectionFilters, NFTCollectionResponse
from app.api.nftCollection import nft_collection_api_bp
from app.collection.schemas import CollectionCreate
from app.collection.models import NFTCollection
from app.jwt.decorators import jwt_required
from app.api.utils import validate_image
from app.nft.models import NFT, Like, NFTView, Offer
from app.extensions import db
from config import settings

@nft_collection_api_bp.route('/create-collection', methods=['POST'])
@jwt_required
def create_collection():
    form_data: dict = request.form.to_dict()

    validated_logo = validate_image(
        'logo_image',
        settings.db.UPLOAD_FOLDER / 'collection-logo',
        form_data
    )

    if isinstance(validated_logo, tuple):
        return validated_logo
    
    validated_feature = validate_image(
        'featured_image',
        settings.db.UPLOAD_FOLDER / 'collection-featured',
        form_data
    )

    if isinstance(validated_feature, tuple):
        return validated_feature

    validated_baner = validate_image(
        'baner_image',
        settings.db.UPLOAD_FOLDER / 'collection-baner',
        form_data
    )

    if isinstance(validated_baner, tuple):
        return validated_baner

    if len(form_data.keys()) != 7:
        return jsonify({'errors': ['Not Enough Data']}), 400
    
    try:
        data: CollectionCreate = CollectionCreate(**form_data)
    except ValidationError as e:
        errors = e.errors()
        error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in errors]
        return jsonify({'status': 'error', 'errors': error_messages}), 400
    
    user_jwt_payload: dict = g.get('jwt_payload', None)
    if not user_jwt_payload:
        return jsonify({'status': 'error', 'message': 'Invalid Token'}), 400
    
    collection: NFTCollection = NFTCollection(
        name=data.collection_name,
        description=data.collection_description,
        royalty=data.royalties,
        logo_file=validated_logo,
        featured_file=validated_feature,
        baner_file=validated_baner,
        user_id=user_jwt_payload.get('user_id'),
        category_id=data.collection_category_id
    )

    db.session.add(collection)
    db.session.commit()
    
    return jsonify({'status': 'ok', 'data': NFTCollectionResponse.model_validate(collection.to_dict()).model_dump()}), 200

@nft_collection_api_bp.route('/<int:collection_id>/get-nfts', methods=['POST'])
def get_collection_nfts(collection_id):
    collection: NFTCollection = NFTCollection.query.filter_by(id=collection_id).first()

    if not collection:
        return jsonify({'status': 'not found', 'errors': ["collection with that id doesn't exists"]}), 400
    
    try:
        filters: NFTCollectionFilters = NFTCollectionFilters(**request.get_json())
    except ValidationError as e:
        errors = e.errors()
        error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in errors]
        return jsonify({'status': 'error', 'errors': error_messages}), 400

    has_nfts = NFT.query.filter_by(collection_id=collection.id).all()
    if not has_nfts:
        return jsonify({'status': 'success', 'nfts': []}), 200
    
    query = NFT.query.filter(NFT.collection_id == collection.id)

    if filters.currentTab == 2:
        query = query.filter(NFT.is_listed == True)

    elif filters.currentTab == 3:
        query = query.filter(NFT.is_listed == False)

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

    nfts: list[NFT] = query.all()

    collection_nfts_dicts: list[dict] = [nft.info() for nft in nfts]

    return jsonify(
        {'status': 'success', 'nfts': collection_nfts_dicts}
    ), 200
    
@nft_collection_api_bp.route('/top-collections')
def get_nft_collection_rankings():
    collections = NFTCollection.query.all()

    collection_data = []

    for collection in collections:
        nfts = collection.get_nfts()
        if not nfts:
            continue

        total_volume = sum(nft.price for nft in nfts if nft.price)

        total_sales = len([nft for nft in nfts if nft.price and nft.is_listed])

        floor_prices = [nft.price for nft in nfts if nft.price]
        floor_price = min(floor_prices) if floor_prices else Decimal("0.00")

        total_nfts = collection.get_nfts_count

        collection_data.append({
            "id": collection.id,
            "name": collection.name,
            "volume": total_volume.quantize(Decimal('1.00'), rounding=ROUND_HALF_UP),
            "floor_price": floor_price.quantize(Decimal('1.00'), rounding=ROUND_HALF_UP),
            "sales": total_sales,
            "owners": collection.owners_count,
            'total_nfts': total_nfts
        })

    # Sort by volume descending
    sorted_collections = sorted(collection_data, key=lambda c: float(c["volume"]), reverse=True)

    # Add ranks
    for idx, c in enumerate(sorted_collections):
        c["rank"] = idx + 1

    top_10_collections = sorted_collections[:10]

    return jsonify(top_10_collections), 200