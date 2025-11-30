import requests
from fastapi import HTTPException

AUTH_SERVICE_URL = "http://127.0.0.1:6701/api/v1/auth/me"

def get_user_data(token: str):
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(AUTH_SERVICE_URL, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return response.json()
