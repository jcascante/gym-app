# Program Builder - Implementation Plan

## Overview

This document provides a detailed, step-by-step implementation plan for the **Template-Based Program Builder** system. The implementation is divided into 8 phases over 18 weeks, with this document focusing on getting started with **Phase 1: Foundation**.

---

## Quick Start - Phase 1: Foundation (Weeks 1-2)

### Goal
Establish the database schema, core models, and exercise library foundation for the template system.

### Prerequisites
- Backend server running with database connection
- Alembic configured for migrations
- FastAPI with SQLAlchemy 2.0 async setup

---

## Phase 1 Tasks Breakdown

### Task 1.1: Database Schema Migrations

#### Step 1: Update Programs Table
Add template-specific fields to the existing `programs` table.

**New Fields to Add:**
```sql
ALTER TABLE programs ADD COLUMN is_default BOOLEAN DEFAULT FALSE;
ALTER TABLE programs ADD COLUMN required_parameters JSONB DEFAULT '[]';
ALTER TABLE programs ADD COLUMN optional_parameters JSONB DEFAULT '[]';
```

**Alembic Migration:**
```bash
cd backend
uv run alembic revision --autogenerate -m "add template fields to programs table"
```

**Expected Changes:**
- `is_default`: Boolean flag for platform-provided templates
- `required_parameters`: JSONB array of parameter definitions
- `optional_parameters`: JSONB array of parameter definitions

#### Step 2: Create Program Assignments Table
New table to track when templates are assigned to clients.

**Migration Command:**
```bash
uv run alembic revision --autogenerate -m "create program assignments table"
```

**Schema Definition:**
```python
# backend/app/models/program_assignment.py
class ProgramAssignment(BaseModel):
    __tablename__ = "program_assignments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subscriptions.id"))

    template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programs.id"))
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    assigned_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programs.id"))

    assignment_parameters: Mapped[dict] = mapped_column(JSONB)

    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="active")
    completion_percentage: Mapped[Decimal] = mapped_column(DECIMAL(5, 2), default=Decimal("0.00"))

    workouts_completed: Mapped[int] = mapped_column(Integer, default=0)
    workouts_total: Mapped[int] = mapped_column(Integer)
    current_week: Mapped[int] = mapped_column(Integer, default=1)
    current_day: Mapped[int] = mapped_column(Integer, default=1)

    client_rating: Mapped[Decimal | None] = mapped_column(DECIMAL(3, 2), nullable=True)
    client_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    coach_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
```

#### Step 3: Create Exercises Library Table
Central repository for all exercises (global and subscription-specific).

**Migration Command:**
```bash
uv run alembic revision --autogenerate -m "create exercises library table"
```

**Schema Definition:**
```python
# backend/app/models/exercise.py
class Exercise(BaseModel):
    __tablename__ = "exercises_library"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("subscriptions.id"), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    muscle_groups: Mapped[list] = mapped_column(JSONB, default=list)
    equipment: Mapped[list] = mapped_column(JSONB, default=list)

    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    is_bilateral: Mapped[bool] = mapped_column(Boolean, default=True)
    is_timed: Mapped[bool] = mapped_column(Boolean, default=False)
    default_rest_seconds: Mapped[int] = mapped_column(Integer, default=90)

    difficulty_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    progression_exercises: Mapped[list] = mapped_column(JSONB, default=list)

    is_global: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
```

#### Step 4: Create Program Weeks/Days/Exercises Tables
Hierarchical structure for program content.

**Migration Command:**
```bash
uv run alembic revision --autogenerate -m "create program structure tables"
```

**Schema Definitions:**

```python
# backend/app/models/program_week.py
class ProgramWeek(BaseModel):
    __tablename__ = "program_weeks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"))
    subscription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subscriptions.id"))

    week_number: Mapped[int] = mapped_column(Integer)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    focus_area: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)

# backend/app/models/program_day.py
class ProgramDay(BaseModel):
    __tablename__ = "program_days"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    program_week_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("program_weeks.id", ondelete="CASCADE"))
    subscription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subscriptions.id"))

    day_number: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    day_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    suggested_day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    warm_up_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cool_down_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)

# backend/app/models/program_day_exercise.py
class ProgramDayExercise(BaseModel):
    __tablename__ = "program_day_exercises"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    program_day_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("program_days.id", ondelete="CASCADE"))
    exercise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exercises_library.id"))
    subscription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subscriptions.id"))

    exercise_order: Mapped[int] = mapped_column(Integer)

    # Exercise prescription
    sets: Mapped[int] = mapped_column(Integer)
    reps_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reps_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reps_target: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Load prescription
    load_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    load_value: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2), nullable=True)
    load_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Tempo and timing
    tempo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rest_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Intensity markers
    rpe_target: Mapped[Decimal | None] = mapped_column(DECIMAL(3, 1), nullable=True)
    percentage_1rm: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    coaching_cues: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Progression tracking (for assigned programs)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    actual_sets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_weight: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2), nullable=True)
    actual_rpe: Mapped[Decimal | None] = mapped_column(DECIMAL(3, 1), nullable=True)
    completion_date: Mapped[datetime | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
```

