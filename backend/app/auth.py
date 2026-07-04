"""
Google OAuth2 web flow for Shundo - now per-session, not one shared token.
Each browser session (identified by the shundo_session cookie) gets its own
real Google token stored in the database, keyed by session_id. This means
when a friend logs in with their own Gmail, THEIR real calendar gets used
for real actions - safely isolated from your account and everyone else's.

The OAuth "state" parameter carries the session_id through Google's
redirect round-trip (cookies aren't always reliable to read back after a
cross-site redirect, but state always survives).
"""
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from app.config import GOOGLE_CLIENT_SECRETS_FILE, GOOGLE_REDIRECT_URI, GOOGLE_SCOPES
from app.db import get_connection


def get_auth_flow() -> Flow:
    return Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE, scopes=GOOGLE_SCOPES, redirect_uri=GOOGLE_REDIRECT_URI,
    )


def get_authorization_url(session_id: str) -> str:
    """session_id is passed as the OAuth 'state' param so the callback
    knows which session to save the resulting token under."""
    flow = get_auth_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent", state=session_id,
    )
    return auth_url


def exchange_code_for_token(code: str, session_id: str) -> dict:
    flow = get_auth_flow()
    flow.fetch_token(code=code)
    creds = flow.credentials
    token_data = {
        "token": creds.token, "refresh_token": creds.refresh_token, "token_uri": creds.token_uri,
        "client_id": creds.client_id, "client_secret": creds.client_secret, "scopes": creds.scopes,
    }

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO oauth_tokens (session_id, token_data) VALUES (?, ?) "
        "ON CONFLICT(session_id) DO UPDATE SET token_data = excluded.token_data",
        (session_id, json.dumps(token_data)),
    )
    conn.commit()
    conn.close()
    return token_data


def load_credentials(session_id: str = "default") -> Credentials | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT token_data FROM oauth_tokens WHERE session_id = ?", (session_id,))
    row = cur.fetchone()

    if row is None:
        conn.close()
        return None

    token_data = json.loads(row["token_data"])
    creds = Credentials(
        token=token_data["token"], refresh_token=token_data["refresh_token"], token_uri=token_data["token_uri"],
        client_id=token_data["client_id"], client_secret=token_data["client_secret"], scopes=token_data["scopes"],
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data["token"] = creds.token
        cur.execute("UPDATE oauth_tokens SET token_data = ? WHERE session_id = ?", (json.dumps(token_data), session_id))
        conn.commit()

    conn.close()
    return creds


def is_authenticated(session_id: str = "default") -> bool:
    return load_credentials(session_id) is not None
