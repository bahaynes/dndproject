import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from sqlalchemy.orm import Session

from .database import get_db
from .config import get_settings
from .modules.auth import models, schemas
from .modules.characters import models as char_models
from sqlalchemy.orm import joinedload

logger = logging.getLogger("app.dependencies")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user_global(
    token: str = Depends(oauth2_scheme),
    settings = Depends(get_settings)
):
    """
    Validates the token and returns the payload (Discord ID, etc.)
    Used for endpoints that only need Discord identity, not campaign scoping.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError:
        logger.warning("JWT rejected: token expired")
        raise _credentials_exception
    except JWTError as exc:
        logger.warning("JWT rejected: decode failure", extra={"error": str(exc)})
        raise _credentials_exception

    discord_id: str = payload.get("sub")
    if discord_id is None:
        logger.warning(
            "JWT rejected: missing 'sub' claim",
            extra={"payload_keys": list(payload.keys())},
        )
        raise _credentials_exception

    return payload


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    settings = Depends(get_settings)
):
    """
    Validates the token AND ensures it is scoped to a campaign.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError:
        logger.warning("JWT rejected: token expired")
        raise _credentials_exception
    except JWTError as exc:
        logger.warning("JWT rejected: decode failure", extra={"error": str(exc)})
        raise _credentials_exception

    discord_id: str = payload.get("sub")
    campaign_id: int = payload.get("campaign_id")

    if discord_id is None:
        logger.warning(
            "JWT rejected: missing 'sub' claim",
            extra={"payload_keys": list(payload.keys())},
        )
        raise _credentials_exception

    if campaign_id is None:
        logger.warning(
            "JWT rejected: missing 'campaign_id' — this is a global token used on a campaign-scoped endpoint",
            extra={"discord_id": discord_id, "token_type": payload.get("type")},
        )
        raise _credentials_exception

    user = db.query(models.User).options(
        joinedload(models.User.active_character),
        joinedload(models.User.campaign)
    ).filter(
        models.User.discord_id == discord_id,
        models.User.campaign_id == campaign_id
    ).first()

    if user is None:
        logger.warning(
            "JWT rejected: no user found for discord_id + campaign_id",
            extra={"discord_id": discord_id, "campaign_id": campaign_id},
        )
        raise _credentials_exception

    return user


async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        logger.warning(
            "Auth rejected: user is inactive",
            extra={"discord_id": current_user.discord_id, "campaign_id": current_user.campaign_id},
        )
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_admin_user(current_user: models.User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return current_user