#### Step 5: Run Migrations
Apply all migrations to the database.

```bash
cd backend
uv run alembic upgrade head
```

**Verification:**
```bash
# Check database schema
uv run python query_db.py --tables
```

---

### Task 1.2: Seed Default Exercise Library

Create a seed script to populate the exercises library with essential exercises.

#### Exercise Categories

**Compound Lifts (10 exercises):**
1. Back Squat
2. Front Squat
3. Bench Press
4. Incline Bench Press
5. Deadlift
6. Romanian Deadlift
7. Overhead Press
8. Barbell Row
9. Pull-up / Chin-up
10. Dip

**Accessory - Upper Body (20 exercises):**
1. Dumbbell Bench Press
2. Dumbbell Row
3. Dumbbell Shoulder Press
4. Lateral Raise
5. Front Raise
6. Face Pull
7. Tricep Extension
8. Tricep Dip
9. Bicep Curl
10. Hammer Curl
11. Preacher Curl
12. Cable Fly
13. Cable Row
14. Lat Pulldown
15. T-Bar Row
16. Shrug
17. Upright Row
18. Skull Crusher
19. Close Grip Bench Press
20. Reverse Fly

**Accessory - Lower Body (15 exercises):**
1. Leg Press
2. Hack Squat
3. Bulgarian Split Squat
4. Walking Lunge
5. Step-up
6. Leg Curl
7. Leg Extension
8. Calf Raise
9. Glute Bridge
10. Hip Thrust
11. Good Morning
12. Goblet Squat
13. Sumo Deadlift
14. Deficit Deadlift
15. Box Squat

**Conditioning (10 exercises):**
1. Kettlebell Swing
2. Kettlebell Clean
3. Kettlebell Press
4. Kettlebell Snatch
5. Rowing (Concept2)
6. Assault Bike
7. Running
8. Sled Push
9. Sled Pull
10. Battle Ropes

**Core & Mobility (10 exercises):**
1. Plank
2. Side Plank
3. Dead Bug
4. Bird Dog
5. Pallof Press
6. Ab Wheel Rollout
7. Hanging Leg Raise
8. Russian Twist
9. Cable Crunch
10. Mountain Climber

#### Seed Script

