
from typing import Optional
from pydantic import BaseModel, EmailStr


class CredentialsSchema(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    name: str
    family_name: str
    role: str
    bio: Optional[str] = None
    figma_client_id: Optional[str] = None
    figma_client_secret: Optional[str] = None
    avatar_url: Optional[str] = None