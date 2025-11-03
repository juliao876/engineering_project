from fastapi import APIRouter, Depends, Response, Request, HTTPException
from fastapi_utils.cbv import cbv
from sqlalchemy.sql.coercions import expect
from src.database.db_connection import get_db
from sqlalchemy.orm import Session
from src.schemas.ProjectSchema import ProjectSchema
from src.database.models import Project
from src.services.Services import Services

project_router = APIRouter(prefix="/project", tags=["Projects"])

@cbv(project_router)
class Projects():
    @project_router.post("/create_project")
    def create_project(self, project: ProjectSchema, db: Session = Depends(get_db)):

        service = Services(db)
        return service.create_project(project)