```python
# backend/app/core/seed_exercises.py
"""Seed default exercise library"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.exercise import Exercise

COMPOUND_LIFTS = [
    {
        "name": "Back Squat",
        "description": "Barbell back squat with bar on upper traps",
        "category": "compound",
        "muscle_groups": ["quadriceps", "glutes", "hamstrings", "core"],
        "equipment": ["barbell", "squat_rack", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 180,
    },
    {
        "name": "Front Squat",
        "description": "Barbell front squat with bar on front deltoids",
        "category": "compound",
        "muscle_groups": ["quadriceps", "glutes", "core"],
        "equipment": ["barbell", "squat_rack", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "advanced",
        "default_rest_seconds": 180,
    },
    {
        "name": "Bench Press",
        "description": "Barbell bench press, flat bench",
        "category": "compound",
        "muscle_groups": ["chest", "triceps", "shoulders"],
        "equipment": ["barbell", "bench", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 180,
    },
    {
        "name": "Incline Bench Press",
        "description": "Barbell bench press on incline bench (30-45 degrees)",
        "category": "compound",
        "muscle_groups": ["chest", "shoulders", "triceps"],
        "equipment": ["barbell", "incline_bench", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 180,
    },
    {
        "name": "Deadlift",
        "description": "Conventional deadlift from floor",
        "category": "compound",
        "muscle_groups": ["hamstrings", "glutes", "back", "core"],
        "equipment": ["barbell", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 240,
    },
    {
        "name": "Romanian Deadlift",
        "description": "RDL emphasizing hamstring stretch",
        "category": "compound",
        "muscle_groups": ["hamstrings", "glutes", "lower_back"],
        "equipment": ["barbell", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 120,
    },
    {
        "name": "Overhead Press",
        "description": "Standing barbell overhead press",
        "category": "compound",
        "muscle_groups": ["shoulders", "triceps", "core"],
        "equipment": ["barbell", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 180,
    },
    {
        "name": "Barbell Row",
        "description": "Bent-over barbell row",
        "category": "compound",
        "muscle_groups": ["back", "biceps", "rear_delts"],
        "equipment": ["barbell", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 120,
    },
    {
        "name": "Pull-up",
        "description": "Bodyweight pull-up (pronated grip)",
        "category": "compound",
        "muscle_groups": ["back", "biceps"],
        "equipment": ["pull_up_bar"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 120,
    },
    {
        "name": "Dip",
        "description": "Bodyweight dip on parallel bars",
        "category": "compound",
        "muscle_groups": ["chest", "triceps", "shoulders"],
        "equipment": ["dip_bars"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 120,
    },
]

CONDITIONING = [
    {
        "name": "Kettlebell Swing",
        "description": "Russian kettlebell swing to eye level",
        "category": "cardio",
        "muscle_groups": ["hamstrings", "glutes", "core", "shoulders"],
        "equipment": ["kettlebell"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
    },
    {
        "name": "Kettlebell Press",
        "description": "Single-arm kettlebell overhead press",
        "category": "compound",
        "muscle_groups": ["shoulders", "triceps", "core"],
        "equipment": ["kettlebell"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 60,
        "is_bilateral": False,
    },
    {
        "name": "Kettlebell Clean",
        "description": "Single-arm kettlebell clean to rack position",
        "category": "cardio",
        "muscle_groups": ["full_body"],
        "equipment": ["kettlebell"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 60,
        "is_bilateral": False,
    },
    {
        "name": "Kettlebell Snatch",
        "description": "Single-arm kettlebell snatch overhead",
        "category": "cardio",
        "muscle_groups": ["full_body"],
        "equipment": ["kettlebell"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "advanced",
        "default_rest_seconds": 90,
        "is_bilateral": False,
    },
    {
        "name": "Rowing Machine",
        "description": "Concept2 rower or similar",
        "category": "cardio",
        "muscle_groups": ["full_body"],
        "equipment": ["rowing_machine"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
        "is_timed": True,
    },
]

async def seed_exercises():
    """Seed exercise library with default exercises"""
    async for db in get_db():
        try:
            # Add compound lifts
            for exercise_data in COMPOUND_LIFTS:
                exercise = Exercise(**exercise_data)
                db.add(exercise)

            # Add conditioning exercises
            for exercise_data in CONDITIONING:
                exercise = Exercise(**exercise_data)
                db.add(exercise)

            await db.commit()
            print(f"✅ Seeded {len(COMPOUND_LIFTS) + len(CONDITIONING)} exercises")
        except Exception as e:
            print(f"❌ Error seeding exercises: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(seed_exercises())
```

**Run Seed Script:**
```bash
cd backend
uv run python -m app.core.seed_exercises
```

---

### Task 1.3: Backend Models and Schemas

#### Create Pydantic Schemas

