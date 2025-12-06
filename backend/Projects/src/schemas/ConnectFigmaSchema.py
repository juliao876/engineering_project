from typing import Optional

from pydantic import BaseModel


class ConnectFigmaSchema(BaseModel):
    figma_link: str
    content_type: Optional[str] = "figma"
    title: Optional[str] = None
    description: Optional[str] = None
    preview_url: Optional[str] = None