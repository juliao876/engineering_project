from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from src.security.auth_utils import get_user_data
from src.database.db_connection import get_db
from src.services.Services import Services

from src.schemas.CommentSchema import CommentSchema, ReplySchema
from src.schemas.NotificationSchema import NotificationCreateSchema
from src.schemas.RatingSchema import RatingSchema

collaboration_router = APIRouter(prefix="/collab", tags=["Collaboration"])


def _extract_token(request: Request) -> str:
    """Try to read JWT from cookie or Authorization header."""
    token = request.cookies.get("token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1]
    return token

@cbv(collaboration_router)
class Collaboration:
    db: Session = Depends(get_db)
    @collaboration_router.post("/projects/{project_id}/rating")
    def rate_project(self, project_id: int, payload: RatingSchema, request: Request):
        # --- auth ---
        token = _extract_token(request)
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_data = get_user_data(token)
        user_id = user_data.get("id") or user_data.get("user_id")

        service = Services(self.db)
        rating = service.rate_project(project_id, user_id, payload)

        return {
            "message": "Rating added/updated",
            "rating": {
                "id": rating.id,
                "project_id": rating.project_id,
                "user_id": rating.user_id,
                "value": rating.stars,
                "created_at": rating.created_at,
            }
        }

    @collaboration_router.get("/projects/{project_id}/rating")
    def get_project_rating(self, project_id: int, request: Request):
        token = _extract_token(request)
        user_id = None
        if token:
            try:
                user_data = get_user_data(token)
                user_id = user_data.get("id") or user_data.get("user_id")
            except Exception:
                user_id = None

        service = Services(self.db)
        return service.get_rating(project_id, user_id)
    @collaboration_router.post("/projects/{project_id}/comments")
    def add_comment(self, project_id: int, payload: CommentSchema, request: Request):
        token = _extract_token(request)
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_data = get_user_data(token)
        user_id = user_data.get("id") or user_data.get("user_id")

        service = Services(self.db)
        new_comment = service.add_comment(project_id, user_id, payload, user_profile=user_data)

        return {
            "message": "Comment added",
            "comment": {
                **new_comment,
            }
        }

    @collaboration_router.post("/comments/{comment_id}/reply")
    def reply_to_comment(self, comment_id: int, payload: ReplySchema, request: Request):
        token = _extract_token(request)
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        user_data = get_user_data(token)
        user_id = user_data.get("id") or user_data.get("user_id")
        service = Services(self.db)
        reply = service.reply_to_comment(comment_id, user_id, payload, user_profile=user_data)
        return {
            "message": "Reply added",
            "reply": {
                **reply,
            }
        }

    @collaboration_router.get("/projects/{project_id}/comments")
    def get_comments(self, project_id: int):
        service = Services(self.db)
        comments = service.get_project_comments(project_id)
        return {"comments": comments}
    @collaboration_router.get("/notifications")
    def get_notifications(self, request: Request):
        token = _extract_token(request)
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        user_data = get_user_data(token)
        user_id = user_data.get("id") or user_data.get("user_id")

        service = Services(self.db)
        return service.get_notifications(user_id)

    @collaboration_router.post("/notifications")
    def create_notification(self, payload: NotificationCreateSchema, request: Request):
        token = _extract_token(request)
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        service = Services(self.db)
        return service.create_notification(
            user_id=payload.user_id,
            notification_type=payload.type,
            message=payload.message,
            project_id=payload.project_id,
            actor_id=payload.actor_id,
            actor_username=payload.actor_username,
        )
    @collaboration_router.post("/notifications/read/{notification_id}")
    def mark_notification_read(self, notification_id: int, request: Request):
        token = _extract_token(request)
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_data = get_user_data(token)
        user_id = user_data.get("id") or user_data.get("user_id")

        service = Services(self.db)
        return service.mark_notification_as_read(notification_id, user_id)

    @collaboration_router.delete("/notifications/{notification_id}")
    def delete_notification(self, notification_id: int, request: Request):
        token = _extract_token(request)
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_data = get_user_data(token)
        user_id = user_data.get("id") or user_data.get("user_id")

        service = Services(self.db)
        return service.delete_notification(notification_id, user_id)