import sys
from pathlib import Path

import pytest

pytest.importorskip("sqlmodel")

from sqlmodel import Session, SQLModel, create_engine

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.database.models.Follow import Follow  # noqa: E402
from src.schemas.FollowerSchema import FollowerSchema  # noqa: E402
from src.services.Services import Services  # noqa: E402


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_follow_user_toggles_follow_state(monkeypatch, session):
    services = Services(session)
    monkeypatch.setattr(services, "_send_notification", lambda *args, **kwargs: None)

    follow_payload = FollowerSchema(following_id=2)

    follow_result = services.follow_user(
        follower_id=1,
        data=follow_payload,
        follower_profile={"username": "bob", "user_id": 1},
    )
    assert follow_result["message"] == "Followed"
    assert session.query(Follow).count() == 1

    unfollow_result = services.follow_user(
        follower_id=1,
        data=follow_payload,
        follower_profile={"username": "bob", "user_id": 1},
    )
    assert unfollow_result["message"] == "Unfollowed"
    assert session.query(Follow).count() == 0