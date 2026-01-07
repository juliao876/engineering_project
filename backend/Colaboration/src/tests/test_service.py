import sys
from pathlib import Path

import pytest

pytest.importorskip("sqlmodel")

from sqlmodel import Session, SQLModel, create_engine

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.database.models.Comment import Comment  # noqa: E402
from src.database.models.Rating import Rating  # noqa: E402
from src.schemas.CommentSchema import CommentSchema  # noqa: E402
from src.services.Services import Services  # noqa: E402


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_get_rating_returns_average_and_user_rating(session):
    session.add_all(
        [
            Rating(project_id=1, user_id=1, stars=5),
            Rating(project_id=1, user_id=2, stars=3),
        ]
    )
    session.commit()

    services = Services(session)

    result = services.get_rating(project_id=1, user_id=1)

    assert result["average"] == 4.0
    assert result["count"] == 2
    assert result["user_rating"] == 5


def test_add_comment_serializes_response(monkeypatch, session):
    services = Services(session)
    monkeypatch.setattr(services, "_notify_project_owner_about_comment", lambda *args, **kwargs: None)

    comment = services.add_comment(
        project_id=10,
        user_id=3,
        data=CommentSchema(content="Great job"),
        user_profile={"username": "alice"},
    )

    assert comment["project_id"] == 10
    assert comment["user_id"] == 3
    assert comment["content"] == "Great job"
    assert comment["replies"] == []

    stored = session.query(Comment).first()
    assert stored is not None
    assert stored.content == "Great job"