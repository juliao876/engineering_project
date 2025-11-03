from fastapi import HTTPException, Response
from pip._internal.network.auth import Credentials
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from starlette import status
from src.database.models.Project import Projects
from src.schemas.ProjectSchema import ProjectSchema

from src.database.models import Project


class Services:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, project: ProjectSchema, user_id=None):
        new_project = Projects(
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
