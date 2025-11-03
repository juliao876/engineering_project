from fastapi import APIRouter
from src.routers.v1.project_router import project_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(project_router, tags=["Projects"])

