"""Authlib wiring: clients, grants, PKCE, revocation, issuer parameter.

What Authlib does: authorization-code and refresh grants, PKCE, RFC 7009
revocation, RFC 9207 ``iss``. What this module adds: CIMD-backed clients,
the RFC 8707 ``resource`` binding, single-use codes and rotated refresh tokens
with reuse detection, and the campaign-admin re-check before any token is issued.

One server is built per request around that request's DB session.
"""
import datetime
import logging
from typing import Optional

from authlib.oauth2.rfc6749 import ClientMixin, InvalidGrantError, InvalidRequestError, InvalidScopeError, OAuth2Error
from authlib.oauth2.rfc6749.grants import AuthorizationCodeGrant, RefreshTokenGrant
from authlib.oauth2.rfc7009 import RevocationEndpoint
from authlib.oauth2.rfc7636 import CodeChallenge
from authlib.oauth2.rfc9207 import IssuerParameter
from sqlalchemy.orm import Session

from ...config import get_settings
from ..auth import models as auth_models
from . import cimd, models
from .authlib_adapter import StarletteAuthorizationServer
from .tokens import (
    SUPPORTED_SCOPES,
    create_access_token,
    decode_access_token,
    hash_secret,
    new_secret,
    scope_string,
    split_scopes,
    utcnow,
)

logger = logging.getLogger("app.oauth")


class InvalidTargetError(OAuth2Error):
    """RFC 8707 section 2: the requested resource is not this server's MCP endpoint."""

    error = "invalid_target"

TOKEN_HEADERS = [("Content-Type", "application/json"), ("Cache-Control", "no-store"), ("Pragma", "no-cache")]


# ---------------------------------------------------------------------------
# Models Authlib sees
# ---------------------------------------------------------------------------

class CimdClient(ClientMixin):
    """A public client described by its client ID metadata document."""

    def __init__(self, row: models.OAuthClient):
        self.client_id = row.client_id
        self.client_name = row.client_name
        self.redirect_uris = list(row.redirect_uris or [])

    def get_client_id(self):
        return self.client_id

    def get_default_redirect_uri(self):
        return None  # redirect_uri is always required

    def get_allowed_scope(self, scope):
        return scope_string(split_scopes(scope))

    def check_redirect_uri(self, redirect_uri):
        return redirect_uri in self.redirect_uris and cimd.is_allowed_redirect_uri(redirect_uri)

    def check_client_secret(self, client_secret):
        return False

    def check_endpoint_auth_method(self, method, endpoint):
        return method == "none"

    def check_response_type(self, response_type):
        return response_type == "code"

    def check_grant_type(self, grant_type):
        return grant_type in ("authorization_code", "refresh_token")


class CodeView:
    """Authorization code row as Authlib's AuthorizationCodeMixin."""

    def __init__(self, row: models.OAuthCode):
        self.row = row
        self.code_challenge = row.code_challenge
        self.code_challenge_method = row.code_challenge_method

    def get_redirect_uri(self):
        return self.row.redirect_uri

    def get_scope(self):
        return self.row.scopes


class RefreshView:
    """Refresh token row (plus its grant) as Authlib's TokenMixin."""

    def __init__(self, row: models.OAuthRefreshToken, grant: models.OAuthGrant):
        self.row = row
        self.grant = grant

    def check_client(self, client):
        return self.grant.client_id == client.get_client_id()

    def get_scope(self):
        return self.grant.scopes

    def get_expires_in(self):
        return int((self.row.expires_at - self.row.issued_at).total_seconds())

    def is_expired(self):
        return self.row.expires_at <= utcnow()

    def is_revoked(self):
        return self.grant.revoked_at is not None


