import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .routers import admin, applications, meta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

# Every public route lives under API_PREFIX. The frontend proxies exactly this prefix to the
# API, and never defines routes of its own beneath it (both rules are enforced in CI).
API_PREFIX = "/api"


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Return the first validation problem as one readable message for the UI."""
    errors = exc.errors()
    first = errors[0] if errors else {}
    message = str(first.get("msg", "Invalid request.")).removeprefix("Value error, ")
    loc = [str(p) for p in first.get("loc", ()) if p not in ("body", "details", "query")]
    return JSONResponse(
        status_code=422, content={"detail": f"{loc[-1]}: {message}" if loc else message}
    )


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Arewa Revival Project API",
        version="1.0.0",
        description="Applications, review workflow and KYC access for the ARP empowerment portal.",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=None,
        openapi_url=f"{API_PREFIX}/openapi.json",
    )
    # In production the browser calls the API through the frontend's own domain (same origin),
    # so CORS only matters for local development or calling the API host directly.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_origin_regex=settings.frontend_origin_regex or None,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=600,
    )

    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cache-Control", "no-store")
        return response

    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.include_router(meta.router)
    app.include_router(applications.router)
    app.include_router(admin.router)
    return app


app = create_app()
