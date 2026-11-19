import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import admin, applications, meta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Arewa Revival Project API",
        version="1.0.0",
        description="Applications, review workflow and KYC access for the ARP empowerment portal.",
    )
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

    app.include_router(meta.router)
    app.include_router(applications.router)
    app.include_router(admin.router)
    return app


app = create_app()
