from typing import Optional

from pydantic import BaseModel


class UpdateSchema(BaseModel):
    name: Optional[str] = None
    family_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    figma_client_id: Optional[str] = None
    figma_client_secret: Optional[str] = None
    avatar_url: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None