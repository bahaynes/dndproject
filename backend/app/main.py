import os
from pathlib import Path
from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from . import crud, models, schemas, security
from .database import get_db, init_db

app = FastAPI(title="DnD Westmarches Hub API")

@app.on_event("startup")
def on_startup():
    """Initialize the database when the application starts."""
    init_db()

# In development, the SvelteKit app runs on a different port and needs CORS.
# In production, Caddy serves both and this is not needed.
if os.environ.get("MODE", "dev") == "dev":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- Auth ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    return current_user

# --- API Endpoints ---
api_router = APIRouter()

@api_router.post("/token", response_model=schemas.Token, tags=["Authentication"])
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.post("/users/", response_model=schemas.User, tags=["Users"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user_by_username = crud.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@api_router.get("/users/me/", response_model=schemas.User, tags=["Users"])
async def read_users_me(current_user: schemas.User = Depends(get_current_active_user)):
    return current_user

# Mount the API router under /api
app.include_router(api_router, prefix="/api")

# --- Static Files for Production ---
# This block will only run when MODE=prod, so it won't crash pytest
if os.environ.get("MODE") == "prod":
    # This path assumes the 'static' dir is at the root of the project,
    # which is where the build script places the frontend build.
    static_dir = Path(__file__).parent.parent.parent / "static"

    app.mount("/_app", StaticFiles(directory=static_dir / "_app"), name="static_assets")

    # This catch-all route serves the SvelteKit SPA's entry point.
    @app.get("/{full_path:path}", response_class=FileResponse)
    async def serve_spa_entrypoint(full_path: str):
        index_path = static_dir / "index.html"
        if not index_path.exists():
            raise HTTPException(status_code=404, detail="SPA entry point not found. Did you build the frontend?")
        return FileResponse(index_path)
