from fastapi import HTTPException, Response
from sqlalchemy.orm import Session
from src.database.models.FigmaFile import FigmaFile
import requests
from datetime import datetime, timedelta

class Services:
    def __init__(self, db: Session):
        self.db = db

    def connect_account(self, code: str, client_id: str, client_secret: str, redirect_uri: str, user_id: str):
        url ="https://www.figma.com/api/oauth/token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
            "grant_type": "authorization_code",
        }

        response = requests.post(url, json=payload)
        data = response.json()
        token = FigmaFile(
            user_id=user_id,
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=datetime.utcnow() + timedelta(seconds=data["expires_in"])
        )
        self.db.add(token)
        self.db.commit()
        return token