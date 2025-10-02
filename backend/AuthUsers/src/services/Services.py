from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from starlette import status
import re

from src.schemas.RegisterSchema import RegisterSchema
from src.database.models.Users import Users
from src.security.PasswordHash import password_verify, hash_password


class Services:
    def __init__(self, db: Session):
        self.db = db

    def register_new_user(self, register_schema: RegisterSchema):
        hash = hash_password(register_schema.password)
        user = Users(username=register_schema.username,
                     email=register_schema.email,
                     password=hash,
                     name=register_schema.name,
                     family_name=register_schema.family_name
                     )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user