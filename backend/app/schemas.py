from pydantic import BaseModel, EmailStr
from typing import Optional, List


# Character Schemas
class CharacterBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None


class CharacterCreate(CharacterBase):
    pass


class Character(CharacterBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True


# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str
    role: str = "player"


class User(UserBase):
    id: int
    is_active: bool
    role: str
    characters: List[Character] = []

    class Config:
        from_attributes = True


# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
