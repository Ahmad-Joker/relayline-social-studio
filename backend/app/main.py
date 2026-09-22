from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import campaigns, health, platforms, posts, webhooks
from app.core.config import get_settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.generated_dir.mkdir(parents=True, exist_ok=True)
    yield


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    settings.generated_dir.mkdir(parents=True, exist_ok=True)
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(health.router)
    app.include_router(posts.router)
    app.include_router(campaigns.router)
    app.include_router(platforms.router)
    app.include_router(webhooks.router)
    app.mount("/media", StaticFiles(directory=settings.data_dir / "generated"), name="media")
    return app


app = create_app()

