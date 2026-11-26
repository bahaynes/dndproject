import hmac
import time
import uuid
from collections import defaultdict, deque
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure structured JSON logging before any other app imports so that
# module-level startup code (e.g. Settings validation) uses the JSON formatter.
from .logging_config import configure_logging, request_id_var
from .config import get_settings
configure_logging()

# Import all models to ensure they are registered with Base
from .modules.auth import models as auth_models
from .modules.characters import models as char_models
from .modules.items import models as item_models
from .modules.missions import models as mission_models
from .modules.sessions import models as session_models
from .modules.maps import models as map_models
from .modules.factions import models as faction_models
from .modules.ship import models as ship_models
from .modules.ledger import models as ledger_models
from .modules.oauth import models as oauth_models

# Import routers
from .modules.auth import router as auth_router
from .modules.campaigns import router as campaign_router
from .modules.characters import router as char_router
from .modules.items import router as item_router
from .modules.items import inventory_router
from .modules.items import store_router
from .modules.missions import router as mission_router
from .modules.sessions import router as session_router
from .modules.maps import router as map_router
from .modules.admin import router as admin_router
from .modules.factions import router as faction_router
from .modules.debug import router as debug_router
from .modules.ship import router as ship_router
from .modules.ledger import router as ledger_router
from .modules.oauth import router as oauth_router

_settings = get_settings()

app = FastAPI(
    docs_url=None if _settings.APP_ENV == "production" else "/docs",
    redoc_url=None if _settings.APP_ENV == "production" else "/redoc",
    openapi_url=None if _settings.APP_ENV == "production" else "/openapi.json",
)

_RATE_LIMIT_WINDOW_SECONDS = 60.0
_AUTH_RATE_LIMIT = 60
_BAKE_EARTH_RATE_LIMIT = 10
_MAX_RATE_LIMIT_BUCKETS = 10000
_rate_limit_buckets: dict[tuple[str, str], deque[float]] = defaultdict(deque)


def _build_allowed_origins(settings) -> list[str]:
    candidates: list[str] = []
    if settings.FRONTEND_URL:
        candidates.append(settings.FRONTEND_URL.rstrip("/"))
    if settings.CORS_ORIGINS:
        candidates.extend(
            origin.strip().rstrip("/")
            for origin in settings.CORS_ORIGINS.split(",")
            if origin.strip()
        )
    candidates.append("https://westmarches.bahaynes.com")
    if settings.APP_ENV == "development":
        candidates.extend([
            "http://localhost",
            "http://localhost:5173",
            "http://localhost:3000",
        ])

    deduped: list[str] = []
    seen: set[str] = set()
    for origin in candidates:
        if origin and origin not in seen:
            seen.add(origin)
            deduped.append(origin)
    return deduped


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if get_settings().RATE_LIMIT_ENABLED:
        path = request.url.path
        bucket_name: str | None = None
        limit = 0
        if path.startswith("/api/auth/"):
            bucket_name = "auth"
            limit = _AUTH_RATE_LIMIT
        elif path.startswith("/api/oauth/"):
            bucket_name = "oauth"
            limit = _AUTH_RATE_LIMIT
        elif path.startswith("/api/maps/") and path.endswith("/bake-earth"):
            bucket_name = "bake_earth"
            limit = _BAKE_EARTH_RATE_LIMIT

        if bucket_name is not None:
            real_ip = request.headers.get("X-Real-IP", "").strip()
            forwarded_for = request.headers.get("X-Forwarded-For", "")
            if real_ip:
                client_ip = real_ip
            elif forwarded_for.strip():
                client_ip = forwarded_for.split(",")[-1].strip()
            else:
                client_ip = request.client.host if request.client else "unknown"
            now = time.monotonic()
            cutoff = now - _RATE_LIMIT_WINDOW_SECONDS
            key = (bucket_name, client_ip)
            if key not in _rate_limit_buckets and len(_rate_limit_buckets) >= _MAX_RATE_LIMIT_BUCKETS:
                stale_keys = [
                    k for k, dq in _rate_limit_buckets.items() if not dq or dq[-1] <= cutoff
                ]
                for stale_key in stale_keys:
                    del _rate_limit_buckets[stale_key]
                if len(_rate_limit_buckets) >= _MAX_RATE_LIMIT_BUCKETS:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many requests"},
                        headers={"Retry-After": "60"},
                    )
            bucket = _rate_limit_buckets[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"},
                    headers={"Retry-After": "60"},
                )
            bucket.append(now)

    return await call_next(request)


@app.middleware("http")
async def proxy_secret_middleware(request: Request, call_next):
    settings = get_settings()
    accepted = [
        s for s in (settings.PROXY_SHARED_SECRET, settings.PROXY_SHARED_SECRET_PREVIOUS) if s
    ]
    if (
        accepted
        and request.url.path.startswith("/api/")
        and request.url.path != "/api/v1/health"
    ):
        provided = request.headers.get("X-Proxy-Secret", "").encode("utf-8")
        if not any(hmac.compare_digest(provided, s.encode("utf-8")) for s in accepted):
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
    return await call_next(request)


# Request ID middleware — injects a UUID into every request and all downstream log lines.
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request_id_var.set(req_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response


# CORS Middleware
origins = _build_allowed_origins(_settings)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Debug-Token"],
)

@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "DnD West Marches API"}

# Include routers
app.include_router(auth_router.router, prefix="/api/auth")
app.include_router(campaign_router.router, prefix="/api/campaigns")
app.include_router(char_router.router, prefix="/api/characters", tags=["Characters"])
app.include_router(item_router.router, prefix="/api/items", tags=["Items"])
app.include_router(inventory_router.router, prefix="/api/characters/{character_id}/inventory", tags=["Inventory"])
app.include_router(store_router.router, prefix="/api/store", tags=["Store"])
app.include_router(mission_router.router, prefix="/api/missions")
app.include_router(session_router.router, prefix="/api/sessions")
app.include_router(map_router.router, prefix="/api/maps")
app.include_router(admin_router.router, prefix="/api/admin")
app.include_router(faction_router.router, prefix="/api/factions")
app.include_router(debug_router.router, prefix="/api/debug")
app.include_router(ship_router.router, prefix="/api/ship")
app.include_router(ledger_router.router, prefix="/api/ledger")
app.include_router(oauth_router.router, prefix="/api/oauth")
app.include_router(oauth_router.well_known_router)
