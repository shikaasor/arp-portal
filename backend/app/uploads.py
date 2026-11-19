from fastapi import HTTPException, UploadFile

SIGNATURES = {
    "application/pdf": (b"%PDF-",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
}
EXTENSIONS = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png"}


def sniff_content_type(data: bytes) -> str | None:
    for content_type, prefixes in SIGNATURES.items():
        if any(data.startswith(p) for p in prefixes):
            return content_type
    return None


def read_validated_upload(
    upload: UploadFile, label: str, allowed: set[str], max_bytes: int
) -> tuple[bytes, str]:
    """Read an upload, enforcing size and checking the real file type from its bytes."""
    data = upload.file.read(max_bytes + 1)
    if not data:
        raise HTTPException(status_code=422, detail=f"{label} is required.")
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=413, detail=f"{label} must be {max_bytes // (1024 * 1024)} MB or smaller."
        )
    detected = sniff_content_type(data)
    if detected is None or detected not in allowed:
        kinds = ", ".join(sorted(EXTENSIONS[t].upper() for t in allowed))
        raise HTTPException(status_code=415, detail=f"{label} must be a {kinds} file.")
    return data, detected
