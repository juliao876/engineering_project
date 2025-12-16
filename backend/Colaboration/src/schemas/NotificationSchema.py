from datetime import datetime
from pydantic import BaseModel


class NotificationSchema(BaseModel):
    id: int
    user_id: int
    type: str
    message: str
    is_read: bool
    created_at: datetime
    read_at: datetime | None = None
    project_id: int | None = None
    actor_id: int | None = None
    actor_username: str | None = None


class NotificationCreateSchema(BaseModel):
    user_id: int
    type: str
    message: str
    project_id: int | None = None
    actor_id: int | None = None
    actor_username: str | None = None