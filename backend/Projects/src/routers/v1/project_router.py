from fastapi import APIRouter, Depends, Response, Request, HTTPException, File, Form, UploadFile
from fastapi_utils.cbv import cbv
from sqlalchemy.sql.coercions import expect
from src.database.db_connection import get_db
from sqlalchemy.orm import Session
from src.schemas.ProjectSchema import ProjectSchema
from src.database.models.Project import Project as ProjectModel
from src.services.Services import Services
from src.security.auth_utils import get_user_data
from src.security.auth_utils import get_user_data_username
from src.schemas.UpdateProjectSchema import ProjectUpdateSchema
from src.schemas.ConnectFigmaSchema import ConnectFigmaSchema

project_router = APIRouter(prefix="/project", tags=["Projects"])

@cbv(project_router)
class Projects():
    @project_router.post("/create_project")
    def create_project(
        self,
        request: Request,
        db: Session = Depends(get_db),
        title: str = Form(...),
        description: str = Form(""),
        is_public: bool = Form(False),
        content_type: str = Form(...),
        contents: str = Form(...),
        figma_link: str | None = Form(None),
        file: UploadFile | None = File(None),
        ):
        project = ProjectSchema(
            title=title,
            description=description,
            is_public=is_public,
            contents=contents,
            content_type=content_type,
            figma_link=figma_link,
        )
        token = request.cookies.get("token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        user_data = get_user_data(token)
        user_id = user_data.get("user_id")

        if not user_id:
            raise HTTPException(status_code=401, detail="Not authenticated")

        service = Services(db)
        new_project = service.create_project(project, user_id, token, upload=file)

        preview_url = service.get_project_preview(new_project)

        return {
            "message": "Project created successfully",
            "project": {
                "id": new_project.project_id,
                "title": new_project.title,
                "user_id": new_project.user_id,
                "is_public": new_project.is_public,
                "content_type": new_project.content_type,
                "preview_url": preview_url,
            }
        }

    @project_router.get("/my")
    def get_my_projects(self, request: Request, db: Session = Depends(get_db)):
        token = request.cookies.get("token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            raise HTTPException(status_code=401, detail="Token not provided")

        user_data = get_user_data(token)
        user_id = user_data.get("user_id") or user_data.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Could not determine user ID")

        service = Services(db)
        projects = service.list_user_projects(user_id)
        return {"projects": projects}
    @project_router.delete("/delete_project/{project_id}")
    def delete_project(self, project_id: int, request: Request, db: Session = Depends(get_db)):
        token = request.cookies.get("token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        user_data = get_user_data(token)
        user_id = user_data.get("user_id")

        service = Services(db)
        deleted = service.delete_project(project_id, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Project not found or not yours")
        return {"message": "Project deleted successfully"}

    @project_router.get("/get_projects")
    def get_projects(self, request: Request, db: Session = Depends(get_db)):
        token = request.cookies.get("token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            raise HTTPException(status_code=401, detail="Token not provided")

        user_data = get_user_data(token)
        print("USER DATA FROM AUTH:", user_data)
        user_id = user_data.get("user_id") or user_data.get("id")

        if not user_id:
            raise HTTPException(status_code=401, detail="Could not determine user ID")

        projects = db.query(ProjectModel).filter(ProjectModel.user_id == user_id).all()
        return {"projects": [p.title for p in projects]}
    @project_router.get("/public/{username}")
    def get_public_project(self, username: str, db: Session = Depends(get_db)):
        service = Services(db)
        public_projects = service.public_project(username)

        projects_payload = [
            {
                "project_id": p.project_id,
                "title": p.title,
                "description": p.description,
                "is_public": p.is_public,
                "user_id": p.user_id,
                "contents": p.contents,
                "figma_link": p.figma_link,
                "content_type": p.content_type,
                "preview_url": service.get_project_preview(p),
            }
            for p in public_projects
        ]

        return {"projects": projects_payload}

    @project_router.get("/public")
    def get_all_public_projects(self, db: Session = Depends(get_db)):
        service = Services(db)
        projects = service.list_public_projects()
        return {"projects": projects}
    @project_router.get("/details/{project_id}")
    def get_project_details(self, project_id: int, db: Session = Depends(get_db)):
        service = Services(db)
        project = service.get_project(project_id)
        return {"project": project}
    @project_router.patch("/update_project/{project_id}")
    def update_project(self, project_id: int, update_data: ProjectUpdateSchema, request: Request,  db: Session = Depends(get_db)):
        token = request.cookies.get("token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        user_data = get_user_data(token)
        user_id = user_data.get("user_id")
        service = Services(db)
        updated = service.update_project(project_id, user_id, update_data)
        return {
            "message": "Project updated successfully",
            "project": {
                "id": updated.project_id,
                "title": updated.title,
                "description": updated.description,
                "is_public": updated.is_public,
                "figma_link": updated.figma_link,
                "contents": updated.contents,
                "preview_url": service.get_project_preview(updated),
            }
        }
    @project_router.put("/{user_id}/connect-figma")
    def connect_figma_project(
        self,
        user_id: int,
        payload: ConnectFigmaSchema,
        request: Request,
        db: Session = Depends(get_db),
    ):
        token = request.cookies.get("token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_data = get_user_data(token)
        requester_id = user_data.get("user_id") or user_data.get("id")
        if requester_id != user_id:
            raise HTTPException(status_code=403, detail="Cannot connect Figma for another user")

        service = Services(db)
        project = service.connect_figma_project(user_id, payload)

        preview_url = service.get_project_preview(project)

        return {
            "message": "Figma link connected",
            "project": {
                "id": project.project_id,
                "title": project.title,
                "description": project.description,
                "is_public": project.is_public,
                "figma_link": project.figma_link,
                "contents": project.contents,
                "content_type": project.content_type,
                "preview_url": preview_url,
            },
        }