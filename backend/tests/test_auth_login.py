from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_redirect():
    """
    Verifies that the Discord login endpoint exists and returns a redirect.
    """
    response = client.get("/api/auth/discord/login", follow_redirects=False)

    # Check for redirect status code (307 is default for RedirectResponse)
    assert response.status_code == 307

    # Check that it redirects to Discord
    assert "location" in response.headers
    assert response.headers["location"].startswith("https://discord.com/api/oauth2/authorize")
