from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from fastapi import Depends, Header, HTTPException, status

from . import constants as c
from .config import Settings, get_settings
from .geo import canonical_lga, canonical_ward
from .repository import AuthUser, Repository, SupabaseRepository


@lru_cache
def _supabase_repository() -> SupabaseRepository:
    return SupabaseRepository(get_settings())


def get_repository(settings: Settings = Depends(get_settings)) -> Repository:
    if not settings.supabase_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The application service has not been configured yet.",
        )
    return _supabase_repository()


@dataclass
class CurrentUser:
    auth: AuthUser
    role: str
    state: str | None
    lga: str | None
    ward: str | None

    @property
    def id(self) -> str:
        return self.auth.id

    @property
    def is_reviewer(self) -> bool:
        return self.role in c.REVIEWER_ROLES


def get_current_user(
    authorization: str | None = Header(default=None),
    repo: Repository = Depends(get_repository),
) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    token = authorization.split(" ", 1)[1].strip()
    auth_user = repo.get_auth_user(token)
    if auth_user is None:
        raise HTTPException(status_code=401, detail="Your session has expired. Sign in again.")
    profile = repo.get_profile(auth_user.id) or {}
    role = profile.get("role") or c.ROLE_APPLICANT
    return CurrentUser(
        auth=auth_user,
        role=role,
        state=profile.get("state"),
        lga=profile.get("lga"),
        ward=profile.get("ward"),
    )


def require_reviewer(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not user.is_reviewer:
        raise HTTPException(status_code=403, detail="Your account has no reviewer assignment.")
    # A geographic reviewer without the geography for their level must not see everything.
    needed = {
        c.ROLE_STATE: ("state",),
        c.ROLE_LGA: ("state", "lga"),
        c.ROLE_WARD: ("state", "lga", "ward"),
    }.get(user.role, ())
    if any(not getattr(user, field) for field in needed):
        raise HTTPException(status_code=403, detail="Your reviewer assignment is incomplete.")
    if user.role in (c.ROLE_LGA, c.ROLE_WARD):
        # Applications store the official LGA spelling, so a misspelt assignment would silently
        # match nothing. Refuse it loudly instead, so whoever assigned the role can fix it.
        lga = canonical_lga(user.state, user.lga)
        if lga is None:
            raise HTTPException(
                status_code=403,
                detail="Your reviewer assignment names an LGA that is not on the official list.",
            )
        user.lga = lga
    if user.role == c.ROLE_WARD:
        # Same for the ward: it must be one of that LGA's wards (case and punctuation ignored).
        ward = canonical_ward(user.state, user.lga, user.ward)
        if ward is None:
            raise HTTPException(
                status_code=403,
                detail="Your reviewer assignment names a ward that is not on the official list "
                "for its LGA.",
            )
        user.ward = ward
    return user


def require_national(user: CurrentUser = Depends(require_reviewer)) -> CurrentUser:
    if user.role != c.ROLE_NATIONAL:
        raise HTTPException(status_code=403, detail="Only national reviewers can view KYC data.")
    return user
