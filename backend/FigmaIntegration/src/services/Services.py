from pyexpat.errors import messages
from urllib import response

from fastapi import HTTPException, Response
from sqlalchemy.orm import Session
from src.database.models.FigmaFile import FigmaFile
import requests
from datetime import datetime, timedelta
from src.schemas.FigmaProjectSchema import FigmaProjectSchema
import re

PROJECTS_SERVICE_URL = ("PROJECTS_SERVICE_URL","http://localhost:6701/api/v1")

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
    def sync_figma_project(self, project_id: int):
        figma_file = self.db.get(FigmaFile, project_id)
        if not figma_file:
            raise HTTPException(status_code=404, detail="Figma file not found")
        url = f"https://api.figma.com/v1/files/{figma_file.file_key}"
        headers = {"Authorization": f"Bearer {figma_file.access_token}"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Failed to fetch Figma file data")
        data = response.json()
        new_name = data.get["name"]
        new_last_modified = data.get["last_modified"]
        new_thumbnail = data.get["thumbnail_url"]

        changes = {}
        if new_name != figma_file.name:
            changes["name"] = {"old": figma_file.name, "new": new_name}
        if new_thumbnail != figma_file.thumbnail_url:
            changes["thumbnail"] = {"old": figma_file.thumbnail_url, "new": new_thumbnail}
        if new_last_modified and new_last_modified != figma_file.last_modified.isoformat():
            changes["last_modified"] = {"old": figma_file.last_modified.isoformat(), "new": new_last_modified}

        figma_file.name = new_name
        figma_file.thumbnail_url = new_thumbnail
        figma_file.last_modified = datetime.fromisoformat(new_last_modified.replace("Z", "+00:00"))
        figma_file.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(figma_file)
        return {
            "message": "Project synced sucessfully",
            "project_id": figma_file.id,
            "file_key": figma_file.file_key,
            "changes": changes or "No changes",
            "last_sync": figma_file.updated_at.isoformat()
        }







