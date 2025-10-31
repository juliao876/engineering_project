from fastapi import APIRouter
from src.routers.v1.projects_router import projects_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(projects_router, tags=["Projects"])

