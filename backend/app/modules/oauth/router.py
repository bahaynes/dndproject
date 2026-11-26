"""OAuth 2.1 authorization server endpoints for the MCP connector.

Flow: /authorize (validate client and request) -> client consent page -> Discord
login -> campaign picker -> code back to the client. /token and /revoke follow
RFC 6749 / 7009. Separate from the frontend's /api/auth/* login.
"""
import datetime
import hmac
import logging
import secrets
from datetime import timedelta
from typing import Optional
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from ...config import get_settings
from ...database import get_db
from ..auth import models as auth_models
from ..campaigns import discord_roles
from ..campaigns import models as campaign_models
from . import cimd, models, pages
from .authlib_adapter import AuthlibResponse, build_request, read_oauth2_request
from .server import authorization_server_metadata, build_server, protected_resource_metadata
from .tokens import new_secret, scope_string, split_scopes, utcnow

logger = logging.getLogger("app.oauth")

def require_mcp_enabled():
    if not get_settings().mcp_enabled:
        raise HTTPException(status_code=503, detail="The MCP connector is not enabled on this server.")


router = APIRouter(dependencies=[Depends(require_mcp_enabled)])
well_known_router = APIRouter(dependencies=[Depends(require_mcp_enabled)])

_DISCORD_NONCE_COOKIE = "mcp_discord_nonce"
_CONSENT_COOKIE_MAX_CLIENTS = 20
_CONSENT_COOKIE_DAYS = 365


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

@well_known_router.get("/.well-known/oauth-authorization-server", tags=["MCP OAuth"])
async def oauth_authorization_server_metadata():
    """RFC 8414 authorization server metadata."""
    return JSONResponse(authorization_server_metadata(), headers={"Cache-Control": "public, max-age=300"})


