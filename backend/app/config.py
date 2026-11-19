from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = ""
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