class AccessView:
    """A decoded MCP access token, for revocation."""

    def __init__(self, claims: dict, grant: models.OAuthGrant):
        self.claims = claims
        self.grant = grant

    def check_client(self, client):
        return self.grant.client_id == client.get_client_id()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def active_admin(db: Session, user_id: int, campaign_id: int) -> Optional[auth_models.User]:
    """The user row if it is still an active admin of that campaign, else None."""
    return (
        db.query(auth_models.User)
        .filter(
            auth_models.User.id == user_id,
            auth_models.User.campaign_id == campaign_id,
            auth_models.User.is_active == True,  # noqa: E712
            auth_models.User.role == "admin",
        )
        .first()
    )


def revoke_grant(db: Session, grant_id: Optional[int], reason: str) -> None:
    if grant_id is None:
        return
    grant = db.get(models.OAuthGrant, grant_id)
    if grant and grant.revoked_at is None:
        grant.revoked_at = utcnow()
        logger.warning("OAuth grant revoked", extra={"grant_id": grant_id, "reason": reason})
    db.commit()


def issue_tokens(db: Session, grant: models.OAuthGrant, scopes: str) -> dict:
    """New access token plus a new refresh token for the grant. Caller commits."""
    settings = get_settings()
    access_token, expires_in = create_access_token(
        user_id=grant.user_id,
        campaign_id=grant.campaign_id,
        client_id=grant.client_id,
        grant_id=grant.id,
        scopes=scopes,
    )
    refresh_token = new_secret(32)
    now = utcnow()
    db.add(models.OAuthRefreshToken(
        token_hash=hash_secret(refresh_token),
        grant_id=grant.id,
        issued_at=now,
        expires_at=now + datetime.timedelta(days=settings.MCP_REFRESH_TOKEN_DAYS),
    ))
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "refresh_token": refresh_token,
        "scope": scopes,
        "_refresh_hash": hash_secret(refresh_token),
    }


def _public(token: dict) -> dict:
    return {k: v for k, v in token.items() if not k.startswith("_")}


def _check_resource(request) -> str:
    settings = get_settings()
    resource = request.payload.data.get("resource")
    if len(request.payload.datalist.get("resource", [])) > 1:
        raise InvalidTargetError("Only one 'resource' is supported.")
    if resource != settings.mcp_resource_url:
        raise InvalidTargetError(f"'resource' must be {settings.mcp_resource_url}")
    return resource


# ---------------------------------------------------------------------------
# PKCE: S256 only, always required
# ---------------------------------------------------------------------------

class S256CodeChallenge(CodeChallenge):
    DEFAULT_CODE_CHALLENGE_METHOD = "S256"
    SUPPORTED_CODE_CHALLENGE_METHOD = ["S256"]

    def validate_code_challenge(self, grant, redirect_uri):
        data = grant.request.payload.data
        if not data.get("code_challenge"):
            raise InvalidRequestError("Missing 'code_challenge' (PKCE is required).")
        if data.get("code_challenge_method") != "S256":
            raise InvalidRequestError("'code_challenge_method' must be S256.")
        return super().validate_code_challenge(grant, redirect_uri)


# ---------------------------------------------------------------------------
# Grants
# ---------------------------------------------------------------------------

