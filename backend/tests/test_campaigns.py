"""
Campaign endpoint integration tests.

Covers /setup, /available, /join, /login, and /mine paths.
These endpoints use global (pre-campaign) tokens and interact with the Discord
API, so Discord calls are mocked via httpx.AsyncClient patches.
"""
from unittest.mock import patch, AsyncMock
from app import security


# ---------------------------------------------------------------------------
# Helpers / mock infrastructure
# ---------------------------------------------------------------------------

def _global_token(discord_id: str, username: str = "TestUser", avatar: str = None) -> str:
    return security.create_access_token(
        data={"sub": discord_id, "type": "global", "username": username, "avatar": avatar}
    )


class _MockResponse:
    def __init__(self, status_code: int, data):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


def _make_httpx_mock(responses: dict):
    """
    Returns an async context manager whose .get() dispatches by URL prefix.
    `responses` maps URL substrings to (status_code, data) tuples.
    """
    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, **kwargs):
            for key, (code, data) in responses.items():
                if key in url:
                    return _MockResponse(code, data)
            return _MockResponse(404, {})

    return _Client()


def _patch_campaigns_httpx(responses: dict):
    client = _make_httpx_mock(responses)
    return patch("app.modules.campaigns.router.httpx.AsyncClient", return_value=client)


# ---------------------------------------------------------------------------
# /api/campaigns/mine
# ---------------------------------------------------------------------------

