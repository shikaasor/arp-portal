"""Guards for the Vercel monorepo routing contract.

The frontend proxies `/api/*` to this service, so every public route must live under `/api`.
(The frontend has a matching check that it never defines its own routes under `/api`.)
"""

import importlib
import sys

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import API_PREFIX, create_app

# Allowed outside the prefix: direct-to-host health checks only.
ALLOWED_OUTSIDE_PREFIX = {"/health"}


def test_all_routes_are_under_api_prefix():
    app = create_app()
    paths = {r.path for r in app.routes if isinstance(r, APIRoute)}
    outside = {p for p in paths if not p.startswith(API_PREFIX + "/")} - ALLOWED_OUTSIDE_PREFIX
    assert not outside, (
        f"Routes outside {API_PREFIX}/ would be unreachable via the frontend: {outside}"
    )


def test_docs_are_reachable_through_the_proxy():
    client = TestClient(create_app())
    assert client.get("/api/openapi.json").status_code == 200
    assert client.get("/api/docs").status_code == 200
    assert client.get("/docs").status_code == 404


def test_vercel_entrypoint_exposes_the_app():
    sys.modules.pop("api.index", None)
    module = importlib.import_module("api.index")
    assert TestClient(module.app).get("/api/health").json()["status"] == "ok"
