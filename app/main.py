from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router, compatibility_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/", tags=["root"])
    def read_root() -> dict[str, str]:
        return {
            "message": "NutriScan backend is running.",
            "docs": "/docs",
            "health": f"{settings.api_v1_prefix}/health/ready",
            "barcode_lookup": "/api/v0/product/{barcode}.json",
            "product_search": "/cgi/search.pl",
            "profile": f"{settings.api_v1_prefix}/profile",
            "settings": f"{settings.api_v1_prefix}/settings",
        }

    application.include_router(compatibility_router)
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
