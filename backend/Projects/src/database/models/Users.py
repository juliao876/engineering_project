from sqlmodel import Field
from typing import Optional
from .BaseSQL import BaseSQL

class Users(BaseSQL, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, nullable=False, index=True)
    password: str = Field(nullable=False)
    name: str = Field(nullable=False)
    family_name: str = Field(nullable=False)
    email: str = Field(unique=True, nullable=False, index=True)
    role: str = Field(default="User", nullable=False)
