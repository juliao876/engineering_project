from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from pathlib import Path

from .global_settings import APP_NAME, APP_DESCRIPTION, APP_VERSION
from .routers.api_router import api_router
from .database.db_connection import engine
from sqlmodel import SQLModel

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"


def _ensure_preview_column():
    inspector = inspect(engine)
    if "projects" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("projects")}
    if "preview_url" in columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE projects ADD COLUMN preview_url VARCHAR"))


def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_NAME,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
        docs_url=None,
        redoc_url=None,
    )

    _ensure_preview_column()
    SQLModel.metadata.create_all(engine)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR, check_dir=False), name="uploads")

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
