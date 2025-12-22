import os
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import HTTPException, Response, UploadFile
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette import status

from src.schemas.LoginSchema import LoginSchema
from src.schemas.RegisterSchema import RegisterSchema
from src.schemas.CredentialsSchema import CredentialsSchema
from src.schemas.UpdateSchema import UpdateSchema
from src.database.models.Users import Users
from src.security.JWT import create_jwt_token
from src.security.PasswordHash import password_verify, hash_password
from src.schemas.RoleSchema import RoleSchema

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:6700")
PROJECTS_SERVICE_URL = os.getenv("PROJECTS_SERVICE_URL", "http://project-service:6701")
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"


class Services:
    def __init__(self, db: Session):
        self.db = db

    def build_public_url(self, stored_path: str | None) -> str | None:
        if not stored_path:
            return None
        if stored_path.startswith("http://") or stored_path.startswith("https://"):
            return stored_path
        normalized = stored_path.lstrip("/")
        return f"{AUTH_SERVICE_URL.rstrip('/')}/{normalized}"

    def save_uploaded_file(self, file: UploadFile) -> str:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid4().hex}_{file.filename}"
        destination = UPLOAD_DIR / filename
        with destination.open("wb") as buffer:
            buffer.write(file.file.read())
        return str(Path("uploads") / filename)

    def serialize_user(self, user: Users) -> CredentialsSchema:
        return CredentialsSchema(
            user_id=user.id,
            username=user.username,
            email=user.email,
            name=user.name,
            family_name=user.family_name,
            role=user.role,
            bio=user.bio,
            figma_client_id=user.figma_client_id,
            figma_client_secret=user.figma_client_secret,
            avatar_url=self.build_public_url(user.avatar_url),
        )

    def register_new_user(self, register_schema: RegisterSchema):
        hash = hash_password(register_schema.password)
        user = Users(
            username=register_schema.username,
            email=register_schema.email,
            password=hash,
            name=register_schema.name,
            family_name=register_schema.family_name,
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

        return {"message": "Successfully logged in", "user": user.username, "token": token}

    def get_user_by_id(self, user_id: int):
        user = self.db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return self.serialize_user(user)

    def get_all_users(self):
        users = self.db.query(Users).all()
        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "family_name": user.family_name,
                "bio": user.bio,
                "avatar_url": self.build_public_url(user.avatar_url),
            }
            for user in users
        ]

    def update_user(self, payload, update_input: UpdateSchema):
        user_id = int(payload["sub"])
        user = self.db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        update_data = update_input.dict(exclude_unset=True)
        new_password = update_data.pop("new_password", None)
        current_password = update_data.pop("current_password", None)

        if new_password:
            if not current_password or not password_verify(current_password, user.password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Current password is incorrect",
                )
            user.password = hash_password(new_password)

        for key, value in update_data.items():
            setattr(user, key, value)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            message = "Unable to update profile"
            if "ix_users_username" in str(exc.orig):
                message = "Username already in use"
            elif "ix_users_email" in str(exc.orig):
                message = "Email already in use"
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

        self.db.refresh(user)
        return self.serialize_user(user)

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
                f"{PROJECTS_SERVICE_URL}/projects/titles",
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

    def search_users(self, query: str):
        if not query:
            return []

        pattern = f"%{query}%"

        users = (
            self.db.query(Users)
            .filter(
                or_(
                    Users.username.ilike(pattern),
                    Users.name.ilike(pattern),
                    Users.family_name.ilike(pattern),
                )
            )
            .limit(25)
            .all()
        )

        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "family_name": user.family_name,
                "bio": user.bio,
                "avatar_url": self.build_public_url(user.avatar_url),
            }
            for user in users
        ]

    def update_avatar(self, user_id: int, upload: UploadFile):
        if not upload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")

        user = self.db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        stored_path = self.save_uploaded_file(upload)
        user.avatar_url = stored_path
        self.db.commit()
        self.db.refresh(user)

        return self.serialize_user(user)