"""Data access. Routers depend on the `Repository` protocol so tests can swap in a fake."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from supabase import Client, create_client

from .config import Settings
from .geo import geo_key

APPLICATION_COLUMNS = (
    "id,reference,user_id,full_name,email,phone,gender,date_of_birth,address,state,lga,ward,"
    "education,occupation,sector,has_business,business_idea,motivation,referral_source,"
    "stage,feedback,returns_to_stage,applicant_response,created_at,updated_at"
)


class DuplicateIdentificationError(Exception):
    """Another application already uses this identification number."""


@dataclass
class AuthUser:
    id: str
    email: str | None
    email_verified: bool


@dataclass
class ApplicationFilter:
    state: str | None = None
    lga: str | None = None
    ward: str | None = None
    stage: str | None = None
    search: str | None = None
    limit: int = 50
    offset: int = 0


class Repository(Protocol):
    def get_auth_user(self, token: str) -> AuthUser | None: ...
    def get_profile(self, user_id: str) -> dict[str, Any] | None: ...
    def get_application_for_user(self, user_id: str) -> dict[str, Any] | None: ...
    def get_application(self, application_id: str) -> dict[str, Any] | None: ...
    def create_application(self, record: dict[str, Any], kyc: dict[str, Any]) -> dict[str, Any]: ...
    def list_applications(self, f: ApplicationFilter) -> tuple[list[dict[str, Any]], int]: ...
    def update_application(self, application_id: str, values: dict[str, Any]) -> None: ...
    def add_event(self, event: dict[str, Any]) -> None: ...
    def list_events(self, application_id: str) -> list[dict[str, Any]]: ...
    def get_kyc(self, application_id: str) -> dict[str, Any] | None: ...
    def update_kyc(self, application_id: str, values: dict[str, Any]) -> None: ...
    def identification_exists(self, identification_type: str, number: str) -> bool: ...
    def create_signed_upload(self, path: str) -> dict[str, str]: ...
    def download_file(self, path: str) -> bytes | None: ...
    def delete_files(self, paths: list[str]) -> None: ...
    def signed_url(self, path: str, expires_in: int) -> str: ...


class SupabaseRepository:
    def __init__(self, settings: Settings) -> None:
        self.client: Client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )
        self.bucket = settings.supabase_storage_bucket

    # --- auth -------------------------------------------------------------------------------
    def get_auth_user(self, token: str) -> AuthUser | None:
        try:
            response = self.client.auth.get_user(token)
        except Exception:
            return None
        user = getattr(response, "user", None)
        if not user:
            return None
        return AuthUser(
            id=str(user.id),
            email=user.email,
            email_verified=bool(getattr(user, "email_confirmed_at", None)),
        )

    # --- profiles ---------------------------------------------------------------------------
    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        res = (
            self.client.table("profiles")
            .select("id,email,role,state,lga,ward")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    # --- applications -----------------------------------------------------------------------
    def get_application_for_user(self, user_id: str) -> dict[str, Any] | None:
        res = (
            self.client.table("applications")
            .select(APPLICATION_COLUMNS)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def get_application(self, application_id: str) -> dict[str, Any] | None:
        res = (
            self.client.table("applications")
            .select(APPLICATION_COLUMNS)
            .eq("id", application_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def create_application(self, record: dict[str, Any], kyc: dict[str, Any]) -> dict[str, Any]:
        res = self.client.table("applications").insert(record).execute()
        created = res.data[0]
        try:
            self.client.table("application_kyc").insert(
                {**kyc, "application_id": created["id"]}
            ).execute()
        except Exception as exc:
            self.client.table("applications").delete().eq("id", created["id"]).execute()
            # 23505 = unique_violation: the same NIN/passport raced in from another account.
            if getattr(exc, "code", None) == "23505":
                raise DuplicateIdentificationError from exc
            raise
        return created

    def list_applications(self, f: ApplicationFilter) -> tuple[list[dict[str, Any]], int]:
        q = self.client.table("applications").select(APPLICATION_COLUMNS, count="exact")
        for column in ("state", "stage"):
            value = getattr(f, column)
            if value:
                q = q.eq(column, value)
        # LGA and ward match on generated key columns (case, spacing and punctuation ignored).
        for column in ("lga", "ward"):
            value = getattr(f, column)
            if value:
                q = q.eq(f"{column}_key", geo_key(value))
        if f.search:
            term = f.search.replace(",", " ").replace("(", " ").replace(")", " ").strip()
            if term:
                q = q.or_(f"full_name.ilike.%{term}%,reference.ilike.%{term}%")
        res = q.order("created_at", desc=True).range(f.offset, f.offset + f.limit - 1).execute()
        return res.data or [], res.count or 0

    def update_application(self, application_id: str, values: dict[str, Any]) -> None:
        self.client.table("applications").update(values).eq("id", application_id).execute()

    # --- events -----------------------------------------------------------------------------
    def add_event(self, event: dict[str, Any]) -> None:
        self.client.table("application_events").insert(event).execute()

    def list_events(self, application_id: str) -> list[dict[str, Any]]:
        res = (
            self.client.table("application_events")
            .select("stage,action,note,created_at")
            .eq("application_id", application_id)
            .eq("visible_to_applicant", True)
            .order("created_at")
            .execute()
        )
        return res.data or []

    # --- KYC --------------------------------------------------------------------------------
    def get_kyc(self, application_id: str) -> dict[str, Any] | None:
        res = (
            self.client.table("application_kyc")
            .select(
                "identification_type,identification_number,identity_document_path,"
                "passport_photograph_path"
            )
            .eq("application_id", application_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def update_kyc(self, application_id: str, values: dict[str, Any]) -> None:
        self.client.table("application_kyc").update(values).eq(
            "application_id", application_id
        ).execute()

    def identification_exists(self, identification_type: str, number: str) -> bool:
        res = (
            self.client.table("application_kyc")
            .select("application_id")
            .eq("identification_type", identification_type)
            .eq("identification_number", number)
            .limit(1)
            .execute()
        )
        return bool(res.data)

    # --- storage ----------------------------------------------------------------------------
    def create_signed_upload(self, path: str) -> dict[str, str]:
        res = self.client.storage.from_(self.bucket).create_signed_upload_url(path)
        return {"token": res["token"], "signed_url": res["signed_url"]}

    def download_file(self, path: str) -> bytes | None:
        try:
            return self.client.storage.from_(self.bucket).download(path)
        except Exception:
            return None

    def delete_files(self, paths: list[str]) -> None:
        if paths:
            self.client.storage.from_(self.bucket).remove(paths)

    def signed_url(self, path: str, expires_in: int) -> str:
        res = self.client.storage.from_(self.bucket).create_signed_url(path, expires_in)
        return res.get("signedURL") or res.get("signedUrl") or ""
