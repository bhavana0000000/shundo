"""Google OAuth2 web flow for Shundo."""
import json
import os
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from app.config import GOOGLE_CLIENT_SECRETS_FILE, GOOGLE_REDIRECT_URI, GOOGLE_SCOPES, TOKEN_STORE_FILE


def get_auth_flow() -> Flow:
    return Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE, scopes=GOOGLE_SCOPES, redirect_uri=GOOGLE_REDIRECT_URI,
    )


def get_authorization_url() -> str:
    flow = get_auth_flow()
    auth_url, _ = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent")
    return auth_url


def exchange_code_for_token(code: str) -> dict:
    flow = get_auth_flow()
    flow.fetch_token(code=code)
    creds = flow.credentials
    token_data = {
        "token": creds.token, "refresh_token": creds.refresh_token, "token_uri": creds.token_uri,
        "client_id": creds.client_id, "client_secret": creds.client_secret, "scopes": creds.scopes,
    }
    with open(TOKEN_STORE_FILE, "w") as f:
        json.dump(token_data, f)
    return token_data


def load_credentials() -> Credentials | None:
    if not os.path.exists(TOKEN_STORE_FILE):
        return None
    with open(TOKEN_STORE_FILE, "r") as f:
        token_data = json.load(f)
    creds = Credentials(
        token=token_data["token"], refresh_token=token_data["refresh_token"], token_uri=token_data["token_uri"],
        client_id=token_data["client_id"], client_secret=token_data["client_secret"], scopes=token_data["scopes"],
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data["token"] = creds.token
        with open(TOKEN_STORE_FILE, "w") as f:
            json.dump(token_data, f)
    return creds


def is_authenticated() -> bool:
    return load_credentials() is not None
