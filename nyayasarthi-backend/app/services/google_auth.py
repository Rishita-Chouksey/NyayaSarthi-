"""
Verifies the Google ID token sent by the frontend's "Sign in with Google"
button (Google Identity Services). We use Google's own client library so
signature, expiry, issuer, and audience checks are all handled correctly —
never decode this token manually.
"""
import os

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


def verify_google_token(credential: str) -> dict:
    """Returns the decoded payload (sub, email, name, email_verified, ...).

    Raises ValueError with a human-readable message on any failure — callers
    should turn that into an HTTP 401/500 as appropriate.
    """
    if not GOOGLE_CLIENT_ID:
        raise ValueError("Google sign-in is not configured on this server (missing GOOGLE_CLIENT_ID).")

    try:
        payload = id_token.verify_oauth2_token(
            credential, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError as e:
        raise ValueError(f"Invalid Google credential: {e}")

    if not payload.get("email_verified", False):
        raise ValueError("Your Google account's email is not verified.")

    return payload
