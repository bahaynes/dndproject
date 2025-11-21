from pydantic import BaseModel
from typing import Optional

class CharacterBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
