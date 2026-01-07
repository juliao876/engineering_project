import sys
from pathlib import Path

import pytest

pytest.importorskip("sqlmodel")

from sqlmodel import Session, SQLModel, create_engine

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.database.models.Project import Project  # noqa: E402
from src.services.Services import Services  # noqa: E402


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_get_project_preview_prefers_explicit_preview(session):
    project = Project(
        title="Previewed",
        description="Has preview",
        user_id=1,
        is_public=True,
        preview_url="https://cdn.example.com/preview.png",
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    services = Services(session)

    assert services.get_project_preview(project) == "https://cdn.example.com/preview.png"


def test_get_project_preview_builds_from_content_type(session):
    project = Project(
        title="With upload",
        description="Uses upload fallback",
        user_id=1,
        is_public=True,
        contents="upload",
        content_type="uploads/preview.png",
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    services = Services(session)
    preview = services.get_project_preview(project)

    assert preview.startswith("http://localhost:6701")
    assert preview.endswith("uploads/preview.png")


def test_list_public_projects_enriches_rating(monkeypatch, session):
    project = Project(
        title="Public project",
        description="Visible to everyone",
        user_id=1,
        is_public=True,
        contents="file",
        content_type="text",
    )
    session.add(project)
    session.commit()

    services = Services(session)

    monkeypatch.setattr(services, "_fetch_rating_summary", lambda project_id: {"average_rating": 4.5, "rating_count": 2})

    feed = services.list_public_projects()

    assert len(feed) == 1
    assert feed[0]["average_rating"] == 4.5
    assert feed[0]["rating_count"] == 2
    assert feed[0]["project_id"] == project.project_id