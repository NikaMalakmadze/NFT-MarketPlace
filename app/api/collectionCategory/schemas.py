
from pydantic import BaseModel, ConfigDict, field_validator
from flask.globals import current_app
from urllib.parse import urlparse
from datetime import datetime
import os

from app.collection.models import CollectionCategory
from config import settings

class CollectionCategoryCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str
    logo_file: str

    @field_validator('logo_file')
    @classmethod
    def validate_logo_file(cls, path: str):
        parsed = urlparse(path)
        if parsed.scheme in ('http', 'https'):
            raise ValueError("Only local image paths are allowed")
        
        path = os.path.join(*path.split('/'))

        if not os.path.isfile(settings.db.APP_FILES / 'collection-categories' / path):
            raise FileNotFoundError('Invalid Path or File Does not exists')
        return path
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, name: str):
        with current_app.app_context():
            if CollectionCategory.query.filter_by(name=name).first():
                raise ValueError(f'{name} Collection Category Already Exists')
        return name
    
class CollectionCategoryResponse(BaseModel):
    id: int
    name: str
    description: str
    logo_file: str
    created_at: datetime
    collections: list

    model_config = ConfigDict(from_attributes=True, extra='ignore')

class CollectionCategoryDelete(BaseModel):
    id: int

    @field_validator('id')
    @classmethod
    def validate_id(cls, value):
        try:
            inted_value: int = int(value)
        except Exception:
            raise ValueError('Invalid Id Value')
        
        collection_category: CollectionCategory = CollectionCategory.query.filter_by(id=inted_value).first()
        if not collection_category:
            raise ValueError('Collection Category with inputed id was not found')

        return inted_value

    class config:
        from_attributes = True