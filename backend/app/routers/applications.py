import logging
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from .. import constants as c
from ..config import Settings, get_settings
from ..deps import CurrentUser, get_current_user, get_repository
from ..repository import DuplicateIdentificationError, Repository
from ..schemas import (
    ApplicantApplication,
    MeResponse,
    Profile,
    RespondRequest,
    ResponseUploadRequest,
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
DUPLICATE_ID_DETAIL = (
    "An application has already been submitted with this identification number. "
    "Each person can apply once."
)


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
        if repo.identification_exists(
            body.details.identification_type, body.details.identification_number
        ):
            raise HTTPException(status_code=409, detail=DUPLICATE_ID_DETAIL)
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
    except DuplicateIdentificationError as exc:
        # Lost a race with another account using the same number (unique index).
        _cleanup(repo, list(paths.values()), reference)
        raise HTTPException(status_code=409, detail=DUPLICATE_ID_DETAIL) from exc
    except Exception as exc:
        # Never log or return applicant data / identity numbers.
        log.exception("Application submission failed (reference=%s)", reference)
        raise HTTPException(
            status_code=503, detail="Application service is temporarily unavailable."
        ) from exc

    return SubmitResponse(id=created["id"], reference=reference, stage=c.STAGE_STATE)


def _awaiting_response(user: CurrentUser, repo: Repository) -> dict:
    record = repo.get_application_for_user(user.id)
    if not record:
        raise HTTPException(status_code=404, detail="You have not submitted an application.")
    if record["stage"] != c.STAGE_NEEDS_INFO:
        raise HTTPException(
            status_code=409, detail="Your application is not waiting for more information."
        )
    return record


@router.post("/applications/me/uploads", response_model=UploadResponse)
def start_response_upload(
    body: ResponseUploadRequest,
    user: CurrentUser = Depends(get_current_user),
    repo: Repository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> UploadResponse:
    """Issue upload URLs for replacement documents sent with a response to a reviewer."""
    record = _awaiting_response(user, repo)
    reference = record["reference"]
    uploads: dict[str, UploadTicket] = {}
    for key in DOCUMENT_KEYS:
        declared = getattr(body, key)
        if declared is None:
            continue
        ext = check_declared_file(
            key, declared.content_type, declared.size, settings.max_upload_bytes
        )
        path = object_path(user.id, reference, key, ext, version=secrets.token_hex(4))
        try:
            ticket = repo.create_signed_upload(path)
        except Exception as exc:
            log.exception("Could not create signed upload URL (reference=%s)", reference)
            raise HTTPException(
                status_code=503, detail="Uploads are temporarily unavailable. Please try again."
            ) from exc
        uploads[key] = UploadTicket(path=path, **ticket)
    if not uploads:
        raise HTTPException(status_code=422, detail="Choose at least one document to replace.")
    return UploadResponse(
        reference=reference, bucket=settings.supabase_storage_bucket, uploads=uploads
    )


@router.post("/applications/me/respond", response_model=ApplicantApplication)
def respond_to_request(
    body: RespondRequest,
    user: CurrentUser = Depends(get_current_user),
    repo: Repository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> ApplicantApplication:
    """Answer a reviewer's request for information. The application returns to the stage
    that asked, with the applicant's note (and any replacement documents) attached."""
    record = _awaiting_response(user, repo)
    reference = record["reference"]
    kyc = repo.get_kyc(record["id"]) or {}
    replacements: dict[str, str] = {}
    for key in DOCUMENT_KEYS:
        path = getattr(body, f"{key}_path")
        if path:
            replacements[key] = check_submitted_path(path, user.id, reference, key)
    new_paths = [p for k, p in replacements.items() if p != kyc.get(f"{k}_path")]
    try:
        for key, path in replacements.items():
            if path in new_paths:
                verify_stored_file(key, path, repo.download_file(path), settings.max_upload_bytes)
    except HTTPException:
        _cleanup(repo, new_paths, reference)
        raise

    now = datetime.now(UTC).isoformat()
    back_to = record.get("returns_to_stage") or c.STAGE_STATE
    replaced = {f"{k}_path": p for k, p in replacements.items() if p in new_paths}
    if replaced:
        superseded = [kyc[f] for f in replaced if kyc.get(f)]
        repo.update_kyc(record["id"], replaced)
        _cleanup(repo, superseded, reference)
    values = {
        "stage": back_to,
        "applicant_response": body.note,
        "returns_to_stage": None,
        "updated_at": now,
    }
    repo.update_application(record["id"], values)
    repo.add_event(
        {
            "application_id": record["id"],
            "stage": c.STAGE_NEEDS_INFO,
            "action": c.ACTION_RESPONDED,
            "note": body.note,
            "actor_id": user.id,
            "visible_to_applicant": True,
            "created_at": now,
        }
    )
    return applicant_view({**record, **values}, repo)


def _cleanup(repo: Repository, paths: list[str], reference: str) -> None:
    try:
        repo.delete_files(paths)
    except Exception:
        log.exception("Failed to clean up uploads for %s", reference)
