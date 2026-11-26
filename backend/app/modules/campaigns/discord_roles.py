"""Discord guild-role check shared by campaign join and MCP consent.

Maps a Discord member's guild roles onto an app role for one campaign:
``dm_role_id`` (or, when that is unset, a role named in ADMIN_DISCORD_ROLE_NAMES)
gives ``"admin"``; ``player_role_id`` gives ``"player"``; anything else gives None.
"""
from typing import List, Optional, Set

import httpx


class GuildMemberNotFound(Exception):
    """The user is not a member of the campaign's Discord server."""


class GuildLookupFailed(Exception):
    """Discord did not answer the membership lookup."""


def parse_admin_role_names(raw) -> Set[str]:
    """Turns the comma-separated ADMIN_DISCORD_ROLE_NAMES setting into a lowercase set."""
    if not isinstance(raw, str):
        return set()
    return {name.strip().lower() for name in raw.split(",") if name.strip()}


async def roles_contain_admin_name(
    client: httpx.AsyncClient,
    guild_id: str,
    member_role_ids: List[str],
    bot_token: str,
    admin_role_names: Set[str],
) -> bool:
    """True if any of the member's roles has one of the configured admin role names."""
    if not member_role_ids or not bot_token or not admin_role_names:
        return False
    roles_res = await client.get(
        f"https://discord.com/api/guilds/{guild_id}/roles",
        headers={"Authorization": f"Bot {bot_token}"},
    )
    if roles_res.status_code != 200:
        return False
    member_role_set = set(member_role_ids)
    for role in roles_res.json():
        if role.get("id") in member_role_set and role.get("name", "").strip().lower() in admin_role_names:
            return True
    return False


async def resolve_campaign_role(
    client: httpx.AsyncClient,
    campaign,
    discord_id: str,
    bot_token,
    admin_role_names: Set[str],
) -> Optional[str]:
    """Returns ``"admin"``, ``"player"`` or None for this user in this campaign.

    Raises GuildMemberNotFound when Discord says the user isn't in the server, and
    GuildLookupFailed for any other non-200 answer. The caller owns ``client``.
    """
    member_response = await client.get(
        f"https://discord.com/api/guilds/{campaign.discord_guild_id}/members/{discord_id}",
        headers={"Authorization": f"Bot {bot_token}"},
    )
    if member_response.status_code == 404:
        raise GuildMemberNotFound()
    if member_response.status_code != 200:
        raise GuildLookupFailed()

    roles = member_response.json().get("roles", [])

    if campaign.dm_role_id and campaign.dm_role_id in roles:
        return "admin"
    if not campaign.dm_role_id and isinstance(bot_token, str) and bot_token.strip():
        if await roles_contain_admin_name(
            client, campaign.discord_guild_id, roles, bot_token, admin_role_names
        ):
            return "admin"
    if campaign.player_role_id and campaign.player_role_id in roles:
        return "player"
    return None
