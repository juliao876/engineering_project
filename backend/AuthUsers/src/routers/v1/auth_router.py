import jwt
from fastapi import APIRouter, Depends, Response, Request, HTTPException, UploadFile, File
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from src.database.db_connection import get_db
from src.schemas.LoginSchema import LoginSchema
from src.schemas.RegisterSchema import RegisterSchema
from src.schemas.RoleSchema import RoleSchema
from src.schemas.UpdateSchema import UpdateSchema
from src.security.JWT import verify_jwt_token
from src.services.Services import Services


auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@cbv(auth_router)
class Auth:
    @auth_router.post("/register")
    def register(self, register_data: RegisterSchema, db: Session = Depends(get_db)):
        auth_service = Services(db)
        user = auth_service.register_new_user(register_data)
        return {"message": "Successfully registered", "user": user.username}

    @auth_router.post("/login")
    def login(self, login_data: LoginSchema, response: Response, db: Session = Depends(get_db)):
        auth_service = Services(db)
        result = auth_service.login_user(login_data, response=response)
        return result

    @auth_router.post("/logout")
    def logout(self, response: Response, db: Session = Depends(get_db)):
        auth_service = Services(db)
        response.delete_cookie(key="token", httponly=True, secure=True, samesite="Lax")
        return auth_service, {"message": "Successfully logged out"}

    @auth_router.post("/role")
    def role(self, request: Request, role_data: RoleSchema, db: Session = Depends(get_db)):
        token = request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Invalid token")
        payload = verify_jwt_token(token)
        user_id = payload.get("sub")
        auth_service = Services(db)
        return auth_service.update_user_role(user_id, role_data)

    @auth_router.get("/me")
    def me(self, request: Request, db: Session = Depends(get_db)):
        token = request.cookies.get("token")

        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            raise HTTPException(status_code=401, detail="Invalid token")

        payload = verify_jwt_token(token)
        user_id = int(payload.get("sub"))
        auth_service = Services(db)
        user_data = auth_service.get_user_by_id(user_id)
        return user_data

    @auth_router.patch("/me")
    def update_me(self, request: Request, update_input: UpdateSchema, db: Session = Depends(get_db)):
        token = request.cookies.get("token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        payload = verify_jwt_token(token)
        auth_service = Services(db)
        return auth_service.update_user(payload, update_input)

    @auth_router.post("/me/avatar")
    def upload_avatar(
        self,
        request: Request,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
    ):
        token = request.cookies.get("token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        payload = verify_jwt_token(token)
        auth_service = Services(db)
        return auth_service.update_avatar(int(payload.get("sub")), file)

    @auth_router.get("/projects")
    def get_my_projects(self, request: Request, db: Session = Depends(get_db)):
        token = request.cookies.get("token")

        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            raise HTTPException(status_code=401, detail="Token not provided")

        try:
            payload = verify_jwt_token(token)
            user_id = int(payload["sub"])
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

        service = Services(db)
        titles = service.get_user_projects_tittle(user_id)
        return {"projects": titles}

    @auth_router.get("/user/{username}")
    def get_user_by_username(self, username: str, db: Session = Depends(get_db)):
        auth_service = Services(db)
        user = auth_service.get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "name": user.name,
            "family_name": user.family_name,
            "role": user.role,
            "bio": user.bio,
            "avatar_url": auth_service.build_public_url(user.avatar_url),
        }

    @auth_router.get("/user/id/{user_id}")
    def get_user_by_id(self, user_id: int, db: Session = Depends(get_db)):
        auth_service = Services(db)
        user = auth_service.get_user_by_id(user_id)
        return user

    @auth_router.get("/search")
    def search_users(self, query: str, db: Session = Depends(get_db)):
        auth_service = Services(db)
        results = auth_service.search_users(query)
        return {"results": results}