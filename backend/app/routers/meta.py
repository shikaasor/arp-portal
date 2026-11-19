from fastapi import APIRouter, Depends

from .. import constants as c
from ..config import Settings, get_settings

router = APIRouter(tags=["meta"])


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "status": "ok",
        "service": "arp-api",
        "supabase_configured": settings.supabase_configured,
    }


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
