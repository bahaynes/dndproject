from typing import List, Optional
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    discord_id: str
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    campaign_id: int
    role: str = "player"
    email: Optional[str] = None # Keeping email here as optional input but not storing in User model for now

class User(UserBase):
    id: int
    is_active: bool
    role: str
    campaign_id: int
    # character: Optional[Character] = None # Avoiding circular import for now

    class Config:
        from_attributes = True

class UserCreateResponse(User):
    access_token: str
    token_type: str
