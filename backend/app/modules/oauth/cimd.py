"""Client ID Metadata Documents (CIMD).

An MCP client's client_id is an HTTPS URL that serves a JSON document describing
the client. We fetch it (with a total deadline, size cap, short cache), require the
document's client_id to equal the URL, and refuse URLs that resolve to private,
loopback or link-local addresses (SSRF). The connection goes to the address that
passed that check (no second DNS lookup); TLS and Host still use the hostname.
Redirects are not followed, and compressed bodies are refused.
"""
import asyncio
import datetime
import ipaddress
import json
import logging
import socket
from typing import Optional
from urllib.parse import urlparse

import httpx
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...config import get_settings
from . import models
from .tokens import utcnow

logger = logging.getLogger("app.oauth.cimd")

CACHE_SECONDS = 300
FETCH_TIMEOUT_SECONDS = 5.0
MAX_DOCUMENT_BYTES = 10 * 1024


class CimdError(Exception):
    """The client_id can't be used. The message is safe to show the user."""


def _allow_insecure() -> bool:
    settings = get_settings()
    return bool(settings.MCP_CIMD_ALLOW_INSECURE and settings.APP_ENV != "production")


def _address_is_public(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return ip.is_global and not ip.is_multicast


async def _check_host_is_public(host: str) -> str:
    """Resolves the host once. Returns an address to connect to; every address must be public."""
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise CimdError("The client's metadata URL does not resolve.")
    addresses = [info[4][0] for info in infos]
    if not addresses or not all(_address_is_public(a) for a in addresses):
        raise CimdError("The client's metadata URL points at a private address.")
    return addresses[0]


def _http_client(**kwargs) -> httpx.AsyncClient:
    """Seam for tests (they pass a MockTransport)."""
    return httpx.AsyncClient(**kwargs)


def _pinned_request(client_id: str, address: str) -> tuple[str, dict, dict]:
    """URL aimed at the checked address, plus the Host header and SNI for the real hostname."""
    parsed = urlparse(client_id)
    ip_host = f"[{address}]" if ":" in address else address
    netloc = f"{ip_host}:{parsed.port}" if parsed.port else ip_host
    host_header = f"{parsed.hostname}:{parsed.port}" if parsed.port else parsed.hostname
    return parsed._replace(netloc=netloc).geturl(), {"Host": host_header}, {"sni_hostname": parsed.hostname}


async def _download(client_id: str, address: Optional[str]) -> bytes:
    url, headers, extensions = client_id, {}, {}
    if address is not None:
        url, headers, extensions = _pinned_request(client_id, address)
    headers.update({"Accept": "application/json", "Accept-Encoding": "identity"})
    async with _http_client(timeout=FETCH_TIMEOUT_SECONDS, follow_redirects=False) as client:
        request = client.build_request("GET", url, headers=headers, extensions=extensions)
        response = await client.send(request, stream=True)
        try:
            if response.status_code != 200:
                raise CimdError(f"The client's metadata document returned HTTP {response.status_code}.")
            encoding = response.headers.get("content-encoding", "identity").strip().lower()
            if encoding not in ("", "identity"):
                raise CimdError("The client's metadata document must not be compressed.")
            body = bytearray()
            # aiter_raw: bytes as sent, so the cap counts what was read off the wire.
            async for chunk in response.aiter_raw():
                body += chunk
                if len(body) > MAX_DOCUMENT_BYTES:
                    raise CimdError("The client's metadata document is too large.")
            return bytes(body)
        finally:
            await response.aclose()


def validate_client_id_url(client_id: str) -> None:
    """Syntax check for a CIMD client_id (no network)."""
    parsed = urlparse(client_id)
    allowed_schemes = ("https", "http") if _allow_insecure() else ("https",)
    if parsed.scheme not in allowed_schemes or not parsed.hostname:
        raise CimdError("client_id must be an https:// URL (a client ID metadata document).")
    if parsed.username or parsed.password or parsed.fragment:
        raise CimdError("client_id must not contain credentials or a fragment.")
    if parsed.path in ("", "/"):
        raise CimdError("client_id must include a path.")


def is_allowed_redirect_uri(uri: str) -> bool:
    """HTTPS anywhere, or plain http only to localhost / 127.0.0.1 (native clients)."""
    try:
        parsed = urlparse(uri)
    except ValueError:
        return False
    if parsed.fragment or parsed.username or parsed.password or not parsed.hostname:
        return False
    if parsed.scheme == "https":
        return True
    return parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1", "[::1]", "::1")


async def fetch_document(client_id: str) -> dict:
    validate_client_id_url(client_id)
    address = None
    if not _allow_insecure():
        address = await _check_host_is_public(urlparse(client_id).hostname)

    try:
        # One deadline for the whole download, not per read: a slow drip can't hold the request.
        async with asyncio.timeout(FETCH_TIMEOUT_SECONDS):
            body = await _download(client_id, address)
    except TimeoutError:
        logger.warning("CIMD fetch timed out", extra={"client_id": client_id})
        raise CimdError("The client's metadata document could not be fetched.")
    except httpx.HTTPError as exc:
        logger.warning("CIMD fetch failed", extra={"client_id": client_id, "error": str(exc)})
        raise CimdError("The client's metadata document could not be fetched.")

    try:
        document = json.loads(body)
    except ValueError:
        raise CimdError("The client's metadata document is not JSON.")
    if not isinstance(document, dict):
        raise CimdError("The client's metadata document is not a JSON object.")
    if document.get("client_id") != client_id:
        raise CimdError("The client's metadata document has a different client_id than its URL.")
    redirect_uris = document.get("redirect_uris")
    if not isinstance(redirect_uris, list) or not redirect_uris or not all(isinstance(u, str) for u in redirect_uris):
        raise CimdError("The client's metadata document lists no redirect_uris.")
    auth_method = document.get("token_endpoint_auth_method", "none")
    if auth_method != "none":
        raise CimdError("Only public clients (token_endpoint_auth_method 'none') are supported.")
    return document


def get_cached(db: Session, client_id: str) -> Optional[models.OAuthClient]:
    return db.query(models.OAuthClient).filter(models.OAuthClient.client_id == client_id).first()


async def load_client(db: Session, client_id: str, *, max_age_seconds: int = CACHE_SECONDS) -> models.OAuthClient:
    """Returns the cached client, re-fetching the document when the cache is older than max_age."""
    if not client_id:
        raise CimdError("Missing client_id.")
    cached = get_cached(db, client_id)
    if cached and cached.fetched_at > utcnow() - datetime.timedelta(seconds=max_age_seconds):
        return cached

    # End the read transaction so no DB connection is held during the network fetch.
    db.commit()
    document = await fetch_document(client_id)
    name = document.get("client_name")
    if not isinstance(name, str) or not name.strip():
        name = urlparse(client_id).hostname
    fields = {
        "client_name": name.strip()[:200],
        "redirect_uris": list(document["redirect_uris"]),
        "fetched_at": utcnow(),
    }
    row = get_cached(db, client_id)
    if row is None:
        db.add(models.OAuthClient(client_id=client_id, **fields))
        try:
            db.commit()
        except IntegrityError:
            # A concurrent request inserted it first: update that row instead.
            db.rollback()
            row = get_cached(db, client_id)
            if row is None:
                raise
    if row is not None:
        for key, value in fields.items():
            setattr(row, key, value)
        db.commit()
    return get_cached(db, client_id)
