import os
from pathlib import Path
from uuid import uuid4

import requests
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from starlette import status

from src.database.models.Project import Project
from src.schemas.ProjectSchema import ProjectSchema
from src.schemas.UpdateProjectSchema import ProjectUpdateSchema
from src.schemas.ConnectFigmaSchema import ConnectFigmaSchema
from src.security.auth_utils import get_user_data
from src.security.auth_utils import get_user_data_username


FIGMA_SERVICE_URL = os.getenv("FIGMA_SERVICE_URL", "http://figma-service:6702/api/v1")
PROJECTS_PUBLIC_URL = os.getenv("PROJECTS_PUBLIC_URL", "http://localhost:6701")
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"

class Services:
    def __init__(self, db: Session):
        self.db = db

    def save_uploaded_file(self, file: UploadFile) -> str:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid4().hex}_{file.filename}"
        destination = UPLOAD_DIR / filename
        with destination.open("wb") as buffer:
            buffer.write(file.file.read())
        return str(Path("uploads") / filename)

    def build_public_url(self, stored_path: str | None) -> str | None:
        if not stored_path:
            return None
        if stored_path.startswith("http://") or stored_path.startswith("https://"):
            return stored_path
        normalized = stored_path.lstrip("/")
        return f"{PROJECTS_PUBLIC_URL.rstrip('/')}/{normalized}"

    def get_project_preview(self, project: Project) -> str | None:
        fallback_path = None
        if isinstance(project.content_type, str) and project.content_type.startswith("uploads"):
            fallback_path = project.content_type

        return self.build_public_url(project.preview_url or fallback_path)

    def create_project(self, project: ProjectSchema, user_id: int, token: str, upload: UploadFile | None = None):
        figma_link = project.figma_link
        saved_path = None
        preview_url = None

        if upload:
            saved_path = self.save_uploaded_file(upload)
            preview_url = self.build_public_url(saved_path)

        if project.contents == "figma" and figma_link:
            try:
                response = requests.post(
                    f"{FIGMA_SERVICE_URL}/figma/import",
                    json={"file_url": figma_link},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=8,
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Figma import failed")
                else:
                    response_payload = response.json()
                    project_data = response_payload.get("project", {}) if isinstance(response_payload, dict) else {}
                    preview_url = project_data.get("preview_url") or response_payload.get("preview_url")
                    figma_link = response_payload.get("figma_link", figma_link)
                    print("Figma import success")
            except Exception as e:
                print(f"[!] Error contacting Figma service: {e}")

        content_reference = saved_path if saved_path else figma_link

        new_project = Project(
            title=project.title,
            description=project.description,
            figma_link=figma_link,
            contents=project.contents,
            content_type=content_reference or project.content_type or project.contents,
            is_public=project.is_public,
            user_id=user_id,
            preview_url=preview_url,
        )
        self.db.add(new_project)
        self.db.commit()
        self.db.refresh(new_project)
        return new_project

    def connect_figma_project(self, user_id: int, payload: ConnectFigmaSchema):
        if not payload.figma_link:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Figma link is required")

        project = (
            self.db.query(Project)
            .filter(Project.user_id == user_id, Project.figma_link == payload.figma_link)
            .first()
        )

        if project:
            if payload.title:
                project.title = payload.title
            if payload.description is not None:
                project.description = payload.description
            project.contents = project.contents or "figma"
            project.content_type = payload.content_type or project.content_type or "figma"
            project.preview_url = self.build_public_url(payload.preview_url) or project.preview_url
        else:
            project = Project(
                title=payload.title or "Figma Project",
                description=payload.description or "",
                figma_link=payload.figma_link,
                contents="figma",
                content_type=payload.content_type or "figma",
                is_public=False,
                user_id=user_id,
                preview_url=self.build_public_url(payload.preview_url),
            )
            self.db.add(project)

        self.db.commit()
        self.db.refresh(project)
        return project

    def delete_project(self, project_id: int, user_id: int):
        project = self.db.get(Project, project_id)
        if not project:
            return False
        if project.user_id != user_id:
            return False
        self.db.delete(project)
        self.db.commit()
        return True
    def public_project(self, username:str):
        user_data = get_user_data_username(username)
        if not user_data:
            raise HTTPException(status_code=401, detail="Could not find user")
        public_projects = self.db.query(Project).filter(
            Project.user_id == user_data["user_id"],
            Project.is_public == True
        ).all()
        return public_projects

    def update_project(self, project_id: int, user_id: int, update_data: ProjectUpdateSchema):
        project = self.db.get(Project, project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to edit this project")
        update_fields = update_data.dict(exclude_unset=True)
        update_fields = {
            k: v for k, v in update_fields.items()
            if v not in [None, "string", ""]
        }
        for key, value in update_fields.items():
            setattr(project, key, value)

        self.db.commit()
        self.db.refresh(project)
        return project

    def list_user_projects(self, user_id: int):
        projects = self.db.query(Project).filter(Project.user_id == user_id).all()
        return [
            {
                "id": project.project_id,
                "title": project.title,
                "description": project.description,
                "is_public": project.is_public,
                "figma_link": project.figma_link,
                "contents": project.contents,
                "content_type": project.content_type,
                "preview_url": self.get_project_preview(project),
            }
            for project in projects
        ]

    # def guess_content_type(filename: str) -> str:
    #     ext = os.path.splitext(filename)[1].lower()
    #     if ext in [".png", ".jpg", ".jpeg", ".gif"]:
    #         return "image"
    #     elif ext in [".mp4", ".mov", ".avi"]:
    #         return "video"
    #     elif ext in [".fig"]:
    #         return "figma"
    #     return "unknown"