from fastapi import APIRouter
from src.routers.v1.collaboration_router import collaboration_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(collaboration_router, tags=["Collaboration"])

