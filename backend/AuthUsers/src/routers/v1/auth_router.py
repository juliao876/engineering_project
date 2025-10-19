from fastapi import APIRouter, Depends, Response
from fastapi_utils.cbv import cbv
from src.schemas.RegisterSchema import RegisterSchema
from src.database.db_connection import get_db
from src.schemas.RoleSchema import RoleSchema
from src.services.Services import Services
from sqlalchemy.orm import Session
from src.schemas.LoginSchema import LoginSchema

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

@cbv(auth_router)
class Auth:

    @auth_router.post("/register")
    def register(self, register_data: RegisterSchema, db: Session = Depends(get_db)):
        auth_service = Services(db)
        auth_service.register_new_user(register_data)
        return auth_service, {"message": "Successfully registered"}
    @auth_router.post("/login")
    def login(self, login_data: LoginSchema, response:Response, db: Session = Depends(get_db)):
        auth_service = Services(db)
        user = auth_service.login_user(login_data, response = response)
        return user, {"message": "Successfully logged in"}
    @auth_router.post("/logout")
    def logout(self, response: Response, db: Session = Depends(get_db)):
        auth_service = Services(db)
        response.delete_cookie(key="token", httponly=True, secure=True, samesite="Lax")
        return auth_service, {"message": "Successfully logged out"}
    @auth_router.post("/role")
    def role(self, role: RoleSchema, db: Session = Depends(get_db)):
        auth_service = Services(db)
        return auth_service
