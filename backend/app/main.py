from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.core.config import settings
from app.core.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events handler.
    Initializes database on startup and closes connections on shutdown.
    """
    # Import models here to ensure they're registered with SQLAlchemy
    from app.models.user import User  # noqa: F401
    from app.models.program import Program, ProgramWeek, ProgramDay, ProgramDayExercise  # noqa: F401
    from app.models.coach_client_assignment import CoachClientAssignment  # noqa: F401
    from app.models.client_program_assignment import ClientProgramAssignment  # noqa: F401
    from app.models.subscription import Subscription  # noqa: F401
    from app.models.location import Location  # noqa: F401
    from app.models.workout_log import WorkoutLog  # noqa: F401
    from app.models.exercise import Exercise  # noqa: F401

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
    description="""
    Gym App API - Multi-tenant fitness management platform with role-based access control.

    ## Overview

    A subscription-based SaaS platform supporting:
    - **Individual Coach Subscriptions**: Solo trainers managing their client roster
    - **Gym Subscriptions**: Single-location gyms with multiple coaches and members
    - **Enterprise Subscriptions**: Multi-location franchises with unlimited users

    ## User Roles

    - **APPLICATION_SUPPORT**: Platform admins (cross-subscription access)
    - **SUBSCRIPTION_ADMIN**: Subscription owners/managers
    - **COACH**: Trainers working with assigned clients (GYM/ENTERPRISE only)
    - **CLIENT**: End users receiving training

    ## Authentication

    All endpoints require JWT authentication with role-based authorization.

    ### How to Authenticate in Swagger:
    1. Create a test user using the seed script (see below)
    2. Click the **Authorize** button (🔓) at the top
    3. For OAuth2: Enter your email and password
    4. For Bearer: Paste your JWT token from the `/auth/login` endpoint
    5. Click "Authorize" - your token will be included in all requests

    ### Test Credentials (After Running Seed Script):
    - **Support User**: `support@gymapp.com` / password set in seed script
    - **Admin User**: Email and password defined in your seed data

    ## Authorization

    Access is controlled by:
    - **User Role**: Different endpoints require different roles
    - **Subscription Context**: Users can only access data within their subscription
    - **Location Context**: ENTERPRISE users may be restricted to specific locations

    ## API Structure

    - **Authentication** (`/auth`): Login, get current user
    - **Users** (`/users`): User management (CRUD with role restrictions)
    - **Subscriptions** (`/subscriptions`): Subscription management (admin only)
    - More endpoints coming soon...
    """,
    swagger_ui_parameters={
        "persistAuthorization": True,  # Remember auth token across page refreshes
        "defaultModelsExpandDepth": 3,  # Expand schema models for better visibility
    }
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
    db_type = "SQLite" if "sqlite" in settings.DATABASE_URL.lower() else "PostgreSQL"
    return {
        "message": "Gym App API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_type
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Include API routers
from app.api import auth, users, subscriptions, locations, programs, clients, coaches, workouts, exercises

app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Authentication"]
)

app.include_router(
    users.router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["Users"]
)

app.include_router(
    subscriptions.router,
    prefix=f"{settings.API_V1_STR}/subscriptions",
    tags=["Subscriptions"]
)

app.include_router(
    locations.router,
    prefix=f"{settings.API_V1_STR}/locations",
    tags=["Locations"]
)

app.include_router(
    programs.router,
    prefix=f"{settings.API_V1_STR}/programs",
    tags=["Programs"]
)

app.include_router(
    clients.router,
    prefix=f"{settings.API_V1_STR}",  # Router already has /coaches/me/clients prefix
    tags=["Client Management"]
)

app.include_router(
    coaches.router,
    prefix=f"{settings.API_V1_STR}",  # Router already has /coaches/me prefix
    tags=["Coach"]
)

app.include_router(
    workouts.router,
    prefix=f"{settings.API_V1_STR}/workouts",
    tags=["Workouts"]
)

app.include_router(
    exercises.router,
    prefix=f"{settings.API_V1_STR}/exercises",
    tags=["Exercise Library"]
)

# Additional routers will be added here as features are implemented
# from app.api import assignments
# app.include_router(assignments.router, prefix=f"{settings.API_V1_STR}/assignments", tags=["Coach-Client Assignments"])


# Customize OpenAPI schema to add both OAuth2 and Bearer token authentication
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add both security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": f"{settings.API_V1_STR}/auth/login",
                    "scopes": {}
                }
            },
            "description": "Use username and password to get access token automatically"
        },
        "BearerToken": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Paste your JWT token directly (get it from /auth/login endpoint)"
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
