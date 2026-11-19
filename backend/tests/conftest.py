import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.deps import get_repository
from app.main import create_app
from app.repository import ApplicationFilter, AuthUser

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"0" * 64
PDF = b"%PDF-1.7\n" + b"0" * 64


class FakeRepo:
    def __init__(self) -> None:
        self.users: dict[str, AuthUser] = {}
        self.profiles: dict[str, dict] = {}
        self.applications: dict[str, dict] = {}
        self.kyc: dict[str, dict] = {}
        self.events: list[dict] = []
        self.files: dict[str, bytes] = {}
        self.issued: list[str] = []
        self.fail_create = False

    # helpers
    def add_user(self, token: str, role: str = "applicant", verified: bool = True, **geo) -> str:
        uid = str(uuid.uuid4())
        self.users[token] = AuthUser(id=uid, email=f"{token}@example.org", email_verified=verified)
        self.profiles[uid] = {"id": uid, "email": f"{token}@example.org", "role": role, **geo}
        return uid

    # protocol
    def get_auth_user(self, token: str) -> AuthUser | None:
        return self.users.get(token)

    def get_profile(self, user_id: str) -> dict | None:
        return self.profiles.get(user_id)

    def get_application_for_user(self, user_id: str) -> dict | None:
        return next((a for a in self.applications.values() if a["user_id"] == user_id), None)

    def get_application(self, application_id: str) -> dict | None:
        return self.applications.get(application_id)

    def create_application(self, record: dict, kyc: dict) -> dict:
        if self.fail_create:
            raise RuntimeError("db down")
        now = datetime.now(UTC).isoformat()
        rec = {
            **record,
            "id": str(uuid.uuid4()),
            "feedback": None,
            "created_at": now,
            "updated_at": now,
        }
        self.applications[rec["id"]] = rec
        self.kyc[rec["id"]] = kyc
        return rec

    def list_applications(self, f: ApplicationFilter) -> tuple[list[dict], int]:
        rows = [
            a
            for a in self.applications.values()
            if all(
                not getattr(f, k) or a[k] == getattr(f, k)
                for k in ("state", "lga", "ward", "stage")
            )
            and (not f.search or f.search.lower() in (a["full_name"] + a["reference"]).lower())
        ]
        return rows[f.offset : f.offset + f.limit], len(rows)

    def update_application(self, application_id: str, values: dict) -> None:
        self.applications[application_id].update(values)

    def add_event(self, event: dict) -> None:
        self.events.append(event)

    def list_events(self, application_id: str) -> list[dict]:
        return [
            {k: e.get(k) for k in ("stage", "action", "note", "created_at")}
            for e in self.events
            if e["application_id"] == application_id and e.get("visible_to_applicant")
        ]

    def get_kyc(self, application_id: str) -> dict | None:
        return self.kyc.get(application_id)

    def create_signed_upload(self, path: str) -> dict[str, str]:
        self.issued.append(path)
        return {"token": "tok-" + path, "signed_url": f"https://storage.example/{path}?token=t"}

    def download_file(self, path: str) -> bytes | None:
        return self.files.get(path)

    # simulate the browser uploading straight to storage
    def browser_upload(self, path: str, data: bytes) -> None:
        self.files[path] = data

    def delete_files(self, paths: list[str]) -> None:
        for p in paths:
            self.files.pop(p, None)

    def signed_url(self, path: str, expires_in: int) -> str:
        return f"https://signed.example/{path}?ttl={expires_in}"


@pytest.fixture
def repo() -> FakeRepo:
    return FakeRepo()


@pytest.fixture
def settings() -> Settings:
    return Settings(
        supabase_url="https://x.supabase.co",
        supabase_service_role_key="k",
        require_email_verification=True,
    )


@pytest.fixture
def client(repo: FakeRepo, settings: Settings) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_repository] = lambda: repo
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def valid_details(**overrides: Any) -> dict[str, Any]:
    base = {
        "full_name": "Aisha Bello",
        "gender": "Female",
        "date_of_birth": "1998-04-12",
        "phone": "+2348012345678",
        "address": "12 Ahmadu Bello Way",
        "state": "Kano",
        "lga": "Nassarawa",
        "ward": "Gama",
        "education": "HND / Bachelor’s Degree",
        "occupation": "Self-employed / Business Owner",
        "sector": "Agriculture & Agribusiness",
        "has_business": True,
        "business_idea": " ".join(["word"] * 35),
        "motivation": "I want to grow my agribusiness and reach export markets.",
        "referral_source": "Friend / Family",
        "identification_type": "NIN",
        "identification_number": "12345678901",
    }
    base.update(overrides)
    return base


def declared(
    identity_type: str = "application/pdf", photo_type: str = "image/jpeg", size: int = 1000
) -> dict:
    return {
        "identity_document": {"content_type": identity_type, "size": size},
        "passport_photograph": {"content_type": photo_type, "size": size},
    }


def apply(
    client,
    repo,
    token="alice",
    details=None,
    identity: bytes = PDF,
    photo: bytes = JPEG,
    identity_type="application/pdf",
    photo_type="image/jpeg",
):
    """Run the full browser flow: get upload URLs, upload to storage, submit."""
    start = client.post(
        "/api/applications/uploads", headers=auth(token), json=declared(identity_type, photo_type)
    )
    if start.status_code != 200:
        return start
    body = start.json()
    up = body["uploads"]
    repo.browser_upload(up["identity_document"]["path"], identity)
    repo.browser_upload(up["passport_photograph"]["path"], photo)
    return client.post(
        "/api/applications",
        headers=auth(token),
        json={
            "reference": body["reference"],
            "details": details or valid_details(),
            "identity_document_path": up["identity_document"]["path"],
            "passport_photograph_path": up["passport_photograph"]["path"],
        },
    )
