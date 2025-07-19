
from pydantic import BaseModel, ConfigDict, field_validator
from decimal import Decimal, InvalidOperation

from app.collection.models import CollectionCategory
from config import settings

class CollectionCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    logo_image: str
    featured_image: str
    collection_name: str
    collection_description: str
    collection_category_id: str
    royalties: str

    @field_validator('collection_category_id')
    @classmethod
    def validate_category(cls, value: str):
        try:
            integer_id = int(value)
        except Exception:
            raise ValueError('Invalid Collection Category id value')
        
        collection_category: CollectionCategory = CollectionCategory.query.filter_by(id=integer_id).first()
        if not collection_category:
            raise ValueError('Category was not found')
        
        return integer_id
    
    @field_validator('royalties')
    @classmethod
    def validate_royalties(cls, value: str):
        try:
            decimaled: Decimal = Decimal(value)
        except InvalidOperation:
            raise ValueError('Invalid royalties value')
        
        if not (0 <= decimaled <= settings.app.MAX_ROYALTIES):
            raise ValueError('Invalid Royalties range')
        
        if decimaled.as_tuple().exponent < -2:
            raise ValueError("Royalties can have at most 2 decimal places")
        
        return decimaled