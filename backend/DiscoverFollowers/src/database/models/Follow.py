from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Follow(SQLModel, table=True):
    __tablename__ = "follows"

    id: Optional[int] = Field(default=None, primary_key=True)

    follower_id: int = Field(index=True)
    following_id: int = Field(index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
