from pydantic import BaseModel

class FollowerSchema(BaseModel):
    following_id: int
    message: str | None = None