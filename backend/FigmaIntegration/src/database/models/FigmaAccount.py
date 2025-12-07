from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class FigmaAccount(SQLModel, table=True):
    __tablename__ = "figma_accounts"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(nullable=False, index=True)
    access_token: str = Field(nullable=False)
    refresh_token: Optional[str] = Field(default=None, nullable=True)
    expires_in: Optional[int] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)