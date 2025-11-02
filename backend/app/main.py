from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events handler.
    Initializes database on startup and closes connections on shutdown.
    """
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Gym App API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "SQLite" if settings.ENVIRONMENT == "development" else "PostgreSQL"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Include API routers here
# from app.api import users, workouts, exercises
# app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
