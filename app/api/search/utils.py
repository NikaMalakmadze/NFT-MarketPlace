
from app.collection.models import NFTCollection
from app.user.models import User
from app.nft.models import NFT
from config import settings

def serialize_nft(nft: NFT) -> dict:
    return {
        "id": nft.id,
        "title": nft.name,
        "subtitle": nft.description,
        "image": f'/nft/{nft.token_id}/get-image',     
        "price": f"{nft.price}",
        "url": f'/nft/{nft.token_id}'
    }

def serialize_collection(collection: NFTCollection) -> dict:
    return {
        "id": collection.id,
        "title": collection.name,
        "subtitle": collection.description or "",
        "image": f'/collection/{collection.id}/get-image/featured',
        "url": f'/collection/{collection.id}'
    }

def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "title": user.username,
        "subtitle": user.bio or "",
        "image": f'/user/{user.id}/get-image/logo',
        "url": f'user/profile/{user.id}' 
    }