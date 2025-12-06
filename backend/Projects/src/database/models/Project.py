from sqlmodel import Field, SQLModel
from typing import Optional

class Project(SQLModel, table=True):
    __tablename__ = "projects"

    project_id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(nullable=False)
    description: str = Field(nullable=False)
    is_public: bool = Field(default=False, nullable=False)
    user_id: int = Field(nullable=False)
    contents: Optional[str] = Field(default=None, nullable=True)
    figma_link: Optional[str] = Field(default=None)
    content_type: Optional[str] = Field(default=None, nullable=True)
    preview_url: Optional[str] = Field(default=None, nullable=True)

