from datetime import datetime, timezone
from app.modules.admin import service as admin_service, schemas as admin_schemas
from app.modules.campaigns import models as campaign_models
from app.modules.factions import models as faction_models
from app.modules.items import models as item_models
from app.modules.maps import models as map_models
from app.modules.missions import models as mission_models
from app.modules.sessions import models as session_models
from app.modules.ship import models as ship_models


def test_seed_baseline_world_endpoint_and_idempotency(client, admin_auth_headers, player_auth_headers, db_session, campaign):
    # Player cannot seed
    r_forbidden = client.post("/api/admin/seed", headers=player_auth_headers)
    assert r_forbidden.status_code == 403

    # Admin seeds baseline world
    r1 = client.post("/api/admin/seed", headers=admin_auth_headers)
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["world_name"] == "The Ashenvale Frontier"
    assert data1["factions_created"] == 3
    assert data1["items_created"] == 8
    assert data1["missions_created"] == 5
    assert data1["maps_created"] == 1
    assert data1["hexes_upserted"] == 61

    hub = db_session.query(ship_models.Ship).filter_by(campaign_id=campaign.id).first()
    assert hub is not None
    assert hub.name == "Crossroads Keep"
    assert "Ashenvale Frontier" in (hub.motd or "")

    # Re-seeding is idempotent (updates rather than duplicating)
    r2 = client.post("/api/admin/seed", headers=admin_auth_headers)
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["factions_created"] == 0
    assert data2["factions_updated"] == 3
    assert data2["missions_created"] == 0
    assert data2["missions_updated"] == 5


def test_export_and_cross_campaign_import_resolves_names(client, admin_auth_headers, db_session, campaign):
    # Seed source campaign with baseline world + add a prerequisite chain
    r_seed = client.post("/api/admin/seed", headers=admin_auth_headers)
    assert r_seed.status_code == 200

    m1 = db_session.query(mission_models.Mission).filter_by(campaign_id=campaign.id, name="The Quiet Convoy").first()
    m2 = db_session.query(mission_models.Mission).filter_by(campaign_id=campaign.id, name="Whispers in the Mire").first()
    m2.prerequisite_id = m1.id
    db_session.commit()

    # Export via API
    r_exp = client.get("/api/admin/world/export", headers=admin_auth_headers)
    assert r_exp.status_code == 200
    bundle_dict = r_exp.json()
    assert bundle_dict["world_name"] == "Crossroads Keep"
    assert len(bundle_dict["factions"]) == 3
    assert len(bundle_dict["items"]) == 8
    assert len(bundle_dict["missions"]) == 5
    assert len(bundle_dict["maps"]) == 1
    assert len(bundle_dict["maps"][0]["hexes"]) == 61

    mire_export = next(m for m in bundle_dict["missions"] if m["name"] == "Whispers in the Mire")
    assert mire_export["prerequisite_name"] == "The Quiet Convoy"

    # Import into a completely separate campaign
    other_camp = campaign_models.Campaign(name="Other Campaign", discord_guild_id="999888777666555444")
    db_session.add(other_camp)
    db_session.commit()
    db_session.refresh(other_camp)

    bundle = admin_schemas.WorldBundle.model_validate(bundle_dict)
    res = admin_service.import_world(db_session, other_camp.id, bundle, mode="merge")
    assert res.factions_created == 3
    assert res.missions_created == 5
    assert res.maps_created == 1
    assert res.hexes_upserted == 61

    # Verify foreign keys resolved to the target campaign's IDs
    target_m1 = db_session.query(mission_models.Mission).filter_by(campaign_id=other_camp.id, name="The Quiet Convoy").first()
    target_m2 = db_session.query(mission_models.Mission).filter_by(campaign_id=other_camp.id, name="Whispers in the Mire").first()
    assert target_m2.prerequisite_id == target_m1.id
    assert target_m1.id != m1.id

    target_map = db_session.query(map_models.HexMap).filter_by(campaign_id=other_camp.id).first()
    convoy_hex = db_session.query(map_models.Hex).filter_by(map_id=target_map.id, q=1, r=-1).first()
    assert convoy_hex.linked_mission_id == target_m1.id
    assert convoy_hex.controlling_faction == "Borderland Wardens"


