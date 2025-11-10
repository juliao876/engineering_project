from fastapi import APIRouter, Depends, Response, Request, HTTPException, Header
from fastapi_utils.cbv import cbv
from sqlalchemy.sql.coercions import expect
from src.database.db_connection import get_db
from sqlalchemy.orm import Session
from src.database.models.FigmaFile import FigmaFile as FigmaFileModel
from src.schemas.FigmaConnectSchema import FigmaConnectSchema
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
