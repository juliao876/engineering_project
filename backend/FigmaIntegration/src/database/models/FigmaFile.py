from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class FigmaFile(SQLModel, table=True):
    __tablename__ = "figma_files"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(nullable=False)
    project_id: Optional[int] = Field(default=None, nullable=True)
    file_key: Optional[str] = Field(default=None, nullable=True)
    name: Optional[str] = Field(default=None, nullable=True)
    thumbnail_url: Optional[str] = Field(default=None, nullable=True)
    last_modified: Optional[datetime] = Field(default=None, nullable=True)

    access_token: str = Field(nullable=False)
    refresh_token: Optional[str] = Field(default=None)
    expires_at: datetime = Field(nullable=False)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
