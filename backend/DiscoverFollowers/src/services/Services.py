import os
from datetime import datetime

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.database.models.Follow import Follow
from src.schemas.FollowerSchema import FollowerSchema
from src.security.auth_utils import get_user_data_username


AUTH_BASE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:6700")
AUTH_API_URL = f"{AUTH_BASE_URL}/api/v1/auth"
PROJECTS_BASE_URL = os.getenv("PROJECTS_SERVICE_URL", "http://project-service:6701/api/v1")
COLLAB_BASE_URL = os.getenv("COLLAB_SERVICE_URL", "http://collab-service:6704/api/v1")

class Services:
    def __init__(self, db: Session):
        self.db = db

    def follow_user(self, follower_id: int, data: FollowerSchema):
        following_id = data.following_id   # ✔ FIX

        if follower_id == following_id:
            raise HTTPException(status_code=400, detail="Cannot follow yourself")

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

    def get_follow_status(self, follower_id: int, username: str):
        user_data = get_user_data_username(username)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        following_id = user_data.get("user_id") or user_data.get("id")

        if not following_id:
            raise HTTPException(status_code=404, detail="User not found")

        if follower_id == following_id:
            return {"is_following": False}

        exists = (
            self.db.query(Follow)
            .filter(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id
            )
            .first()
        )

        return {"is_following": bool(exists)}

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
                r = requests.get(f"{AUTH_API_URL}/user/id/{f.follower_id}")
                if r.status_code == 200:
                    data = r.json()
                    result.append({
                        "id": data.get("user_id"),
                        "username": data.get("username"),
                        "avatar_url": data.get("avatar_url")
                    })
            except requests.RequestException:
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
                r = requests.get(f"{AUTH_API_URL}/user/id/{f.following_id}")
                if r.status_code == 200:
                    data = r.json()
                    result.append({
                        "id": data.get("user_id"),
                        "username": data.get("username"),
                        "avatar_url": data.get("avatar_url")
                    })
            except requests.RequestException:
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
                user_response = requests.get(f"{AUTH_API_URL}/user/id/{uid}")
                if user_response.status_code != 200:
                    continue
                user_info = user_response.json()
                username = user_info.get("username")

                r = requests.get(f"{PROJECTS_BASE_URL}/project/public/{username}")
                if r.status_code != 200:
                    continue
                projects = r.json().get("projects", [])

                for p in projects:
                    feed.append({
                        "user_id": uid,
                        "username": username,
                        **p
                    })
            except requests.RequestException:
                continue

        return feed

    def get_discover_feed(self):


        projects = []
        try:
            r = requests.get(f"{PROJECTS_BASE_URL}/project/public/all")
            if r.status_code == 200:
                projects = r.json().get("projects", [])
            else:
                print(f"[!] Project service responded with {r.status_code}: {r.text}")
        except requests.RequestException as exc:
            # Keep discover feed online even if the project service is temporarily unavailable
            print(f"[!] Project service unavailable: {exc}")

        feed = []

        for p in projects:
            project_id = p.get("project_id")
            try:
                rating_res = requests.get(f"{COLLAB_BASE_URL}/projects/{project_id}/rating")
                rating_data = rating_res.json()
                avg_rating = rating_data.get("average_rating", 0)
                rating_count = rating_data.get("total_ratings", 0)
            except requests.RequestException:
                avg_rating = 0
                rating_count = 0
            try:
                comments_res = requests.get(f"{COLLAB_BASE_URL}/projects/{project_id}/comments")
                comments_data = comments_res.json()
                comments_count = len(comments_data.get("comments", []))
            except requests.RequestException:
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