import sys
from pathlib import Path

import pytest

pytest.importorskip("requests")

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.services.Services import Services  # noqa: E402


def test_extract_file_key_supports_standard_urls():
    services = Services(db=None)
    key = services.extract_file_key("https://www.figma.com/file/Abc123XYZ/design-name")
    assert key == "Abc123XYZ"


def test_build_authorize_url_uses_explicit_params(monkeypatch):
    monkeypatch.delenv("FIGMA_CLIENT_ID", raising=False)
    services = Services(db=None)

    url = services.build_authorize_url(
        state="state123",
        client_id="client-id",
        redirect_uri="http://example.com/callback",
    )

    assert url.startswith("https://www.figma.com/oauth?")
    assert "client_id=client-id" in url
    assert "state=state123" in url
    assert "redirect_uri=http%3A%2F%2Fexample.com%2Fcallback" in url


def test_get_preview_image_returns_url(monkeypatch):
    services = Services(db=None)

    class DummyResponse:
        status_code = 200

        def json(self):
            return {"images": {"12:34": "http://image.cdn/preview.png"}}

    def fake_get(url, headers, timeout):
        return DummyResponse()

    monkeypatch.setattr("src.services.Services.requests.get", fake_get)

    preview = services.get_preview_image("file-key", "12:34", "token")

    assert preview == "http://image.cdn/preview.png"