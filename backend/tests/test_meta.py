from fastapi.testclient import TestClient

from app.main import create_app


def test_health_works_without_configuration():
    res = TestClient(create_app()).get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_options_lists_states():
    res = TestClient(create_app()).get("/api/options")
    assert "Kano" in res.json()["states"]


def test_api_returns_503_when_supabase_not_configured(monkeypatch):
    from app.config import Settings, get_settings

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        supabase_url="", supabase_service_role_key=""
    )
    res = TestClient(app).get("/api/me", headers={"Authorization": "Bearer x"})
    assert res.status_code == 503
