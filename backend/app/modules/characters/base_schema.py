from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CharacterBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    character_sheet_url: Optional[str] = None
    class_name: Optional[str] = None
    level: int = 1
