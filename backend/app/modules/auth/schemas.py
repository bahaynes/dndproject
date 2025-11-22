from pydantic import BaseModel, EmailStr
from typing import Optional, List
from ..characters.schemas import Character


class UserBase(BaseModel):
    """Shared user fields."""

    username: str
    email: EmailStr


class UserCreate(UserBase):
    """Payload to create a new account."""

    password: str
    role: str = "player"


class User(UserBase):
    """User response including roster (if loaded)."""

    id: int
    is_active: bool
    role: str
    characters: List[Character] = []

    class Config:
        from_attributes = True


class UserCreateResponse(User):
    """Signup response plus bearer token."""

    access_token: str
    token_type: str = "bearer"


class Token(BaseModel):
    """JWT token pair."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload extracted from JWT."""

    username: Optional[str] = None
