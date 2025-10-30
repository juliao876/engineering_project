from fastapi import HTTPException, Response
from pip._internal.network.auth import Credentials
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from starlette import status

from src.schemas.LoginSchema import LoginSchema
from src.schemas.RegisterSchema import RegisterSchema
from src.schemas.CredentialsSchema import CredentialsSchema
from src.schemas.UpdateSchema import UpdateSchema
from src.database.models.Users import Users
from src.security.JWT import create_jwt_token
from src.security.PasswordHash import password_verify, hash_password
from src.schemas.RoleSchema import RoleSchema


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

    def get_user_by_id(self, user_id: int):
        user = self.db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        credentials = CredentialsSchema(username=user.username, email=user.email, name=user.name, family_name=user.family_name, role=user.role)
        return credentials

    def update_user(self, payload, update_input: UpdateSchema):
        user_id = payload["sub"]
        user = self.db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        # if "name" in update_input:
        #     user.name = update_input["name"]
        # if "family_name" in update_input:
        #     user.family_name = update_input["family_name"]
        # if "password" in update_input:
        #     user.password = update_input["password"]
        #     #user.set_password(update_input["password"])
        update_data = update_input.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user, {"message": "Profile updated successfully"}

    def update_user_role(self, user_id: int, role_data: RoleSchema):
        user = self.db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.role = role_data.role
        self.db.commit()
        self.db.refresh(user)

        return {"username": user.username, "new_role": user.role, "message": "Role updated successfully"}