class McpAuthorizationCodeGrant(AuthorizationCodeGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ["none"]

    @property
    def db(self) -> Session:
        return self.server.db

    def validate_authorization_request(self):
        redirect_uri = super().validate_authorization_request()
        try:
            _check_resource(self.request)
        except InvalidTargetError as error:
            error.redirect_uri = redirect_uri
            raise
        return redirect_uri

    def save_authorization_code(self, code, request):
        settings = get_settings()
        user: auth_models.User = request.user
        now = utcnow()
        self.db.add(models.OAuthCode(
            code_hash=hash_secret(code),
            client_id=request.client.get_client_id(),
            redirect_uri=request.payload.redirect_uri,
            code_challenge=request.payload.data["code_challenge"],
            code_challenge_method="S256",
            resource=request.payload.data["resource"],
            scopes=request.scope,
            user_id=user.id,
            campaign_id=user.campaign_id,
            created_at=now,
            expires_at=now + datetime.timedelta(seconds=settings.MCP_AUTH_CODE_SECONDS),
        ))
        self.db.commit()

    def query_authorization_code(self, code, client):
        row = self.db.get(models.OAuthCode, hash_secret(code))
        if row is None or row.client_id != client.get_client_id():
            return None
        if row.used_at is not None:
            # A code is single-use. A second use means it leaked: kill what it issued.
            revoke_grant(self.db, row.grant_id, "authorization code reused")
            return None
        if row.expires_at <= utcnow():
            return None
        return CodeView(row)

    def validate_token_request(self):
        super().validate_token_request()
        resource = _check_resource(self.request)
        if resource != self.request.authorization_code.row.resource:
            raise InvalidTargetError("'resource' does not match the authorization request.")

    def authenticate_user(self, authorization_code):
        row = authorization_code.row
        return active_admin(self.db, row.user_id, row.campaign_id)

    def create_token_response(self):
        code: models.OAuthCode = self.request.authorization_code.row
        user = self.authenticate_user(self.request.authorization_code)
        if not user:
            raise InvalidGrantError("You are no longer a GM of this campaign.")

        # Burn the code atomically, so two concurrent exchanges can't both win.
        now = utcnow()
        burned = (
            self.db.query(models.OAuthCode)
            .filter(models.OAuthCode.code_hash == code.code_hash, models.OAuthCode.used_at.is_(None))
            .update({models.OAuthCode.used_at: now}, synchronize_session=False)
        )
        if burned != 1:
            self.db.rollback()
            revoke_grant(self.db, code.grant_id, "authorization code reused")
            raise InvalidGrantError("Invalid 'code' in request.")

        grant = models.OAuthGrant(
            user_id=user.id,
            campaign_id=code.campaign_id,
            client_id=code.client_id,
            scopes=code.scopes,
            resource=code.resource,
            created_at=now,
        )
        self.db.add(grant)
        self.db.flush()
        self.db.query(models.OAuthCode).filter(models.OAuthCode.code_hash == code.code_hash).update(
            {models.OAuthCode.grant_id: grant.id}, synchronize_session=False
        )
        token = issue_tokens(self.db, grant, code.scopes)
        self.db.commit()
        return 200, _public(token), TOKEN_HEADERS


class McpRefreshTokenGrant(RefreshTokenGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ["none"]
    INCLUDE_NEW_REFRESH_TOKEN = True

    @property
    def db(self) -> Session:
        return self.server.db

    def authenticate_refresh_token(self, refresh_token):
        row = self.db.get(models.OAuthRefreshToken, hash_secret(refresh_token))
        if row is None:
            return None
        grant = self.db.get(models.OAuthGrant, row.grant_id)
        if grant is None or grant.revoked_at is not None:
            return None
        if row.used_at is not None:
            grace = get_settings().MCP_REFRESH_REUSE_GRACE_SECONDS
            if grace > 0 and row.used_at > utcnow() - datetime.timedelta(seconds=grace):
                return None  # concurrent refresh: refuse this one, keep the grant
            revoke_grant(self.db, grant.id, "refresh token reused")
            return None
        if row.expires_at <= utcnow():
            return None
        return RefreshView(row, grant)

    def validate_token_request(self):
        super().validate_token_request()
        resource = self.request.payload.data.get("resource")
        if resource is not None and resource != self.request.refresh_token.grant.resource:
            raise InvalidTargetError("'resource' does not match the grant.")

    def authenticate_user(self, refresh_token):
        grant = refresh_token.grant
        return active_admin(self.db, grant.user_id, grant.campaign_id)

    def create_token_response(self):
        view: RefreshView = self.request.refresh_token
        user = self.authenticate_user(view)
        if not user:
            revoke_grant(self.db, view.grant.id, "user is no longer a GM")
            raise InvalidGrantError("You are no longer a GM of this campaign.")

        now = utcnow()
        claimed = (
            self.db.query(models.OAuthRefreshToken)
            .filter(
                models.OAuthRefreshToken.token_hash == view.row.token_hash,
                models.OAuthRefreshToken.used_at.is_(None),
            )
            .update({models.OAuthRefreshToken.used_at: now}, synchronize_session=False)
        )
        if claimed != 1:
            self.db.rollback()
            if get_settings().MCP_REFRESH_REUSE_GRACE_SECONDS <= 0:
                revoke_grant(self.db, view.grant.id, "refresh token reused")
            raise InvalidGrantError()

        # A refresh may narrow scopes but never widen them past the grant.
        requested = self.request.payload.scope
        scopes = scope_string(split_scopes(requested)) if requested else view.grant.scopes
        token = issue_tokens(self.db, view.grant, scopes)
        self.db.query(models.OAuthRefreshToken).filter(
            models.OAuthRefreshToken.token_hash == view.row.token_hash
        ).update({models.OAuthRefreshToken.replaced_by: token["_refresh_hash"]}, synchronize_session=False)
        self.db.commit()
        return 200, _public(token), TOKEN_HEADERS


class McpRevocationEndpoint(RevocationEndpoint):
    CLIENT_AUTH_METHODS = ["none"]

    def query_token(self, token_string, token_type_hint):
        db = self.server.db
        row = db.get(models.OAuthRefreshToken, hash_secret(token_string))
        if row is not None:
            grant = db.get(models.OAuthGrant, row.grant_id)
            return RefreshView(row, grant) if grant else None
        claims = decode_access_token(token_string)
        if claims:
            grant = db.get(models.OAuthGrant, claims.get("grant_id"))
            return AccessView(claims, grant) if grant else None
        return None

    def revoke_token(self, token, request):
        # Either token revokes the whole connection: there is no partial state worth keeping.
        revoke_grant(self.server.db, token.grant.id, "revoked by client")


class McpIssuerParameter(IssuerParameter):
    def get_issuer(self) -> str:
        return get_settings().public_origin


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

class McpAuthorizationServer(StarletteAuthorizationServer):
    def __init__(self, db: Session):
        super().__init__(scopes_supported=SUPPORTED_SCOPES)
        self.db = db

    def query_client(self, client_id):
        # Only cached documents: routes call cimd.load_client() (async) before Authlib runs.
        row = cimd.get_cached(self.db, client_id) if client_id else None
        return CimdClient(row) if row else None

    def save_token(self, token, request):
        pass  # grants persist their own tokens in create_token_response

    def validate_requested_scope(self, scope):
        requested = set(split_scopes(scope))
        if requested - set(SUPPORTED_SCOPES):
            raise InvalidScopeError()


def build_server(db: Session) -> McpAuthorizationServer:
    server = McpAuthorizationServer(db)
    server.register_grant(McpAuthorizationCodeGrant, [S256CodeChallenge(required=True)])
    server.register_grant(McpRefreshTokenGrant)
    server.register_endpoint(McpRevocationEndpoint)
    server.register_extension(McpIssuerParameter())
    return server


def authorization_server_metadata() -> dict:
    """RFC 8414 document."""
    origin = get_settings().public_origin
    return {
        "issuer": origin,
        "authorization_endpoint": f"{origin}/api/oauth/authorize",
        "token_endpoint": f"{origin}/api/oauth/token",
        "revocation_endpoint": f"{origin}/api/oauth/revoke",
        "response_types_supported": ["code"],
        "response_modes_supported": ["query"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "revocation_endpoint_auth_methods_supported": ["none"],
        "scopes_supported": SUPPORTED_SCOPES,
        "client_id_metadata_document_supported": True,
        "authorization_response_iss_parameter_supported": True,
    }


def protected_resource_metadata() -> dict:
    """RFC 9728 document for /api/mcp."""
    settings = get_settings()
    return {
        "resource": settings.mcp_resource_url,
        "authorization_servers": [settings.public_origin],
        "scopes_supported": SUPPORTED_SCOPES,
        "bearer_methods_supported": ["header"],
        "resource_name": "West Marches campaign board",
    }
