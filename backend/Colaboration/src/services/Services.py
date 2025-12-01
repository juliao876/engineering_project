from fastapi import HTTPException, Response, requests
from pip._internal.network.auth import Credentials
from sqlalchemy.orm import Session
from sqlalchemy import func
import os
import json
from datetime import datetime
from src.database.models.Rating import Rating
from src.database.models.Comment import Comment
from src.database.models.Follow import Follow
from src.schemas.FollowerSchema import FollowerSchema
from src.database.models.Notification import Notification
from src.schemas.NotificationSchema import NotificationSchema
from src.schemas.RatingSchema import RatingSchema
from src.schemas.CommentSchema import CommentSchema
from src.schemas.CommentSchema import ReplySchema


PROJECTS_URL = "http://127.0.0.1:6701"

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
            rating.value = data.value
            rating.created_at = datetime.utcnow()
        else:
            rating = Rating(
                project_id=project_id,
                user_id=user_id,
                value=data.value,
            )
            self.db.add(rating)

        self.db.commit()
        self.db.refresh(rating)

        return rating

    def get_rating(self, project_id: int):
        avg_rating = self.db.query(func.avg(Rating.value)).filter(
            Rating.project_id == project_id
        ).scalar()

        count = self.db.query(func.count(Rating.id)).filter(
            Rating.project_id == project_id
        ).scalar()

        return {
            "project_id": project_id,
            "average": float(avg_rating) if avg_rating else 0.0,
            "count": count,
        }

    def add_comment(self, project_id: int, user_id: int, data: CommentSchema):
        """Create new top-level comment"""
        new_comment = Comment(
            project_id=project_id,
            user_id=user_id,
            content=data.content,
            parent_comment_id=None,
            created_at=datetime.utcnow(),
        )

        self.db.add(new_comment)
        self.db.commit()
        self.db.refresh(new_comment)

        return new_comment

    def reply_to_comment(self, comment_id: int, user_id: int, data: ReplySchema):
        parent = self.db.query(Comment).filter(Comment.id == comment_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")

        reply = Comment(
            project_id=parent.project_id,
            user_id=user_id,
            content=data.content,
            parent_comment_id=comment_id,
            created_at=datetime.utcnow(),
        )

        self.db.add(reply)
        self.db.commit()
        self.db.refresh(reply)

        return reply

    def get_project_comments(self, project_id: int):
        comments = (
            self.db.query(Comment)
            .filter(Comment.project_id == project_id)
            .order_by(Comment.created_at.asc())
            .all()
        )
        comment_map = {c.id: c for c in comments}
        tree = []

        for c in comments:
            if c.parent_comment_id:
                parent = comment_map.get(c.parent_comment_id)
                if not hasattr(parent, "replies"):
                    parent.replies = []
                parent.replies.append(c)
            else:
                tree.append(c)

        return tree

    def get_notifications(self, user_id: int):
        notifications = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .all()
        )

        return notifications

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

        return {"message": "Notification marked as read"}