#!/usr/bin/env python
"""
Dev helper: ensure an admin user exists with a default password.

Run inside the backend container:
    python /app/scripts/seed_admin_dev.py

Environment overrides:
    DEV_ADMIN_USERNAME (default: admin)
    DEV_ADMIN_EMAIL    (default: admin@example.com)
    DEV_ADMIN_PASSWORD (default: admin)
"""
import os
from app.database import SessionLocal, Base, engine
from app import security
from app.modules.auth import schemas as auth_schemas, service as auth_service
from app.modules.characters import models as char_models
# Ensure all models are registered before accessing mappers
from app import all_models  # noqa: F401


def ensure_character(db, user_id, username):
    """Make sure the user has a character and stats (matches create_user behavior)."""
    character = db.query(char_models.Character).filter(char_models.Character.owner_id == user_id).first()
    if not character:
        character = char_models.Character(name=f"{username}'s Character", owner_id=user_id)
        db.add(character)
        db.commit()
        db.refresh(character)

    if not character.stats:
        stats = char_models.CharacterStats(character_id=character.id)
        db.add(stats)
        db.commit()
        db.refresh(stats)

    return character


def main():
    username = os.getenv("DEV_ADMIN_USERNAME", "admin")
    email = os.getenv("DEV_ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("DEV_ADMIN_PASSWORD", "admin")

    # Ensure tables exist (useful in fresh dev environments)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing = auth_service.get_user_by_username(db, username=username)

        if existing:
            existing.role = "admin"
            existing.is_active = True
            existing.hashed_password = security.get_password_hash(password)
            ensure_character(db, existing.id, existing.username)
            db.commit()
            db.refresh(existing)
            print(f"Admin user already existed; updated password/role. id={existing.id}, username={existing.username}")
            return

        payload = auth_schemas.UserCreate(username=username, email=email, password=password, role="admin")
        user = auth_service.create_user(db, payload)
        ensure_character(db, user.id, user.username)
        print(f"Created admin user. id={user.id}, username={user.username}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
