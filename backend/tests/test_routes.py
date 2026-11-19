"""Guards for the Vercel Services routing contract.

The root `vercel.json` sends `/api/*` to this service (with the path unchanged) and everything
else to the Next.js service, so every public route must live under `/api`. (The frontend has a
matching check that it never defines its own routes under `/api`.)
"""

import importlib
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import API_PREFIX, create_app

VERCEL_JSON = Path(__file__).resolve().parents[2] / "vercel.json"

# Allowed outside the prefix: direct-to-host health checks only (Docker fallback).
ALLOWED_OUTSIDE_PREFIX = {"/health"}


def test_all_routes_are_under_api_prefix():
    app = create_app()
    paths = {r.path for r in app.routes if isinstance(r, APIRoute)}
    outside = {p for p in paths if not p.startswith(API_PREFIX + "/")} - ALLOWED_OUTSIDE_PREFIX
    assert not outside, (
        f"Routes outside {API_PREFIX}/ would be unreachable on the public domain: {outside}"
    )


def test_docs_are_reachable_through_the_proxy():
    client = TestClient(create_app())
    assert client.get("/api/openapi.json").status_code == 200
    assert client.get("/api/docs").status_code == 200
    assert client.get("/docs").status_code == 404


def _vercel_config() -> dict:
    return json.loads(VERCEL_JSON.read_text(encoding="utf-8"))


def _api_service() -> tuple[str, dict]:
    services = _vercel_config()["services"]
    backend = [(n, svc) for n, svc in services.items() if svc["root"].rstrip("/") == "backend"]
    assert len(backend) == 1, "vercel.json must declare exactly one service rooted at backend/"
    return backend[0]


def test_vercel_entrypoint_exposes_the_app():
    _, service = _api_service()
    module_name, _, attr = service["entrypoint"].partition(":")
    app = getattr(importlib.import_module(module_name), attr)
    assert isinstance(app, FastAPI)
    assert TestClient(app).get("/api/health").json()["status"] == "ok"


def test_vercel_routes_api_prefix_to_this_service_first():
    name, _ = _api_service()
    rewrites = _vercel_config()["rewrites"]
    first_api = next(i for i, r in enumerate(rewrites) if r["source"].startswith(API_PREFIX + "/"))
    assert rewrites[first_api]["destination"] == {"service": name}
    # Nothing before it may capture /api paths (e.g. the frontend catch-all).
    for earlier in rewrites[:first_api]:
        assert not earlier["source"].startswith("/("), f"{earlier} shadows {API_PREFIX}/*"
