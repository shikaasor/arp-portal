from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Local dev reads the repo-root `.env.local` shared with the frontend (see `.env.example`),
# then an optional `backend/.env` override. Real environment variables win over both files.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILES = (_BACKEND_DIR.parent / ".env.local", _BACKEND_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILES, extra="ignore")

    # Falls back to the frontend's NEXT_PUBLIC_SUPABASE_URL, so the URL is set only once.
    supabase_url: str = Field(
        "", validation_alias=AliasChoices("supabase_url", "next_public_supabase_url")
    )
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "applicant-documents"

    frontend_origins: str = "http://localhost:3000"
    frontend_origin_regex: str = ""

    require_email_verification: bool = True
    max_upload_bytes: int = 5 * 1024 * 1024
    signed_url_ttl_seconds: int = 300

    @property
    def origins(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.frontend_origins.split(",") if o.strip()]

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
