from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session
from src.schemas.FollowerSchema import FollowerSchema
from src.security.auth_utils import get_user_data
from src.database.db_connection import get_db
from src.services.Services import Services



discover_followers_router = APIRouter(prefix="/DF", tags=["Discover & Followers"])


@cbv(discover_followers_router)
class DiscoverFollowers:
    db: Session = Depends(get_db)

    @discover_followers_router.post("/users/follow")
    def follow_user(self, payload: FollowerSchema, request: Request):
        token = request.cookies.get("token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.lower().startswith("bearer "):
                token = auth_header.split(" ", 1)[1]

        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_data = get_user_data(token)
        user_id = user_data.get("id") or user_data.get("user_id")

        service = Services(self.db)
        result = service.follow_user(user_id, payload, token=token, follower_profile=user_data)

        return result

    @discover_followers_router.get("/users/{username}/followers")
    def get_followers(self, username: str, request: Request):

        token = request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        service = Services(self.db)
        return service.get_followers(username)

    @discover_followers_router.get("/users/{username}/following")
    def get_following(self, username: str, request: Request):

        token = request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        service = Services(self.db)
        return service.get_following(username)

    @discover_followers_router.get("/users/{username}/follow-status")
    def get_follow_status(self, username: str, request: Request):

        token = request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_data = get_user_data(token)
        user_id = user_data.get("id") or user_data.get("user_id")

        service = Services(self.db)
        return service.get_follow_status(user_id, username)

    @discover_followers_router.get("/feed/following")
    def get_following_feed(self, request: Request):

        token = request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_data = get_user_data(token)
        user_id = user_data.get("id") or user_data.get("user_id")

        service = Services(self.db)
        return service.get_following_feed(user_id)

    @discover_followers_router.get("/discover")
    def discover(self):

        service = Services(self.db)
        return service.get_discover_feed()