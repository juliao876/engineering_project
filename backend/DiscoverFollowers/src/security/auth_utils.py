import json
import os
from urllib.error import URLError

import requests
from fastapi import HTTPException, status


AUTH_BASE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:6700")
AUTH_ME_URL = f"{AUTH_BASE_URL}/api/v1/auth/me"
AUTH_USER_URL = f"{AUTH_BASE_URL}/api/v1/auth/user"


def get_user_data(token: str):
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(AUTH_ME_URL, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return response.json()


def get_user_data_username(username: str) -> dict:
    try:
        response = requests.get(f"{AUTH_USER_URL}/{username}")
        if response.status_code != status.HTTP_200_OK:
            return None
        return response.json()
    except (requests.RequestException, URLError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable",
        )
