from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(index=True)  # who receives the notification
    type: str = Field()  # "like", "comment", "reply", "follow"
    message: str = Field()

    project_id: Optional[int] = Field(default=None)
    actor_id: Optional[int] = Field(default=None)
    actor_username: Optional[str] = Field(default=None)

    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = Field(default=None, nullable=True)