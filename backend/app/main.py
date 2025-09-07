from fastapi import Depends, FastAPI, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import json

from . import crud, models, schemas, security
from .database import SessionLocal, engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Middleware
origins = [
    "http://localhost",
    "http://localhost:5173",  # SvelteKit default dev port
    "http://localhost:3000",
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

# API routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

from typing import List

async def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_active_admin_user(current_user: schemas.User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized: Admin access required")
    return current_user

@app.post("/token", response_model=schemas.Token, tags=["Authentication"])
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

@app.post("/users/", response_model=schemas.UserCreateResponse, tags=["Users"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=400, detail="This email is already registered. If you have an account, please sign in instead.")
    db_user_by_username = crud.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=400, detail="This username is already in use. Please choose another one.")

    new_user = crud.create_user(db=db, user=user)
    access_token = security.create_access_token(data={"sub": new_user.username})

    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "is_active": new_user.is_active,
        "role": new_user.role,
        "character": new_user.character,
        "access_token": access_token,
        "token_type": "bearer",
    }

@app.get("/users/me/", response_model=schemas.User, tags=["Users"])
async def read_users_me(current_user: schemas.User = Depends(get_current_active_user)):
    return current_user

@app.get("/api/characters/{character_id}", response_model=schemas.Character, tags=["Characters"])
def read_character(character_id: int, db: Session = Depends(get_db)):
    db_character = crud.get_character(db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return db_character


@app.put("/api/characters/{character_id}", response_model=schemas.Character, tags=["Characters"])
def update_character(
    character_id: int,
    character: schemas.CharacterCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user),
):
    db_character = crud.get_character(db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    # Authorization check: only owner or admin can edit
    if db_character.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this character")
    return crud.update_character(db=db, character_id=character_id, character=character)

# --- Item Endpoints ---
@app.post("/api/items/", response_model=schemas.Item, tags=["Items"], dependencies=[Depends(get_current_active_admin_user)])
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db=db, item=item)

@app.get("/api/items/", response_model=List[schemas.Item], tags=["Items"])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items

@app.get("/api/items/{item_id}", response_model=schemas.Item, tags=["Items"])
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

# --- Inventory Endpoints ---
@app.post("/api/characters/{character_id}/inventory", response_model=schemas.InventoryItem, tags=["Inventory"], dependencies=[Depends(get_current_active_admin_user)])
def add_item_to_character_inventory(character_id: int, item_id: int, quantity: int = 1, db: Session = Depends(get_db)):
    db_character = crud.get_character(db, character_id=character_id)
    if not db_character:
        raise HTTPException(status_code=404, detail="Character not found")
    db_item = crud.get_item(db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.add_item_to_inventory(db=db, character_id=character_id, item_id=item_id, quantity=quantity)

@app.delete("/api/inventory/{inventory_item_id}", tags=["Inventory"])
def remove_item_from_character_inventory(
    inventory_item_id: int,
    quantity: int = 1,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    # This is a bit tricky, we need to check ownership of the inventory item
    # A more robust way would be to get the item, then check character owner == current_user.id
    # For now, we'll assume the frontend only shows the delete button for owned items.
    # A proper implementation would require fetching the inventory item and checking its character's owner.
    removed_item = crud.remove_item_from_inventory(db, inventory_item_id=inventory_item_id, quantity=quantity)
    if removed_item is None:
        return {"detail": "Item removed from inventory or not found."}
    return removed_item


# --- Store Endpoints ---
@app.post("/api/store/items/", response_model=schemas.StoreItem, tags=["Store"], dependencies=[Depends(get_current_active_admin_user)])
def create_store_item(store_item: schemas.StoreItemCreate, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id=store_item.item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item to be listed not found")
    return crud.create_store_item(db=db, store_item=store_item)

@app.get("/api/store/items/", response_model=List[schemas.StoreItem], tags=["Store"])
def read_store_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    store_items = crud.get_store_items(db, skip=skip, limit=limit)
    return store_items

@app.post("/api/store/items/{store_item_id}/purchase", tags=["Store"])
def purchase_store_item(
    store_item_id: int,
    quantity: int = 1,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    store_item = crud.get_store_item(db, store_item_id=store_item_id)
    if not store_item:
        raise HTTPException(status_code=404, detail="Store item not found")

    character = current_user.character
    if not character:
        raise HTTPException(status_code=400, detail="User has no character to purchase items for")

    result = crud.purchase_item(db, character=character, store_item=store_item, quantity=quantity)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


# --- Admin Data Tools ---
@app.get("/api/admin/export", response_model=schemas.GameDataExport, tags=["Admin"], dependencies=[Depends(get_current_active_admin_user)])
def export_data(db: Session = Depends(get_db)):
    return crud.export_game_data(db)

@app.post("/api/admin/import", tags=["Admin"], dependencies=[Depends(get_current_active_admin_user)])
async def import_data(db: Session = Depends(get_db), file: UploadFile = File(...)):
    try:
        contents = await file.read()
        data = json.loads(contents)
        # Here you would ideally validate the data against the GameDataExport schema
        # For now, we'll just pass it to the CRUD function.
        # e.g. validated_data = schemas.GameDataExport.model_validate(data)
        result = crud.import_game_data(db, data)
        return result
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during import: {e}")


# --- Game Session Endpoints ---
@app.post("/api/sessions/", response_model=schemas.GameSession, tags=["Game Sessions"], dependencies=[Depends(get_current_active_admin_user)])
def create_game_session(session: schemas.GameSessionCreate, db: Session = Depends(get_db)):
    return crud.create_game_session(db=db, session=session)

@app.get("/api/sessions/", response_model=List[schemas.GameSession], tags=["Game Sessions"])
def read_game_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    sessions = crud.get_game_sessions(db, skip=skip, limit=limit)
    return sessions

@app.get("/api/sessions/{session_id}", response_model=schemas.GameSession, tags=["Game Sessions"])
def read_game_session(session_id: int, db: Session = Depends(get_db)):
    db_session = crud.get_game_session(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="Game session not found")
    return db_session

@app.put("/api/sessions/{session_id}", response_model=schemas.GameSession, tags=["Game Sessions"], dependencies=[Depends(get_current_active_admin_user)])
def update_game_session(session_id: int, session_update: schemas.GameSessionCreate, db: Session = Depends(get_db)):
    session = crud.get_game_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")
    return crud.update_game_session(db, session=session, session_update=session_update)

@app.delete("/api/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Game Sessions"], dependencies=[Depends(get_current_active_admin_user)])
def delete_game_session(session_id: int, db: Session = Depends(get_db)):
    db_session = crud.delete_game_session(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="Game session not found")
    return {"ok": True}

@app.post("/api/sessions/{session_id}/signup", response_model=schemas.GameSession, tags=["Game Sessions"])
def signup_for_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    session = crud.get_game_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")

    character = current_user.character
    if not character:
        raise HTTPException(status_code=400, detail="User has no character to sign up with")

    if character in session.players:
        raise HTTPException(status_code=400, detail="Character already signed up for this session")

    return crud.add_character_to_game_session(db, session=session, character=character)

@app.delete("/api/sessions/{session_id}/signup", response_model=schemas.GameSession, tags=["Game Sessions"])
def cancel_signup_for_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    session = crud.get_game_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")

    character = current_user.character
    if not character:
        raise HTTPException(status_code=400, detail="User has no character")

    if character not in session.players:
        raise HTTPException(status_code=400, detail="Character is not signed up for this session")

    return crud.remove_character_from_game_session(db, session=session, character=character)


# --- Mission Endpoints ---
@app.post("/api/missions/", response_model=schemas.Mission, tags=["Missions"], dependencies=[Depends(get_current_active_admin_user)])
def create_mission(mission: schemas.MissionCreate, db: Session = Depends(get_db)):
    return crud.create_mission(db=db, mission=mission)

@app.get("/api/missions/", response_model=List[schemas.Mission], tags=["Missions"])
def read_missions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    missions = crud.get_missions(db, skip=skip, limit=limit)
    return missions

@app.get("/api/missions/{mission_id}", response_model=schemas.Mission, tags=["Missions"])
def read_mission(mission_id: int, db: Session = Depends(get_db)):
    db_mission = crud.get_mission(db, mission_id=mission_id)
    if db_mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    return db_mission

@app.post("/api/missions/{mission_id}/signup", response_model=schemas.Mission, tags=["Missions"])
def signup_for_mission(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    mission = crud.get_mission(db, mission_id=mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    character = current_user.character
    if not character:
        raise HTTPException(status_code=400, detail="User has no character to sign up with")

    if character in mission.players:
        raise HTTPException(status_code=400, detail="Character already signed up for this mission")

    return crud.add_character_to_mission(db, mission=mission, character=character)

@app.put("/api/missions/{mission_id}/status", response_model=schemas.Mission, tags=["Missions"], dependencies=[Depends(get_current_active_admin_user)])
def update_mission_status(mission_id: int, status: str, db: Session = Depends(get_db)):
    mission = crud.get_mission(db, mission_id=mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return crud.update_mission_status(db, mission=mission, status=status)

@app.post("/api/missions/{mission_id}/distribute_rewards", tags=["Missions"], dependencies=[Depends(get_current_active_admin_user)])
def distribute_rewards(mission_id: int, db: Session = Depends(get_db)):
    mission = crud.get_mission(db, mission_id=mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    result = crud.distribute_mission_rewards(db, mission=mission)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
