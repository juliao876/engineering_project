from fastapi import APIRouter
from src.routers.v1.analysis_router import analysis_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(analysis_router, tags=["Projects"])

