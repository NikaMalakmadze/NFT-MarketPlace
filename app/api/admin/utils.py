
from datetime import datetime, timezone
from app.collection.models import NFTCollection
from app.user.models import User
from app.nft.models import NFT, Like, NFTView, Offer

def serialize_user(user: User) -> dict:
    user_all_nfts = user.created_nfts + user.owned_nfts

    return {
        "id": user.id,
        "username": user.username,
        "displayName": user.display_name,
        "email": user.email,
        "role": user.role,
        "balance": f"{user.balance:.2f} ETH" if user.balance is not None else "0.00 ETH",
        "status": 'active' if not user.is_blocked else 'blocked',
        "nfts": [
            {
                "id": nft.id,
                "name": nft.name,
                "price": f"{nft.price:.2f} ETH" if nft.price is not None else "0.00 ETH",
                "image": f'/nft/{nft.token_id}/get-image',
                "url": f'/nft/{nft.token_id}'
            }
            for nft in user_all_nfts
        ]
    }

def serialize_nft(nft: NFT) -> dict:
    return {
        "tokenId": nft.token_id,
        "name": nft.name,
        "price": f"{nft.price:.2f} ETH" if nft.price is not None else "0.00 ETH",
        "creator": nft.creator.username if nft.creator else None,
        "owner": nft.owner.username if nft.owner else None,
        "listed": nft.is_listed,  
        "status": 'active' if not nft.is_blocked else 'blocked',
        "createdAt": nft.created_at.strftime("%Y-%m-%d") if nft.created_at else None,
        "image": f'/nft/{nft.token_id}/get-image',
        "url": f'/nft/{nft.token_id}'
    }

def serialize_collection(collection: NFTCollection) -> dict:
    return {
        "id": collection.id,
        "name": collection.name,
        "description": collection.description,
        "owner": collection.user.username if collection.user else None,
        "category": collection.category.name if collection.category else None,
        "royalty": float(collection.royalty),
        "nftCount": len(collection.total_nfts),
        "floorPrice": collection.floor,
        "volume": collection.volume,
    }

def serialize_category(category):
    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
    }

def serialize_offer(offer: Offer) -> dict:
    try:
        percentage = (offer.amount / offer.price_at_offer) * 100
    except (ZeroDivisionError, TypeError):
        percentage = "N/A"

    created_at = offer.created_at.strftime("%Y-%m-%d") if offer.created_at else None

    now = datetime.now(timezone.utc)

    expires_at = offer.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at > now:
        expires_in_days = (expires_at - now).days
        expires_in = f"{expires_in_days} days"
    elif offer.expires_at:
        expires_in = "Expired"
    else:
        expires_in = "Unknown"

    status = "active" if offer.is_active else (
        "accepted" if offer.is_accepted else (
            "cancelled" if offer.is_cancelled else "expired"
        )
    )

    return {
        "id": offer.id,
        "tokenId": offer.nft.token_id if offer.nft.token_id else None,
        "buyer": offer.buyer.username if offer.buyer else None,
        "amount": float(offer.amount),
        "percentage": percentage,
        "createdAt": created_at,
        "expiresIn": expires_in,
        "status": status,
    }

def serialize_like(like: Like) -> dict:
    return {
        "id": like.id,
        "nftName": like.nft.name if like.nft else None,
        "user": like.user.username if like.user else None,
        "type": "like",
        "timestamp": like.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(like, "created_at") and like.created_at else None,
    }

def serialize_view(view: NFTView) -> dict:
    return {
        "id": view.id,
        "nftName": view.nft.name if view.nft else None,
        "user": view.user.username if view.user else None,
        "type": "view",
        "timestamp": view.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(view, "created_at") and view.created_at else None,
    }