from pydantic import BaseModel, Field
from typing import Optional

class ProjectSchema(BaseModel):
    user_id: int = Field(foreign_key="users.id", nullable=False)
    title: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    contents: Optional[str] = Field(default=None)
    figma_link: Optional[str] = Field(default=None)
    is_public: Optional[bool] = Field(default=False)
