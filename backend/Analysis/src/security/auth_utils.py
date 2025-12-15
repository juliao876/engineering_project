import os

import requests
from fastapi import HTTPException, status

# Prefer service hostname in docker, but allow overriding for local runs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:6700")


def get_user_data(token: str):
    """Validate token with Auth service and return the decoded payload."""

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/api/v1/auth/me", headers=headers, timeout=5)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable",
        )

    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    return response.json() if response.headers.get("content-type", "").startswith("application/json") else {}