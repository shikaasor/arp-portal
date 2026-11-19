import logging
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from .. import constants as c
from ..config import Settings, get_settings
from ..deps import CurrentUser, get_current_user, get_repository
from ..repository import Repository
from ..schemas import (
    ApplicantApplication,
    MeResponse,
    Profile,
    ReviewEvent,
    SubmitRequest,
    SubmitResponse,
    UploadRequest,
    UploadResponse,
    UploadTicket,
)
from ..uploads import (
    check_declared_file,
    check_submitted_path,
    object_path,
    verify_stored_file,
)

log = logging.getLogger("arp.applications")
router = APIRouter(prefix="/api", tags=["applicant"])

DOCUMENT_KEYS = ("identity_document", "passport_photograph")


def new_reference() -> str:
    return "ARP-" + secrets.token_hex(5).upper()


def applicant_view(record: dict, repo: Repository) -> ApplicantApplication:
    history = [ReviewEvent(**e) for e in repo.list_events(record["id"])]
    return ApplicantApplication(**{**record, "history": history})


def ensure_can_apply(user: CurrentUser, repo: Repository, settings: Settings) -> None:
    if settings.require_email_verification and not user.auth.email_verified:
        raise HTTPException(status_code=403, detail="Verify your email address before applying.")
    if repo.get_application_for_user(user.id):
        raise HTTPException(status_code=409, detail="You have already submitted an application.")


@router.get("/me", response_model=MeResponse)
def me(
    user: CurrentUser = Depends(get_current_user), repo: Repository = Depends(get_repository)
) -> MeResponse:
    record = repo.get_application_for_user(user.id)
    return MeResponse(
        profile=Profile(
            id=user.id,
            email=user.auth.email,
            role=user.role,
            state=user.state,
            lga=user.lga,
            ward=user.ward,
        ),
        email_verified=user.auth.email_verified,
        application=applicant_view(record, repo) if record else None,
    )


@router.post("/applications/uploads", response_model=UploadResponse)
def start_upload(
    body: UploadRequest,
    user: CurrentUser = Depends(get_current_user),
    repo: Repository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> UploadResponse:
    """Step 1: issue one-time signed URLs so the browser uploads documents straight to storage."""
    ensure_can_apply(user, repo, settings)
    reference = new_reference()
    uploads: dict[str, UploadTicket] = {}
    for key in DOCUMENT_KEYS:
        declared = getattr(body, key)
        ext = check_declared_file(
            key, declared.content_type, declared.size, settings.max_upload_bytes
        )
        path = object_path(user.id, reference, key, ext)
        try:
            ticket = repo.create_signed_upload(path)
        except Exception as exc:
            log.exception("Could not create signed upload URL (reference=%s)", reference)
            raise HTTPException(
                status_code=503, detail="Uploads are temporarily unavailable. Please try again."
            ) from exc
        uploads[key] = UploadTicket(path=path, **ticket)
    return UploadResponse(
        reference=reference, bucket=settings.supabase_storage_bucket, uploads=uploads
    )


@router.post("/applications", response_model=SubmitResponse, status_code=status.HTTP_201_CREATED)
def submit_application(
    body: SubmitRequest,
    user: CurrentUser = Depends(get_current_user),
    repo: Repository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> SubmitResponse:
    """Step 2: verify the uploaded documents and record the application."""
    ensure_can_apply(user, repo, settings)
    reference = body.reference
    paths = {
        key: check_submitted_path(getattr(body, f"{key}_path"), user.id, reference, key)
        for key in DOCUMENT_KEYS
    }
    try:
        for key, path in paths.items():
            verify_stored_file(key, path, repo.download_file(path), settings.max_upload_bytes)
    except HTTPException:
        # The files are unusable: remove them so the applicant can simply retry.
        _cleanup(repo, list(paths.values()), reference)
        raise

    data = body.details.model_dump(mode="json")
    kyc = {
        "identification_type": data.pop("identification_type"),
        "identification_number": data.pop("identification_number"),
        "identity_document_path": paths["identity_document"],
        "passport_photograph_path": paths["passport_photograph"],
    }
    try:
        created = repo.create_application(
            {
                **data,
                "reference": reference,
                "user_id": user.id,
                "email": (user.auth.email or "").lower(),
                "stage": c.STAGE_STATE,
            },
            kyc,
        )
        repo.add_event(
            {
                "application_id": created["id"],
                "stage": c.STAGE_STATE,
                "action": "submitted",
                "actor_id": user.id,
                "visible_to_applicant": True,
                "created_at": datetime.now(UTC).isoformat(),
            }
        )
    except Exception as exc:
        # Never log or return applicant data / identity numbers.
        log.exception("Application submission failed (reference=%s)", reference)
        raise HTTPException(
            status_code=503, detail="Application service is temporarily unavailable."
        ) from exc

    return SubmitResponse(id=created["id"], reference=reference, stage=c.STAGE_STATE)


def _cleanup(repo: Repository, paths: list[str], reference: str) -> None:
    try:
        repo.delete_files(paths)
    except Exception:
        log.exception("Failed to clean up uploads for %s", reference)
