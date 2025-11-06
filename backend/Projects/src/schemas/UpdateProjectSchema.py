from pydantic import BaseModel
from typing import Optional

class ProjectUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    figma_link: Optional[str] = None
    contents: Optional[str] = None
    is_public: Optional[bool] = None
