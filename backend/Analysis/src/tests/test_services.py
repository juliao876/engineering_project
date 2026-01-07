import sys
from pathlib import Path

import pytest
pytest.importorskip("sqlmodel")

from sqlmodel import Session, SQLModel, create_engine

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.database.models.Analysis import Analysis  # noqa: E402
from src.services.Services import Services  # noqa: E402


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_figma_color_to_rgb():
    services = Services(db=None)
    rgb = services.figma_color_to_rgb({"r": 0.5, "g": 0.25, "b": 0.0})
    assert rgb == [127, 63, 0]


def test_run_analysis_persists_results(session):
    services = Services(session)
    figma_data = {
        "document": {
            "children": [
                {
                    "id": "button-1",
                    "type": "FRAME",
                    "name": "Primary Button",
                    "children": [
                        {"type": "RECTANGLE", "absoluteBoundingBox": {"width": 72, "height": 60, "x": 0, "y": 0}},
                        {"type": "TEXT", "style": {"fontSize": 16, "fontWeight": 700}, "fills": [{"color": {"r": 0, "g": 0, "b": 0}}]},
                    ],
                    "absoluteBoundingBox": {"width": 72, "height": 60, "x": 0, "y": 0},
                },
                {
                    "id": "label-1",
                    "type": "TEXT",
                    "style": {"fontSize": 12},
                    "fills": [{"color": {"r": 1, "g": 1, "b": 1}}],
                    "parent": {"fills": [{"color": {"r": 1, "g": 1, "b": 1}}]},
                },
            ]
        }
    }

    result = services.run_analysis(project_id=5, device="desktop", figma_data=figma_data)

    assert result["project_id"] == 5
    assert "summary" in result and result["summary"]
    assert "metrics" in result and result["metrics"]["button_size"]["min_detected"] is not None

    stored = session.query(Analysis).first()
    assert stored is not None
    assert str(stored.project_id) == "5"