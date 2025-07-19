
from sqlalchemy.types import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from flask_login import UserMixin
from sqlalchemy import Numeric
from decimal import Decimal
import bcrypt

from app.extensions import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    username: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(300), default=username)
    hashed_password: Mapped[str | bytes] = mapped_column(String(400), nullable=False)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    wallet: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_avatar: Mapped[str] = mapped_column(
        String(250), default="defaultAvatar.png"
    )
    profile_background: Mapped[str] = mapped_column(
        String(250), default="defaultBg.png"
    )
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    following = db.relationship(
        'Follower',
        foreign_keys='Follower.follower_id',
        back_populates='follower_user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    followers = db.relationship(
        'Follower',
        foreign_keys='Follower.followed_id',
        back_populates='followed_user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    balance: Mapped[Decimal] = mapped_column(Numeric(36, 18), default=0)

    offers_made: Mapped[list["Offer"]] = relationship(
        back_populates="buyer",
        foreign_keys="[Offer.buyer_id]"
    )

    offers_received: Mapped[list["Offer"]] = relationship(
        back_populates="owner",
        foreign_keys="[Offer.owner_id]"
    )
    def follow(self, user):
        if not self.is_following(user):
            follow = Follower(follower_id=self.id, followed_id=user.id)
            db.session.add(follow)

    def unfollow(self, user):
        Follower.query.filter_by(follower_id=self.id, followed_id=user.id).delete()

    def is_following(self, user):
        return Follower.query.filter_by(follower_id=self.id, followed_id=user.id).count() > 0

    def is_followed_by(self, user):
        return Follower.query.filter_by(follower_id=user.id, followed_id=self.id).count() > 0

    def get_following_users(self):
        return User.query.join(Follower, Follower.followed_id == User.id)\
            .filter(Follower.follower_id == self.id).all()

    def get_follower_users(self):
        return User.query.join(Follower, Follower.follower_id == User.id)\
            .filter(Follower.followed_id == self.id).all()

    def hash_password(self, password: str) -> None:
        bcrypt_salt: bytes = bcrypt.gensalt()
        password_bytes: bytes = password.encode()
        self.hashed_password = bcrypt.hashpw(password_bytes, salt=bcrypt_salt)

    def validate_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode(), self.hashed_password)

    def get_generated_nfts(self):
        from app.nft.models import NFT

        return NFT.query.filter_by(creator_id=self.id).all()

    def get_owned_nfts(self):
        from app.nft.models import NFT

        return NFT.query.filter_by(owner_id=self.id).all()

    def get_wallet_name(self):
        from app.api.allowedwallets.models import AllowedWallet

        wallet: AllowedWallet = AllowedWallet.query.filter_by(
            id=int(self.wallet)
        ).first()
        return wallet.name

    @property
    def wallet_name(self):
        return self.get_wallet_name()

    @property
    def created_nfts(self):
        return self.get_generated_nfts()

    @property
    def owned_nfts(self):
        return self.get_owned_nfts()

    def to_dict(self) -> dict[str, int | str | bool]:
        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "email": self.email,
            "wallet": self.wallet,
            "role": self.role,
            "is_active": self.is_active,
            "is_blocked": self.is_blocked,
            "profile_avatar": self.profile_avatar,
            "profile_background": self.profile_background,
            "bio": self.bio,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
class Follower(db.Model):
    __tablename__ = 'followers'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    follower_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    followed_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    follower_user: Mapped["User"] = db.relationship("User", foreign_keys=[follower_id], back_populates="following")
    followed_user: Mapped["User"] = db.relationship("User", foreign_keys=[followed_id], back_populates="followers")