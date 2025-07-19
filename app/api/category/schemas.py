
from pydantic import BaseModel, Field, field_validator
from urllib.parse import urlparse
from datetime import datetime
import os

from config import BASE_DIR

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    logo: str = Field(..., min_length=2, max_length=500)

    @field_validator('logo')
    @classmethod
    def validate_logo_path(cls, path: str):
        parsed = urlparse(path)
        if parsed.scheme in ('http', 'https'):
            raise ValueError("Only local image paths are allowed")
        
        path = os.path.join(*path.split('/'))

        if not os.path.isfile(BASE_DIR / 'app' / 'app-files' / 'category-icons' / path):
            raise FileNotFoundError('Invalid Path or File Does not exists')
        return path

class CategoryResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    logo_url: str

    class Config:
        from_attributes = True
