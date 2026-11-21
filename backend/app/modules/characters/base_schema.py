from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


def validate_http_url(value: Optional[str]) -> Optional[str]:
    """Validate that an optional URL uses http:// or https:// with a host."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("URL must be a string")
    stripped = value.strip()
    if not stripped:
        return None
    parsed = urlparse(stripped)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        raise ValueError("URL must start with http:// or https://")
    return stripped


class CharacterBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    character_sheet_url: Optional[str] = None
    class_name: Optional[str] = None
    level: int = Field(default=1, ge=1, le=20)

    @field_validator("character_sheet_url", "image_url", mode="before")
    @classmethod
    def _validate_urls(cls, v: Optional[str]) -> Optional[str]:
        return validate_http_url(v)
