import requests
import json
from urllib.request import Request, urlopen
from urllib.error import URLError
from fastapi import HTTPException, status

AUTH_SERVICE_URL = "http://127.0.0.1:6701/api/v1/auth/me"

def get_user_data(token: str):
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(AUTH_SERVICE_URL, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return response.json()
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