from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FigmaProjectSchema(BaseModel):
    file_key:str
    name:str
    thumbnail_url:Optional[str] = None
    last_modified:Optional[datetime] = None

    class Config:
        from_attributes = True

