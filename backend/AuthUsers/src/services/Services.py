from fastapi import HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from starlette import status

from src.schemas.LoginSchema import LoginSchema
from src.schemas.RegisterSchema import RegisterSchema
from src.database.models.Users import Users
from src.security.JWT import create_jwt_token
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

    def login_user(self, login_schema: LoginSchema, response: Response):
        login_data = login_schema.login
        user = None
        if "@" in login_data:
            user = self.db.query(Users).filter(Users.email == login_data).first()
        elif login_data:
            user = self.db.query(Users).filter(Users.username == login_data).first()
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username or email is required",
            )
        if not user or not password_verify(login_schema.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Insufficient credentials",
            )
        token = create_jwt_token({"sub": str(user.id)})
        response.set_cookie(key="token", value=token, httponly=True, secure=True, samesite="Lax")

        return {"message": "Successfully logged in", "user": user.username}
