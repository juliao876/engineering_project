from typing import Literal, Optional

from pydantic import BaseModel


class ProjectSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    contents: Literal["figma", "image", "video"] | None = None
    figma_link: Optional[str] = None
    is_public: Optional[bool] = None
    content_type: Optional[str] = None

    class Config:
        from_attributes = True


class ResponseModel(ProjectSchema):
    project_id: int
    user_id: int
