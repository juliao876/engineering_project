from datetime import datetime
from typing import Optional
import logging
import os

import requests
from urllib.parse import urlencode, urlparse, parse_qs
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.database.models.FigmaAccount import FigmaAccount
from src.database.models.FigmaFile import FigmaFile

PROJECTS_SERVICE_URL = os.getenv("PROJECTS_SERVICE_URL", "http://project-service:6701/api/v1")
DEFAULT_FIGMA_REDIRECT = "http://localhost:3000/figma/callback"
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class Services:
    def __init__(self, db: Session):
        self.db = db

    # OAuth
    def build_authorize_url(
        self,
        *,
        state: Optional[str] = None,
        client_id: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ) -> str:
        resolved_client_id = client_id or os.getenv("FIGMA_CLIENT_ID")
        resolved_redirect = redirect_uri or os.getenv("FIGMA_REDIRECT_URI") or DEFAULT_FIGMA_REDIRECT
        if not resolved_client_id:
            raise HTTPException(status_code=500, detail="Figma OAuth is not configured")
        if os.getenv("FIGMA_REDIRECT_URI") is None and redirect_uri is None:
            logger.warning(
                "FIGMA_REDIRECT_URI is not set; using default frontend callback %s", resolved_redirect
            )

        params = {
            "client_id": resolved_client_id,
            "redirect_uri": resolved_redirect,
            "scope": "current_user:read file_content:read file_metadata:read",
            "state": state or "",
            "response_type": "code",
        }
        return f"https://www.figma.com/oauth?{urlencode(params)}"

    def connect_account(self, code: str, client_id: str, client_secret: str, redirect_uri: str, user_id: int) -> FigmaAccount:
        if not all([code, client_id, client_secret, redirect_uri]):
            raise HTTPException(status_code=400, detail="Missing Figma OAuth configuration")

        url = "https://api.figma.com/v1/oauth/token"
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
            "grant_type": "authorization_code",
        }

        response = requests.post(url, data=data, timeout=10)
        if response.status_code != 200:
            logger.error(
                "Figma token exchange failed (status=%s): %s", response.status_code, response.text
            )
            raise HTTPException(status_code=400, detail="Invalid code or Figma rejected the token")

        tokens = response.json()
        account = self.db.query(FigmaAccount).filter(FigmaAccount.user_id == user_id).first()
        if account:
            account.access_token = tokens["access_token"]
            account.refresh_token = tokens.get("refresh_token")
            account.expires_in = tokens.get("expires_in")
            account.updated_at = datetime.utcnow()
        else:
            account = FigmaAccount(
                user_id=user_id,
                access_token=tokens["access_token"],
                refresh_token=tokens.get("refresh_token"),
                expires_in=tokens.get("expires_in"),
            )
            self.db.add(account)

        self.db.commit()
        self.db.refresh(account)
        return account

    # Projects
    def extract_file_key(self, url: str) -> str:
        """Extract the Figma file key from multiple share URL formats."""
        if not url:
            raise HTTPException(status_code=404, detail="Invalid Figma URL")

        parsed = urlparse(url.strip())
        path_parts = [part for part in parsed.path.split("/") if part]

        if not path_parts:
            raise HTTPException(status_code=404, detail="Invalid Figma URL")

        for marker in ("file", "design", "proto"):
            if marker in path_parts:
                marker_index = path_parts.index(marker)
                if len(path_parts) > marker_index + 1:
                    return path_parts[marker_index + 1]

        # fallback: some links may be shared without the marker, so allow the first
        # path part when it resembles the usual file key structure
        first_part = path_parts[0]
        if len(first_part) >= 10:  # typical Figma keys are 10+ chars
            return first_part

        raise HTTPException(status_code=404, detail="Invalid Figma URL")

    def _get_account_token(self, user_id: int) -> str:
        account = self.db.query(FigmaAccount).filter(FigmaAccount.user_id == user_id).first()
        if not account:
            raise HTTPException(status_code=401, detail="You must connect Figma first")
        return account.access_token

    def get_projects(self, file_url: str, access_token: Optional[str], user_id: int):
        token = access_token or self._get_account_token(user_id)
        file_key = self.extract_file_key(file_url)

        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(
            f"https://api.figma.com/v1/files/{file_key}", headers=headers, timeout=10
        )
        if res.status_code != 200:
            try:
                error_detail = res.json().get("err")
            except Exception:
                error_detail = None

            detail = "Cannot fetch file from Figma"
            if error_detail:
                detail = f"{detail}: {error_detail}"
            logger.error(
                "Failed to fetch Figma file %s for user %s (status=%s): %s",
                file_key,
                user_id,
                res.status_code,
                res.text,
            )
            raise HTTPException(status_code=400, detail=detail)

        data = res.json()
        document = data.get("document") or {}
        children = document.get("children") or []
        logger.info(
            "Fetched Figma file %s (name=%s, nodes=%s) for user %s",
            file_key,
            data.get("name"),
            len(children),
            user_id,
        )

        parsed_url = urlparse(file_url)
        query_params = parse_qs(parsed_url.query)
        node_candidates = query_params.get("node-id") or query_params.get("node_id")
        node_id = node_candidates[0] if node_candidates else None

        if not node_id and children and isinstance(children, list):
            node_id = (children[0] or {}).get("id")

        preview_url = None
        if node_id:
            preview_url = self.get_preview_image(file_key, node_id, token)
        else:
            logger.warning("Could not determine Figma node id for preview for file %s", file_key)

        last_modified_raw = data.get("lastModified")
        last_modified = None
        if isinstance(last_modified_raw, str):
            try:
                last_modified = datetime.fromisoformat(last_modified_raw.replace("Z", "+00:00"))
            except ValueError:
                last_modified = None

        figma_file = (
            self.db.query(FigmaFile)
            .filter(FigmaFile.user_id == user_id, FigmaFile.file_key == file_key)
            .first()
        )
        if not figma_file:
            figma_file = FigmaFile(user_id=user_id, file_key=file_key)

        figma_file.name = data.get("name")
        figma_file.thumbnail_url = preview_url or data.get("thumbnailUrl") or figma_file.thumbnail_url
        figma_file.last_modified = last_modified
        figma_file.updated_at = datetime.utcnow()

        self.db.add(figma_file)
        self.db.commit()
        self.db.refresh(figma_file)

        project_payload = {
            "id": figma_file.id,
            "file_key": file_key,
            "document": data.get("document"),
            "name": data.get("name"),
            "preview_url": preview_url,
            "project_id": figma_file.project_id,
        }
        logger.info("Imported project payload for %s: %s", file_key, project_payload)
        return project_payload, figma_file

    def get_preview_image(self, file_key: str, node_id: str, token: str) -> Optional[str]:
        normalized_node_id = node_id.replace("-", ":") if node_id else node_id
        params = {"ids": normalized_node_id, "format": "png"}
        url = f"https://api.figma.com/v1/images/{file_key}?{urlencode(params)}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
        except Exception:
            logger.exception(
                "Failed to contact Figma for preview (file %s, node %s)",
                file_key,
                normalized_node_id,
            )
            return None

        if response.status_code != 200:
            logger.error(
                "Failed to fetch preview for file %s (node %s) with status %s: %s",
                file_key,
                normalized_node_id,
                response.status_code,
                response.text,
            )
            return None

        data = response.json()
        images = data.get("images") or {}
        preview_url = images.get(normalized_node_id) or images.get(node_id)
        if not preview_url:
            logger.error(
                "Figma preview missing for file %s (node %s): %s",
                file_key,
                normalized_node_id,
                data,
            )
            return None

        return preview_url

    def notify_projects_service(
        self,
        user_id: int,
        figma_url: str,
        token: str,
        figma_file: FigmaFile,
        project_name: Optional[str] = None,
        preview_url: Optional[str] = None,
    ):
        payload = {
            "content_type": "figma",
            "figma_link": figma_url,
            "user_id": user_id,
        }
        if project_name:
            payload["title"] = project_name
        if preview_url:
            payload["preview_url"] = preview_url
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.put(
                f"{PROJECTS_SERVICE_URL}/project/{user_id}/connect-figma",
                json=payload,
                headers=headers,
                timeout=5,
            )
            if response.status_code != 200:
                print(f"[!] Failed to update project in Projects: {response.text}")
            else:
                data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                project_payload = data.get("project") if isinstance(data, dict) else None
                project_id = None
                if isinstance(project_payload, dict):
                    project_id = project_payload.get("id") or project_payload.get("project_id")

                if project_id and figma_file.project_id != project_id:
                    figma_file.project_id = project_id
                    self.db.add(figma_file)
                    self.db.commit()
                    self.db.refresh(figma_file)
        except Exception as e:
            print(f"[!] Error contacting Projects service: {e}")

    def fetch_figma_data(self, project_id: int):
        project = self.db.get(FigmaFile, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Figma file not found")

        token = self._get_account_token(project.user_id)
        headers = {"Authorization": f"Bearer {token}"}

        url = f"https://api.figma.com/v1/files/{project.file_key}"
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            raise HTTPException(status_code=400, detail="Cannot fetch file from Figma")

        return res.json()

    def sync_figma_project(self, project_id: int):
        figma_file = self.db.get(FigmaFile, project_id)
        if not figma_file:
            raise HTTPException(status_code=404, detail="Figma file not found")

        token = self._get_account_token(figma_file.user_id)
        url = f"https://api.figma.com/v1/files/{figma_file.file_key}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Failed to fetch Figma file data")
        data = response.json()

        new_name = data.get("name")
        new_last_modified = data.get("lastModified")
        new_thumbnail = data.get("thumbnailUrl")

        changes = {}
        if new_name and new_name != figma_file.name:
            changes["name"] = {"old": figma_file.name, "new": new_name}
        if new_thumbnail and new_thumbnail != figma_file.thumbnail_url:
            changes["thumbnail"] = {"old": figma_file.thumbnail_url, "new": new_thumbnail}
        if new_last_modified:
            try:
                parsed_last_modified = datetime.fromisoformat(new_last_modified.replace("Z", "+00:00"))
            except ValueError:
                parsed_last_modified = figma_file.last_modified
            if parsed_last_modified and figma_file.last_modified != parsed_last_modified:
                changes["last_modified"] = {
                    "old": figma_file.last_modified.isoformat() if figma_file.last_modified else None,
                    "new": parsed_last_modified.isoformat(),
                }
                figma_file.last_modified = parsed_last_modified

        figma_file.name = new_name or figma_file.name
        figma_file.thumbnail_url = new_thumbnail or figma_file.thumbnail_url
        figma_file.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(figma_file)
        return {
            "message": "Project synced sucessfully",
            "project_id": figma_file.id,
            "file_key": figma_file.file_key,
            "changes": changes or "No changes",
            "last_sync": figma_file.updated_at.isoformat(),
        }