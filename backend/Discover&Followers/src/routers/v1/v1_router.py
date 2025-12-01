from fastapi import APIRouter
from src.routers.v1.discover_followers_router import discover_followers_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(discover_followers_router, tags=["Discover & Followers"])