class TestGetMyCampaigns:
    def test_returns_empty_list_for_new_user(self, client):
        token = _global_token("new_user_999")
        r = client.get("/api/campaigns/mine", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_campaign_user_is_member_of(self, client, db_session):
        from app.modules.campaigns import models as campaign_models
        from app.modules.auth import models as auth_models

        camp = campaign_models.Campaign(name="My Guild", discord_guild_id="guild_mine_1")
        db_session.add(camp)
        db_session.flush()

        user = auth_models.User(
            username="MineUser", discord_id="mine_discord_1", campaign_id=camp.id, role="player"
        )
        db_session.add(user)
        db_session.commit()

        token = _global_token("mine_discord_1", username="MineUser")
        r = client.get("/api/campaigns/mine", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["name"] == "My Guild"

    def test_rejects_missing_token(self, client):
        r = client.get("/api/campaigns/mine")
        assert r.status_code == 401

    def test_rejects_unauthenticated(self, client):
        r = client.get("/api/campaigns/mine")
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# /api/campaigns/login
# ---------------------------------------------------------------------------

class TestLoginToCampaign:
    def test_returns_campaign_scoped_token(self, client, db_session):
        from app.modules.campaigns import models as campaign_models
        from app.modules.auth import models as auth_models

        camp = campaign_models.Campaign(name="Login Camp", discord_guild_id="guild_login_1")
        db_session.add(camp)
        db_session.flush()

        user = auth_models.User(
            username="LoginUser", discord_id="login_discord_1", campaign_id=camp.id, role="player"
        )
        db_session.add(user)
        db_session.commit()

        token = _global_token("login_discord_1")
        r = client.post(
            "/api/campaigns/login",
            json={"campaign_id": camp.id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_rejects_non_member(self, client, db_session):
        from app.modules.campaigns import models as campaign_models

        camp = campaign_models.Campaign(name="Exclusive Camp", discord_guild_id="guild_excl_1")
        db_session.add(camp)
        db_session.commit()

        token = _global_token("outsider_discord_1")
        r = client.post(
            "/api/campaigns/login",
            json={"campaign_id": camp.id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# /api/campaigns/setup
# ---------------------------------------------------------------------------

class TestSetupCampaign:
    def _admin_token(self, discord_id: str) -> str:
        return _global_token(discord_id, username="AdminSetup")

    def test_creates_campaign_and_returns_token(self, client, db_session):
        with patch("app.modules.campaigns.router.settings") as mock_settings:
            mock_settings.ADMIN_DISCORD_IDS = "setup_admin_1"
            token = self._admin_token("setup_admin_1")
            r = client.post(
                "/api/campaigns/setup",
                json={"name": "New Campaign", "discord_guild_id": "guild_setup_1"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_setup_binds_creator_as_admin_user(self, client, db_session):
        """Creator must get a User record in the new campaign with role=admin."""
        with patch("app.modules.campaigns.router.settings") as mock_settings:
            mock_settings.ADMIN_DISCORD_IDS = "setup_admin_2"
            token = self._admin_token("setup_admin_2")
            r = client.post(
                "/api/campaigns/setup",
                json={"name": "Bound Campaign", "discord_guild_id": "guild_setup_2"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 200, r.text

        from app.modules.auth import models as auth_models
        from app.modules.campaigns import models as campaign_models

        camp = db_session.query(campaign_models.Campaign).filter_by(
            discord_guild_id="guild_setup_2"
        ).first()
        assert camp is not None

        user = db_session.query(auth_models.User).filter_by(
            discord_id="setup_admin_2", campaign_id=camp.id
        ).first()
        assert user is not None
        assert user.role == "admin"

    def test_rejects_non_admin_discord_id(self, client):
        with patch("app.modules.campaigns.router.settings") as mock_settings:
            mock_settings.ADMIN_DISCORD_IDS = "real_admin_only"
            token = self._admin_token("some_random_user")
            r = client.post(
                "/api/campaigns/setup",
                json={"name": "Sneaky Campaign", "discord_guild_id": "guild_sneaky_1"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 403

    def test_rejects_duplicate_guild(self, client, db_session):
        from app.modules.campaigns import models as campaign_models

        camp = campaign_models.Campaign(name="Existing", discord_guild_id="guild_dup_1")
        db_session.add(camp)
        db_session.commit()

        with patch("app.modules.campaigns.router.settings") as mock_settings:
            mock_settings.ADMIN_DISCORD_IDS = "dup_admin_1"
            token = self._admin_token("dup_admin_1")
            r = client.post(
                "/api/campaigns/setup",
                json={"name": "Duplicate", "discord_guild_id": "guild_dup_1"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# /api/campaigns/available
# ---------------------------------------------------------------------------

class TestAvailableCampaigns:
    def test_returns_campaigns_matching_user_guilds(self, client, db_session):
        from app.modules.campaigns import models as campaign_models

        camp = campaign_models.Campaign(name="Available Camp", discord_guild_id="guild_avail_1")
        db_session.add(camp)
        db_session.commit()

        discord_guilds = [{"id": "guild_avail_1"}, {"id": "guild_avail_other"}]
        with _patch_campaigns_httpx({"users/@me/guilds": (200, discord_guilds)}):
            token = _global_token("avail_discord_1")
            r = client.post(
                "/api/campaigns/available",
                json={"discord_token": "fake_discord_token"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["discord_guild_id"] == "guild_avail_1"

    def test_excludes_already_joined_campaigns(self, client, db_session):
        from app.modules.campaigns import models as campaign_models
        from app.modules.auth import models as auth_models

        camp = campaign_models.Campaign(name="Already Joined", discord_guild_id="guild_avail_2")
        db_session.add(camp)
        db_session.flush()

        user = auth_models.User(
            username="AlreadyIn", discord_id="avail_discord_2", campaign_id=camp.id, role="player"
        )
        db_session.add(user)
        db_session.commit()

        discord_guilds = [{"id": "guild_avail_2"}]
        with _patch_campaigns_httpx({"users/@me/guilds": (200, discord_guilds)}):
            token = _global_token("avail_discord_2")
            r = client.post(
                "/api/campaigns/available",
                json={"discord_token": "fake_discord_token"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 200
        assert r.json() == []

    def test_discord_api_failure_returns_400(self, client):
        with _patch_campaigns_httpx({"users/@me/guilds": (401, {})}):
            token = _global_token("avail_discord_3")
            r = client.post(
                "/api/campaigns/available",
                json={"discord_token": "bad_token"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# /api/campaigns/join
# ---------------------------------------------------------------------------

class TestJoinCampaign:
    def test_player_can_join_with_player_role(self, client, db_session):
        from app.modules.campaigns import models as campaign_models

        camp = campaign_models.Campaign(
            name="Joinable Camp",
            discord_guild_id="guild_join_1",
            player_role_id="role_player_1",
            dm_role_id="role_dm_1",
        )
        db_session.add(camp)
        db_session.commit()

        member_data = {"roles": ["role_player_1"]}
        with _patch_campaigns_httpx({f"guilds/guild_join_1/members": (200, member_data)}):
            token = _global_token("join_discord_1", username="JoinUser")
            r = client.post(
                "/api/campaigns/join",
                json={"discord_guild_id": "guild_join_1", "discord_access_token": "fake"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_dm_joins_with_admin_role(self, client, db_session):
        from app.modules.campaigns import models as campaign_models
        from app.modules.auth import models as auth_models

        camp = campaign_models.Campaign(
            name="DM Camp",
            discord_guild_id="guild_join_2",
            player_role_id="role_player_2",
            dm_role_id="role_dm_2",
        )
        db_session.add(camp)
        db_session.commit()

        member_data = {"roles": ["role_dm_2"]}
        with _patch_campaigns_httpx({f"guilds/guild_join_2/members": (200, member_data)}):
            token = _global_token("join_discord_2", username="DMUser")
            r = client.post(
                "/api/campaigns/join",
                json={"discord_guild_id": "guild_join_2", "discord_access_token": "fake"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 200, r.text

        user = db_session.query(auth_models.User).filter_by(
            discord_id="join_discord_2"
        ).first()
        assert user is not None
        assert user.role == "admin"

    def test_join_creates_user_record(self, client, db_session):
        from app.modules.campaigns import models as campaign_models
        from app.modules.auth import models as auth_models

        camp = campaign_models.Campaign(
            name="Record Camp",
            discord_guild_id="guild_join_3",
            player_role_id="role_player_3",
        )
        db_session.add(camp)
        db_session.commit()

        member_data = {"roles": ["role_player_3"]}
        with _patch_campaigns_httpx({"guilds/guild_join_3/members": (200, member_data)}):
            token = _global_token("join_discord_3", username="NewPlayer")
            r = client.post(
                "/api/campaigns/join",
                json={"discord_guild_id": "guild_join_3", "discord_access_token": "fake"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 200, r.text

        user = db_session.query(auth_models.User).filter_by(discord_id="join_discord_3").first()
        assert user is not None
        assert user.campaign_id == camp.id

    def test_rejects_user_without_required_role(self, client, db_session):
        from app.modules.campaigns import models as campaign_models

        camp = campaign_models.Campaign(
            name="Strict Camp",
            discord_guild_id="guild_join_4",
            player_role_id="role_player_4",
            dm_role_id="role_dm_4",
        )
        db_session.add(camp)
        db_session.commit()

        member_data = {"roles": ["some_unrelated_role"]}
        with _patch_campaigns_httpx({"guilds/guild_join_4/members": (200, member_data)}):
            token = _global_token("join_discord_4", username="Unauthorized")
            r = client.post(
                "/api/campaigns/join",
                json={"discord_guild_id": "guild_join_4", "discord_access_token": "fake"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 403

    def test_rejects_user_not_in_discord_server(self, client, db_session):
        from app.modules.campaigns import models as campaign_models

        camp = campaign_models.Campaign(
            name="Members Only",
            discord_guild_id="guild_join_5",
            player_role_id="role_player_5",
        )
        db_session.add(camp)
        db_session.commit()

        with _patch_campaigns_httpx({"guilds/guild_join_5/members": (404, {})}):
            token = _global_token("join_discord_5", username="Ghost")
            r = client.post(
                "/api/campaigns/join",
                json={"discord_guild_id": "guild_join_5", "discord_access_token": "fake"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 403

    def test_returns_404_for_unknown_guild(self, client):
        token = _global_token("join_discord_6")
        r = client.post(
            "/api/campaigns/join",
            json={"discord_guild_id": "guild_nonexistent", "discord_access_token": "fake"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 404

    def test_discord_api_error_returns_400(self, client, db_session):
        from app.modules.campaigns import models as campaign_models

        camp = campaign_models.Campaign(
            name="Error Camp",
            discord_guild_id="guild_join_7",
            player_role_id="role_player_7",
        )
        db_session.add(camp)
        db_session.commit()

        # 500 from Discord (not 200 and not 404) should surface as 400
        with _patch_campaigns_httpx({"guilds/guild_join_7/members": (500, {})}):
            token = _global_token("join_discord_7", username="ErrorUser")
            r = client.post(
                "/api/campaigns/join",
                json={"discord_guild_id": "guild_join_7", "discord_access_token": "fake"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# /api/campaigns/discord/guilds
# ---------------------------------------------------------------------------

class TestDiscordGuilds:
    def _admin_token(self, discord_id: str) -> str:
        return _global_token(discord_id, username="AdminGuilds")

    def test_returns_manage_guild_filtered_guilds(self, client):
        guilds = [
            {"id": "g1", "name": "Has Manage", "permissions": str(0x20)},
            {"id": "g2", "name": "No Manage", "permissions": "0"},
        ]
        with patch("app.modules.campaigns.router.settings") as mock_settings:
            mock_settings.ADMIN_DISCORD_IDS = "guilds_admin_1"
            with _patch_campaigns_httpx({"users/@me/guilds": (200, guilds)}):
                token = self._admin_token("guilds_admin_1")
                r = client.post(
                    "/api/campaigns/discord/guilds",
                    json={"discord_token": "fake"},
                    headers={"Authorization": f"Bearer {token}"},
                )
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["id"] == "g1"

    def test_rejects_non_admin(self, client):
        with patch("app.modules.campaigns.router.settings") as mock_settings:
            mock_settings.ADMIN_DISCORD_IDS = "real_admin_only"
            token = self._admin_token("not_an_admin")
            r = client.post(
                "/api/campaigns/discord/guilds",
                json={"discord_token": "fake"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 403

    def test_discord_api_failure_returns_400(self, client):
        with patch("app.modules.campaigns.router.settings") as mock_settings:
            mock_settings.ADMIN_DISCORD_IDS = "guilds_admin_2"
            with _patch_campaigns_httpx({"users/@me/guilds": (401, {})}):
                token = self._admin_token("guilds_admin_2")
                r = client.post(
                    "/api/campaigns/discord/guilds",
                    json={"discord_token": "bad"},
                    headers={"Authorization": f"Bearer {token}"},
                )
        assert r.status_code == 400
