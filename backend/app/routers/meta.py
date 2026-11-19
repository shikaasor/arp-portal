from fastapi import APIRouter, Depends

from .. import constants as c
from ..config import Settings, get_settings

router = APIRouter(tags=["meta"])


def _health(settings: Settings) -> dict:
    return {
        "status": "ok",
        "service": "arp-api",
        "supabase_configured": settings.supabase_configured,
    }


@router.get("/api/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    return _health(settings)


# Bare /health is kept for container/platform health checks hitting the API host directly.
@router.get("/health", include_in_schema=False)
def root_health(settings: Settings = Depends(get_settings)) -> dict:
    return _health(settings)


@router.get("/api/options")
def options() -> dict:
    """Reference data for building the application form."""
    return {
        "states": c.NORTHERN_STATES,
        "genders": c.GENDERS,
        "education_levels": c.EDUCATION_LEVELS,
        "occupations": c.OCCUPATIONS,
        "sectors": c.SECTORS,
        "referral_sources": c.REFERRAL_SOURCES,
        "identification_types": c.IDENTIFICATION_TYPES,
        "stages": c.STAGES,
    }
