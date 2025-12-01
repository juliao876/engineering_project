from fastapi import HTTPException, Response, requests
from pip._internal.network.auth import Credentials
from sqlalchemy.orm import Session
from sqlalchemy import func
import os
import json
from datetime import datetime
from src.database.models.Follow import Follow
from src.schemas.FollowerSchema import FollowerSchema
import requests
from src.security.auth_utils import get_user_data_username


AUTH_URL = "http://127.0.0.1:6700"
PROJECTS_URL = "http://127.0.0.1:6701"
COLLAB_URL = "http://127.0.0.1:6704"

class Services:
    def __init__(self, db: Session):
        self.db = db

    def follow_user(self, follower_id: int, data: FollowerSchema):
        following_id = data.following_id   # ✔ FIX

        follow = (
            self.db.query(Follow)
            .filter(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id
            )
            .first()
        )
        if follow:
            self.db.delete(follow)
            self.db.commit()
            return {"message": "Unfollowed"}

        new_follow = Follow(
            follower_id=follower_id,
            following_id=following_id,
            created_at=datetime.utcnow()
        )
        self.db.add(new_follow)
        self.db.commit()

        return {"message": "Followed"}

    def get_followers(self, username: str):
        user_data = get_user_data_username(username)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user_data.get("user_id")
        rows = (
            self.db.query(Follow)
            .filter(Follow.following_id == user_id)
            .all()
        )

        if not rows:
            return []
        result = []
        for f in rows:
            try:
                r = requests.get(f"{AUTH_URL}/api/v1/users/{f.follower_id}")
                if r.status_code == 200:
                    data = r.json()
                    result.append({
                        "id": data.get("user_id"),
                        "username": data.get("username"),
                        "avatar_url": data.get("avatar_url")
                    })
            except:
                continue

        return result

    def get_following(self, username: str):
        user_data = get_user_data_username(username)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user_data.get("user_id")
        rows = (
            self.db.query(Follow)
            .filter(Follow.follower_id == user_id)
            .all()
        )

        if not rows:
            return []
        result = []
        for f in rows:
            try:
                r = requests.get(f"{AUTH_URL}/api/v1/users/{f.following_id}")
                if r.status_code == 200:
                    data = r.json()
                    result.append({
                        "id": data.get("user_id"),
                        "username": data.get("username"),
                        "avatar_url": data.get("avatar_url")
                    })
            except:
                continue

        return result

    def get_following_feed(self, user_id: int):
        following_rows = (
            self.db.query(Follow)
            .filter(Follow.follower_id == user_id)
            .all()
        )

        if not following_rows:
            return []  # nic nie obserwuje → pusty feed

        following_ids = [f.following_id for f in following_rows]

        feed = []
        for uid in following_ids:
            try:
                r = requests.get(f"{PROJECTS_URL}/project/public/{uid}")
                if r.status_code == 200:
                    projects = r.json().get("projects", [])
                    user_response = requests.get(f"{AUTH_URL}/api/v1/users/{uid}")
                    if user_response.status_code == 200:
                        user_info = user_response.json()
                        username = user_info.get("username")
                    else:
                        username = None
                    for p in projects:
                        feed.append({
                            "user_id": uid,
                            "username": username,
                            **p
                        })
            except:
                continue

        return feed

    def get_discover_feed(self):


        try:
            r = requests.get(f"{PROJECTS_URL}/project/public/all")
            if r.status_code != 200:
                raise HTTPException(status_code=500, detail="Cannot fetch projects")
            projects = r.json().get("projects", [])
        except:
            raise HTTPException(status_code=500, detail="Project service unavailable")

        feed = []

        for p in projects:
            project_id = p.get("project_id")
            try:
                rating_res = requests.get(f"{COLLAB_URL}/projects/{project_id}/rating")
                rating_data = rating_res.json()
                avg_rating = rating_data.get("average_rating", 0)
                rating_count = rating_data.get("total_ratings", 0)
            except:
                avg_rating = 0
                rating_count = 0
            try:
                comments_res = requests.get(f"{COLLAB_URL}/projects/{project_id}/comments")
                comments_data = comments_res.json()
                comments_count = len(comments_data.get("comments", []))
            except:
                comments_count = 0

            feed.append({
                **p,
                "average_rating": avg_rating,
                "rating_count": rating_count,
                "comments_count": comments_count,
            })

        feed.sort(
            key=lambda item: (
                item.get("rating_count", 0),
                item.get("comments_count", 0),
                item.get("created_at") or "1970-01-01"
            ),
            reverse=True
        )

        return feed
