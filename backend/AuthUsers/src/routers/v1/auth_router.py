from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv
from src.schemas.RegisterSchema import RegisterSchema
from src.database.db_connection import get_db
from src.services.Services import Services
from sqlalchemy.orm import Session

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

@cbv(auth_router)
class Auth:

    @auth_router.post("/register")
    def register(self, register_data: RegisterSchema, db: Session = Depends(get_db)):
        auth_service = Services(db)
        auth_service.register_new_user(register_data)
        return auth_service