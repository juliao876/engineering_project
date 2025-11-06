import json
from urllib.request import Request, urlopen
from urllib.error import URLError
from fastapi import HTTPException, status

AUTH_SERVICE_URL = "http://127.0.0.1:6700"  # ← zmień na swój Auth Service

def get_user_data(token: str) -> dict:
    """Pobiera dane użytkownika z Auth Service."""
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")

    request = Request(
        f"{AUTH_SERVICE_URL}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    try:
        with urlopen(request) as response:
            if response.status != status.HTTP_200_OK:
                raise HTTPException(
                    status_code=response.status,
                    detail="Failed to fetch user data"
                )
            data = json.loads(response.read().decode())
            print(data)
            return data
    except URLError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )
def get_user_data_username(username: str) -> dict:
    try:
        request = Request(f"{AUTH_SERVICE_URL}/api/v1/auth/user/{username}")
        with urlopen(request) as response:
            if response.status != status.HTTP_200_OK:
                return None
            data = json.loads(response.read().decode())
            return data
    except URLError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )