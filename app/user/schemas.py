
from pydantic.root_model import BaseModel
from pydantic import EmailStr, ConfigDict

class UserRegister(BaseModel):
    model_config = ConfigDict(strict=True)

    email: EmailStr
    username: str
    displayName: str
    password: str
    wallet_id: int

class UserLogin(BaseModel):
    model_config = ConfigDict(strict=True)

    email: EmailStr
    username: str
    password: str
    