import os
import requests
from fastapi import HTTPException

AUTH_BASE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:6700")
AUTH_ME_PATH = os.getenv("AUTH_ME_PATH", "/api/v1/auth/me")


def _build_auth_me_url() -> str:
    """Return a usable /auth/me URL from configurable pieces.

    The ENV `AUTH_SERVICE_URL` can now be either the bare service host
    (e.g. ``http://auth-service:6700``) or the full ``/api/v1/auth/me``
    endpoint. We normalize it here so downstream callers always hit the
    correct path.
    """

    base = AUTH_BASE_URL.rstrip("/")

    # If the configured base already targets the desired endpoint, keep it.
    if base.endswith("/api/v1/auth/me"):
        return base

    path = AUTH_ME_PATH or "/api/v1/auth/me"
    if not path.startswith("/"):
        path = f"/{path}"

    return f"{base}{path}"


def get_user_data(token: str):
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(_build_auth_me_url(), headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        return response.json()
    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="Auth service returned an unexpected response format",
        )