
from app.collection.models import NFTCollection
from config import ALLOWED_EXTENSIONS
from app.user.models import User
from app.nft.models import NFT
from app.extensions import db

def configure_relationships() -> None:

    User.created_nfts = db.relationship('NFT', foreign_keys=[NFT.creator_id], lazy=True)
    User.owned_nfts = db.relationship('NFT', foreign_keys=[NFT.owner_id], lazy=True)
    User.collections = db.relationship('NFTCollection', foreign_keys=[NFTCollection.user_id], lazy=True, back_populates='user')
    User.liked_nfts = db.relationship('Like', back_populates='user')
    User.views = db.relationship('NFTView', back_populates='user', cascade='all, delete-orphan',)

    NFT.creator = db.relationship(
        'User', 
        foreign_keys=[NFT.creator_id], 
        back_populates='created_nfts'
    )
    NFT.owner = db.relationship(
        'User', 
        foreign_keys=[NFT.owner_id], 
        back_populates='owned_nfts'
    )
    NFT.collection = db.relationship(NFTCollection, back_populates='nfts', lazy='select')

def allowed_image_type(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def delete_table(className, db) -> None:
    className.__table__.drop(db.engine)