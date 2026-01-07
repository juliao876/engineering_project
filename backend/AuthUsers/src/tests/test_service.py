import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlmodel")

from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.database.models.Users import Users  # noqa: E402
from src.schemas.UpdateSchema import UpdateSchema  # noqa: E402
from src.security.PasswordHash import hash_password, password_verify  # noqa: E402
from src.services.Services import Services  # noqa: E402


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_update_user_password_flow(session):
    user = Users(
        username="tester",
        email="tester@example.com",
        password=hash_password("old-pass"),
        name="Test",
        family_name="User",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    services = Services(session)
    updated = services.update_user(
        {"sub": str(user.id)},
        UpdateSchema(current_password="old-pass", new_password="new-pass", bio="Updated bio"),
    )

    stored = session.get(Users, user.id)
    assert password_verify("new-pass", stored.password)
    assert updated.bio == "Updated bio"
    assert updated.username == "tester"


def test_update_user_rejects_invalid_current_password(session):
    user = Users(
        username="tester",
        email="tester@example.com",
        password=hash_password("correct-pass"),
        name="Test",
        family_name="User",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    services = Services(session)

    with pytest.raises(HTTPException) as exc:
        services.update_user(
            {"sub": str(user.id)},
            UpdateSchema(current_password="wrong-pass", new_password="new-pass"),
        )

    assert exc.value.status_code == 401
    assert password_verify("correct-pass", session.get(Users, user.id).password)


def test_build_public_url_handles_relative_and_absolute(session):
    services = Services(session)

    assert services.build_public_url(None) is None
    assert services.build_public_url("https://example.com/image.png") == "https://example.com/image.png"
    assert services.build_public_url("uploads/avatar.png").endswith("/uploads/avatar.png")