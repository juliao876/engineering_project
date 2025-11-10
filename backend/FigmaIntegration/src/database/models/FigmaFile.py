from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timedelta

class FigmaFile(SQLModel, table=True):
    __tablename__ = "figmafiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(nullable=False)
    access_token: str = Field(nullable=False)
    refresh_token: Optional[str] = None
    expires_at: datetime = Field(nullable=False)