```python
# backend/app/schemas/program.py
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

class TemplateParameter(BaseModel):
    """Schema for template parameter definition"""
    key: str = Field(..., description="Parameter key (e.g., 'goal', 'focus_lifts')")
    label: str = Field(..., description="Human-readable label")
    type: str = Field(..., description="Parameter type: text, number, select, multi-select")
    required: bool = Field(True, description="Whether parameter is required")
    options: Optional[List[str]] = Field(None, description="Options for select types")
    validation: Optional[dict] = Field(None, description="Validation rules (min, max, pattern)")
    help_text: Optional[str] = Field(None, description="Help text for users")

class ProgramTemplateBase(BaseModel):
    """Base schema for program template"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    program_type: str = Field(..., description="strength, conditioning, hypertrophy, etc.")
    difficulty_level: Optional[str] = Field(None, description="beginner, intermediate, advanced, elite")
    duration_weeks: int = Field(..., gt=0, le=52)
    days_per_week: int = Field(..., gt=0, le=7)

    is_template: bool = True
    is_default: bool = False
    is_public: bool = False

    required_parameters: List[TemplateParameter] = Field(default_factory=list)
    optional_parameters: List[TemplateParameter] = Field(default_factory=list)

    tags: List[str] = Field(default_factory=list)
    goals: Optional[List[str]] = None
    equipment_required: Optional[List[str]] = None

class ProgramTemplateCreate(ProgramTemplateBase):
    """Schema for creating a program template"""
    pass

class ProgramTemplateResponse(ProgramTemplateBase):
    """Schema for program template response"""
    id: UUID
    subscription_id: Optional[UUID]
    created_by: UUID
    times_assigned: int = 0
    average_rating: Optional[Decimal] = None
    average_completion_rate: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProgramAssignmentCreate(BaseModel):
    """Schema for assigning a template to a client"""
    template_id: UUID
    client_id: UUID
    assignment_parameters: dict = Field(..., description="Parameter values for this assignment")
    start_date: date
    coach_notes: Optional[str] = None

class ProgramAssignmentResponse(BaseModel):
    """Schema for program assignment response"""
    id: UUID
    template_id: UUID
    client_id: UUID
    assigned_by: UUID
    program_id: UUID
    assignment_parameters: dict
    start_date: date
    end_date: Optional[date]
    status: str
    completion_percentage: Decimal
    workouts_completed: int
    workouts_total: int
    current_week: int
    current_day: int
    created_at: datetime

    class Config:
        from_attributes = True

# backend/app/schemas/exercise.py
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class ExerciseBase(BaseModel):
    """Base schema for exercise"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, description="compound, isolation, cardio, mobility")
    muscle_groups: List[str] = Field(default_factory=list)
    equipment: List[str] = Field(default_factory=list)

    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    is_bilateral: bool = True
    is_timed: bool = False
    default_rest_seconds: int = 90

    difficulty_level: Optional[str] = None

class ExerciseCreate(ExerciseBase):
    """Schema for creating an exercise"""
    pass

class ExerciseResponse(ExerciseBase):
    """Schema for exercise response"""
    id: UUID
    subscription_id: Optional[UUID]
    created_by: Optional[UUID]
    is_global: bool
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

---

### Task 1.4: Update Core Database Module

Update `backend/app/core/database.py` to import new models:

```python
# Add imports for new models
from app.models.exercise import Exercise
from app.models.program_assignment import ProgramAssignment
from app.models.program_week import ProgramWeek
from app.models.program_day import ProgramDay
from app.models.program_day_exercise import ProgramDayExercise

# Models will be automatically created via metadata
```

---

## Phase 1 Checklist

- [ ] **Task 1.1**: Database migrations created and applied
  - [ ] Programs table updated with template fields
  - [ ] Program assignments table created
  - [ ] Exercises library table created
  - [ ] Program weeks/days/exercises tables created
  - [ ] All migrations applied successfully
  - [ ] Database schema verified

- [ ] **Task 1.2**: Exercise library seeded
  - [ ] Compound lifts added (10 exercises)
  - [ ] Accessory exercises added (35 exercises)
  - [ ] Conditioning exercises added (10 exercises)
  - [ ] Core/mobility exercises added (10 exercises)
  - [ ] Seed script runs successfully
  - [ ] Exercises visible in database

- [ ] **Task 1.3**: Backend models created
  - [ ] Exercise model
  - [ ] ProgramAssignment model
  - [ ] ProgramWeek model
  - [ ] ProgramDay model
  - [ ] ProgramDayExercise model
  - [ ] All models have proper relationships
  - [ ] Indexes created

- [ ] **Task 1.4**: Pydantic schemas created
  - [ ] TemplateParameter schema
  - [ ] ProgramTemplate schemas (Base, Create, Response)
  - [ ] ProgramAssignment schemas
  - [ ] Exercise schemas
  - [ ] All schemas validated

---

## Next Steps After Phase 1

Once Phase 1 is complete, you'll be ready to move to **Phase 2: Template Management API** which includes:
- GET /api/v1/programs/templates (list templates)
- GET /api/v1/programs/templates/{id} (get template details)
- POST /api/v1/programs/templates (create custom template)
- PUT /api/v1/programs/templates/{id} (update template)
- DELETE /api/v1/programs/templates/{id} (soft delete template)

---

## Commands Reference

```bash
# Create migration
cd backend
uv run alembic revision --autogenerate -m "migration description"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1

# Seed exercises
uv run python -m app.core.seed_exercises

# Check database
uv run python query_db.py --tables
uv run python query_db.py --sql "SELECT * FROM exercises_library LIMIT 10"

# Start development server
uv run uvicorn app.main:app --reload
```

---

## Success Criteria for Phase 1

- ✅ All 5 database tables created successfully
- ✅ At least 65 exercises seeded in library
- ✅ All models have proper typing and relationships
- ✅ Pydantic schemas validate correctly
- ✅ Database queries return expected results
- ✅ No migration errors
- ✅ Server starts without errors

**Estimated Time**: 1-2 weeks

---

**Status**: 📋 Ready to Start Phase 1

**Last Updated**: 2025-11-29

**Next Phase**: Phase 2 - Template Management API (Weeks 3-4)
