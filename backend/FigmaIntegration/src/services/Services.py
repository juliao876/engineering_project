from fastapi import HTTPException, Response
from sqlalchemy.orm import Session
from src.database.models.FigmaFile import FigmaFile
import requests
from datetime import datetime, timedelta
from src.schemas.FigmaProjectSchema import FigmaProjectSchema
import re

PROJECTS_SERVICE_URL = "http://127.0.0.1:6701/api/v1"

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

    def get_projects(self, file_url: str, access_token: str, user_id: int):
        match = re.search(r"/file/([A-Za-z0-9]+)", file_url)
        if not match:
            raise HTTPException(status_code=404, detail="Invalid Figma URL")
        file_key = match.group(1)
        headers={"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"https://api.figma.com/v1/files/{file_key}", headers=headers)
        data = response.json()
        return FigmaProjectSchema(
            file_key=file_key,
            name=data["name"],
            thumbnail_url=data.get("thumbnailUrl"),
            last_modified=data.get("lastModified")
        )
    def notify_projects_service(self, figma_url: str, user_id: int, token: str):
        payload = {
            "content_type": "figma",
            "figma_link": figma_url,
            "user_id": user_id,
        }
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.put(
                f"{PROJECTS_SERVICE_URL}/project/{user_id}/connect-figma",
                json=payload,
                headers=headers,
                timeout=5
            )
            if response.status_code != 200:
                print(f"[!] Failed to update project in Projects: {response.text}")
        except Exception as e:
            print(f"[!] Error contacting Projects service: {e}")

    def fetch_figma_data(self, project_id:int):
        file = self.db.get(FigmaFile, project_id)
        if not file:
            raise HTTPException(status_code=404, detail="Figma file not found")

        data = response.json()

        name = data["name"]
        last_modified = data.get("lastModified")
        thumbnail_url = data.get("thumbnailUrl")
        document=data.get("document", {})
        total_layers = 0
        total_texts = 0
        total_buttons = 0

        def traverse(node):
            nonlocal total_layers, total_texts, total_buttons
            total_layers += 1
            if node.get("type") == "TEXT":
                total_texts += 1
            if "button" in node.get("name", "").lower():
                total_buttons += 1
            for child in node.get("children", []):
                traverse(child)

        traverse(document)
        file.name = name
        file.thumbnail_url = thumbnail_url
        file.last_modified = datetime.fromtimestamp(last_modified)
        file.updated_at = datetime.utcnow()
        self.db.commit()

        return{
            "project_id": file.id,
            "file_key": file.file_key,
            "name": name,
            "last_modified": file.last_modified,
            "thumbnail_url": file.thumbnail_url,
            "total_layers": total_layers,
            "total_texts": total_texts,
            "total_buttons": total_buttons,
        }




