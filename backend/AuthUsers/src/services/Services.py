from fastapi import HTTPException, Response

from pip._internal.network.auth import Credentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
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
import httpx


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
        try:
            self.db.commit()
            self.db.refresh(user)
        except IntegrityError as exc:
            self.db.rollback()
            message = "User already exists"
            if "ix_users_username" in str(exc.orig):
                message = "Username already in use"
            elif "ix_users_email" in str(exc.orig):
                message = "Email already in use"
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

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
        response.set_cookie(key="token", value=token, httponly=True)

        return {"message": "Successfully logged in", "user": user.username}

    def get_user_by_id(self, user_id: int):
        user = self.db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        credentials = CredentialsSchema(user_id=user.id, username=user.username, email=user.email, name=user.name, family_name=user.family_name, role=user.role)
        return credentials

    def update_user(self, payload, update_input: UpdateSchema):
        user_id = int(payload["sub"])
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

    def get_user_projects_tittle(self, user_id: int):
        user = self.db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        try:
            response = httpx.post(
                "http://127.0.0.1:6701/projects/titles",
                json=user.projects,
                headers={"Content-Type": "application/json"},
                timeout=5.0,
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.json() if response.content else "Unable to fetch projects",
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error connecting to Projects service: {e}")

    def get_user_by_username(self, username: str):
        user = self.db.query(Users).filter(Users.username == username).first()
        return user