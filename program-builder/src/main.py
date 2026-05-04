"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.definitions import router as definitions_router
from src.api.routes.exercises import router as exercises_router
from src.api.routes.generate import router as generate_router
from src.api.routes.library import router as library_router
from src.api.routes.plans import router as plans_router
from src.api.routes.validate import router as validate_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Dynamic Training Program Generator",
        version="0.1.0",
        description="Deterministic training plan generation engine",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(library_router, prefix="/api/v1")
    app.include_router(definitions_router, prefix="/api/v1")
    app.include_router(generate_router, prefix="/api/v1")
    app.include_router(exercises_router, prefix="/api/v1")
    app.include_router(plans_router, prefix="/api/v1")
    app.include_router(validate_router, prefix="/api/v1")

    return app


app = create_app()
