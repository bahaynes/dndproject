"""Server-rendered pages for the MCP authorization flow.

These live in the backend, not SvelteKit, so the frontend auth contract is untouched.
Decisions are same-origin POST forms carrying the pending ID and its CSRF value. The site
CSP has ``form-action 'self'``, which in Chrome also blocks a form's redirect to Discord or
to the client, so the POST answers with a continuation page (same origin) that navigates
there itself. That navigation is a plain GET and never resubmits the decision.
"""
from html import escape
from typing import Iterable
from urllib.parse import urlparse

from starlette.responses import HTMLResponse

from .tokens import SCOPE_DESCRIPTIONS

_STYLE = """
:root { color-scheme: light dark; --bg:#f6f3ee; --fg:#1d1a16; --muted:#6b645a; --card:#fff; --line:#ddd5c8;
        --accent:#7a3b12; --accent-fg:#fff; --warn:#8a5a00; --warn-bg:#fff4d6; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#16130f; --fg:#eee7dc; --muted:#a69d90; --card:#211d18; --line:#3a332b;
          --accent:#d98b4a; --accent-fg:#16130f; --warn:#f0c060; --warn-bg:#3a2d10; } }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:16px/1.5 system-ui, sans-serif; }
main { max-width: 34rem; margin: 3rem auto; padding: 0 16px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:1.5rem; }
h1 { font-size:1.35rem; margin:0 0 .75rem; }
p { margin:.5rem 0; }
.muted { color:var(--muted); font-size:.9rem; }
ul { padding-left:1.2rem; }
code { overflow-wrap:anywhere; }
.warn { background:var(--warn-bg); color:var(--warn); border-radius:6px; padding:.6rem .8rem; margin:1rem 0; }
.actions { display:flex; flex-wrap:wrap; gap:.75rem; margin-top:1.25rem; }
form { margin:0; }
.btn { display:inline-block; font:inherit; cursor:pointer; background:none; padding:.6rem 1rem; border-radius:6px; text-decoration:none; border:1px solid var(--line);
        color:var(--fg); }
.btn.primary { background:var(--accent); color:var(--accent-fg); border-color:var(--accent); }
.campaigns .btn { display:block; width:100%; text-align:left; margin:.5rem 0; }
"""

_HEADERS = {
    "Cache-Control": "no-store",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'",
    "Referrer-Policy": "no-referrer",
}


def _page(title: str, body: str, status_code: int = 200) -> HTMLResponse:
    html = (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{escape(title)}</title><style>{_STYLE}</style></head>"
        f"<body><main><div class=\"card\">{body}</div></main></body></html>"
    )
    return HTMLResponse(html, status_code=status_code, headers=_HEADERS)


def _scope_list(scopes: Iterable[str]) -> str:
    items = "".join(f"<li>{escape(SCOPE_DESCRIPTIONS.get(s, s))}</li>" for s in scopes)
    return f"<ul>{items}</ul>"


def _redirect_notice(redirect_uri: str) -> str:
    host = urlparse(redirect_uri).hostname or redirect_uri
    html = f"<p class=\"muted\">After you approve, you will be sent to <strong>{escape(host)}</strong>.</p>"
    if host in ("localhost", "127.0.0.1", "::1", "[::1]"):
        html += (
            "<div class=\"warn\">This app runs on your own computer (it redirects to localhost). "
            "Only continue if you started this connection yourself, for example from Claude Code.</div>"
        )
    return html


def _form(action: str, fields: dict, label: str, primary: bool = False) -> str:
    inputs = "".join(
        f"<input type=\"hidden\" name=\"{escape(k)}\" value=\"{escape(str(v))}\">" for k, v in fields.items()
    )
    css = "btn primary" if primary else "btn"
    return f"<form method=\"post\" action=\"{escape(action)}\">{inputs}<button class=\"{css}\" type=\"submit\">{escape(label)}</button></form>"


def continue_page(location: str) -> HTMLResponse:
    """Navigates to ``location`` (Discord or the client) after a POST, without resubmitting it."""
    return _page(
        "Continuing",
        f"<meta http-equiv=\"refresh\" content=\"0;url={escape(location)}\">"
        "<h1>Continuing…</h1>"
        f"<p><a class=\"btn primary\" href=\"{escape(location)}\">Continue</a></p>",
    )


def error_page(message: str, status_code: int = 400) -> HTMLResponse:
    return _page(
        "Can't connect",
        f"<h1>Can't connect this app</h1><p>{escape(message)}</p>"
        "<p class=\"muted\">Close this tab and try connecting again from the app.</p>",
        status_code,
    )


def client_consent_page(*, pending_id: str, csrf: str, client_name: str, client_id: str,
                        redirect_uri: str, scopes: list[str]) -> HTMLResponse:
    fields = {"pending": pending_id, "csrf": csrf}
    body = (
        f"<h1>Connect {escape(client_name)} to West Marches?</h1>"
        f"<p class=\"muted\">App ID: <code>{escape(client_id)}</code></p>"
        "<p>It is asking to:</p>"
        f"{_scope_list(scopes)}"
        f"{_redirect_notice(redirect_uri)}"
        "<p class=\"muted\">Next you sign in with Discord and pick the campaign. Only campaigns where you are a GM "
        "can be connected.</p>"
        "<div class=\"actions\">"
        + _form("/api/oauth/consent", {**fields, "decision": "approve"}, "Continue with Discord", primary=True)
        + _form("/api/oauth/consent", {**fields, "decision": "deny"}, "Cancel")
        + "</div>"
    )
    return _page("Connect an app", body)


def campaign_picker_page(*, pending_id: str, csrf: str, client_name: str, redirect_uri: str,
                         username: str, scopes: list[str], campaigns: list) -> HTMLResponse:
    fields = {"pending": pending_id, "csrf": csrf}
    buttons = "".join(
        _form("/api/oauth/approve", {**fields, "campaign_id": c.id}, f"Connect {c.name}", primary=True)
        for c in campaigns
    )
    body = (
        f"<h1>Which campaign should {escape(client_name)} use?</h1>"
        f"<p class=\"muted\">Signed in as {escape(username)}.</p>"
        f"<p>{escape(client_name)} will be able to:</p>"
        f"{_scope_list(scopes)}"
        f"{_redirect_notice(redirect_uri)}"
        f"<div class=\"campaigns\">{buttons}</div>"
        "<div class=\"actions\">"
        + _form("/api/oauth/approve", {**fields, "decision": "deny"}, "Cancel")
        + "</div>"
    )
    return _page("Pick a campaign", body)
