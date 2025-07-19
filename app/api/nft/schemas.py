
from pydantic import Field, field_validator
from pydantic.config import ConfigDict
from pydantic.main import BaseModel
from typing import Literal, List
from datetime import timedelta
from decimal import Decimal

from app.collection.models import NFTCollection
from app.nft.models import Category

class NFTCreate(BaseModel):
    model_config = ConfigDict(strict=True, arbitrary_types_allowed=True, from_str=True)

    name: str = Field(..., min_length=5, max_length=100)
    description: str = Field(..., min_length=1, max_length=1000)
    price: str
    category_id: str
    collection_id: str
    image_url: str

    @field_validator('price')
    @classmethod
    def validate_name(cls, value: str):
        try: 
            prc: float = float(value)
        except (TypeError, ValueError):
            raise ValueError("NFT Price must be a valid number")

        if prc < 0:
            raise ValueError("NFT Price Must be NonNegativeFLoat")
        return round(float(value), 2) 
    
    @field_validator('category_id')
    @classmethod
    def validate_category_id(cls, value: str):
        try:
            id: int = int(value)
        except (TypeError, ValueError):
            raise ValueError("Category Id must be valid Integer")
        
        if not Category.query.filter_by(id=id).first():
            raise ValueError("Category Doesn't exists")
        
        return id
    
    @field_validator('collection_id')
    @classmethod
    def validate_collection_id(cls, value: str):
        try:
            id: int = int(value)
        except (TypeError, ValueError):
            raise ValueError('Collection Id must be valid integer')
        
        if id == -1:
            return 'NoCategory'
        
        if not NFTCollection.query.filter_by(id=id).first():
            raise ValueError("Collection Doesn't exists")
        
        return id

class NFTCreateResponse(BaseModel):
    token_id: str
    name: str
    description: str
    image_file: str
    price: float
    category_id: int
    category: dict
    creator: str
    owner: str

    model_config = ConfigDict(
        from_attributes=True, 
        extra='allow', 
        arbitrary_types_allowed=True
    )
    
class OfferCreate(BaseModel):
    amount: Decimal
    expires_in: Literal["1h", "6h", "24h", "3d", "7d"]

    @field_validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Offer amount must be greater than zero")
        if v > Decimal("1000000"):
            raise ValueError("Offer amount is too large")
        return v
    
    @property
    def expires_delta(self) -> timedelta:
        mapping = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
            "3d": timedelta(days=3),
            "7d": timedelta(days=7),
        }
        return mapping[self.expires_in]
    
class NFTFilterSchema(BaseModel):
    categoryInputs: List[int] = []
    fileTypeInputs: List[int] = []
    isListedInputs: List[int] = []
    sortBy: int = 1
    minValue: float = 0
    maxValue: float = -1
    search: str | None = None

    @field_validator("categoryInputs", "fileTypeInputs", "isListedInputs", mode="before")
    @classmethod
    def check_positive_ids(cls, v):
        if not isinstance(v, list):
            raise ValueError("Must be a list of positive integers")
        if not all(isinstance(i, int) and i > 0 for i in v):
            raise ValueError("Each ID must be a positive integer")
        return v

    @field_validator("sortBy")
    @classmethod
    def validate_sort_by(cls, v):
        if v not in {1, 2, 3, 4, 5, 6, 7}:
            raise ValueError("sortBy must be one of 1, 2, 3, 4, 5, 6 or 7")
        return v

    @field_validator("minValue", "maxValue")
    @classmethod
    def validate_price_values(cls, v, info):
        field_name = info.field_name
        if not isinstance(v, (int, float)):
            raise ValueError(f"{field_name} must be a number")
        if field_name == "minValue" and v < 0:
            raise ValueError("minValue must be a positive number")
        if field_name == "maxValue" and v != -1 and v < 0:
            raise ValueError("maxValue must be a positive number or -1")
        return v