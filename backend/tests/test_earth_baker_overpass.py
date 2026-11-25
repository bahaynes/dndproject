import asyncio

import httpx
import pytest

from app.modules.maps import earth_baker
from app.modules.maps.storage import LocalMapLayerStorage

BBOX = (46.0, 7.0, 47.0, 8.0)


@pytest.fixture
def overpass(monkeypatch):
    """Serve canned Overpass responses and record requests and pauses."""
    state = {"responses": [], "requests": [], "pauses": []}

    def handler(request):
        state["requests"].append(request)
        resp = state["responses"].pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        earth_baker.httpx,
        "AsyncClient",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    async def fake_sleep(seconds):
        state["pauses"].append(seconds)

    monkeypatch.setattr(earth_baker.asyncio, "sleep", fake_sleep)
    return state


def fetch(cache=None):
    return asyncio.run(earth_baker._fetch_osm_natural_masks(*BBOX, 100, 100, cache=cache))


def ok(elements, **extra):
    return httpx.Response(200, json={"elements": elements, **extra})


def ring(lat0, lon0, lat1, lon1):
    return [
        {"lat": lat0, "lon": lon0},
        {"lat": lat0, "lon": lon1},
        {"lat": lat1, "lon": lon1},
        {"lat": lat1, "lon": lon0},
        {"lat": lat0, "lon": lon0},
    ]


WOOD = {"type": "way", "tags": {"natural": "wood"}, "geometry": ring(46.2, 7.2, 46.8, 7.8)}


def test_success_identifies_app_and_has_no_warning(overpass):
    overpass["responses"] = [ok([WOOD])]
    masks, warnings = fetch()
    assert masks["wood"][50, 50] and not masks["wood"][5, 5]
    assert warnings == []
    assert "westmarches.bahaynes.com" in overpass["requests"][0].headers["user-agent"]


def test_busy_server_is_retried_once_after_a_pause(overpass):
    overpass["responses"] = [httpx.Response(502), ok([WOOD])]
    masks, warnings = fetch()
    assert masks["wood"].any() and warnings == []
    assert overpass["pauses"] == [30.0]


@pytest.mark.parametrize(
    "responses, requests",
    [
        ([httpx.Response(502), httpx.Response(502)], 2),
        ([httpx.Response(406)], 1),  # may be a block: do not ask again
        ([httpx.ConnectTimeout("slow")], 1),
        ([httpx.Response(200, text="<html>")], 1),
        ([httpx.Response(200, json={"elements": [], "remark": "runtime error: Query timed out"})], 1),
    ],
)
def test_failures_warn_instead_of_passing_silently(overpass, responses, requests):
    overpass["responses"] = list(responses)
    masks, warnings = fetch()
    assert len(warnings) == 1 and "missing" in warnings[0]
    assert not any(m.any() for m in masks.values())
    assert len(overpass["requests"]) == requests


def test_multipolygon_relation_joins_segments_and_keeps_holes(overpass):
    outer = ring(46.1, 7.1, 46.9, 7.9)
    relation = {
        "type": "relation",
        "tags": {"natural": "water", "type": "multipolygon"},
        "members": [
            {"type": "way", "role": "outer", "geometry": outer[:3]},
            {"type": "way", "role": "outer", "geometry": list(reversed(outer[2:]))},
            {"type": "way", "role": "inner", "geometry": ring(46.4, 7.4, 46.6, 7.6)},
        ],
    }
    overpass["responses"] = [ok([relation])]
    masks, _ = fetch()
    assert masks["water"][20, 20]
    assert not masks["water"][50, 50]


def test_responses_are_cached_but_failures_are_not(overpass, tmp_path):
    cache = LocalMapLayerStorage(str(tmp_path))
    overpass["responses"] = [httpx.Response(406), ok([WOOD])]
    assert fetch(cache)[1]
    assert fetch(cache)[1] == []
    masks, warnings = fetch(cache)
    assert masks["wood"].any() and warnings == []
    assert len(overpass["requests"]) == 2
