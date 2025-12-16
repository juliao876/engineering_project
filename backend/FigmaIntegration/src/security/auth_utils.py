import os
import json
from urllib.request import Request, urlopen
from urllib.error import URLError
from fastapi import HTTPException, status

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:6700")

def get_user_data(token: str) -> dict:
    """Pobiera dane użytkownika z Auth Service na podstawie tokena."""
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")

    request = Request(
        url=f"{AUTH_SERVICE_URL}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    try:
        with urlopen(request) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status, detail="Failed to fetch user data")
            data = json.loads(response.read().decode())
            return data
    except URLError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")