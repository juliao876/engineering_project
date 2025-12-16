import os

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.middleware.cors import CORSMiddleware

from sqlalchemy import inspect, text

from .global_settings import APP_NAME, APP_DESCRIPTION, APP_VERSION
from .routers.api_router import api_router
from .database.db_connection import engine
from sqlmodel import SQLModel


def _ensure_optional_columns():
    inspector = inspect(engine)
    if "notifications" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("notifications")}

    alter_statements = []

    if "read_at" not in columns:
        alter_statements.append("ALTER TABLE notifications ADD COLUMN read_at TIMESTAMP")

    if "actor_id" not in columns:
        alter_statements.append("ALTER TABLE notifications ADD COLUMN actor_id INTEGER")

    if "actor_username" not in columns:
        alter_statements.append("ALTER TABLE notifications ADD COLUMN actor_username VARCHAR(255)")

    if not alter_statements:
        return

    with engine.begin() as connection:
        for statement in alter_statements:
            connection.execute(text(statement))


def _get_cors_origins():
    raw_origins = os.getenv("CORS_ORIGINS")
    if raw_origins:
        origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    else:
        origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

    return origins

def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_NAME,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
        docs_url=None,
        redoc_url=None,
    )

    _ensure_optional_columns()
    SQLModel.metadata.create_all(engine)

    cors_origins = _get_cors_origins()
    allow_credentials = cors_origins != ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=allow_credentials,
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