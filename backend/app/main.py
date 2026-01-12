from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base

# Import all models to ensure they are registered with Base
from .modules.auth import models as auth_models
from .modules.characters import models as char_models
from .modules.items import models as item_models
from .modules.missions import models as mission_models
from .modules.sessions import models as session_models

# Import routers
from .modules.auth import router as auth_router
from .modules.characters import router as char_router
from .modules.items import router as item_router
from .modules.items import inventory_router
from .modules.items import store_router
from .modules.missions import router as mission_router
from .modules.sessions import router as session_router
from .modules.admin import router as admin_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Middleware
origins = [
    "http://localhost",
    "http://localhost:5173",  # SvelteKit default dev port
    "http://localhost:3000",
    "https://*.vercel.app",   # Allow Vercel deployments
    "*",                      # Allow all for testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

# Include routers
# Mount auth under /api so /token becomes /api/token, consistent with other routes
app.include_router(auth_router.router, prefix="/api")
app.include_router(char_router.router, prefix="/api/characters", tags=["Characters"])
app.include_router(item_router.router, prefix="/api/items", tags=["Items"])
app.include_router(inventory_router.router, prefix="/api/characters/{character_id}/inventory", tags=["Inventory"])
app.include_router(store_router.router, prefix="/api/store", tags=["Store"])
app.include_router(mission_router.router, prefix="/api/missions")
app.include_router(session_router.router, prefix="/api/sessions")
app.include_router(admin_router.router, prefix="/api/admin")
