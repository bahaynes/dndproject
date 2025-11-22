"""Shared domain enums used across models and schemas."""
from enum import Enum


class CharacterStatus(str, Enum):
    READY = "ready"
    DEPLOYED = "deployed"
    FATIGUED = "fatigued"
    MEDICAL_LEAVE = "medical_leave"


class HexOwnership(str, Enum):
    ALLIANCE = "alliance"
    HEGEMONY = "hegemony"
    NEUTRAL = "neutral"


class FogLevel(str, Enum):
    BLACK = "black"  # unexplored
    GREY = "grey"  # explored, no live intel
    BLUE = "blue"  # active intel


class SessionStatus(str, Enum):
    OPEN = "open"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
