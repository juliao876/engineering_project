from pydantic import BaseModel
from typing import Optional

class UpdateSchema(BaseModel):
    name: Optional[str] = None
    family_name: Optional[str] = None
    password: Optional[str] = None