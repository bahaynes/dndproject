from sqlalchemy.orm import Session, joinedload
from ..auth import models as auth_models
from ..characters import models as char_models
from ..items import models as item_models
from ..missions import models as mission_models
from ..sessions import models as session_models
from . import schemas

def export_game_data(db: Session) -> schemas.GameDataExport:
    users = db.query(auth_models.User).options(joinedload(auth_models.User.campaign)).all()
    items = db.query(item_models.Item).all()
    store_items = db.query(item_models.StoreItem).all()
    missions = db.query(mission_models.Mission).all()
    game_sessions = db.query(session_models.GameSession).all()

    return schemas.GameDataExport(
        users=users,
        items=items,
        store_items=store_items,
        missions=missions,
        game_sessions=game_sessions,
    )

def import_game_data(db: Session, data: schemas.GameDataExport):
    # Wipe existing data in reverse order of dependency
    db.execute(session_models.game_session_players.delete())
    db.execute(mission_models.mission_players.delete())
    db.query(item_models.InventoryItem).delete()
    db.query(item_models.StoreItem).delete()
    db.query(mission_models.MissionReward).delete()
    db.query(session_models.GameSession).delete()
    db.query(mission_models.Mission).delete()
    db.query(item_models.Item).delete()
    db.query(char_models.CharacterStats).delete()
    db.query(char_models.Character).delete()
    db.query(auth_models.User).delete()
    db.commit()

    return {"message": "Data wipe successful. Full import is not yet implemented."}
