
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class UserProfileUpdate(BaseModel):
    display_name: str
    email: EmailStr
    bio: str = Field(..., min_length=1, max_length=500)

    model_config = ConfigDict(
        from_attributes=True, 
    )

class UserProfileFilters(BaseModel):
    currentTab: int = 1
    sortBy: int = 1
    search: str | None = None

    @field_validator("sortBy")
    @classmethod
    def validate_sort_by(cls, v):
        if v not in {1, 2, 3, 4, 5, 6, 7}:
            raise ValueError("sortBy must be one of 1, 2, 3, 4, 5, 6 or 7")
        return v

    @field_validator('currentTab')
    @classmethod
    def validate_current_tab(cls, v):
        if v not in {1, 2, 3, 4, 5}:
            raise ValueError("sortBy must be one of 1, 2, 3, 4 or 5")
        return v