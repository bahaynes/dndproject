import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from sqlalchemy.orm import Session, joinedload

from ..auth import models as auth_models
from ..campaigns import models as campaign_models
from ..characters import models as char_models
from ..factions import models as faction_models
from ..items import models as item_models
from ..maps import models as map_models
from ..missions import models as mission_models
from ..sessions import models as session_models
from ..ship import models as ship_models
from . import schemas


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
BASELINE_WORLD_PATH = DATA_DIR / "baseline_world.json"


def _preset_paths() -> dict[str, Path]:
    if not DATA_DIR.exists():
        return {}
    return {p.stem: p for p in sorted(DATA_DIR.glob("*.json"))}


def list_world_presets() -> list[schemas.WorldPresetSummary]:
    """Return summaries for all built-in starter world JSON presets."""
    presets: list[schemas.WorldPresetSummary] = []
    for slug, path in _preset_paths().items():
        with open(path, "r", encoding="utf-8") as f:
            bundle = schemas.WorldBundle.model_validate(json.load(f))
        hex_count = sum(len(m.hexes) for m in bundle.maps)
        presets.append(
            schemas.WorldPresetSummary(
                slug=slug,
                world_name=bundle.world_name,
                hub_name=bundle.hub.name if bundle.hub else None,
                summary=bundle.hub.motd if bundle.hub else None,
                factions=len(bundle.factions),
                items=len(bundle.items),
                missions=len(bundle.missions),
                maps=len(bundle.maps),
                hexes=hex_count,
            )
        )
    return presets


