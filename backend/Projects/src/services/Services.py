from fastapi import HTTPException, Response
from pip._internal.network.auth import Credentials
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from sqlalchemy.testing.pickleable import User
from starlette import status
from src.database.models.Project import Project
from src.schemas.ProjectSchema import ProjectSchema
from src.security.auth_utils import get_user_data_username
from src.security.auth_utils import get_user_data
from src.schemas.UpdateProjectSchema import ProjectUpdateSchema

class Services:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, project: ProjectSchema, user_id = int):
        new_project = Project(
            title=project.title,
            description=project.description,
            figma_link=project.figma_link,
            contents=project.contents,
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

    def update_project(self, project_id: int, user_id: int, update_data: ProjectSchema):
        project = self.db.get(Project, project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to edit this project")
        update_fields = update_data.dict(exclude_unset=True)
        for key, value in update_data.dict().items():
            setattr(project, key, value)

        self.db.commit()
        self.db.refresh(project)
        return project
