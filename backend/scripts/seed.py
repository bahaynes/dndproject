#!/usr/bin/env python3
"""
Seed script — populates a campaign with world-bible data.

Usage:
    cd backend && uv run python scripts/seed.py --campaign-id 1
    cd backend && uv run python scripts/seed.py  # seeds first campaign found

Safe to run multiple times — skips records that already exist.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.modules.factions.models import FactionReputation
from app.modules.missions.models import Mission, MissionReward


# ── Factions ────────────────────────────────────────────────────────────────

FACTIONS = [
    {
        "faction_name": "The Guildhall",
        "color": "#3b82f6",
        "description": (
            "The chartered expeditionary guild that maintains maps, bounties, "
            "and safe-conduct passes across the frontier."
        ),
    },
    {
        "faction_name": "Borderland Wardens",
        "color": "#d97706",
        "description": (
            "Independent scouts, waystation keepers, and rangers holding the "
            "outer watchtowers beyond settled lands."
        ),
    },
]


# ── Opening missions ─────────────────────────────────────────────────────────
# Standard D&D 5e Tier 1 rewards (gold + XP per player).

MISSIONS = [
    {
        "name": "The Quiet Convoy",
        "description": (
            "A supply caravan out of Crossroads Keep went silent three days ago. "
            "The manifest is routine — timber, lamp oil, and rations — nothing worth "
            "a bandit raid, yet no rider has returned."
        ),
        "tier": "Tier 1",
        "region": "Ashwood Trail",
        "cooldown_days": 14,
        "gold": 50,
        "xp": 300,
    },
    {
        "name": "Beacon on the Ridge",
        "description": (
            "An old watchtower on the northern ridge began flashing its signal lantern "
            "on loop last night. The Wardens abandoned that post three winters ago; "
            "someone—or something—has relit the brazier."
        ),
        "tier": "Tier 1",
        "region": "Northern Ridge",
        "cooldown_days": 14,
        "gold": 75,
        "xp": 450,
    },
    {
        "name": "Clearance Work",
        "description": (
            "Miners expanding the quarry at Stonebridge broke into a sealed vault "
            "of pre-kingdom stonework. The foreman wants the chambers cleared and "
            "surveyed before the Guildhall claims salvage rights."
        ),
        "tier": "Tier 1",
        "region": "Stonebridge Quarry",
        "cooldown_days": 7,
        "gold": 60,
        "xp": 350,
    },
]


# ── Seed functions ───────────────────────────────────────────────────────────

def seed_factions(db, campaign_id: int) -> int:
    created = 0
    for f in FACTIONS:
        exists = (
            db.query(FactionReputation)
            .filter_by(campaign_id=campaign_id, faction_name=f["faction_name"])
            .first()
        )
        if not exists:
            db.add(FactionReputation(campaign_id=campaign_id, level=0, **f))
            created += 1
    db.flush()
    return created


def seed_missions(db, campaign_id: int) -> int:
    created = 0
    for m in MISSIONS:
        exists = (
            db.query(Mission)
            .filter_by(campaign_id=campaign_id, name=m["name"])
            .first()
        )
        if not exists:
            mission = Mission(
                campaign_id=campaign_id,
                name=m["name"],
                description=m["description"],
                tier=m["tier"],
                region=m["region"],
                cooldown_days=m["cooldown_days"],
                status="Available",
                is_discoverable=True,
                is_retired=False,
            )
            db.add(mission)
            db.flush()
            db.add(MissionReward(mission_id=mission.id, gold=m["gold"], xp=m["xp"]))
            created += 1
    db.flush()
    return created


def seed_campaign(campaign_id: int) -> None:
    from app.modules.campaigns.models import Campaign  # noqa: import side effect

    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter_by(id=campaign_id).first()
        if not campaign:
            print(f"Campaign {campaign_id} not found.", file=sys.stderr)
            sys.exit(1)

        print(f"Seeding campaign '{campaign.name}' (id={campaign_id})…")

        factions_created = seed_factions(db, campaign_id)
        missions_created = seed_missions(db, campaign_id)

        db.commit()

        print(f"  Factions: {factions_created} created (skipped existing)")
        print(f"  Missions: {missions_created} created (skipped existing)")
        print("Done.")
    finally:
        db.close()


def find_first_campaign_id() -> int | None:
    from app.modules.campaigns.models import Campaign  # noqa

    db = SessionLocal()
    try:
        c = db.query(Campaign).order_by(Campaign.id).first()
        return c.id if c else None
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed world-bible data into a campaign")
    parser.add_argument("--campaign-id", type=int, help="Campaign ID to seed")
    args = parser.parse_args()

    campaign_id = args.campaign_id or find_first_campaign_id()
    if campaign_id is None:
        print("No campaigns found. Create a campaign first via /campaigns.", file=sys.stderr)
        sys.exit(1)

    seed_campaign(campaign_id)
