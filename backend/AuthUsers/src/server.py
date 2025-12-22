from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from sqlmodel import SQLModel

from .database.db_connection import engine
from .global_settings import APP_NAME, APP_DESCRIPTION, APP_VERSION
from .routers.api_router import api_router

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"


def _ensure_new_columns():
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("users")}

    # Used for migration of previous database to add new columns
    alter_statements = []
    if "bio" not in columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN bio VARCHAR")
    if "figma_client_id" not in columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN figma_client_id VARCHAR")
    if "figma_client_secret" not in columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN figma_client_secret VARCHAR")
    if "avatar_url" not in columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN avatar_url VARCHAR")

    if alter_statements:
        with engine.begin() as connection:
            for statement in alter_statements:
                connection.execute(text(statement))


def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_NAME,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
        docs_url=None,
        redoc_url=None,
    )

    _ensure_new_columns()
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