def load_world_preset(preset: str = "baseline_world") -> schemas.WorldBundle:
    """Load a built-in starter world preset by slug."""
    paths = _preset_paths()
    path = paths.get(preset)
    if path is None:
        raise ValueError(f"Unknown world preset: {preset}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return schemas.WorldBundle.model_validate(data)


def load_baseline_world() -> schemas.WorldBundle:
    return load_world_preset("baseline_world")


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
    # Legacy stub kept for backwards compatibility
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


def export_world(db: Session, campaign_id: int) -> schemas.WorldBundle:
    campaign = db.query(campaign_models.Campaign).filter_by(id=campaign_id).first()
    hub = db.query(ship_models.Ship).filter_by(campaign_id=campaign_id).first()
    factions = (
        db.query(faction_models.FactionReputation)
        .filter_by(campaign_id=campaign_id)
        .order_by(faction_models.FactionReputation.id.asc())
        .all()
    )
    items = (
        db.query(item_models.Item)
        .options(joinedload(item_models.Item.store_listing))
        .filter_by(campaign_id=campaign_id)
        .order_by(item_models.Item.id.asc())
        .all()
    )
    missions = (
        db.query(mission_models.Mission)
        .options(joinedload(mission_models.Mission.rewards).joinedload(mission_models.MissionReward.item))
        .filter_by(campaign_id=campaign_id)
        .order_by(mission_models.Mission.id.asc())
        .all()
    )
    maps = (
        db.query(map_models.HexMap)
        .options(joinedload(map_models.HexMap.hexes))
        .filter_by(campaign_id=campaign_id)
        .order_by(map_models.HexMap.id.asc())
        .all()
    )

    mission_name_by_id = {m.id: m.name for m in missions}

    world_name = hub.name if hub and hub.name else (campaign.name if campaign else "World")
    hub_out = (
        schemas.WorldHub(
            name=hub.name,
            motd=hub.motd,
            town_locations=[ship_schemas.TownLocation.model_validate(loc) for loc in (hub.town_locations or [])]
            if hasattr(schemas, "TownLocation")
            else [schemas.TownLocation.model_validate(loc) for loc in (hub.town_locations or [])],
        )
        if hub
        else None
    )

    factions_out = [
        schemas.WorldFaction(
            faction_name=f.faction_name,
            level=f.level,
            color=f.color,
            description=f.description,
        )
        for f in factions
    ]

    items_out = [
        schemas.WorldItem(
            name=i.name,
            description=i.description,
            store_price=i.store_listing.price if i.store_listing else None,
            store_quantity=i.store_listing.quantity_available if i.store_listing else None,
        )
        for i in items
    ]

    missions_out = [
        schemas.WorldMission(
            name=m.name,
            description=m.description,
            status=m.status,
            tier=m.tier,
            region=m.region,
            cooldown_days=m.cooldown_days if m.cooldown_days is not None else 7,
            is_discoverable=bool(m.is_discoverable),
            is_retired=bool(m.is_retired),
            prerequisite_name=mission_name_by_id.get(m.prerequisite_id) if m.prerequisite_id else None,
            rewards=[
                schemas.WorldMissionReward(
                    gold=r.gold,
                    xp=r.xp if r.xp is not None else 0,
                    item_name=r.item.name if r.item else None,
                    is_hidden=bool(r.is_hidden),
                    hint=r.hint,
                )
                for r in m.rewards
            ],
        )
        for m in missions
    ]

    maps_out = [
        schemas.WorldMap(
            name=mp.name,
            width=mp.width,
            height=mp.height,
            hex_size=mp.hex_size,
            default_terrain=mp.default_terrain,
            hexes=[
                schemas.WorldHex(
                    q=h.q,
                    r=h.r,
                    terrain=h.terrain,
                    is_discovered=bool(h.is_discovered),
                    hex_state=h.hex_state or "wilderness",
                    controlling_faction=h.controlling_faction,
                    linked_location_name=h.linked_location_name,
                    linked_mission_name=mission_name_by_id.get(h.linked_mission_id) if h.linked_mission_id else None,
                    notes=h.notes,
                )
                for h in sorted(mp.hexes, key=lambda x: (x.q, x.r))
            ],
        )
        for mp in maps
    ]

    return schemas.WorldBundle(
        schema_version=1,
        world_name=world_name,
        exported_at=datetime.now(timezone.utc).isoformat(),
        hub=hub_out,
        factions=factions_out,
        items=items_out,
        missions=missions_out,
        maps=maps_out,
    )


def import_world(
    db: Session,
    campaign_id: int,
    bundle: schemas.WorldBundle,
    mode: Literal["merge", "replace"] = "merge",
) -> schemas.WorldImportResult:
    result = schemas.WorldImportResult(world_name=bundle.world_name, mode=mode)

    if mode == "replace":
        # Detach any GameSession mission references so sessions are preserved
        db.query(session_models.GameSession).filter(
            session_models.GameSession.campaign_id == campaign_id
        ).update({session_models.GameSession.confirmed_mission_id: None}, synchronize_session=False)

        # Delete campaign maps (cascades to hexes)
        for mp in db.query(map_models.HexMap).filter_by(campaign_id=campaign_id).all():
            db.delete(mp)

        # Delete campaign missions (cascades to rewards), mission_players, and session_proposals
        campaign_mission_ids = [
            m.id for m in db.query(mission_models.Mission.id).filter_by(campaign_id=campaign_id).all()
        ]
        if campaign_mission_ids:
            proposal_ids = [
                p.id
                for p in db.query(session_models.SessionProposal.id)
                .filter(session_models.SessionProposal.mission_id.in_(campaign_mission_ids))
                .all()
            ]
            if proposal_ids:
                db.execute(
                    session_models.proposal_backers.delete().where(
                        session_models.proposal_backers.c.proposal_id.in_(proposal_ids)
                    )
                )
                db.query(session_models.SessionProposal).filter(
                    session_models.SessionProposal.id.in_(proposal_ids)
                ).delete(synchronize_session=False)

            db.execute(
                mission_models.mission_players.delete().where(
                    mission_models.mission_players.c.mission_id.in_(campaign_mission_ids)
                )
            )
            for m in db.query(mission_models.Mission).filter_by(campaign_id=campaign_id).all():
                m.prerequisite_id = None
                db.delete(m)

        # Delete campaign factions (cascades to events)
        for fac in db.query(faction_models.FactionReputation).filter_by(campaign_id=campaign_id).all():
            db.delete(fac)

        # Remove store listings for campaign items (preserve Item rows still in character inventories)
        campaign_item_ids = [
            i.id for i in db.query(item_models.Item.id).filter_by(campaign_id=campaign_id).all()
        ]
        if campaign_item_ids:
            db.query(item_models.StoreItem).filter(
                item_models.StoreItem.item_id.in_(campaign_item_ids)
            ).delete(synchronize_session=False)

        db.flush()

    # 1. Hub / Bulletin (Ship)
    if bundle.hub:
        locations_data = [loc.model_dump() for loc in bundle.hub.town_locations]
        hub = db.query(ship_models.Ship).filter_by(campaign_id=campaign_id).first()
        if not hub:
            hub = ship_models.Ship(
                campaign_id=campaign_id,
                name=bundle.hub.name,
                motd=bundle.hub.motd,
                town_locations=locations_data,
            )
            db.add(hub)
        else:
            hub.name = bundle.hub.name
            hub.motd = bundle.hub.motd
            hub.town_locations = locations_data
        db.flush()

    # 2. Factions
    existing_factions = {
        f.faction_name: f
        for f in db.query(faction_models.FactionReputation).filter_by(campaign_id=campaign_id).all()
    }
    for fac_in in bundle.factions:
        fac = existing_factions.get(fac_in.faction_name)
        if not fac:
            fac = faction_models.FactionReputation(
                campaign_id=campaign_id,
                faction_name=fac_in.faction_name,
                level=max(-5, min(5, fac_in.level)),
                color=fac_in.color,
                description=fac_in.description,
            )
            db.add(fac)
            existing_factions[fac_in.faction_name] = fac
            result.factions_created += 1
        else:
            fac.color = fac_in.color
            fac.description = fac_in.description
            result.factions_updated += 1
    db.flush()

    # 3. Items & Store Listings
    item_by_name = {
        i.name: i
        for i in db.query(item_models.Item).options(joinedload(item_models.Item.store_listing)).filter_by(campaign_id=campaign_id).all()
    }
    for item_in in bundle.items:
        item = item_by_name.get(item_in.name)
        if not item:
            item = item_models.Item(
                campaign_id=campaign_id,
                name=item_in.name,
                description=item_in.description,
            )
            db.add(item)
            db.flush()
            item_by_name[item_in.name] = item
            result.items_created += 1
        else:
            item.description = item_in.description
            result.items_updated += 1

        if item_in.store_price is not None:
            qty = item_in.store_quantity if item_in.store_quantity is not None else -1
            if item.store_listing:
                item.store_listing.price = item_in.store_price
                item.store_listing.quantity_available = qty
            else:
                db.add(item_models.StoreItem(
                    item_id=item.id,
                    price=item_in.store_price,
                    quantity_available=qty,
                ))
    db.flush()

    # 4. Missions (Pass 1: upsert missions & rewards; Pass 2: prerequisites)
    mission_by_name = {
        m.name: m
        for m in db.query(mission_models.Mission).options(joinedload(mission_models.Mission.rewards)).filter_by(campaign_id=campaign_id).all()
    }
    for m_in in bundle.missions:
        mission = mission_by_name.get(m_in.name)
        if not mission:
            mission = mission_models.Mission(
                campaign_id=campaign_id,
                name=m_in.name,
                description=m_in.description,
                status=m_in.status,
                tier=m_in.tier,
                region=m_in.region,
                cooldown_days=m_in.cooldown_days,
                is_discoverable=m_in.is_discoverable,
                is_retired=m_in.is_retired,
            )
            db.add(mission)
            db.flush()
            mission_by_name[m_in.name] = mission
            result.missions_created += 1
        else:
            mission.description = m_in.description
            mission.status = m_in.status
            mission.tier = m_in.tier
            mission.region = m_in.region
            mission.cooldown_days = m_in.cooldown_days
            mission.is_discoverable = m_in.is_discoverable
            mission.is_retired = m_in.is_retired
            mission.rewards.clear()
            db.flush()
            result.missions_updated += 1

        for r_in in m_in.rewards:
            linked_item = item_by_name.get(r_in.item_name) if r_in.item_name else None
            db.add(mission_models.MissionReward(
                mission_id=mission.id,
                gold=r_in.gold,
                xp=r_in.xp or 0,
                item_id=linked_item.id if linked_item else None,
                is_hidden=r_in.is_hidden,
                hint=r_in.hint,
            ))
    db.flush()

    for m_in in bundle.missions:
        if m_in.prerequisite_name:
            mission = mission_by_name.get(m_in.name)
            prereq = mission_by_name.get(m_in.prerequisite_name)
            if mission and prereq and prereq.id != mission.id:
                mission.prerequisite_id = prereq.id
    db.flush()

    # 5. Maps & Hexes
    existing_maps = {
        mp.name: mp
        for mp in db.query(map_models.HexMap).options(joinedload(map_models.HexMap.hexes)).filter_by(campaign_id=campaign_id).all()
    }
    for map_in in bundle.maps:
        db_map = existing_maps.get(map_in.name)
        if not db_map:
            db_map = map_models.HexMap(
                campaign_id=campaign_id,
                name=map_in.name,
                width=map_in.width,
                height=map_in.height,
                hex_size=map_in.hex_size,
                default_terrain=map_in.default_terrain,
            )
            db.add(db_map)
            db.flush()
            existing_maps[map_in.name] = db_map
            result.maps_created += 1
        else:
            db_map.width = map_in.width
            db_map.height = map_in.height
            db_map.hex_size = map_in.hex_size
            db_map.default_terrain = map_in.default_terrain
            result.maps_updated += 1

        hex_by_coord = {(h.q, h.r): h for h in db_map.hexes}
        for h_in in map_in.hexes:
            linked_mission = mission_by_name.get(h_in.linked_mission_name) if h_in.linked_mission_name else None
            db_hex = hex_by_coord.get((h_in.q, h_in.r))
            if not db_hex:
                db_hex = map_models.Hex(
                    map_id=db_map.id,
                    q=h_in.q,
                    r=h_in.r,
                    terrain=h_in.terrain,
                    is_discovered=h_in.is_discovered,
                    hex_state=h_in.hex_state,
                    controlling_faction=h_in.controlling_faction,
                    linked_location_name=h_in.linked_location_name,
                    linked_mission_id=linked_mission.id if linked_mission else None,
                    notes=h_in.notes,
                )
                db.add(db_hex)
            else:
                db_hex.terrain = h_in.terrain
                db_hex.is_discovered = h_in.is_discovered
                db_hex.hex_state = h_in.hex_state
                db_hex.controlling_faction = h_in.controlling_faction
                db_hex.linked_location_name = h_in.linked_location_name
                db_hex.linked_mission_id = linked_mission.id if linked_mission else None
                db_hex.notes = h_in.notes
            result.hexes_upserted += 1

    db.commit()
    return result
