from sqlmodel import Field, Column, JSON
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
    # projects: list[int] = Field(default=None, sa_column=Column(JSON))
    role: str = Field(default="User", nullable=False)
