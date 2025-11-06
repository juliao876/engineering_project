from typing import Optional, Union
from pydantic import BaseModel, EmailStr

class CredentialsSchema(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    name: str
    family_name: str
    role: str