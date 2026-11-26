"""The MCP resource server at /api/mcp.

An MCPServer (official Python SDK) in stateless streamable-HTTP mode, behind:
- a gate that answers 401 with ``resource_metadata`` and ``scope`` (so clients can
  discover the authorization server) and 403 ``insufficient_scope`` for a write
  tool called with a read-only token (so clients can step up);
- the SDK's bearer middleware, fed by McpTokenVerifier.

Nothing lives in process memory between requests: Cloud Run runs several
instances with two workers each.
"""
import contextlib
import contextvars
import json
import logging
import re
from typing import Optional

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from sqlalchemy.orm import Session
from starlette.types import Receive, Scope, Send

from ...config import get_settings
from ...database import get_db
from ..factions import schemas as faction_schemas
from ..factions import service as faction_service
from ..items import schemas as item_schemas
from ..items import service as item_service
from ..missions import models as mission_models
from ..missions import schemas as mission_schemas
from ..missions import service as mission_service
from ..oauth import models as oauth_models
from ..oauth.server import active_admin
from ..oauth.tokens import SCOPE_READ, SCOPE_WRITE, decode_access_token, split_scopes
from ..sessions import schemas as session_schemas
from ..sessions import service as session_service

logger = logging.getLogger("app.mcp")

MAX_BODY_BYTES = 4 * 1024 * 1024
WRITE_TOOLS = {"create_mission", "update_mission", "set_mission_module"}
MODULE_ID_RE = re.compile(r"oneshot-[a-z0-9][a-z0-9-]{0,98}")  # use fullmatch


# ---------------------------------------------------------------------------
# DB access outside FastAPI's dependency injection
# ---------------------------------------------------------------------------

# Tests point this at their session the same way they override get_db.
db_provider = get_db


@contextlib.contextmanager
def open_db():
    gen = db_provider()
    db = next(gen)
    try:
        yield db
    finally:
        with contextlib.suppress(StopIteration):
            next(gen)


# ---------------------------------------------------------------------------
# Token verification
# ---------------------------------------------------------------------------

_verified: contextvars.ContextVar[Optional[tuple[str, AccessToken]]] = contextvars.ContextVar(
    "mcp_verified_token", default=None
)


def verify_access_token(token: str) -> Optional[AccessToken]:
    """Signature, iss, aud, exp; then the grant must be live and the user still an active GM."""
    claims = decode_access_token(token)
    if not claims:
        return None
    with open_db() as db:
        grant = db.get(oauth_models.OAuthGrant, claims.get("grant_id"))
        if grant is None or grant.revoked_at is not None:
            return None
        try:
            user_id = int(claims["sub"])
        except (KeyError, TypeError, ValueError):
            return None
        if grant.user_id != user_id or grant.campaign_id != claims.get("campaign_id"):
            return None
        if active_admin(db, user_id, grant.campaign_id) is None:
            return None
    return AccessToken(
        token=token,
        client_id=claims["client_id"],
        scopes=split_scopes(claims.get("scope")),
        expires_at=int(claims["exp"]),
        resource=claims["aud"],
        subject=claims["sub"],
        claims={"user_id": user_id, "campaign_id": grant.campaign_id, "grant_id": grant.id, "iss": claims["iss"]},
    )


class McpTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> Optional[AccessToken]:
        cached = _verified.get()
        if cached and cached[0] == token:
            return cached[1]
        return verify_access_token(token)


# ---------------------------------------------------------------------------
# Tool context
# ---------------------------------------------------------------------------

def _principal(require_write: bool = False) -> tuple[int, int]:
    """(user_id, campaign_id) of the caller. Scope is checked here too, not only at the gate."""
    token = get_access_token()
    if token is None or not token.claims:
        raise ToolError("Not authenticated.")
    if require_write and SCOPE_WRITE not in token.scopes:
        raise ToolError(f"This tool needs the {SCOPE_WRITE} scope.")
    return token.claims["user_id"], token.claims["campaign_id"]


def _write_context(db: Session) -> int:
    """Re-checks in the database that the caller is still a GM. Returns the campaign id."""
    user_id, campaign_id = _principal(require_write=True)
    if active_admin(db, user_id, campaign_id) is None:
        raise ToolError("You are no longer a GM of this campaign.")
    return campaign_id


