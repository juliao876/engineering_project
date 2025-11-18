from fastapi import HTTPException, Response, requests
from pip._internal.network.auth import Credentials
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from sqlalchemy.sql.coercions import expect
from sqlalchemy.testing.pickleable import User
from starlette import status
from src.database.models.Project import Project
from src.schemas.UpdateProjectSchema import ProjectUpdateSchema
from src.schemas.ProjectSchema import ProjectSchema
from src.security.auth_utils import get_user_data_username
from src.security.auth_utils import get_user_data
import os


FIGMA_SERVICE_URL = os.getenv("FIGMA_SERVICE_URL", "http://localhost:6702/api/v1")

class Services:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, project: ProjectSchema, user_id = int):
        figma_link =  project.figma_link
        if project.content_type == "figma" and figma_link:
            try:
                response = requests.post(
                f"{FIGMA_SERVICE_URL}/projects",
                    json={"file_url": figma_link},
                    headers={"Authorization": f"Bearer"},
                    timeout = 8
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Figma import failed")
                else:
                    print("Figma import success")
            except Exception as e:
                    print(f"[!] Error contacting Figma service: {e}")

        new_project = Project(
            title=project.title,
            description=project.description,
            figma_link=project.figma_link,
            contents=project.contents,
            content_type=project.content_type,
            is_public=project.is_public,
            user_id=user_id
        )
        self.db.add(new_project)
        self.db.commit()
        self.db.refresh(new_project)
        return new_project

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

    # def guess_content_type(filename: str) -> str:
    #     ext = os.path.splitext(filename)[1].lower()
    #     if ext in [".png", ".jpg", ".jpeg", ".gif"]:
    #         return "image"
    #     elif ext in [".mp4", ".mov", ".avi"]:
    #         return "video"
    #     elif ext in [".fig"]:
    #         return "figma"
    #     return "unknown"
