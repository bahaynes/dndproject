"""Tables for the MCP OAuth 2.1 authorization server.

Kept apart from the frontend login: nothing here is read by
get_current_active_user, and the frontend JWT never touches these rows.
Datetimes are naive UTC, like the rest of the app.
"""
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from ...database import Base


class OAuthClient(Base):
    """Cache of fetched Client ID Metadata Documents (CIMD). client_id is the document URL."""

    __tablename__ = "oauth_clients"

    client_id = Column(String, primary_key=True)
    client_name = Column(String, nullable=True)
    redirect_uris = Column(JSON, nullable=False, default=list)
    fetched_at = Column(DateTime, nullable=False)


class OAuthPendingAuthorization(Base):
    """One /authorize request in flight: validated parameters, then Discord identity, then consent."""

    __tablename__ = "oauth_pending_authorizations"

    id = Column(String, primary_key=True)
    client_id = Column(String, nullable=False)
    redirect_uri = Column(String, nullable=False)
    state = Column(String, nullable=True)
    code_challenge = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    scopes = Column(String, nullable=False)
    # Random value the consent forms post back, so a third-party page can't submit them.
    csrf = Column(String, nullable=False)
    client_consented = Column(Boolean, nullable=False, default=False)
    discord_id = Column(String, nullable=True)
    discord_username = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class OAuthGrant(Base):
    """One connection of one MCP client to one campaign for one user. Revoking it kills its tokens."""

    __tablename__ = "oauth_grants"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    client_id = Column(String, nullable=False)
    scopes = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)


class OAuthCode(Base):
    """Single-use authorization code. Stored hashed; a second use revokes the grant it produced."""

    __tablename__ = "oauth_codes"

    code_hash = Column(String, primary_key=True)
    client_id = Column(String, nullable=False)
    redirect_uri = Column(String, nullable=False)
    code_challenge = Column(String, nullable=False)
    code_challenge_method = Column(String, nullable=False, default="S256")
    resource = Column(String, nullable=False)
    scopes = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    grant_id = Column(Integer, ForeignKey("oauth_grants.id"), nullable=True)


class OAuthRefreshToken(Base):
    """Opaque refresh token, stored hashed and rotated on every use."""

    __tablename__ = "oauth_refresh_tokens"

    token_hash = Column(String, primary_key=True)
    grant_id = Column(Integer, ForeignKey("oauth_grants.id"), nullable=False, index=True)
    issued_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    replaced_by = Column(String, nullable=True)


class OAuthConsent(Base):
    """A user's remembered approval of a client for a campaign and scopes."""

    __tablename__ = "oauth_consents"
    __table_args__ = (UniqueConstraint("discord_id", "client_id", "campaign_id", name="uq_oauth_consent"),)

    id = Column(Integer, primary_key=True, index=True)
    discord_id = Column(String, nullable=False, index=True)
    client_id = Column(String, nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    scopes = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
