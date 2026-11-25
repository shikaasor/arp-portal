import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import constants as c
from ..config import Settings, get_settings
from ..deps import CurrentUser, get_repository, require_national, require_reviewer
from ..geo import geo_key
from ..repository import ApplicationFilter, Repository
from ..schemas import AdminApplication, AdminList, KycResponse, ReviewRequest

log = logging.getLogger("arp.admin")
router = APIRouter(prefix="/api/admin", tags=["review"])


def in_scope(user: CurrentUser, record: dict) -> bool:
    if user.role == c.ROLE_NATIONAL:
        return True
    if record["state"] != user.state:
        return False
    if user.role in (c.ROLE_LGA, c.ROLE_WARD) and geo_key(record["lga"]) != geo_key(user.lga):
        return False
    return not (user.role == c.ROLE_WARD and geo_key(record["ward"]) != geo_key(user.ward))


def can_review(user: CurrentUser, record: dict) -> bool:
    if record["stage"] not in c.ACTIVE_STAGES or not in_scope(user, record):
        return False
    return user.role == c.ROLE_NATIONAL or c.ROLE_STAGE.get(user.role) == record["stage"]


@router.get("/applications", response_model=AdminList)
def list_applications(
    state: str | None = None,
    stage: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_reviewer),
    repo: Repository = Depends(get_repository),
) -> AdminList:
    if stage and stage not in c.STAGES:
        raise HTTPException(status_code=422, detail="Unknown stage.")
    f = ApplicationFilter(stage=stage, search=search, limit=limit, offset=offset)
    if user.role == c.ROLE_NATIONAL:
        f.state = state
    else:
        # Geography is always taken from the reviewer's assignment, never from the query.
        f.state = user.state
        if user.role in (c.ROLE_LGA, c.ROLE_WARD):
            f.lga = user.lga
        if user.role == c.ROLE_WARD:
            f.ward = user.ward
    rows, total = repo.list_applications(f)
    return AdminList(items=[AdminApplication(**r) for r in rows], total=total)


@router.post("/applications/{application_id}/review", response_model=AdminApplication)
def review_application(
    application_id: str,
    body: ReviewRequest,
    user: CurrentUser = Depends(require_reviewer),
    repo: Repository = Depends(get_repository),
) -> AdminApplication:
    record = repo.get_application(application_id)
    if not record or not in_scope(user, record):
        raise HTTPException(status_code=404, detail="Application not found.")
    if not can_review(user, record):
        raise HTTPException(status_code=409, detail="This application is not at your review stage.")

    current = record["stage"]
    if body.action == "approve":
        new_stage = c.NEXT_STAGE[current]
    elif body.action == "reject":
        new_stage = c.STAGE_REJECTED
    else:
        new_stage = c.STAGE_NEEDS_INFO

    now = datetime.now(UTC).isoformat()
    values = {
        "stage": new_stage,
        "feedback": body.note or record.get("feedback"),
        # Where the application goes back to once the applicant answers a request for info.
        "returns_to_stage": current if new_stage == c.STAGE_NEEDS_INFO else None,
        "updated_at": now,
    }
    repo.update_application(application_id, values)
    repo.add_event(
        {
            "application_id": application_id,
            "stage": current,
            "action": body.action,
            "note": body.note,
            "actor_id": user.id,
            "visible_to_applicant": True,
            "created_at": now,
        }
    )
    return AdminApplication(**{**record, **values})


@router.get("/applications/{application_id}/kyc", response_model=KycResponse)
def get_kyc(
    application_id: str,
    user: CurrentUser = Depends(require_national),
    repo: Repository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> KycResponse:
    record = repo.get_application(application_id)
    kyc = repo.get_kyc(application_id) if record else None
    if not record or not kyc:
        raise HTTPException(status_code=404, detail="Application not found.")
    ttl = settings.signed_url_ttl_seconds
    response = KycResponse(
        reference=record["reference"],
        identification_type=kyc["identification_type"],
        identification_number=kyc["identification_number"],
        identity_document_url=repo.signed_url(kyc["identity_document_path"], ttl),
        passport_photograph_url=repo.signed_url(kyc["passport_photograph_path"], ttl),
        expires_in=ttl,
    )
    # Audit every KYC access (hidden from the applicant's timeline).
    repo.add_event(
        {
            "application_id": application_id,
            "stage": record["stage"],
            "action": "kyc_viewed",
            "actor_id": user.id,
            "visible_to_applicant": False,
            "created_at": datetime.now(UTC).isoformat(),
        }
    )
    return response
