"""
Tests for workout endpoints.

Uses an in-memory SQLite database and a test client to verify:
- Creating workout logs
- Retrieving workouts for an assignment
- Retrieving workout history (paginated)
- Updating a workout log
- Deleting a workout log
- Workout stats endpoint
- Authorization rules (clients can only see their own workouts)
"""
import pytest
import uuid
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import get_db, init_db
from app.core.deps import get_current_user
from app.models.user import User, UserRole
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.base import Base

# ── In-memory test database ─────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_test_db():
    """Override the database dependency to use in-memory SQLite."""
    async with TestSessionLocal() as session:
        yield session


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
async def setup_database():
    """Create all tables in the in-memory database before tests run."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


# Use fixed IDs so data is only inserted once per module (avoids UNIQUE violations)
_SUBSCRIPTION_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
_CLIENT_USER_ID  = uuid.UUID("10000000-0000-0000-0000-000000000002")
_COACH_USER_ID   = uuid.UUID("10000000-0000-0000-0000-000000000003")
_PROGRAM_ID      = uuid.UUID("10000000-0000-0000-0000-000000000004")
_ASSIGNMENT_ID   = uuid.UUID("10000000-0000-0000-0000-000000000005")


@pytest.fixture
def client_user_id():
    return _CLIENT_USER_ID


@pytest.fixture
def coach_user_id():
    return _COACH_USER_ID


@pytest.fixture
def subscription_id():
    return _SUBSCRIPTION_ID


@pytest.fixture(scope="module", autouse=True)
async def seed_data(setup_database):
    """Seed required data once for all tests in the module."""
    from app.models.subscription import Subscription, SubscriptionType
    from app.models.program import Program
    from app.models.client_program_assignment import ClientProgramAssignment

    async with TestSessionLocal() as session:
        # Subscription
        sub = Subscription(
            id=_SUBSCRIPTION_ID,
            name="Test Subscription",
            subscription_type=SubscriptionType.INDIVIDUAL,
            created_by=_SUBSCRIPTION_ID,
            updated_by=_SUBSCRIPTION_ID,
        )
        session.add(sub)
        await session.flush()

        # Users
        client = User(
            id=_CLIENT_USER_ID,
            email="client@test.com",
            hashed_password="hashed",
            role=UserRole.CLIENT,
            subscription_id=_SUBSCRIPTION_ID,
            is_active=True,
            created_by=_CLIENT_USER_ID,
            updated_by=_CLIENT_USER_ID,
        )
        coach = User(
            id=_COACH_USER_ID,
            email="coach@test.com",
            hashed_password="hashed",
            role=UserRole.COACH,
            subscription_id=_SUBSCRIPTION_ID,
            is_active=True,
            created_by=_COACH_USER_ID,
            updated_by=_COACH_USER_ID,
        )
        session.add(client)
        session.add(coach)
        await session.flush()

        # Program
        prog = Program(
            id=_PROGRAM_ID,
            subscription_id=_SUBSCRIPTION_ID,
            created_by_user_id=_COACH_USER_ID,
            name="Test Program",
            builder_type="strength_linear_5x5",
            duration_weeks=4,
            days_per_week=3,
            is_template=True,
            created_by=_COACH_USER_ID,
            updated_by=_COACH_USER_ID,
        )
        session.add(prog)
        await session.flush()

        # Assignment
        asgn = ClientProgramAssignment(
            id=_ASSIGNMENT_ID,
            subscription_id=_SUBSCRIPTION_ID,
            coach_id=_COACH_USER_ID,
            client_id=_CLIENT_USER_ID,
            program_id=_PROGRAM_ID,
            start_date=datetime.utcnow().date(),
            status="assigned",
            current_week=1,
            current_day=1,
            is_active=True,
            created_by=_COACH_USER_ID,
            updated_by=_COACH_USER_ID,
        )
        session.add(asgn)
        await session.commit()

    yield


@pytest.fixture
async def subscription(seed_data):
    from app.models.subscription import Subscription
    async with TestSessionLocal() as s:
        return await s.get(Subscription, _SUBSCRIPTION_ID)


@pytest.fixture
async def client_user(seed_data):
    async with TestSessionLocal() as s:
        return await s.get(User, _CLIENT_USER_ID)


@pytest.fixture
async def coach_user(seed_data):
    async with TestSessionLocal() as s:
        return await s.get(User, _COACH_USER_ID)


@pytest.fixture
async def program(seed_data):
    from app.models.program import Program
    async with TestSessionLocal() as s:
        return await s.get(Program, _PROGRAM_ID)


@pytest.fixture
async def assignment(seed_data):
    from app.models.client_program_assignment import ClientProgramAssignment
    async with TestSessionLocal() as s:
        return await s.get(ClientProgramAssignment, _ASSIGNMENT_ID)



def make_auth_override(user: User):
    """Return a FastAPI dependency override that always returns the given user."""
    async def _override():
        return user
    return _override


def get_client(user: User) -> AsyncClient:
    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[get_current_user] = make_auth_override(user)
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ── Tests ────────────────────────────────────────────────────────────────────

class TestCreateWorkout:
    async def test_client_can_log_own_workout(self, client_user, assignment):
        async with get_client(client_user) as c:
            resp = await c.post("/api/v1/workouts", json={
                "assignment_id": str(assignment.id),
                "status": "completed",
                "duration_minutes": "60",
                "notes": "Felt great",
            })
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "completed"
        assert data["duration_minutes"] == "60"
        assert data["notes"] == "Felt great"
        assert data["client_id"] == str(client_user.id)

    async def test_client_cannot_log_for_other_assignment(self, client_user, db_session, subscription_id, coach_user_id, program):
        """A client should get 404 when assignment doesn't belong to them."""
        from app.models.client_program_assignment import ClientProgramAssignment
        other_client_id = uuid.uuid4()
        other_assignment = ClientProgramAssignment(
            subscription_id=subscription_id,
            coach_id=coach_user_id,
            client_id=other_client_id,
            program_id=program.id,
            start_date=datetime.utcnow().date(),
            status="assigned",
            current_week=1,
            current_day=1,
            is_active=True,
            created_by=coach_user_id,
            updated_by=coach_user_id,
        )
        db_session.add(other_assignment)
        await db_session.commit()

        async with get_client(client_user) as c:
            resp = await c.post("/api/v1/workouts", json={
                "assignment_id": str(other_assignment.id),
                "status": "completed",
            })
        assert resp.status_code == 403

    async def test_invalid_assignment_returns_404(self, client_user):
        async with get_client(client_user) as c:
            resp = await c.post("/api/v1/workouts", json={
                "assignment_id": str(uuid.uuid4()),
                "status": "completed",
            })
        assert resp.status_code == 404

    async def test_skipped_status_accepted(self, client_user, assignment):
        async with get_client(client_user) as c:
            resp = await c.post("/api/v1/workouts", json={
                "assignment_id": str(assignment.id),
                "status": "skipped",
            })
        assert resp.status_code == 201
        assert resp.json()["status"] == "skipped"


