from fastapi import APIRouter, Depends, Response, Request, HTTPException
from fastapi_utils.cbv import cbv
from sqlalchemy.sql.coercions import expect
from src.database.db_connection import get_db
from sqlalchemy.orm import Session
from src.schemas.ProjectSchema import ProjectSchema
from src.database.models import Project
from src.services.Services import Services
from src.security.auth_utils import get_user_data

project_router = APIRouter(prefix="/project", tags=["Projects"])

@cbv(project_router)
class Projects():
    @project_router.post("/create_project")
    def create_project(self, request: Request,  project: ProjectSchema, session: Session = Depends(get_db)):
        token = request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        user_data = get_user_data(token)
        user_id = user_data.get("id")

        if not user_id:
            raise HTTPException(status_code=401, detail="Not authenticated")

        service = Services(user_id)
        new_project = service.create_project(project, user_id)

        service = Services(self.db)
        return {
            "message": "Project created successfully",
            "project": {
                "id": new_project.project_id,
                "title": new_project.title,
                "user_id": new_project.user_id,
                "is_public": new_project.is_public,
            }
        }
    @project_router.delete("/delete_project/{project_id}")
    def delete_project(self, project_id: int, request: Request):
        token = request.cookies.get("token") or request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        if token.startswith("Bearer "):
            token = token.split(" ")[1]

        user_data = get_user_data(token)
        user_id = user_data.get("id")

        service = Services(self.db)
        deleted = service.delete_project(project_id, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Project not found or not yours")
        return {"message": "Project deleted successfully"}
