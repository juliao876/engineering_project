import os

import logging
from uuid import uuid4
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, Request, HTTPException, Header
from fastapi.responses import RedirectResponse
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from src.database.db_connection import get_db
from src.database.models.FigmaAccount import FigmaAccount
from src.schemas.FigmaConnectSchema import FigmaConnectSchema
from src.schemas.FigmaImportSchema import FigmaImportSchema
from src.security.auth_utils import get_user_data
from src.services.Services import Services, DEFAULT_FIGMA_REDIRECT

figma_router = APIRouter(prefix="/figma", tags=["Figma Integration"])
logger = logging.getLogger(__name__)


def _extract_user_id(user_data: dict) -> int:
    user_id = (
        user_data.get("user_id")
        or user_data.get("id")
        or (user_data.get("user") or {}).get("id")
    )
    if not user_id:
        raise HTTPException(status_code=401, detail="Could not determine user ID")
    return user_id


@cbv(figma_router)
class Fig:
    @figma_router.get("/auth-url")
    def build_auth_url(
        self,
        request: Request,
        state: str | None = None,
        db: Session = Depends(get_db),
        authorization: str = Header(None),
        figma_client_id: str | None = Header(None, alias="x-figma-client-id"),
        figma_client_secret: str | None = Header(None, alias="x-figma-client-secret"),
        figma_redirect: str | None = Header(None, alias="x-figma-redirect-uri"),
    ):
        token = authorization.replace("Bearer ", "") if authorization else request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        user_data = get_user_data(token)
        user_id = _extract_user_id(user_data)

        service = Services(db)
        generated_state = state or f"{user_id}-{uuid4().hex}"
        auth_url = service.build_authorize_url(
            state=generated_state,
            client_id=figma_client_id,
            redirect_uri=figma_redirect,
        )
        return {
            "authorize_url": auth_url,
            "state": generated_state,
            "client_id": figma_client_id,
        }

    @figma_router.post("/connect")
    def connect(
        self,
        auth: FigmaConnectSchema,
        request: Request,
        db: Session = Depends(get_db),
        authorization: str = Header(None),
        figma_client_id: str | None = Header(None, alias="x-figma-client-id"),
        figma_client_secret: str | None = Header(None, alias="x-figma-client-secret"),
        figma_redirect: str | None = Header(None, alias="x-figma-redirect-uri"),
    ):
        token = authorization.replace("Bearer ", "") if authorization else request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        user_data = get_user_data(token)
        user_id = _extract_user_id(user_data)
        logger.info("Starting Figma connect for user %s with state=%s", user_id, auth.state)

        client_id = auth.client_id or figma_client_id or os.getenv("FIGMA_CLIENT_ID")
        client_secret = auth.client_secret or figma_client_secret or os.getenv("FIGMA_CLIENT_SECRET")
        redirect_uri = (
            auth.redirect_uri
            or figma_redirect
            or os.getenv("FIGMA_REDIRECT_URI")
            or DEFAULT_FIGMA_REDIRECT
        )

        service = Services(db)
        figma_account = service.connect_account(
            code=auth.code,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            user_id=user_id,
        )
        return {"message": "Connected", "access_token": figma_account.access_token}

    @figma_router.post("/import")
    def import_project(
        self,
        schema: FigmaImportSchema,
        request: Request,
        db: Session = Depends(get_db),
        authorization: str = Header(None),
    ):
        token = authorization.replace("Bearer ", "") if authorization else request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        user_data = get_user_data(token)
        user_id = _extract_user_id(user_data)

        figma_account = db.query(FigmaAccount).filter(FigmaAccount.user_id == user_id).first()
        if not figma_account:
            raise HTTPException(status_code=401, detail="You must connect Figma first")

        service = Services(db)
        project_data, figma_file = service.get_projects(
            file_url=schema.file_url,
            access_token=figma_account.access_token,
            user_id=user_id,
        )
        logger.info(
            "Figma import fetched file %s for user %s: name=%s",
            project_data.get("file_key"),
            user_id,
            project_data.get("name"),
        )
        return {
            "message": "Project imported successfully",
            "figma_link": f"https://www.figma.com/file/{project_data['file_key']}",
            "preview_url": project_data.get("preview_url"),
            "project": project_data,
        }

    @figma_router.get("/callback")
    def figma_callback(self, request: Request, db: Session = Depends(get_db)):
        """
        Handle the Figma OAuth callback by exchanging the code for tokens and
        redirecting the user back to the frontend with a status flag.
        """

        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")
        if not state or "-" not in state:
            raise HTTPException(status_code=400, detail="Missing or invalid state")

        try:
            user_id = int(state.split("-", 1)[0])
        except ValueError:
            raise HTTPException(status_code=400, detail="Could not parse user from state")

        client_id = os.getenv("FIGMA_CLIENT_ID")
        client_secret = os.getenv("FIGMA_CLIENT_SECRET")
        redirect_uri = os.getenv("FIGMA_REDIRECT_URI") or DEFAULT_FIGMA_REDIRECT

        service = Services(db)

        status = "connected"
        error_reason = None
        try:
            service.connect_account(
                code=code,
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                user_id=user_id,
            )
            logger.info("Figma OAuth connected for user %s via callback", user_id)
        except HTTPException as exc:  # keep the message for the frontend
            status = "error"
            error_reason = exc.detail if isinstance(exc.detail, str) else "oauth_failed"
            logger.exception("Figma OAuth failed for user %s: %s", user_id, error_reason)
        except Exception:
            status = "error"
            error_reason = "unexpected_error"
            logger.exception("Unexpected error while connecting Figma for user %s", user_id)

        forward_callback = (
            os.getenv("FIGMA_CALLBACK_FORWARD_URL")
            or os.getenv("FIGMA_FRONTEND_CALLBACK_URL")
            or redirect_uri
            or DEFAULT_FIGMA_REDIRECT
        )

        query = {"status": status, "state": state}
        if error_reason:
            query["reason"] = error_reason

        forward_url = f"{forward_callback}?{urlencode(query)}"
        logger.info("Redirecting Figma OAuth callback to frontend: %s", forward_url)
        return RedirectResponse(url=forward_url, status_code=302)

    @figma_router.get("/{project_id}/data")
    def get_figma_project_data(self, project_id: int, db: Session = Depends(get_db)):
        service = Services(db)
        data = service.fetch_figma_data(project_id)
        if not data:
            raise HTTPException(status_code=404, detail="Figma not found")
        return data

    @figma_router.get("/sync/{project_id}")
    def sync_project(self, project_id: int, db: Session = Depends(get_db)):
        service = Services(db)
        result = service.sync_figma_project(project_id)
        return result