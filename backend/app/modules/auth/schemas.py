from pydantic import BaseModel, EmailStr
from typing import Optional
from ..characters.schemas import Character

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
    character: Optional[Character] = None

    class Config:
        from_attributes = True

class UserCreateResponse(User):
    access_token: str
    token_type: str = "bearer"

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
