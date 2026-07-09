"""
One-time Canva Connect authorization (authorization-code flow with PKCE).

Run this ONCE, locally, in your own terminal — ideally with no active Claude
session watching this repo, so the refresh token never lands in a transcript.

  python scripts/canva_auth.py

It will:
  1. Open Canva's consent page in your browser
  2. Catch the redirect on a local callback server
  3. Exchange the authorization code for access + refresh tokens
  4. Save the refresh token to secrets/canva_refresh_token (chmod 600)

Prerequisites:
  - CANVA_CLIENT_ID and CANVA_CLIENT_SECRET set (in .env)
  - The redirect URI below is registered in the Canva Developer Portal, exactly:
        http://127.0.0.1:8000/oauth/callback
    (matches settings.canva_redirect_uri)
  - Your Canva account is added as a test user on the integration
"""

import base64
import hashlib
import secrets
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import httpx

# Make the app package importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.integrations import canva_client  # noqa: E402

_AUTHORIZE_URL = "https://www.canva.com/api/oauth/authorize"

_captured: dict = {}


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        callback_path = urllib.parse.urlparse(settings.canva_redirect_uri).path

        # Ignore stray requests (e.g. /favicon.ico) so we keep waiting for the
        # real callback rather than treating the first noise request as the result.
        if parsed.path != callback_path:
            self.send_response(204)
            self.end_headers()
            return

        params = urllib.parse.parse_qs(parsed.query)
        code = params.get("code", [None])[0]
        error = params.get("error", [None])[0]

        # A bare hit on the callback path with neither code nor error is noise —
        # typically a stale browser tab reloading. Ignore it and keep waiting.
        if not code and not error:
            self.send_response(204)
            self.end_headers()
            return

        _captured["code"] = code
        _captured["state"] = params.get("state", [None])[0]
        _captured["error"] = error
        _captured["error_description"] = params.get("error_description", [None])[0]
        _captured["raw_query"] = parsed.query
        _captured["done"] = True

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        if _captured["code"]:
            body = (
                b"<h2>Authorization received.</h2>"
                b"<p>You can close this tab and return to the terminal.</p>"
            )
        else:
            body = (
                b"<h2>Authorization failed.</h2>"
                b"<p>Check the terminal for details.</p>"
            )
        self.wfile.write(
            b"<html><body style='font-family:sans-serif;text-align:center;padding:48px'>"
            + body
            + b"</body></html>"
        )

    def log_message(self, *args):  # silence default logging
        pass


def _pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode()
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    return verifier, challenge


def main() -> None:
    if not settings.canva_client_id or not settings.canva_client_secret:
        sys.exit("CANVA_CLIENT_ID / CANVA_CLIENT_SECRET are not set. Fill them in .env first.")

    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(16)

    query = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": settings.canva_client_id,
            "redirect_uri": settings.canva_redirect_uri,
            "scope": settings.canva_scopes,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
        }
    )
    authorize_url = f"{_AUTHORIZE_URL}?{query}"

    redirect = urllib.parse.urlparse(settings.canva_redirect_uri)
    host, port = redirect.hostname, redirect.port or 80

    print(f"Opening browser for Canva consent…\nIf it doesn't open, visit:\n{authorize_url}\n")
    webbrowser.open(authorize_url)

    server = HTTPServer((host, port), _CallbackHandler)
    print(f"Waiting for redirect on {settings.canva_redirect_uri} …")
    # Keep serving until the real callback lands (skips favicon/other noise).
    while not _captured.get("done"):
        server.handle_request()

    code = _captured.get("code")
    if not code:
        err = _captured.get("error")
        desc = _captured.get("error_description")
        if err:
            sys.exit(
                f"\n✗ Canva returned an error instead of a code:\n"
                f"  error: {err}\n"
                f"  description: {desc}\n"
                f"  raw query: {_captured.get('raw_query')}\n"
            )
        sys.exit(
            f"\n✗ No authorization code and no error in the callback.\n"
            f"  raw query: {_captured.get('raw_query')!r}\n"
            f"  Check that the redirect URI registered in Canva exactly matches:\n"
            f"  {settings.canva_redirect_uri}\n"
        )
    if _captured.get("state") != state:
        sys.exit("State mismatch — possible CSRF. Aborting.")

    print("Exchanging authorization code for tokens…")
    resp = httpx.post(
        canva_client._TOKEN_URL,
        headers={
            "Authorization": canva_client._basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": verifier,
            "redirect_uri": settings.canva_redirect_uri,
        },
    )
    if resp.status_code != 200:
        sys.exit(f"Token exchange failed ({resp.status_code}): {resp.text}")

    data = resp.json()
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        sys.exit(f"No refresh_token in response: {data}")

    canva_client._write_refresh_token(refresh_token)
    print(
        f"\n✓ Success. Refresh token saved to {settings.canva_refresh_token_path}\n"
        f"  Access token valid for ~{data.get('expires_in', 14400)}s.\n"
        f"  You can now run: python scripts/canva_smoke_test.py"
    )


if __name__ == "__main__":
    main()
