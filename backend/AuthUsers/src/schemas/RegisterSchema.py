from pydantic import BaseModel
from typing import Optional, List
from sqlmodel import Field

class RegisterSchema(BaseModel):
    name: str = Field(nullable=False)
    family_name: str = Field(nullable=False)
    username: str = Field(nullable=False)
    email: str = Field(nullable=False)
    password: str = Field(nullable=False)
