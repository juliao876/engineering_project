from fastapi import APIRouter, Depends, Response, Request, HTTPException, Header
from fastapi_utils.cbv import cbv
from src.database.db_connection import get_db
from sqlalchemy.orm import Session
from src.database.models.FigmaFile import FigmaFile as FigmaFileModel
from src.schemas.FigmaConnectSchema import FigmaConnectSchema
from src.schemas.FigmaImportSchema import FigmaImportSchema
from src.security.auth_utils import get_user_data
from src.services.Services import Services

figma_router = APIRouter(prefix="/figma", tags=["Figma_Files"])

@cbv(figma_router)
class Fig:
    @figma_router.post("/connect")
    def connect(self, auth: FigmaConnectSchema, db: Session = Depends(get_db), authorization: str = Header(None)):
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")

        token = authorization.replace("Bearer ", "")
        user_data = get_user_data(token)
        user_id = user_data["id"]

        service = Services(db)
        figma_token = service.connect(
            code=auth.code,
            client_id="Client ID",
            client_secret="Client Secret",
            redirect_uri="Redirect URI",
            user_id=user_id
        )
        return {"access_token": figma_token.access_token}
    @figma_router.post("/import")
    def import_project(self, schema: FigmaImportSchema, db: Session = Depends(get_db), authorization: str = Header(None)):
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        token = authorization.replace("Bearer ", "")
        user_data = get_user_data(token)
        user_id = user_data["id"]

        figma_token = db.query(FigmaFileModel).filter(FigmaFileModel.user_id == user_id).first()
        if not figma_token:
            raise HTTPException(status_code=404, detail="Figma file not found")
        service = Services(db)
        project_data = service.get_projects(
            file_url=schema.file_url,
            access_token=figma_token.access_token,
            user_id=user_id
        )
        figma_url = f"https://www.figma.com/file/{project_data.file_key}"
        service.notify_projects_service(user_id, figma_url, token)

        return {
            "message": "Project imported successfully",
            "figma_link": figma_url,
            "project": project_data
        }
    @figma_router.get("/{project_id}/data")
    def get_figma_project_data(self, project_id: int, db: Session = Depends(get_db)):
        service = Services(db)
        data = service.fetch_figma_data(project_id)
        if not data:
            raise HTTPException(status_code=404, detail="Figma not found")
        return data