def _mission_out(mission) -> dict:
    return mission_schemas.Mission.model_validate(mission).model_dump(mode="json")


def _campaign_mission(db: Session, mission_id: int, campaign_id: int):
    mission = mission_service.get_mission(db, mission_id, campaign_id=campaign_id)
    if mission is None:
        raise ToolError(f"Mission {mission_id} not found.")
    return mission


def _check_prerequisite(db: Session, prerequisite_id: Optional[int], campaign_id: int, mission_id: Optional[int] = None):
    if prerequisite_id is None:
        return
    if prerequisite_id == mission_id:
        raise ToolError("A mission can't be its own prerequisite.")
    _campaign_mission(db, prerequisite_id, campaign_id)


def _check_module_id(module_id: Optional[str]) -> Optional[str]:
    if module_id is None or module_id == "":
        return None
    if not MODULE_ID_RE.fullmatch(module_id):
        raise ToolError("module_id must look like 'oneshot-<slug>' (lowercase letters, digits, hyphens).")
    return module_id


def _rewards_of(mission) -> list:
    return [
        mission_schemas.MissionRewardCreate(
            item_id=r.item_id, gold=r.gold, xp=r.xp, is_hidden=r.is_hidden, hint=r.hint
        )
        for r in mission.rewards
    ]


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

mcp = MCPServer(
    name="westmarches",
    title="West Marches campaign board",
    instructions=(
        "Tools for one West Marches campaign board (the campaign chosen when this connection was approved). "
        "Missions you create are always hidden from players; a GM publishes them on the site."
    ),
)

_READ = ToolAnnotations(readOnlyHint=True, openWorldHint=False)
_WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False)


@mcp.tool(annotations=_READ)
def list_missions(status: Optional[str] = None, include_retired: bool = False) -> list[dict]:
    """List the campaign's missions, hidden ones included. Optionally filter by status
    (e.g. "Available", "In-Progress", "Completed")."""
    _, campaign_id = _principal()
    with open_db() as db:
        missions = mission_service.get_missions(
            db, campaign_id=campaign_id, limit=500, include_retired=include_retired, include_hidden=True,
            status=status or None,
        )
        return [_mission_out(m) for m in missions]


@mcp.tool(annotations=_READ)
def get_mission(mission_id: int) -> dict:
    """Get one mission with its rewards, signed-up characters and Foundry module link."""
    _, campaign_id = _principal()
    with open_db() as db:
        return _mission_out(_campaign_mission(db, mission_id, campaign_id))


@mcp.tool(annotations=_READ)
def list_sessions(upcoming_only: bool = False) -> list[dict]:
    """List game sessions with the characters signed up for each."""
    _, campaign_id = _principal()
    with open_db() as db:
        sessions = session_service.get_game_sessions(db, campaign_id=campaign_id, limit=500, upcoming_only=upcoming_only)
        return [session_schemas.GameSession.model_validate(s).model_dump(mode="json") for s in sessions]


@mcp.tool(annotations=_READ)
def list_items() -> list[dict]:
    """List the campaign's item catalogue."""
    _, campaign_id = _principal()
    with open_db() as db:
        return [item_schemas.Item.model_validate(i).model_dump(mode="json")
                for i in item_service.get_items(db, campaign_id=campaign_id, limit=1000)]


@mcp.tool(annotations=_READ)
def list_factions() -> list[dict]:
    """List factions with their reputation level and recent reputation events."""
    _, campaign_id = _principal()
    with open_db() as db:
        return [faction_schemas.FactionReputation.model_validate(f).model_dump(mode="json")
                for f in faction_service.get_all_reputations(db, campaign_id)]


