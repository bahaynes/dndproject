from datetime import datetime, timezone
from app.modules.characters.service import level_for_xp, award_xp_and_gold
from app.modules.ledger.models import LedgerEntry
from app.modules.items.models import Item, StoreItem
from tests.conftest import _create_user_with_token


def test_level_for_xp_5e_thresholds():
    assert level_for_xp(0) == 1
    assert level_for_xp(299) == 1
    assert level_for_xp(300) == 2
    assert level_for_xp(900) == 3
    assert level_for_xp(6500) == 5
    assert level_for_xp(355000) == 20
    assert level_for_xp(500000) == 20


def test_award_xp_and_gold_auto_levels(db_session, campaign):
    user, _ = _create_user_with_token(db_session, "xp_user_1", "XpHero", "player", campaign.id)
    char = user.active_character
    assert char.level == 1
    assert char.stats.xp == 0
    assert char.stats.gold == 0

    new_lvl = award_xp_and_gold(db_session, char, gold_delta=50, xp_delta=300)
    assert new_lvl == 2
    assert char.level == 2
    assert char.stats.gold == 50
    assert char.stats.xp == 300
    assert char.stats.next_level_xp == 900

    # Second award that doesn't cross a threshold returns None
    no_lvl = award_xp_and_gold(db_session, char, gold_delta=25, xp_delta=100)
    assert no_lvl is None
    assert char.level == 2
    assert char.stats.gold == 75
    assert char.stats.xp == 400


def test_session_signup_respects_max_players_and_cancel(client, db_session, campaign, admin_auth_headers, player_auth_headers):
    # Create a session with max_players=1
    res = client.post(
        "/api/sessions/",
        headers=admin_auth_headers,
        json={
            "name": "Small Delve",
            "session_date": datetime.now(timezone.utc).isoformat(),
            "min_players": 1,
            "max_players": 1,
        },
    )
    assert res.status_code == 200
    session_id = res.json()["id"]

    # First player signs up -> succeeds
    r1 = client.post(f"/api/sessions/{session_id}/signup", headers=player_auth_headers)
    assert r1.status_code == 200
    assert len(r1.json()["players"]) == 1

    # Second player tries to sign up -> rejected (full)
    _, token2 = _create_user_with_token(db_session, "p2_disc", "PlayerTwo", "player", campaign.id)
    r2 = client.post(f"/api/sessions/{session_id}/signup", headers={"Authorization": f"Bearer {token2}"})
    assert r2.status_code == 400
    assert "full" in r2.json()["detail"].lower()

    # Admin cancels session
    rc = client.post(f"/api/sessions/{session_id}/cancel", headers=admin_auth_headers)
    assert rc.status_code == 200
    assert rc.json()["status"] == "Cancelled"


def test_store_purchase_logs_ledger_and_admin_can_delete(client, db_session, campaign, admin_auth_headers, player_auth_headers):
    # Create item & store item
    item = Item(name="Healing Potion", description="2d4+2 HP", campaign_id=campaign.id)
    db_session.add(item)
    db_session.flush()
    store_item = StoreItem(item_id=item.id, price=50, quantity_available=5)
    db_session.add(store_item)
    db_session.commit()
    db_session.refresh(store_item)

    # Give player 100 GP
    from app.modules.auth.models import User
    player = db_session.query(User).filter_by(discord_id="player_discord_123").first()
    player.active_character.stats.gold = 100
    db_session.commit()

    # Purchase 1 potion
    res = client.post(f"/api/store/items/{store_item.id}/purchase?quantity=1", headers=player_auth_headers)
    assert res.status_code == 200

    # Verify ledger entry was recorded
    entry = db_session.query(LedgerEntry).filter_by(campaign_id=campaign.id, event_type="Purchase").first()
    assert entry is not None
    assert "Healing Potion" in entry.description
    assert "50 GP" in entry.description

    # Admin deletes store item
    del_res = client.delete(f"/api/store/items/{store_item.id}", headers=admin_auth_headers)
    assert del_res.status_code == 204
    assert db_session.query(StoreItem).filter_by(id=store_item.id).first() is None
