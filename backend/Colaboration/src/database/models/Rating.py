from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Rating(SQLModel, table=True):
    __tablename__ = "ratings"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    user_id: int = Field(index=True)

    stars: int = Field(default=0)  # 0–5 stars

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
