from pydantic import BaseModel, Field
from typing import Optional

class ProjectSchema(BaseModel):
    title: Optional[str]
    description: Optional[str]
    contents: Optional[str]
    figma_link: Optional[str]
    is_public: Optional[bool]
    content_type: Optional[str]

    class Config:
        from_attributes = True

class ResponseModel(ProjectSchema):
    project_id: int
    user_id: int