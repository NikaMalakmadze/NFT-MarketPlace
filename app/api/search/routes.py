
from flask import jsonify, request
from sqlalchemy import func, or_

from app.api.search.utils import serialize_collection, serialize_nft, serialize_user
from app.collection.models import NFTCollection
from app.jwt.decorators import jwt_required
from app.api.search import search_api_bp
from app.user.models import User
from app.nft.models import NFT

@search_api_bp.route("/")
@jwt_required
def search():
    query = request.args.get("q", "").strip().lower()

    if not query:
        return jsonify({"nfts": [], "collections": [], "users": []})

    nfts = NFT.query.filter(
        or_(
            func.lower(NFT.name).like(f"%{query}%"),
            func.lower(NFT.description).like(f"%{query}%")
        )
    ).limit(10).all()

    collections = NFTCollection.query.filter(
        func.lower(NFTCollection.name).like(f"%{query}%")
    ).limit(10).all()

    users = User.query.filter(
        func.lower(User.username).like(f"%{query}%")
    ).limit(10).all()

    return jsonify({'status': 'success', 'data': {
        "nfts": [serialize_nft(nft) for nft in nfts],
        "collections": [serialize_collection(c) for c in collections],
        "users": [serialize_user(u) for u in users],
    }}), 200