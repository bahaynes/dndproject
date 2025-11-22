from pydantic import BaseModel
from typing import Optional

from ..common.enums import CharacterStatus


class CharacterBase(BaseModel):
    """Public character profile information."""

    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    status: CharacterStatus = CharacterStatus.READY
