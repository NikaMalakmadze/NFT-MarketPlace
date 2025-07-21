
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text,  Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone

from app.nft.models import NFT
from app.extensions import db

class NFTCollection(db.Model):
    __tablename__ = 'nftcollections'

    id: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    royalty: Mapped[Decimal] = mapped_column(Numeric(precision=2, scale=2), nullable=False)
    logo_file: Mapped[str] = mapped_column(String(300), nullable=False)
    featured_file: Mapped[str] = mapped_column(String(300), nullable=False)
    baner_file: Mapped[str] = mapped_column(String(300), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('collectionCategories.id'), nullable=False)

    user = relationship('User', back_populates='collections')
    category = relationship('CollectionCategory', back_populates='collections')
    nfts = relationship('NFT', foreign_keys=[NFT.collection_id], lazy='select', back_populates='collection')

    def get_nfts(self) -> list[NFT]:
        return NFT.query.filter_by(collection_id=self.id).all()
    
    @property
    def total_nfts(self):
        return self.get_nfts()

    @property
    def get_nfts_count(self) -> list[NFT]:
        return NFT.query.filter_by(collection_id=self.id).count()

    @property
    def floor(self):
        prices: list[int] = [nft.price for nft in self.get_nfts()]
        if not prices: return 0
        return min(prices)

    @property
    def volume(self):
        return sum([nft.price for nft in self.get_nfts()])
    
    @property
    def owners_count(self):
        return len(set([nft.owner for nft in self.get_nfts()]))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'royalty': self.royalty,
            'logo_file': self.logo_file,
            'featured_file': self.featured_file,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'user_id': self.user_id,
            'user': self.user.username,
            'category_id': self.category_id,
            'category': self.category.name,
            'nfts': self.nfts
        }

class CollectionCategory(db.Model):
    __tablename__ = 'collectionCategories'

    id: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(100), nullable=False)
    logo_file: Mapped[str] = mapped_column(String(300), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    collections = relationship('NFTCollection', foreign_keys=[NFTCollection.category_id], lazy=True)