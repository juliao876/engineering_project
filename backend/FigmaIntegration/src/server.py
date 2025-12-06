import os

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.middleware.cors import CORSMiddleware

from .global_settings import APP_NAME, APP_DESCRIPTION, APP_VERSION
from .routers.api_router import api_router
from .database.db_connection import engine
from .database import models  # noqa: F401
from sqlmodel import SQLModel

def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_NAME,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
        docs_url=None,
        redoc_url=None,
    )

    SQLModel.metadata.create_all(engine)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv(
            "FIGMA_ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:6702",
        ).split(","),
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    @app.get("/", include_in_schema=False)
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{APP_NAME} — Swagger UI"
        )

    app.include_router(api_router)

    return app


app = create_app()