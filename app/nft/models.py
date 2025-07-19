from sqlalchemy.types import Integer, String, Boolean, Text, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import ROUND_HALF_UP, Decimal
from sqlalchemy.schema import ForeignKey
from datetime import datetime, timedelta, timezone

from config import ALLOWED_EXTENSIONS
from app.extensions import db

class NFT(db.Model):
    __tablename__ = "nfts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    token_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    image_file: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    creator_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('categories.id'), nullable=False)
    collection_id: Mapped[int] = mapped_column(Integer, ForeignKey('nftcollections.id'), nullable=True)

    is_listed: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    likes = relationship(
        'Like', 
        back_populates='nft',
        cascade='all, delete-orphan'
    )
    views = relationship('NFTView', back_populates='nft', cascade='all, delete-orphan')

    creator = relationship("User", foreign_keys=[creator_id])
    owner = relationship("User", foreign_keys=[owner_id])
    category = relationship('Category', back_populates='nfts')
    offers: Mapped[list["Offer"]] = relationship(back_populates="nft", cascade="all, delete-orphan")
    
    def get_owner(self):
        return str(self.owner.username)

    def get_likes(self):
        return len(Like.query.filter_by(token_id=self.token_id).all())

    def get_views(self):
        return len(NFTView.query.filter_by(token_id=self.token_id).all())

    @property
    def owner_name(self):
        return self.get_owner()
    
    @property
    def total_likes(self):
        return self.get_likes()

    @property
    def total_views(self):
        return self.get_views()
    
    @property
    def extension_id(self):
        ext: str = self.image_file.rsplit('.', 1)[-1].lower()
        ext_id = None
        for index, ext_type in enumerate(ALLOWED_EXTENSIONS, 1):
            if ext_type == ext: 
                ext_id = index
        return ext_id

    def info(self):
        return {
            'name': self.name,
            "owner": self.owner.username if self.owner else "None",
            'owner_id': self.owner.id,
            "price": float(self.price) if self.price else "None",
            "is_listed": self.is_listed,
            'token_id': self.token_id,
            'created_at': self.created_at
        }

    def to_dict(self):
        return {
            "id": self.id,
            "token_id": self.token_id,
            "name": self.name,
            "description": self.description,
            "image_file": self.image_file,
            "price": float(self.price) if self.price else "None",
            "creator": self.creator.username if self.creator else "None",
            "owner": self.owner.username if self.owner else "None",
            "creator_id": self.creator_id,
            "owner_id": self.owner_id,
            "is_listed": self.is_listed,
            "created_at": self.created_at,
            "category_id": self.category_id,
            "category": {
                "name": self.category.name,
                "logo": self.category.logo
            },
            "collection_id": self.collection_id
        }
    
    def __str__(self):
        return f'{self.name} NFT'

class Category(db.Model):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    logo: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    nfts = relationship('NFT', back_populates='category', passive_deletes=True)

    @property
    def logo_url(self):
        return f'/nft/category/{self.id}'

    @property
    def category_nfts(self):
        return NFT.query.filter_by(category_id=self.id).all()
    
    def __str__(self):
        return f'{self.name.capitalize()} Category'

class Like(db.Model):
    __tablename__ = 'likes'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)

    nft_id: Mapped[int] = mapped_column(Integer, ForeignKey('nfts.id', ondelete='CASCADE'), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    token_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    user = relationship('User', back_populates='liked_nfts')
    nft = relationship('NFT', back_populates='likes')

    def to_dict(self):
        return {
            'id': self.id,
            'nft': self.nft.to_dict(),
            'user': self.user.to_dict()
        }
    
class NFTView(db.Model):
    __tablename__ = 'views'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    nft_id: Mapped[int] = mapped_column(Integer, ForeignKey('nfts.id', ondelete='CASCADE'), nullable=False)
    token_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship('User', back_populates='views')
    nft = relationship('NFT', back_populates='views')

    def to_dict(self):
        return {
            'id': self.id,
            'nft': self.nft,
            'user': self.user.to_dict()
        }
    
class Offer(db.Model):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(primary_key=True)

    nft_id: Mapped[int] = mapped_column(ForeignKey("nfts.id"), nullable=False)
    nft: Mapped["NFT"] = relationship(back_populates="offers")

    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    buyer: Mapped["User"] = relationship(
        back_populates="offers_made",
        foreign_keys=[buyer_id]
    )

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    owner: Mapped["User"] = relationship(
        back_populates="offers_received",
        foreign_keys=[owner_id]
    )

    price_at_offer: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc)
    )

    is_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False)

    @property
    def is_active(self):
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        return not self.is_accepted and not self.is_cancelled and expires_at > datetime.now(timezone.utc)

    def info(self) -> dict:
        return {
            'id': self.id,
            'nft': {
                'id': self.nft_id,
                'token_id': self.nft.token_id,
                'name': self.nft.name,
                'image': self.nft.image_file
            },
            'buyer': {
                'id': self.buyer_id,
                'username': self.buyer.username,
            },
            'amount': self.amount.quantize(Decimal('1.00'), rounding=ROUND_HALF_UP),
            'percentage': (
                (self.amount / self.price_at_offer) * Decimal('100'))
                .quantize(Decimal('1.00'), rounding=ROUND_HALF_UP
            ),
            'price_at_offer': self.price_at_offer, 
            'expires_in': self.expires_at.isoformat(),
            'created_at': self.created_at.isoformat()
        }