class TestGetAssignmentWorkouts:
    async def test_client_can_see_own_assignment_workouts(self, client_user, assignment):
        # Create a workout first
        async with get_client(client_user) as c:
            await c.post("/api/v1/workouts", json={
                "assignment_id": str(assignment.id),
                "status": "completed",
            })
            resp = await c.get(f"/api/v1/workouts/assignments/{assignment.id}/workouts")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    async def test_coach_can_see_own_assignment_workouts(self, coach_user, client_user, assignment):
        async with get_client(coach_user) as c:
            resp = await c.get(f"/api/v1/workouts/assignments/{assignment.id}/workouts")
        assert resp.status_code == 200

    async def test_nonexistent_assignment_returns_404(self, client_user):
        async with get_client(client_user) as c:
            resp = await c.get(f"/api/v1/workouts/assignments/{uuid.uuid4()}/workouts")
        assert resp.status_code == 404


class TestWorkoutStats:
    async def test_client_gets_stats(self, client_user, assignment):
        async with get_client(client_user) as c:
            resp = await c.get("/api/v1/workouts/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_workouts" in data
        assert "completed_workouts" in data
        assert "skipped_workouts" in data

    async def test_coach_cannot_access_stats(self, coach_user):
        async with get_client(coach_user) as c:
            resp = await c.get("/api/v1/workouts/stats")
        assert resp.status_code == 403


class TestUpdateWorkout:
    async def test_client_can_update_own_workout(self, client_user, assignment):
        # Create
        async with get_client(client_user) as c:
            create_resp = await c.post("/api/v1/workouts", json={
                "assignment_id": str(assignment.id),
                "status": "scheduled",
            })
            workout_id = create_resp.json()["id"]

            # Update
            update_resp = await c.put(f"/api/v1/workouts/{workout_id}", json={
                "status": "completed",
                "duration_minutes": "45",
                "notes": "Updated notes",
            })
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["status"] == "completed"
        assert data["duration_minutes"] == "45"
        assert data["notes"] == "Updated notes"

    async def test_update_nonexistent_workout_returns_404(self, client_user):
        async with get_client(client_user) as c:
            resp = await c.put(f"/api/v1/workouts/{uuid.uuid4()}", json={"status": "completed"})
        assert resp.status_code == 404


class TestDeleteWorkout:
    async def test_client_can_delete_own_workout(self, client_user, assignment):
        async with get_client(client_user) as c:
            create_resp = await c.post("/api/v1/workouts", json={
                "assignment_id": str(assignment.id),
                "status": "completed",
            })
            workout_id = create_resp.json()["id"]

            delete_resp = await c.delete(f"/api/v1/workouts/{workout_id}")
        assert delete_resp.status_code == 204

    async def test_deleted_workout_not_in_history(self, client_user, assignment):
        async with get_client(client_user) as c:
            create_resp = await c.post("/api/v1/workouts", json={
                "assignment_id": str(assignment.id),
                "status": "completed",
                "notes": "unique-marker-to-delete",
            })
            workout_id = create_resp.json()["id"]
            await c.delete(f"/api/v1/workouts/{workout_id}")

            # Verify it's gone from assignment workouts
            list_resp = await c.get(f"/api/v1/workouts/assignments/{assignment.id}/workouts")
        remaining_ids = [w["id"] for w in list_resp.json()]
        assert workout_id not in remaining_ids

    async def test_delete_nonexistent_returns_404(self, client_user):
        async with get_client(client_user) as c:
            resp = await c.delete(f"/api/v1/workouts/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestWorkoutHistory:
    async def test_client_gets_paginated_history(self, client_user, assignment):
        async with get_client(client_user) as c:
            resp = await c.get("/api/v1/workouts?limit=10&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "workouts" in data
        assert isinstance(data["workouts"], list)

    async def test_coach_cannot_access_history(self, coach_user):
        async with get_client(coach_user) as c:
            resp = await c.get("/api/v1/workouts")
        assert resp.status_code == 403
