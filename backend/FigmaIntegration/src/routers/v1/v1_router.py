from fastapi import APIRouter
from src.routers.v1.figma_router import figma_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(figma_router, tags=["Figma Integration"])

