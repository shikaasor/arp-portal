"""Document upload rules.

Files never pass through the API (Vercel functions cap request bodies at 4.5 MB). Instead:

1. The API issues one-time signed upload URLs for paths it chooses:
   ``{user_id}/{reference}/{key}.{ext}``.
2. The browser uploads straight to the private Supabase bucket.
3. On submit, the API re-checks each path, downloads the object and verifies its real type and size.
"""

import re

from fastapi import HTTPException

from . import constants as c

SIGNATURES = {
    "application/pdf": (b"%PDF-",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
}
EXTENSIONS = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png"}
LABELS = {"identity_document": "Identity document", "passport_photograph": "Passport photograph"}


def sniff_content_type(data: bytes) -> str | None:
    for content_type, prefixes in SIGNATURES.items():
        if any(data.startswith(p) for p in prefixes):
            return content_type
    return None


def _kinds(allowed: set[str]) -> str:
    return ", ".join(sorted(EXTENSIONS[t].upper() for t in allowed))


def check_declared_file(key: str, content_type: str, size: int, max_bytes: int) -> str:
    """Validate what the browser says it will upload. Returns the storage file extension."""
    label, allowed = LABELS[key], c.DOCUMENT_TYPES[key]
    if content_type not in allowed:
        raise HTTPException(status_code=415, detail=f"{label} must be a {_kinds(allowed)} file.")
    if size <= 0:
        raise HTTPException(status_code=422, detail=f"{label} is required.")
    if size > max_bytes:
        raise HTTPException(
            status_code=413, detail=f"{label} must be {max_bytes // (1024 * 1024)} MB or smaller."
        )
    return EXTENSIONS[content_type]


def object_path(user_id: str, reference: str, key: str, ext: str, version: str = "") -> str:
    """Storage path for a document. Replacements sent later carry a random `version` suffix,
    so they never collide with (or overwrite) the file a reviewer has already seen."""
    suffix = f"-{version}" if version else ""
    return f"{user_id}/{reference}/{key}{suffix}.{ext}"


def check_submitted_path(path: str, user_id: str, reference: str, key: str) -> str:
    """Make sure a client-supplied path is one we could have issued to this user."""
    exts = "|".join(EXTENSIONS[t] for t in c.DOCUMENT_TYPES[key])
    pattern = rf"{re.escape(user_id)}/{re.escape(reference)}/{key}(-[0-9a-f]{{8}})?\.({exts})"
    if not re.fullmatch(pattern, path):
        raise HTTPException(status_code=422, detail=f"{LABELS[key]} upload is invalid.")
    return path


def verify_stored_file(key: str, path: str, data: bytes | None, max_bytes: int) -> str:
    """Check an uploaded object really is what its path claims. Returns its content type."""
    label, allowed = LABELS[key], c.DOCUMENT_TYPES[key]
    if not data:
        raise HTTPException(status_code=422, detail=f"{label} was not uploaded. Please try again.")
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=413, detail=f"{label} must be {max_bytes // (1024 * 1024)} MB or smaller."
        )
    detected = sniff_content_type(data)
    if detected is None or detected not in allowed or not path.endswith("." + EXTENSIONS[detected]):
        raise HTTPException(status_code=415, detail=f"{label} must be a {_kinds(allowed)} file.")
    return detected
