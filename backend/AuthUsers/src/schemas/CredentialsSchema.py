from typing import Optional, Union
from pydantic import BaseModel, EmailStr

class CredentialsSchema(BaseModel):
    username: str
    email: EmailStr
    name: str
    family_name: str
    role: str