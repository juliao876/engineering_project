from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: Optional[int] = Field(default=None, primary_key=True)

    project_id: int = Field(index=True)
    user_id: int = Field(index=True)

    parent_id: Optional[int] = Field(default=None, index=True)  # reply -> comment.id
    content: str = Field(nullable=False)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    is_deleted: bool = Field(default=False)
