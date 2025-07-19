
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime

class NFTCollectionResponse(BaseModel):
    id: int
    name: str
    description: str
    royalty: float
    logo_file: str
    featured_file: str
    created_at: datetime
    updated_at: datetime
    user_id: int
    category_id: int
    user: str
    category: str
    nfts: list

    model_config = ConfigDict(
        from_attributes=True, 
        extra='allow', 
        arbitrary_types_allowed=True
    )

class NFTCollectionFilters(BaseModel):
    currentTab: int = 1
    sortBy: int = 1

    @field_validator("sortBy")
    @classmethod
    def validate_sort_by(cls, v):
        if v not in {1, 2, 3, 4, 5, 6, 7}:
            raise ValueError("sortBy must be one of 1, 2, 3, 4, 5, 6 or 7")
        return v

    @field_validator('currentTab')
    @classmethod
    def validate_current_tab(cls, v):
        if v not in {1, 2, 3}:
            raise ValueError("sortBy must be one of 1, 2 or 3")
        return v