@mcp.tool(annotations=_WRITE)
def create_mission(
    name: str,
    description: Optional[str] = None,
    tier: Optional[str] = None,
    region: Optional[str] = None,
    cooldown_days: int = 7,
    prerequisite_id: Optional[int] = None,
    foundry_module: Optional[str] = None,
) -> dict:
    """Draft a new mission. It is always created hidden from players; a GM publishes it on the site.
    foundry_module optionally links the Foundry one-shot that runs it (e.g. "oneshot-gilded-moth")."""
    with open_db() as db:
        campaign_id = _write_context(db)
        _check_prerequisite(db, prerequisite_id, campaign_id)
        module_id = _check_module_id(foundry_module)
        payload = mission_schemas.MissionCreate(
            name=name,
            description=description,
            tier=tier,
            region=region,
            cooldown_days=cooldown_days,
            prerequisite_id=prerequisite_id,
            is_discoverable=False,  # forced hidden
            is_retired=False,
        )
        mission = mission_service.create_mission(db, payload, campaign_id=campaign_id, foundry_module=module_id)
        logger.info("MCP created mission", extra={"mission_id": mission.id, "campaign_id": campaign_id})
        return _mission_out(mission)


@mcp.tool(annotations=_WRITE)
def update_mission(
    mission_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tier: Optional[str] = None,
    region: Optional[str] = None,
    cooldown_days: Optional[int] = None,
    prerequisite_id: Optional[int] = None,
) -> dict:
    """Edit a mission's text and details. Fields left out keep their value. Visibility, status,
    retirement and rewards can't be changed here; a GM does that on the site."""
    with open_db() as db:
        campaign_id = _write_context(db)
        mission = _campaign_mission(db, mission_id, campaign_id)
        new_prereq = prerequisite_id if prerequisite_id is not None else mission.prerequisite_id
        if prerequisite_id is not None:
            _check_prerequisite(db, prerequisite_id, campaign_id, mission_id=mission.id)
        payload = mission_schemas.MissionCreate(
            name=name if name is not None else mission.name,
            description=description if description is not None else mission.description,
            status=mission.status,
            tier=tier if tier is not None else mission.tier,
            region=region if region is not None else mission.region,
            last_run_date=mission.last_run_date,
            cooldown_days=cooldown_days if cooldown_days is not None else mission.cooldown_days,
            is_retired=mission.is_retired,
            is_discoverable=mission.is_discoverable,  # passed through: the service copies it
            prerequisite_id=new_prereq,
            rewards=_rewards_of(mission),  # passed through: the service replaces rewards
        )
        mission = mission_service.update_mission(db, mission, payload)
        return _mission_out(mission)


@mcp.tool(annotations=_WRITE)
def set_mission_module(mission_id: int, module_id: Optional[str] = None) -> dict:
    """Link a mission to the Foundry one-shot module that runs it ("oneshot-<slug>").
    Pass no module_id to clear the link."""
    with open_db() as db:
        campaign_id = _write_context(db)
        mission = _campaign_mission(db, mission_id, campaign_id)
        mission.foundry_module = _check_module_id(module_id)
        db.commit()
        db.refresh(mission)
        return _mission_out(mission)


# ---------------------------------------------------------------------------
# ASGI wiring
# ---------------------------------------------------------------------------

def _allowed_hosts(settings) -> list[str]:
    from urllib.parse import urlparse

    hosts = ["localhost", "127.0.0.1"]
    public = urlparse(settings.public_origin)
    if public.hostname:
        hosts.append(public.hostname)
    hosts += [h.strip().lower() for h in settings.MCP_ALLOWED_HOSTS.split(",") if h.strip()]
    return hosts


def host_allowed(host_header: str, allowed: list[str]) -> bool:
    """DNS-rebinding guard. Ports are ignored; "*.example.com" matches any subdomain.
    Done here rather than by the SDK, whose list can't express Cloud Run's *.run.app host."""
    host = host_header.strip().lower()
    if host.startswith("["):
        host = host[1:host.find("]")] if "]" in host else host
    else:
        host = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
    if not host:
        return False
    for pattern in allowed:
        if pattern.startswith("*."):
            if host.endswith(pattern[1:]) and len(host) > len(pattern) - 1:
                return True
        elif host == pattern:
            return True
    return False


def origin_allowed(origin: str, settings) -> bool:
    """Browsers send Origin; MCP clients usually don't. Allow our own origin and localhost."""
    from urllib.parse import urlparse

    if not origin:
        return True
    if origin.rstrip("/") == settings.public_origin:
        return True
    parsed = urlparse(origin)
    return parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1")


