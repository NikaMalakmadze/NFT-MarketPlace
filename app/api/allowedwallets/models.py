
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.extensions import db

class AllowedWallet(db.Model):
    __tablename__ = 'allowed_Wallets'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now)
    logo = Column(String(500), nullable=False, unique=True)
