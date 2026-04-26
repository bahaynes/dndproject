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
        "faction_name": "The Alliance",
        "color": "#3b82f6",
        "description": (
            "Controls core worlds via stable monument-bound Vincula. "
            "Institutional, bureaucratic, resource-rich. Their real power is "
            "transit — controlling sworn Vincula means controlling who moves "
            "between worlds. Not evil; they built a functional system. "
            "The darkness is structural."
        ),
    },
    {
        "faction_name": "The Rim",
        "color": "#d97706",
        "description": (
            "Not an organization — a condition. Frontier worlds, independent "
            "crews, pirates, salvagers, waystation economies. Everyone the "
            "Alliance didn't reach in time, or who refused the deal, or who "
            "got priced out. The Alliance needs Rim output; they just prefer "
            "the Rim not to know that."
        ),
    },
]


# ── Opening missions ─────────────────────────────────────────────────────────
# Net Essence (transit already deducted). Tier 1 standard = 4 net.
# Gross posted bounty = net + tier transit (1 for Tier 1).

MISSIONS = [
    {
        "name": "Belated",
        "description": (
            "A supply convoy out of Waystation Krel went quiet three days ago. "
            "The manifest is routine — water reclamation parts, nothing worth "
            "hijacking. No one's heard a shot fired. Meridian has a course "
            "plotted. She hasn't said why she's being quiet about it."
        ),
        "tier": "Tier 1",
        "region": "Near Rim",
        "cooldown_days": 14,
        "essence_net": 3,  # Routine difficulty: 2 net + 1 transit = 3 gross posted
    },
    {
        "name": "Last Transmission",
        "description": (
            "A listening post on the edge of the contested band sent a partial "
            "burst three weeks ago — coordinates, an Alliance vessel ID, and "
            "the word 'derelict'. The Alliance hasn't sent a recovery team. "
            "That's either an oversight or a decision. Either way, the post "
            "is still broadcasting on loop."
        ),
        "tier": "Tier 1",
        "region": "Contested Band",
        "cooldown_days": 14,
        "essence_net": 5,  # Standard difficulty: 4 net + 1 transit = 5 gross posted
    },
    {
        "name": "Clearance Work",
        "description": (
            "Waystation Krel is expanding a docking bay and hit something "
            "buried in the rock — old, pre-Calamity construction. "
            "The station master wants it cleared and catalogued before the "
            "Alliance notices and starts asking questions about permits. "
            "Pay is flat. Anything you find in there you keep."
        ),
        "tier": "Tier 1",
        "region": "Near Rim",
        "cooldown_days": 7,
        "essence_net": 4,  # Standard: 4 net + 1 transit = 5 gross, minus some for item upside
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
            # Essence reward row
            db.add(MissionReward(mission_id=mission.id, gold=m["essence_net"] * 10))
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
