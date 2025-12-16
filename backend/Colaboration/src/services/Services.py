from fastapi import HTTPException, Response
import requests
from pip._internal.network.auth import Credentials
from sqlalchemy.orm import Session
from sqlalchemy import func
import os
import json
from datetime import datetime
from src.database.models.Rating import Rating
from src.database.models.Comment import Comment
from src.database.models.Notification import Notification
from src.schemas.NotificationSchema import NotificationSchema
from src.schemas.RatingSchema import RatingSchema
from src.schemas.CommentSchema import CommentSchema
from src.schemas.CommentSchema import ReplySchema


PROJECTS_URL = os.getenv("PROJECTS_SERVICE_URL", "http://project-service:6701/api/v1")
AUTH_BASE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:6700")


def _build_auth_url(path: str) -> str:
    base = AUTH_BASE_URL.rstrip("/")

    if not base.endswith("/api/v1"):
        base = f"{base}/api/v1"

    if not path.startswith("/"):
        path = f"/{path}"

    return f"{base}{path}"

class Services:
    def __init__(self, db: Session):
        self.db = db

    def rate_project(self, project_id: int, user_id: int, data: RatingSchema):
        rating = (
            self.db.query(Rating)
            .filter(Rating.project_id == project_id, Rating.user_id == user_id)
            .first()
        )

        if rating:
            rating.stars = data.value
            rating.updated_at = datetime.utcnow()
        else:
            rating = Rating(
                project_id=project_id,
                user_id=user_id,
                stars=data.value,
            )
            self.db.add(rating)

        self.db.commit()
        self.db.refresh(rating)

        self._notify_project_owner_about_rating(project_id, user_id, data.value)

        return rating

    def get_rating(self, project_id: int, user_id: int | None = None):
        avg_rating = self.db.query(func.avg(Rating.stars)).filter(
            Rating.project_id == project_id
        ).scalar()

        count = self.db.query(func.count(Rating.id)).filter(
            Rating.project_id == project_id
        ).scalar()

        user_rating = None
        if user_id:
            existing = (
                self.db.query(Rating)
                .filter(Rating.project_id == project_id, Rating.user_id == user_id)
                .first()
            )
            user_rating = existing.stars if existing else None

        return {
            "project_id": project_id,
            "average": float(avg_rating) if avg_rating else 0.0,
            "count": count,
            "average_rating": float(avg_rating) if avg_rating else 0.0,
            "total_ratings": count,
            "user_rating": user_rating,
        }

    def _fetch_project_owner(self, project_id: int):
        try:
            response = requests.get(f"{PROJECTS_URL}/project/details/{project_id}")
            if response.status_code != 200:
                return None
            payload = response.json() or {}
            return payload.get("project")
        except Exception:
            return None

    def _notify_user(
        self,
        user_id: int,
        notification_type: str,
        message: str,
        project_id: int | None = None,
        actor_id: int | None = None,
        actor_username: str | None = None,
    ):
        if not user_id:
            return None

        notification = Notification(
            user_id=user_id,
            type=notification_type,
            message=message,
            project_id=project_id,
            actor_id=actor_id,
            actor_username=actor_username,
        )

        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        return notification

    def _notify_project_owner_about_rating(self, project_id: int, rater_id: int, value: int):
        project = self._fetch_project_owner(project_id)
        if not project:
            return

        owner_id = project.get("user_id")
        if not owner_id or owner_id == rater_id:
            return

        profile = self._fetch_user_profile(rater_id)
        rater_username = profile.get("username") or profile.get("name")
        message = f"Your project '{project.get('title', 'project')}' received a {value}/5 rating"

        self._notify_user(
            owner_id,
            "rating",
            message,
            project_id=project_id,
            actor_id=rater_id,
            actor_username=rater_username,
        )

    def _fetch_user_profile(self, user_id: int) -> dict:
        try:
            response = requests.get(_build_auth_url(f"auth/user/id/{user_id}"), timeout=5)
            if response.status_code != 200:
                return {}
            payload = response.json() or {}
            return {
                "user_id": payload.get("user_id") or payload.get("id"),
                "username": payload.get("username"),
                "name": payload.get("name"),
                "family_name": payload.get("family_name"),
            }
        except Exception:
            return {}

    def _serialize_comment(self, comment: Comment, profiles: dict) -> dict:
        return {
            "id": comment.id,
            "project_id": comment.project_id,
            "user_id": comment.user_id,
            "parent_id": getattr(comment, "parent_id", None),
            "content": comment.content,
            "created_at": comment.created_at,
            "author": profiles.get(comment.user_id, {}),
            "replies": [],
        }

    def add_comment(self, project_id: int, user_id: int, data: CommentSchema, user_profile: dict | None = None):
        """Create new top-level comment"""
        new_comment = Comment(
            project_id=project_id,
            user_id=user_id,
            content=data.content,
            parent_id=None,
            created_at=datetime.utcnow(),
        )

        self.db.add(new_comment)
        self.db.commit()
        self.db.refresh(new_comment)

        profile = user_profile or self._fetch_user_profile(user_id)

        self._notify_project_owner_about_comment(project_id, user_id, profile)

        return self._serialize_comment(new_comment, {user_id: profile})

    def reply_to_comment(self, comment_id: int, user_id: int, data: ReplySchema, user_profile: dict | None = None):
        parent = self.db.query(Comment).filter(Comment.id == comment_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")

        reply = Comment(
            project_id=parent.project_id,
            user_id=user_id,
            content=data.content,
            parent_id=comment_id,
            created_at=datetime.utcnow(),
        )

        self.db.add(reply)
        self.db.commit()
        self.db.refresh(reply)

        profile = user_profile or self._fetch_user_profile(user_id)

        if parent.user_id != user_id:
            author = profile.get("username") or profile.get("name") or "Ktoś"
            self._notify_user(
                parent.user_id,
                "reply",
                f"{author} replied to your comment",
                project_id=parent.project_id,
                actor_id=user_id,
                actor_username=profile.get("username") or profile.get("name"),
            )

        return self._serialize_comment(reply, {user_id: profile})

    def get_project_comments(self, project_id: int):
        comments = (
            self.db.query(Comment)
            .filter(Comment.project_id == project_id)
            .order_by(Comment.created_at.asc())
            .all()
        )

        profiles = {}
        user_ids = {c.user_id for c in comments}
        for uid in user_ids:
            profiles[uid] = self._fetch_user_profile(uid)

        nodes = {c.id: self._serialize_comment(c, profiles) for c in comments}

        tree: list[dict] = []
        for comment in comments:
            node = nodes[comment.id]
            parent_id = getattr(comment, "parent_id", None)
            if parent_id and parent_id in nodes:
                nodes[parent_id]["replies"].append(node)
            else:
                tree.append(node)

        return tree

    def get_notifications(self, user_id: int):
        notifications = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .all()
        )

        return [
            NotificationSchema(
                id=n.id,
                user_id=n.user_id,
                type=n.type,
                message=n.message,
                is_read=n.is_read,
                created_at=n.created_at,
                read_at=n.read_at,
                project_id=n.project_id,
                actor_id=n.actor_id,
                actor_username=n.actor_username,
            )
            for n in notifications
        ]

    def mark_notification_as_read(self, notification_id: int, user_id: int):
        notification = (
            self.db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        notification.is_read = True
        notification.read_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(notification)

        return NotificationSchema(
            id=notification.id,
            user_id=notification.user_id,
            type=notification.type,
            message=notification.message,
            is_read=notification.is_read,
            created_at=notification.created_at,
            read_at=notification.read_at,
            project_id=notification.project_id,
            actor_id=notification.actor_id,
            actor_username=notification.actor_username,
        )

    def delete_notification(self, notification_id: int, user_id: int):
        notification = (
            self.db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        self.db.delete(notification)
        self.db.commit()

        return {"message": "Notification deleted"}

    def create_notification(
        self,
        user_id: int,
        notification_type: str,
        message: str,
        project_id: int | None = None,
        actor_id: int | None = None,
        actor_username: str | None = None,
    ):
        notification = self._notify_user(
            user_id=user_id,
            notification_type=notification_type,
            message=message,
            project_id=project_id,
            actor_id=actor_id,
            actor_username=actor_username,
        )

        if not notification:
            raise HTTPException(status_code=400, detail="Unable to create notification")

        return NotificationSchema(
            id=notification.id,
            user_id=notification.user_id,
            type=notification.type,
            message=notification.message,
            is_read=notification.is_read,
            created_at=notification.created_at,
            read_at=notification.read_at,
            project_id=notification.project_id,
            actor_id=notification.actor_id,
            actor_username=notification.actor_username,
        )

    def _notify_project_owner_about_comment(self, project_id: int, commenter_id: int, profile: dict):
        project = self._fetch_project_owner(project_id)
        if not project:
            return

        owner_id = project.get("user_id")
        if not owner_id or owner_id == commenter_id:
            return

        author = profile.get("username") or profile.get("name") or "Ktoś"
        title = project.get("title", "project")
        message = f"{author} commented on your project '{title}'"

        self._notify_user(
            owner_id,
            "comment",
            message,
            project_id=project_id,
            actor_id=commenter_id,
            actor_username=profile.get("username") or profile.get("name"),
        )