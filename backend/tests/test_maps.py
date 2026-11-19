import pytest
from conftest import _create_user_with_token
from app.modules.campaigns import models as campaign_models


def _create_map(client, admin_headers, name="Test Map", seed=True):
    res = client.post(
        "/api/maps/",
        json={"name": name, "width": 5, "height": 5, "hex_size": 60},
        headers=admin_headers,
    )
    assert res.status_code == 200
    return res.json()


def test_get_maps_lazy_creates_default(client, campaign, player_auth_headers):
    res = client.get("/api/maps/", headers=player_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["name"] == "The Known World"


def test_get_maps_returns_existing(client, campaign, player_auth_headers, admin_auth_headers):
    _create_map(client, admin_auth_headers, name="My Map")
    res = client.get("/api/maps/", headers=player_auth_headers)
    assert res.status_code == 200
    assert any(m["name"] == "My Map" for m in res.json())


def test_create_map_admin(client, campaign, admin_auth_headers):
    res = client.post(
        "/api/maps/",
        json={"name": "Admin Map", "width": 10, "height": 10, "hex_size": 60},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Admin Map"


def test_create_map_player_forbidden(client, campaign, player_auth_headers):
    res = client.post(
        "/api/maps/",
        json={"name": "Player Map", "width": 10, "height": 10, "hex_size": 60},
        headers=player_auth_headers,
    )
    assert res.status_code == 403


def test_get_map_by_id(client, campaign, player_auth_headers, admin_auth_headers):
    m = _create_map(client, admin_auth_headers)
    res = client.get(f"/api/maps/{m['id']}", headers=player_auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == m["id"]


def test_get_map_not_found(client, campaign, player_auth_headers):
    res = client.get("/api/maps/99999", headers=player_auth_headers)
    assert res.status_code == 404


def test_get_map_other_campaign_returns_404(client, db_session, campaign, player_auth_headers):
    other_camp = campaign_models.Campaign(name="Other Camp", discord_guild_id="999")
    db_session.add(other_camp)
    db_session.commit()
    db_session.refresh(other_camp)
    _, other_token = _create_user_with_token(db_session, "other_map", "OtherMap", "admin", other_camp.id)
    other_headers = {"Authorization": f"Bearer {other_token}"}
    other_map = client.post(
        "/api/maps/",
        json={"name": "Other Map", "width": 5, "height": 5, "hex_size": 60},
        headers=other_headers,
    ).json()

    res = client.get(f"/api/maps/{other_map['id']}", headers=player_auth_headers)
    assert res.status_code == 404


def test_update_hex_admin(client, campaign, admin_auth_headers):
    m = _create_map(client, admin_auth_headers)
    res = client.put(
        f"/api/maps/{m['id']}/hexes/0/0",
        json={"is_discovered": True, "hex_state": "friendly"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["is_discovered"] is True
    assert res.json()["hex_state"] == "friendly"


def test_update_hex_player_forbidden(client, campaign, admin_auth_headers, player_auth_headers):
    m = _create_map(client, admin_auth_headers)
    res = client.put(
        f"/api/maps/{m['id']}/hexes/0/0",
        json={"is_discovered": True},
        headers=player_auth_headers,
    )
    assert res.status_code == 403


def test_add_player_note_on_discovered_hex(client, campaign, player_auth_headers):
    # Lazy-created map seeds q=0,r=0 as discovered
    maps = client.get("/api/maps/", headers=player_auth_headers).json()
    map_id = maps[0]["id"]
    res = client.post(
        f"/api/maps/{map_id}/hexes/0/0/notes",
        json={"text": "There's a cave here"},
        headers=player_auth_headers,
    )
    assert res.status_code == 200
    assert any(n["text"] == "There's a cave here" for n in res.json()["player_notes"])


def test_add_player_note_on_undiscovered_hex(client, campaign, player_auth_headers):
    # q=1,r=0 exists in the seeded grid (radius=5) but is_discovered=False
    maps = client.get("/api/maps/", headers=player_auth_headers).json()
    map_id = maps[0]["id"]
    res = client.post(
        f"/api/maps/{map_id}/hexes/1/0/notes",
        json={"text": "Secret note"},
        headers=player_auth_headers,
    )
    assert res.status_code == 400
    assert "undiscovered" in res.json()["detail"].lower()


def test_add_note_wrong_campaign(client, db_session, campaign, player_auth_headers):
    other_camp = campaign_models.Campaign(name="Other Camp 2", discord_guild_id="888")
    db_session.add(other_camp)
    db_session.commit()
    db_session.refresh(other_camp)
    _, other_token = _create_user_with_token(db_session, "note_other", "NoteOther", "admin", other_camp.id)
    other_headers = {"Authorization": f"Bearer {other_token}"}
    other_map = client.post(
        "/api/maps/",
        json={"name": "Other Map", "width": 5, "height": 5, "hex_size": 60},
        headers=other_headers,
    ).json()

    res = client.post(
        f"/api/maps/{other_map['id']}/hexes/0/0/notes",
        json={"text": "Cross-campaign note"},
        headers=player_auth_headers,
    )
    assert res.status_code == 404


def test_earth_baker_renders_pngs_and_classifies_terrain():
    import io
    import numpy as np
    from PIL import Image
    from app.modules.maps.earth_baker import (
        classify_hex_terrains,
        compute_hex_layer_bounds,
        render_topo_and_satellite,
    )

    coords = [(0, 0), (1, 0), (-1, 0), (0, 1)]
    bounds = compute_hex_layer_bounds(coords, hex_size=60)
    elev = np.full((128, 128), 100.0, dtype=np.float32)
    elev[:, :32] = -10.0  # ocean on left
    elev[:, 96:] = 1500.0  # mountains on right
    masks = {
        "water": np.zeros((128, 128), dtype=bool),
        "wood": np.zeros((128, 128), dtype=bool),
        "wetland": np.zeros((128, 128), dtype=bool),
    }
    masks["wood"][64:, 32:64] = True

    topo_png, sat_png = render_topo_and_satellite(elev, masks)
    assert Image.open(io.BytesIO(topo_png)).format == "PNG"
    assert Image.open(io.BytesIO(sat_png)).format == "PNG"

    terrains = classify_hex_terrains(elev, masks, coords, hex_size=60, bounds=bounds)
    assert terrains[(-1, 0)] == "water"
    assert terrains[(1, 0)] == "mountain"
    assert terrains[(0, 1)] == "forest"


def test_bake_earth_and_fetch_layers(client, db_session, campaign, admin_auth_headers, player_auth_headers, tmp_path, monkeypatch):
    from unittest.mock import AsyncMock
    from app.modules.maps import router as maps_router
    from app.modules.maps.earth_baker import BakedMapResult
    from app.modules.maps.storage import LocalMapLayerStorage

    m = _create_map(client, admin_auth_headers)
    storage = LocalMapLayerStorage(str(tmp_path))
    monkeypatch.setattr(maps_router, "get_layer_storage", lambda: storage)

    fake_result = BakedMapResult(
        topo_png=b"\x89PNG\r\n\x1a\ntopo",
        satellite_png=b"\x89PNG\r\n\x1a\nsat",
        layer_bounds={"min_x": -510.0, "min_y": -571.5, "max_x": 510.0, "max_y": 571.5},
        hex_terrains={(0, 0): "mountain"},
        zoom=8,
    )
    monkeypatch.setattr(maps_router, "bake_earth_region", AsyncMock(return_value=fake_result))

    # Player cannot bake
    res_forbidden = client.post(
        f"/api/maps/{m['id']}/bake-earth",
        json={"min_lat": 64.0, "min_lon": -22.0, "max_lat": 65.0, "max_lon": -20.0},
        headers=player_auth_headers,
    )
    assert res_forbidden.status_code == 403

    # Invalid bbox rejected
    res_bad = client.post(
        f"/api/maps/{m['id']}/bake-earth",
        json={"min_lat": 65.0, "min_lon": -20.0, "max_lat": 64.0, "max_lon": -22.0},
        headers=admin_auth_headers,
    )
    assert res_bad.status_code == 400

    # Admin bake succeeds
    res = client.post(
        f"/api/maps/{m['id']}/bake-earth",
        json={"min_lat": 64.0, "min_lon": -22.0, "max_lat": 65.0, "max_lon": -20.0, "auto_seed_terrain": True},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["topo_image_url"] == f"/api/maps/{m['id']}/layers/topo"
    assert body["satellite_image_url"] == f"/api/maps/{m['id']}/layers/satellite"
    assert body["layer_bounds"]["min_x"] == -510.0
    assert body["source_region"]["zoom"] == 8
    center_hex = next(h for h in body["hexes"] if h["q"] == 0 and h["r"] == 0)
    assert center_hex["terrain"] == "mountain"

    # Player in same campaign can fetch both layers
    topo_resp = client.get(body["topo_image_url"], headers=player_auth_headers)
    assert topo_resp.status_code == 200
    assert topo_resp.content == b"\x89PNG\r\n\x1a\ntopo"
    assert topo_resp.headers["content-type"] == "image/png"

    sat_resp = client.get(body["satellite_image_url"], headers=player_auth_headers)
    assert sat_resp.status_code == 200
    assert sat_resp.content == b"\x89PNG\r\n\x1a\nsat"

    # Cross-campaign user gets 404
    other_camp = campaign_models.Campaign(name="Other Camp 3", discord_guild_id="999")
    db_session.add(other_camp)
    db_session.commit()
    db_session.refresh(other_camp)
    _, other_token = _create_user_with_token(db_session, "layer_other", "LayerOther", "player", other_camp.id)
    res_other = client.get(
        body["topo_image_url"],
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert res_other.status_code == 404


def test_bake_earth_from_center_pin_and_travel_scale(client, campaign, admin_auth_headers, tmp_path, monkeypatch):
    from unittest.mock import AsyncMock
    from app.modules.maps import router as maps_router
    from app.modules.maps.earth_baker import BakedMapResult, compute_bbox_from_center
    from app.modules.maps.storage import LocalMapLayerStorage

    min_lat, min_lon, max_lat, max_lon = compute_bbox_from_center(
        center_lat=64.1466,
        center_lon=-21.9426,
        hex_coords=[(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)],
        hex_size=60,
        travel_scale="frontier",
    )
    assert min_lat < 64.1466 < max_lat
    assert min_lon < -21.9426 < max_lon

    m = _create_map(client, admin_auth_headers)
    storage = LocalMapLayerStorage(str(tmp_path))
    monkeypatch.setattr(maps_router, "get_layer_storage", lambda: storage)

    fake_result = BakedMapResult(
        topo_png=b"\x89PNG\r\n\x1a\ntopo2",
        satellite_png=b"\x89PNG\r\n\x1a\nsat2",
        layer_bounds={"min_x": -510.0, "min_y": -571.5, "max_x": 510.0, "max_y": 571.5},
        hex_terrains={(0, 0): "plains"},
        zoom=9,
    )
    monkeypatch.setattr(maps_router, "bake_earth_region", AsyncMock(return_value=fake_result))

    res = client.post(
        f"/api/maps/{m['id']}/bake-earth",
        json={"center_lat": 64.1466, "center_lon": -21.9426, "travel_scale": "frontier"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    sr = res.json()["source_region"]
    assert sr["center_lat"] == 64.1466
    assert sr["center_lon"] == -21.9426
    assert sr["travel_scale"] == "frontier"


def test_update_map_routes(client, campaign, admin_auth_headers, player_auth_headers):
    m = _create_map(client, admin_auth_headers)
    payload = {
        "routes": [
            {
                "id": "route-1",
                "name": "King's Road",
                "type": "road",
                "hexes": [{"q": 0, "r": 0}, {"q": 1, "r": 0}, {"q": 2, "r": -1}],
            },
            {
                "id": "route-2",
                "name": "Meridian Sea Lane",
                "type": "sea_lane",
                "hexes": [{"q": 0, "r": 0}, {"q": -1, "r": 1}],
            },
        ]
    }

    # Player cannot update routes
    res_forbidden = client.put(f"/api/maps/{m['id']}/routes", json=payload, headers=player_auth_headers)
    assert res_forbidden.status_code == 403

    # Admin updates routes
    res = client.put(f"/api/maps/{m['id']}/routes", json=payload, headers=admin_auth_headers)
    assert res.status_code == 200
    routes = res.json()["routes"]
    assert len(routes) == 2
    assert routes[0]["name"] == "King's Road"
    assert routes[0]["type"] == "road"
    assert len(routes[0]["hexes"]) == 3

    # GET returns saved routes
    fetched = client.get(f"/api/maps/{m['id']}", headers=player_auth_headers).json()
    assert len(fetched["routes"]) == 2