def _www_authenticate(error: Optional[str], scope: str, description: Optional[str] = None) -> str:
    settings = get_settings()
    from mcp.server.auth.routes import build_resource_metadata_url

    metadata_url = str(build_resource_metadata_url(settings.mcp_resource_url))
    parts = []
    if error:
        parts.append(f'error="{error}"')
    if description:
        parts.append(f'error_description="{description}"')
    parts.append(f'resource_metadata="{metadata_url}"')
    parts.append(f'scope="{scope}"')
    return "Bearer " + ", ".join(parts)


async def _send_json(send: Send, status: int, body: dict, headers: list[tuple[bytes, bytes]] = ()) -> None:
    payload = json.dumps(body).encode()
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(payload)).encode()), *headers],
    })
    await send({"type": "http.response.body", "body": payload})


def _called_tools(body: bytes) -> set[str]:
    try:
        message = json.loads(body)
    except ValueError:
        return set()
    messages = message if isinstance(message, list) else [message]
    names = set()
    for m in messages:
        if isinstance(m, dict) and m.get("method") == "tools/call":
            params = m.get("params") or {}
            if isinstance(params, dict) and isinstance(params.get("name"), str):
                names.add(params["name"])
    return names


class McpEndpoint:
    """ASGI app mounted at /api/mcp. Rebuilt on each app startup (a session manager runs once)."""

    def __init__(self):
        self._app = None
        self.verifier = McpTokenVerifier()

    def _build(self):
        settings = get_settings()
        mcp._token_verifier = self.verifier
        mcp.settings.auth = AuthSettings(
            issuer_url=settings.public_origin,
            resource_server_url=settings.mcp_resource_url,
            required_scopes=[SCOPE_READ],
            validate_token_resource=True,
        )
        return mcp.streamable_http_app(
            streamable_http_path="/api/mcp",
            stateless_http=True,
            json_response=True,
            # Host/Origin are checked in __call__ (host_allowed / origin_allowed) instead.
            transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        )

    @contextlib.asynccontextmanager
    async def run(self):
        self._app = self._build()
        async with mcp.session_manager.run():
            yield

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return
        settings = get_settings()
        if not settings.mcp_enabled or self._app is None:
            await _send_json(send, 503, {"error": "temporarily_unavailable",
                                         "error_description": "The MCP connector is not enabled on this server."})
            return

        headers = {k: v.decode("latin-1") for k, v in scope["headers"]}
        if not host_allowed(headers.get(b"host", ""), _allowed_hosts(settings)):
            await _send_json(send, 421, {"error": "misdirected_request", "error_description": "Invalid Host header"})
            return
        if not origin_allowed(headers.get(b"origin", ""), settings):
            await _send_json(send, 403, {"error": "forbidden", "error_description": "Invalid Origin header"})
            return

        auth = headers.get(b"authorization", "")
        token = auth[7:].strip() if auth[:7].lower() == "bearer " else ""
        access = verify_access_token(token) if token else None
        if access is None:
            await _send_json(
                send, 401,
                {"error": "invalid_token", "error_description": "Authentication required"},
                [(b"www-authenticate", _www_authenticate("invalid_token" if token else None, SCOPE_READ).encode())],
            )
            return

        # Buffer the body so a write tool called with a read-only token gets a real 403 to step up on.
        buffer = bytearray()
        more = True
        while more:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            buffer += message.get("body", b"")
            more = message.get("more_body", False)
            if len(buffer) > MAX_BODY_BYTES:
                await _send_json(send, 413, {"error": "request_too_large"})
                return
        body = bytes(buffer)

        if SCOPE_WRITE not in access.scopes and _called_tools(body) & WRITE_TOOLS:
            await _send_json(
                send, 403,
                {"error": "insufficient_scope", "error_description": f"Required scope: {SCOPE_WRITE}"},
                [(b"www-authenticate", _www_authenticate(
                    "insufficient_scope", f"{SCOPE_READ} {SCOPE_WRITE}", f"Required scope: {SCOPE_WRITE}"
                ).encode())],
            )
            return

        replayed = False

        async def replay() -> dict:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        reset = _verified.set((token, access))
        try:
            await self._app(scope, replay, send)
        finally:
            _verified.reset(reset)


endpoint = McpEndpoint()