@well_known_router.get("/.well-known/oauth-protected-resource/api/mcp", tags=["MCP OAuth"])
@well_known_router.get("/.well-known/oauth-protected-resource", tags=["MCP OAuth"])
async def oauth_protected_resource_metadata():
    """RFC 9728 protected resource metadata for /api/mcp."""
    return JSONResponse(protected_resource_metadata(), headers={"Cache-Control": "public, max-age=300"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_prod() -> bool:
    return get_settings().APP_ENV == "production"


def _consent_cookie_name() -> str:
    # __Host- needs Secure, which dev (plain http) can't set.
    return "__Host-mcp_consent" if _is_prod() else "mcp_consent"


def _consented_clients(request: Request) -> list[str]:
    raw = request.cookies.get(_consent_cookie_name())
    if not raw:
        return []
    try:
        data = jwt.decode(raw, get_settings().mcp_token_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return []
    if data.get("typ") != "mcp_consent" or not isinstance(data.get("clients"), list):
        return []
    return [c for c in data["clients"] if isinstance(c, str)]


def _set_consent_cookie(response, request: Request, client_id: str) -> None:
    clients = [c for c in _consented_clients(request) if c != client_id]
    clients = (clients + [client_id])[-_CONSENT_COOKIE_MAX_CLIENTS:]
    value = jwt.encode(
        {
            "typ": "mcp_consent",
            "clients": clients,
            "exp": datetime.datetime.now(datetime.timezone.utc) + timedelta(days=_CONSENT_COOKIE_DAYS),
        },
        get_settings().mcp_token_secret,
        algorithm="HS256",
    )
    response.set_cookie(
        _consent_cookie_name(), value, max_age=_CONSENT_COOKIE_DAYS * 86400,
        httponly=True, secure=_is_prod(), samesite="lax", path="/",
    )


def _client_redirect(redirect_uri: str, params: dict) -> RedirectResponse:
    """Redirect back to the client. Always carries iss (RFC 9207)."""
    query = {k: v for k, v in params.items() if v is not None}
    query["iss"] = get_settings().public_origin
    separator = "&" if "?" in redirect_uri else "?"
    return RedirectResponse(f"{redirect_uri}{separator}{urlencode(query)}", status_code=302)


def _to_response(result: AuthlibResponse):
    return result.to_starlette()


def _cleanup(db: Session) -> None:
    now = utcnow()
    db.query(models.OAuthPendingAuthorization).filter(models.OAuthPendingAuthorization.expires_at < now).delete(
        synchronize_session=False
    )
    # Used codes are kept a day past expiry so a replay still finds and revokes their grant.
    db.query(models.OAuthCode).filter(models.OAuthCode.expires_at < now - timedelta(days=1)).delete(
        synchronize_session=False
    )
    db.query(models.OAuthRefreshToken).filter(models.OAuthRefreshToken.expires_at < now).delete(
        synchronize_session=False
    )
    db.commit()


def _load_pending(db: Session, pending_id: Optional[str], csrf: Optional[str]) -> Optional[models.OAuthPendingAuthorization]:
    if not pending_id or not csrf:
        return None
    pending = db.get(models.OAuthPendingAuthorization, pending_id)
    if pending is None or pending.expires_at <= utcnow():
        return None
    if not hmac.compare_digest(pending.csrf, csrf):
        return None
    return pending


def _pending_oauth2_request(pending: models.OAuthPendingAuthorization):
    """Rebuilds the original /authorize request from the pending row, for Authlib."""
    origin = get_settings().public_origin
    args = [
        ("response_type", "code"),
        ("client_id", pending.client_id),
        ("redirect_uri", pending.redirect_uri),
        ("scope", pending.scopes),
        ("code_challenge", pending.code_challenge),
        ("code_challenge_method", "S256"),
        ("resource", pending.resource),
    ]
    if pending.state is not None:
        args.append(("state", pending.state))
    return build_request("GET", f"{origin}/api/oauth/authorize?{urlencode(args)}", {}, args, [])


def _redirect_to_discord(pending: models.OAuthPendingAuthorization) -> RedirectResponse:
    settings = get_settings()
    nonce = secrets.token_urlsafe(32)
    state = jwt.encode(
        {
            "typ": "mcp_discord_state",
            "pending": pending.id,
            "nonce": nonce,
            "exp": datetime.datetime.now(datetime.timezone.utc) + timedelta(minutes=10),
        },
        settings.mcp_token_secret,
        algorithm="HS256",
    )
    query = urlencode({
        "client_id": settings.DISCORD_CLIENT_ID,
        "redirect_uri": settings.mcp_discord_redirect_uri,
        "response_type": "code",
        "scope": "identify",
        "state": state,
        # Our own consent page already ran, so Discord's approval screen can be skipped.
        "prompt": "none",
    })
    response = RedirectResponse(f"https://discord.com/api/oauth2/authorize?{query}", status_code=302)
    response.set_cookie(
        _DISCORD_NONCE_COOKIE, nonce, max_age=600, httponly=True, secure=_is_prod(), samesite="lax", path="/api/oauth",
    )
    return response


async def eligible_campaigns(db: Session, discord_id: str) -> list:
    """Campaigns this Discord user may connect: an active admin row here, and a GM role on Discord now."""
    settings = get_settings()
    rows = (
        db.query(auth_models.User, campaign_models.Campaign)
        .join(campaign_models.Campaign, auth_models.User.campaign_id == campaign_models.Campaign.id)
        .filter(
            auth_models.User.discord_id == discord_id,
            auth_models.User.is_active == True,  # noqa: E712
            auth_models.User.role == "admin",
        )
        .all()
    )
    if not rows:
        return []
    bot_token = settings.DISCORD_BOT_TOKEN
    if not (isinstance(bot_token, str) and bot_token.strip()):
        if settings.APP_ENV == "production":
            logger.error("MCP consent: DISCORD_BOT_TOKEN unset, refusing every campaign")
            return []
        logger.warning("MCP consent: DISCORD_BOT_TOKEN unset, skipping the live Discord role check (dev only)")
        return [campaign for _, campaign in rows]

    admin_names = discord_roles.parse_admin_role_names(settings.ADMIN_DISCORD_ROLE_NAMES)
    eligible = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for _, campaign in rows:
            try:
                role = await discord_roles.resolve_campaign_role(client, campaign, discord_id, bot_token, admin_names)
            except (discord_roles.GuildMemberNotFound, discord_roles.GuildLookupFailed):
                role = None
            if role == "admin":
                eligible.append(campaign)
    return eligible


def _remembered_campaign(db: Session, pending: models.OAuthPendingAuthorization, campaigns: list):
    """The campaign of the newest remembered consent that covers this request, if still eligible."""
    wanted = set(split_scopes(pending.scopes))
    eligible_ids = {c.id for c in campaigns}
    consents = (
        db.query(models.OAuthConsent)
        .filter(models.OAuthConsent.discord_id == pending.discord_id, models.OAuthConsent.client_id == pending.client_id)
        .order_by(models.OAuthConsent.created_at.desc())
        .all()
    )
    for consent in consents:
        if consent.campaign_id in eligible_ids and wanted <= set(split_scopes(consent.scopes)):
            return next(c for c in campaigns if c.id == consent.campaign_id)
    return None


def _remember_consent(db: Session, pending: models.OAuthPendingAuthorization, campaign_id: int) -> None:
    consent = (
        db.query(models.OAuthConsent)
        .filter(
            models.OAuthConsent.discord_id == pending.discord_id,
            models.OAuthConsent.client_id == pending.client_id,
            models.OAuthConsent.campaign_id == campaign_id,
        )
        .first()
    )
    if consent is None:
        consent = models.OAuthConsent(discord_id=pending.discord_id, client_id=pending.client_id, campaign_id=campaign_id)
        db.add(consent)
    consent.scopes = scope_string(split_scopes(consent.scopes or "") + split_scopes(pending.scopes))
    consent.created_at = utcnow()
    db.commit()


def _issue_code(db: Session, pending: models.OAuthPendingAuthorization, campaign) -> object:
    user = (
        db.query(auth_models.User)
        .filter(
            auth_models.User.discord_id == pending.discord_id,
            auth_models.User.campaign_id == campaign.id,
            auth_models.User.is_active == True,  # noqa: E712
            auth_models.User.role == "admin",
        )
        .first()
    )
    if user is None:
        return pages.error_page("You are not a GM of that campaign.", 403)
    server = build_server(db)
    request = _pending_oauth2_request(pending)
    grant = server.get_consent_grant(request)
    result = server.create_authorization_response(request, grant_user=user, grant=grant)
    db.delete(pending)
    db.commit()
    return _to_response(result)


# ---------------------------------------------------------------------------
# /authorize and the steps after it
# ---------------------------------------------------------------------------

@router.get("/authorize", tags=["MCP OAuth"])
async def authorize(request: Request, db: Session = Depends(get_db)):
    """Validates the client and request, then starts consent."""
    from authlib.oauth2.rfc6749 import OAuth2Error

    settings = get_settings()
    _cleanup(db)

    client_id = request.query_params.get("client_id")
    redirect_uri = request.query_params.get("redirect_uri")
    # Logged so we can see which clients send a CIMD URL (plan question 2) and which don't.
    logger.info("MCP authorize request", extra={"client_id": client_id, "redirect_uri": redirect_uri})
    try:
        client_row = await cimd.load_client(db, client_id)
    except cimd.CimdError as exc:
        logger.warning("MCP authorize refused client", extra={"client_id": client_id, "reason": str(exc)})
        return pages.error_page(str(exc))
    if not redirect_uri or redirect_uri not in (client_row.redirect_uris or []):
        return pages.error_page("The app's redirect address is not listed in its metadata document.")
    if not cimd.is_allowed_redirect_uri(redirect_uri):
        return pages.error_page("The app's redirect address must be https:// or a localhost address.")

    oauth_request = await read_oauth2_request(request, settings.public_origin)
    if oauth_request.payload.data.get("scope") is None:
        # No scope requested: default to read-only.
        args = [*oauth_request.args.items(), ("scope", "board:read")]
        oauth_request = build_request("GET", oauth_request.uri, oauth_request.headers, args, [])
    server = build_server(db)
    try:
        grant = server.get_consent_grant(oauth_request)
    except OAuth2Error as error:
        if error.redirect_uri:
            return _client_redirect(error.redirect_uri, {
                "error": error.error,
                "error_description": error.description or None,
                "state": oauth_request.payload.state,
            })
        return pages.error_page(error.description or error.error)

    scopes = grant.request.scope or "board:read"
    pending = models.OAuthPendingAuthorization(
        id=new_secret(24),
        client_id=client_row.client_id,
        redirect_uri=redirect_uri,
        state=oauth_request.payload.state,
        code_challenge=oauth_request.payload.data["code_challenge"],
        resource=oauth_request.payload.data["resource"],
        scopes=scopes,
        csrf=new_secret(24),
        client_consented=False,
        created_at=utcnow(),
        expires_at=utcnow() + timedelta(seconds=settings.MCP_PENDING_AUTH_SECONDS),
    )
    db.add(pending)
    db.commit()

    if client_row.client_id in _consented_clients(request):
        pending.client_consented = True
        db.commit()
        return _redirect_to_discord(pending)

    return pages.client_consent_page(
        pending_id=pending.id,
        csrf=pending.csrf,
        client_name=client_row.client_name or client_row.client_id,
        client_id=client_row.client_id,
        redirect_uri=redirect_uri,
        scopes=split_scopes(scopes),
    )


@router.get("/consent", tags=["MCP OAuth"])
async def client_consent(request: Request, pending: str = "", csrf: str = "", decision: str = "",
                         db: Session = Depends(get_db)):
    """The user's answer on the client consent page, before Discord is involved."""
    row = _load_pending(db, pending, csrf)
    if row is None:
        return pages.error_page("This sign-in link has expired.")
    if decision != "approve":
        db.delete(row)
        db.commit()
        return _client_redirect(row.redirect_uri, {"error": "access_denied", "state": row.state})
    row.client_consented = True
    db.commit()
    response = _redirect_to_discord(row)
    _set_consent_cookie(response, request, row.client_id)
    return response


@router.get("/discord/callback", tags=["MCP OAuth"])
async def discord_callback(request: Request, code: Optional[str] = None, state: Optional[str] = None,
                           error: Optional[str] = None, db: Session = Depends(get_db)):
    """Discord identifies the user; then the campaign picker (or a remembered consent) follows."""
    settings = get_settings()
    try:
        data = jwt.decode(state or "", settings.mcp_token_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return pages.error_page("The Discord sign-in expired or was tampered with.")
    cookie_nonce = request.cookies.get(_DISCORD_NONCE_COOKIE) or ""
    if data.get("typ") != "mcp_discord_state" or not hmac.compare_digest(str(data.get("nonce", "")), cookie_nonce):
        return pages.error_page("The Discord sign-in did not start in this browser.")

    pending = db.get(models.OAuthPendingAuthorization, data.get("pending"))
    if pending is None or pending.expires_at <= utcnow() or not pending.client_consented:
        return pages.error_page("This sign-in link has expired.")

    if error or not code:
        db.delete(pending)
        db.commit()
        return _client_redirect(pending.redirect_uri, {"error": "access_denied", "state": pending.state})

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_response = await client.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": settings.DISCORD_CLIENT_ID,
                "client_secret": settings.DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.mcp_discord_redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_response.status_code != 200:
            logger.error("MCP Discord token exchange failed", extra={"status_code": token_response.status_code})
            return pages.error_page("Discord sign-in failed.", 502)
        user_response = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {token_response.json().get('access_token')}"},
        )
    if user_response.status_code != 200:
        return pages.error_page("Discord sign-in failed.", 502)
    discord_user = user_response.json()

    pending.discord_id = str(discord_user.get("id"))
    pending.discord_username = discord_user.get("global_name") or discord_user.get("username") or "you"
    db.commit()

    campaigns = await eligible_campaigns(db, pending.discord_id)
    if not campaigns:
        db.delete(pending)
        db.commit()
        return _client_redirect(pending.redirect_uri, {
            "error": "access_denied",
            "error_description": "You are not a GM of any campaign on this board.",
            "state": pending.state,
        })

    remembered = _remembered_campaign(db, pending, campaigns)
    if remembered is not None:
        response = _issue_code(db, pending, remembered)
    else:
        client_row = cimd.get_cached(db, pending.client_id)
        response = pages.campaign_picker_page(
            pending_id=pending.id,
            csrf=pending.csrf,
            client_name=(client_row.client_name if client_row else None) or pending.client_id,
            redirect_uri=pending.redirect_uri,
            username=pending.discord_username,
            scopes=split_scopes(pending.scopes),
            campaigns=campaigns,
        )
    response.delete_cookie(_DISCORD_NONCE_COOKIE, path="/api/oauth")
    return response


@router.get("/approve", tags=["MCP OAuth"])
async def approve(pending: str = "", csrf: str = "", campaign_id: Optional[int] = None, decision: str = "",
                  db: Session = Depends(get_db)):
    """The user picked a campaign (or cancelled). Issues the authorization code."""
    row = _load_pending(db, pending, csrf)
    if row is None or not row.discord_id:
        return pages.error_page("This sign-in link has expired.")
    if decision == "deny" or campaign_id is None:
        db.delete(row)
        db.commit()
        return _client_redirect(row.redirect_uri, {"error": "access_denied", "state": row.state})

    campaigns = await eligible_campaigns(db, row.discord_id)
    campaign = next((c for c in campaigns if c.id == campaign_id), None)
    if campaign is None:
        return pages.error_page("You are not a GM of that campaign.", 403)
    _remember_consent(db, row, campaign.id)
    return _issue_code(db, row, campaign)


# ---------------------------------------------------------------------------
# /token and /revoke
# ---------------------------------------------------------------------------

async def _prefetch_client(db: Session, request: Request) -> None:
    """Authlib looks clients up synchronously; make sure the CIMD cache holds this one."""
    form = await request.form()
    client_id = form.get("client_id")
    if isinstance(client_id, str) and client_id:
        try:
            # A long cache is fine here: the document was validated at /authorize.
            await cimd.load_client(db, client_id, max_age_seconds=86400)
        except cimd.CimdError:
            pass  # Authlib then answers invalid_client


@router.post("/token", tags=["MCP OAuth"])
async def token(request: Request, db: Session = Depends(get_db)):
    """Authorization-code and refresh-token grants (public clients, PKCE)."""
    await _prefetch_client(db, request)
    oauth_request = await read_oauth2_request(request, get_settings().public_origin)
    return _to_response(build_server(db).create_token_response(oauth_request))


@router.post("/revoke", tags=["MCP OAuth"])
async def revoke(request: Request, db: Session = Depends(get_db)):
    """RFC 7009: revokes the connection a refresh or access token belongs to."""
    await _prefetch_client(db, request)
    oauth_request = await read_oauth2_request(request, get_settings().public_origin)
    return _to_response(build_server(db).create_endpoint_response("revocation", oauth_request))
