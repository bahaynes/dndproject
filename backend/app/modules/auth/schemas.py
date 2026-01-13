from typing import List, Optional, ForwardRef
from pydantic import BaseModel

# Forward reference for Character to avoid circular import issues at module level
# We use a string forward reference if possible, or conditional import
# In Pydantic v2, we can just use the class name if it's imported later or use a string.

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
    email: Optional[str] = None

class CharacterOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class User(UserBase):
    id: int
    is_active: bool
    role: str
    campaign_id: int

    character: Optional[CharacterOut] = None

    class Config:
        from_attributes = True

class UserCreateResponse(User):
    access_token: str
    token_type: str