def test_import_replace_mode_preserves_sessions_and_inventory(client, admin_auth_headers, db_session, campaign):
    client.post("/api/admin/seed", headers=admin_auth_headers)

    old_mission = db_session.query(mission_models.Mission).filter_by(campaign_id=campaign.id, name="The Quiet Convoy").first()
    gs = session_models.GameSession(
        campaign_id=campaign.id,
        name="Monday Session",
        session_date=datetime.now(timezone.utc),
        confirmed_mission_id=old_mission.id,
    )
    db_session.add(gs)
    db_session.commit()

    new_bundle = admin_schemas.WorldBundle(
        world_name="Fresh World",
        hub=admin_schemas.WorldHub(name="Ironhold", motd="New pitch"),
        factions=[admin_schemas.WorldFaction(faction_name="Iron Pact", color="#ef4444")],
        items=[admin_schemas.WorldItem(name="Torch", store_price=1, store_quantity=-1)],
        missions=[admin_schemas.WorldMission(name="Hold the Gate", tier="Tier 1", rewards=[admin_schemas.WorldMissionReward(gold=40, xp=250)])],
        maps=[admin_schemas.WorldMap(name="Iron Coast", hexes=[admin_schemas.WorldHex(q=0, r=0, terrain="mountain", is_discovered=True, linked_location_name="Ironhold", linked_mission_name="Hold the Gate")])],
    )

    r_imp = client.post(
        "/api/admin/world/import",
        headers=admin_auth_headers,
        json={"bundle": new_bundle.model_dump(), "mode": "replace"},
    )
    assert r_imp.status_code == 200
    res = r_imp.json()
    assert res["factions_created"] == 1
    assert res["missions_created"] == 1
    assert res["maps_created"] == 1

    # Old factions & missions replaced
    assert db_session.query(faction_models.FactionReputation).filter_by(campaign_id=campaign.id).count() == 1
    assert db_session.query(mission_models.Mission).filter_by(campaign_id=campaign.id).count() == 1

    # Existing GameSession preserved with confirmed_mission_id cleanly detached
    db_session.refresh(gs)
    assert gs.name == "Monday Session"
    assert gs.confirmed_mission_id is None


def test_rattleguard_preset_seeds_map_with_routes_that_survive_export(client, admin_auth_headers, db_session, campaign):
    r = client.post("/api/admin/seed?preset=rattleguard_world", headers=admin_auth_headers)
    assert r.status_code == 200
    assert r.json()["maps_created"] == 1

    db_map = db_session.query(map_models.HexMap).filter_by(campaign_id=campaign.id).one()
    assert {rt["id"] for rt in db_map.routes} == {"ridge-road", "bellwatch-spur", "switchbacks", "first-finger"}
    ruin = next(h for h in db_map.hexes if h.linked_location_name == "Tarnhollow (ruin)")
    assert ruin.linked_mission.name == "The Last Bell of Tarnhollow"

    bundle = client.get("/api/admin/world/export", headers=admin_auth_headers).json()
    assert bundle["maps"][0]["routes"] == db_map.routes

    # A bundle without routes must not wipe existing ones on merge
    bundle["maps"][0]["routes"] = []
    admin_service.import_world(
        db_session, campaign.id, admin_schemas.WorldBundle.model_validate(bundle), mode="merge"
    )
    db_session.refresh(db_map)
    assert len(db_map.routes) == 4


def test_starting_gold_follows_world_bundle_but_old_bundles_keep_it(client, admin_auth_headers, campaign, db_session):
    client.post("/api/admin/seed?preset=rattleguard_world", headers=admin_auth_headers)
    assert client.get("/api/ship/", headers=admin_auth_headers).json()["starting_gold"] == 1200

    bundle = client.get("/api/admin/world/export", headers=admin_auth_headers).json()
    assert bundle["hub"]["starting_gold"] == 1200

    del bundle["hub"]["starting_gold"]
    admin_service.import_world(
        db_session, campaign.id, admin_schemas.WorldBundle.model_validate(bundle), mode="merge"
    )
    assert client.get("/api/ship/", headers=admin_auth_headers).json()["starting_gold"] == 1200
