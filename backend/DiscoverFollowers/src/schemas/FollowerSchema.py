from pydantic import BaseModel

class FollowerSchema(BaseModel):
    follower_id: int
    following_id: int
    message: str
