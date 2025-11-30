from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from src.security.auth_utils import get_user_data
from src.database.db_connection import get_db
from src.services.Services import Services

from src.schemas.CommentSchema import CommentSchema, ReplySchema
from src.schemas.RatingSchema import RatingSchema
from src.schemas.FollowerSchema import FollowerSchema


collaboration_router = APIRouter(prefix="/collab", tags=["Collaboration"])


@cbv(collaboration_router)
class CollaborationEndpoints:
    db: Session = Depends(get_db)

    # ============================================================
    #                          ⭐ RATING
    # ============================================================
    @collaboration_router.post("/projects/{project_id}/rating")
    def rate_project(self, project_id: int, payload: RatingSchema, request: Request):
        # --- auth ---
        token = request.cookies.get("token")
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
                "value": rating.value,
                "created_at": rating.created_at,
            }
        }

    @collaboration_router.get("/projects/{project_id}/rating")
    def get_project_rating(self, project_id: int):
        service = Services(self.db)
        return service.get_rating(project_id)

    # ============================================================
    #                     💬 COMMENTS + REPLIES
    # ============================================================
    @collaboration_router.post("/projects/{project_id}/comments")
    def add_comment(self, project_id: int, payload: CommentSchema, request: Request):

        token = request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_data = get_user_data(token)
        user_id = user_data.get("id") or user_data.get("user_id")

        service = Services(self.db)
        new_comment = service.add_comment(project_id, user_id, payload)

        return {
            "message": "Comment added",
            "comment": {
                "id": new_comment.id,
                "project_id": new_comment.project_id,
                "user_id": new_comment.user_id,
                "content": new_comment.content,
                "parent_comment_id": new_comment.parent_comment_id,
                "created_at": new_comment.created_at,
            }
        }

    @collaboration_router.post("/comments/{comment_id}/reply")
    def reply_to_comment(self, comment_id: int, payload: ReplySchema, request: Request):

        token = request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_data = get_user_data(token)
        user_id = user_data.get("id") or user_data.get("user_id")

        service = Services(self.db)
        reply = service.reply_to_comment(comment_id, user_id, payload)

        return {
            "message": "Reply added",
            "reply": {
                "id": reply.id,
                "project_id": reply.project_id,
                "user_id": reply.user_id,
                "content": reply.content,
                "parent_comment_id": reply.parent_comment_id,
                "created_at": reply.created_at,
            }
        }

    @collaboration_router.get("/projects/{project_id}/comments")
    def get_comments(self, project_id: int):
        service = Services(self.db)
        comments = service.get_project_comments(project_id)

        def serialize(comment):
            return {
                "id": comment.id,
                "project_id": comment.project_id,
                "user_id": comment.user_id,
                "content": comment.content,
                "created_at": comment.created_at,
                "replies": [serialize(r) for r in getattr(comment, "replies", [])]
            }

        return [serialize(c) for c in comments]

    # ============================================================
    #                     👤 FOLLOW / UNFOLLOW
    # ============================================================
    @collaboration_router.post("/users/follow")
    def follow_user(self, payload: FollowerSchema, request: Request):

        token = request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_data = get_user_data(token)
        user_id = user_data.get("id") or user_data.get("user_id")

        service = Services(self.db)
        result = service.follow_user(user_id, payload)

        return result

    # ============================================================
    #                      🔔 NOTIFICATIONS
    # ============================================================
    @collaboration_router.get("/notifications")
    def get_notifications(self, request: Request):

        token = request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_data = get_user_data(token)
        user_id = user_data.get("id") or user_data.get("user_id")

        service = Services(self.db)
        notifications = service.get_notifications(user_id)

        return [
            {
                "id": n.id,
                "user_id": n.user_id,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at,
                "read_at": n.read_at,
            }
            for n in notifications
        ]

    @collaboration_router.post("/notifications/read/{notification_id}")
    def mark_notification_read(self, notification_id: int, request: Request):

        token = request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_data = get_user_data(token)
        user_id = user_data.get("id") or user_data.get("user_id")

        service = Services(self.db)
        return service.mark_notification_as_read(notification_id, user_id)
