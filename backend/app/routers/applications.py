import json
import logging
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError

from .. import constants as c
from ..config import Settings, get_settings
from ..deps import CurrentUser, get_current_user, get_repository
from ..repository import Repository
from ..schemas import (
    ApplicantApplication,
    ApplicationDetails,
    MeResponse,
    Profile,
    ReviewEvent,
    SubmitResponse,
)
from ..uploads import EXTENSIONS, read_validated_upload

log = logging.getLogger("arp.applications")
router = APIRouter(prefix="/api", tags=["applicant"])


def new_reference() -> str:
    return "ARP-" + secrets.token_hex(5).upper()


def applicant_view(record: dict, repo: Repository) -> ApplicantApplication:
    history = [ReviewEvent(**e) for e in repo.list_events(record["id"])]
    return ApplicantApplication(**{**record, "history": history})


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


@router.post("/applications", response_model=SubmitResponse, status_code=status.HTTP_201_CREATED)
def submit_application(
    details: str = Form(..., description="JSON-encoded ApplicationDetails"),
    identity_document: UploadFile = File(...),
    passport_photograph: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
    repo: Repository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> SubmitResponse:
    if settings.require_email_verification and not user.auth.email_verified:
        raise HTTPException(status_code=403, detail="Verify your email address before applying.")
    if repo.get_application_for_user(user.id):
        raise HTTPException(status_code=409, detail="You have already submitted an application.")

    try:
        payload = ApplicationDetails.model_validate(json.loads(details))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="Invalid application data.") from exc
    except ValidationError as exc:
        first = exc.errors()[0]
        message = str(first.get("msg", "Invalid application data.")).removeprefix("Value error, ")
        field = ".".join(str(p) for p in first.get("loc", ()))
        raise HTTPException(
            status_code=422, detail=f"{field}: {message}" if field else message
        ) from exc

    files = {
        "identity_document": read_validated_upload(
            identity_document,
            "Identity document",
            c.DOCUMENT_TYPES["identity_document"],
            settings.max_upload_bytes,
        ),
        "passport_photograph": read_validated_upload(
            passport_photograph,
            "Passport photograph",
            c.DOCUMENT_TYPES["passport_photograph"],
            settings.max_upload_bytes,
        ),
    }

    reference = new_reference()
    uploaded: list[str] = []
    paths: dict[str, str] = {}
    data = payload.model_dump(mode="json")
    kyc = {
        "identification_type": data.pop("identification_type"),
        "identification_number": data.pop("identification_number"),
    }
    try:
        for key, (blob, content_type) in files.items():
            path = f"{user.id}/{reference}/{key}.{EXTENSIONS[content_type]}"
            repo.upload_file(path, blob, content_type)
            uploaded.append(path)
            paths[key] = path
        created = repo.create_application(
            {
                **data,
                "reference": reference,
                "user_id": user.id,
                "email": (user.auth.email or "").lower(),
                "stage": c.STAGE_STATE,
            },
            {
                **kyc,
                "identity_document_path": paths["identity_document"],
                "passport_photograph_path": paths["passport_photograph"],
            },
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
    except HTTPException:
        raise
    except Exception as exc:
        # Never log or return applicant data / identity numbers.
        log.exception("Application submission failed (reference=%s)", reference)
        try:
            repo.delete_files(uploaded)
        except Exception:
            log.exception("Failed to clean up uploads for %s", reference)
        raise HTTPException(
            status_code=503, detail="Application service is temporarily unavailable."
        ) from exc

    return SubmitResponse(id=created["id"], reference=reference, stage=c.STAGE_STATE)
