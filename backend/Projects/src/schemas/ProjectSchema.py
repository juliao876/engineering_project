from pydantic import BaseModel, Field
from typing import Optional

class ProjectSchema(BaseModel):
    title: Optional[str]
    description: Optional[str]
    contents: Optional[str]
    figma_link: Optional[str]
    is_public: Optional[bool]

    class Config:
        orm_mode = True

class ResponseModel(ProjectSchema):
    project_id: int
    user_id: int