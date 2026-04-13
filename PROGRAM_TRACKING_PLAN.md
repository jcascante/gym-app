# Program Tracking — Implementation Plan
_Last updated: 2026-04-09_

## Decisions locked in

| # | Decision |
|---|---|
| 1 | Auto-advance current_week/current_day on workout completion |
| 2 | Skipped days count toward progress but shown as "skipped" (color-coded) |
| 3 | start_date required on every assignment |
| 4 | Remove deprecated ProgramAssignment model |
| 5 | Option A: full program tree copy per client (not shared template rows) |
| 6 | Engine (TrainGen) is the source of program definitions and generation |

---

## Architecture: Two template sources

Template library visible to clients shows both:

| Source | What it is | How "start" works |
|---|---|---|
| **Engine definitions** | Programs defined in TrainGen Engine (`GET /engine/program-definitions`) | Backend calls `engine_client.generate_plan(inputs)` → materializes engine response into Program tree → creates assignment |
| **Coach-created templates** | Programs with `is_template=True` in our DB (subscription-scoped + public) | Backend copies program tree → creates assignment |

---

## Full client self-service flow

```
GET /engine/program-definitions          → list engine program types
GET /programs/templates                  → list coach-created templates (subscription + public)
        ↓ user picks one
GET /engine/program-definitions/{id}     → engine template detail (required inputs schema)
GET /programs/templates/{id}             → coach template detail (required_parameters)
        ↓ user fills inputs
POST /programs/templates/{id}/preview    → dry run: call engine or run generator, return full structure
        ↓ user confirms + sets start_date
POST /programs/templates/{id}/start      → generate full copy + create assignment + schedule days
        ↓ redirect to /my-programs/{assignment_id}
GET /workouts/assignments/{id}/today     → today's prescribed exercises
POST /workouts                           → log session with per-exercise sets → auto-advance
```

---

## Phase 0 — Cleanup

**Delete:**
- `backend/app/models/program_assignment.py`
- `backend/app/models/program_template.py` (empty)

**Prune from:**
- `models/__init__.py` — remove ProgramAssignment
- `core/database.py` — remove ProgramAssignment from init_db()
- `schemas/program.py` — remove ProgramAssignmentCreate, ProgramAssignmentResponse, ProgramAssignmentListResponse (dead schemas)

---

## Phase 1 — Data model changes

### New model: `WorkoutExerciseLog`
File: `backend/app/models/workout_exercise_log.py`

```
workout_exercise_logs
  id                        UUID PK
  subscription_id           FK → subscriptions (required)
  workout_log_id            FK → workout_logs CASCADE
  program_day_exercise_id   FK → program_day_exercises (nullable)
  exercise_name             String (denormalized for display)
  set_number                Integer
  actual_reps               Integer (nullable)
  actual_weight_lbs         Float (nullable)
  actual_rpe                Float 1–10 (nullable)
  notes                     Text (nullable)
  completed_at              DateTime
```

> One row per set — gives real training data (set 1: 225lbs RPE 7, set 2: 215lbs RPE 9).

### Extend `WorkoutLog`
Add columns:
- `program_day_id` FK → program_days (nullable for backward compat)
- `day_status` String enum: `completed | skipped | partial` (more explicit than overloading status)
- `session_rating` Integer 1–5 (nullable)

### Extend `ClientProgramAssignment`
Add columns:
- `workouts_completed` Integer default 0
- `workouts_skipped` Integer default 0
- `client_rating` Float 1–5 (nullable)
- `client_feedback` Text (nullable)

Fix:
- `progress_percentage` property: `(completed + skipped) / total_program_days * 100`
- `progress_health` property: `"green" | "yellow" | "red"` based on skip ratio

Make required (remove Optional/default):
- `start_date` — must always be set at assignment time

### Extend `ProgramDay`
Add column:
- `scheduled_date` Date (nullable — computed when program is assigned based on start_date + suggested_day_of_week)

### Extend `Program`
Add column:
- `engine_program_id` String (nullable) — links back to the engine definition that was used to generate this program
- `engine_program_version` String (nullable) — version of the engine definition

---

## Phase 2 — New service: `assignment_service.py`

```python
async def schedule_program_days(program_id, start_date, db) -> None
    """Compute and set scheduled_date on every ProgramDay based on start_date + suggested_day_of_week."""

async def self_start_program(template_source, template_id, inputs, start_date, current_user, db) -> ClientProgramAssignment
    """
    For engine templates:
      1. Call engine_client.generate_plan(inputs)
      2. Materialize engine response into Program + Week + Day + Exercise rows (is_template=False)
      3. Set engine_program_id / engine_program_version on Program
      4. Create ClientProgramAssignment
      5. Call schedule_program_days()
    
    For coach templates:
      1. Load template tree from DB
      2. Deep-copy Program + Week + Day + Exercise rows (is_template=False)
      3. Create ClientProgramAssignment
      4. Call schedule_program_days()
    """

async def advance_progress(assignment_id, day_status, db) -> ClientProgramAssignment
    """
    Called after every workout log.
    1. Increment workouts_completed or workouts_skipped
    2. Determine next position:
       - If current_day < days_in_week → current_day++
       - Else → current_week++, current_day = 1
    3. If current_week > duration_weeks → status = "completed", actual_completion_date = now
    4. Recalculate progress_percentage and progress_health
    5. Persist and return updated assignment
    """
```

---

## Phase 3 — New & updated API endpoints

### Engine template browsing (already exists, keep as-is)
```
GET  /api/v1/engine/program-definitions          → list engine programs (client auth)
GET  /api/v1/engine/program-definitions/{id}     → detail + required inputs schema
```

### Coach template browsing (extend existing)
```
GET  /api/v1/programs/templates                  → list templates visible to clients
     Query params: source=coach|engine|all, difficulty, duration_weeks, tags
     Auth: any authenticated user (currently coach-only, open this up)

GET  /api/v1/programs/templates/{id}             → template detail
     Auth: any authenticated user
```

### Self-service program start (new)
```
POST /api/v1/programs/templates/{id}/preview     → dry-run generation, return full structure
     Body: { source: "engine"|"coach", inputs: {...}, movements: [...] }
     Auth: any authenticated user

POST /api/v1/programs/templates/{id}/start       → generate copy + assign to self
     Body: { source: "engine"|"coach", inputs: {...}, movements: [...], start_date: date, assignment_name?: string }
     Auth: any authenticated user
     Response: { assignment_id, program_id, start_date, end_date, status }
```

### Today's workout (new)
```
GET  /api/v1/workouts/assignments/{assignment_id}/today
     Returns: current ProgramDay with all exercises (sets, reps, weight_lbs, rpe_target, coaching_cues)
     Auth: client (their own assignment) or coach (their client's assignment)
```

### Log workout (extend existing POST /workouts)
Extended body:
```json
{
  "assignment_id": "uuid",
  "program_day_id": "uuid",
  "day_status": "completed",
  "duration_minutes": 55,
  "session_rating": 4,
  "notes": "Felt strong",
  "exercise_logs": [
    {
      "program_day_exercise_id": "uuid",
      "exercise_name": "Squat",
      "sets": [
        { "set_number": 1, "actual_reps": 5, "actual_weight_lbs": 225, "actual_rpe": 7.5 },
        { "set_number": 2, "actual_reps": 5, "actual_weight_lbs": 225, "actual_rpe": 8.5 }
      ]
    }
  ]
}
```
After creating WorkoutLog + WorkoutExerciseLogs → call `advance_progress()`.

### Assignment management (new)
```
PATCH /api/v1/workouts/assignments/{id}/progress    → coach manual override of current_week/day
      Body: { current_week, current_day, status }

PATCH /api/v1/workouts/assignments/{id}/feedback    → client submits rating + feedback
      Body: { client_rating: 4.5, client_feedback: "Great program" }
```

---

## Phase 4 — Frontend changes

### New pages

| Route | Component | Purpose |
|---|---|---|
| `/templates` | `TemplateLibrary.tsx` | Browse engine + coach templates with filters |
| `/templates/:source/:templateId` | `TemplateDetail.tsx` | View structure, fill inputs, preview, set start date, save |
| `/my-programs/:assignmentId/log` | `ProgramDayView.tsx` | Today's workout with per-exercise set logging |

### Updated pages

| Page | Change |
|---|---|
| `MyPrograms.tsx` | Progress bar (color-coded green/yellow/red). Show current_week/current_day. Link to /log |
| `ClientDetail.tsx` programs tab | Progress bar per assignment. Day-by-day completion history |
| `App.tsx` | Add new routes |

### New frontend services

| Function | Endpoint |
|---|---|
| `listTemplates(filters)` | `GET /programs/templates` |
| `getTemplateDetail(source, id)` | `GET /programs/templates/{id}` |
| `previewTemplate(source, id, inputs)` | `POST /programs/templates/{id}/preview` |
| `selfStartProgram(source, id, body)` | `POST /programs/templates/{id}/start` |
| `getTodayWorkout(assignmentId)` | `GET /workouts/assignments/{id}/today` |
| `logWorkout(body)` | `POST /workouts` (extended) |
| `submitFeedback(assignmentId, body)` | `PATCH /workouts/assignments/{id}/feedback` |
| `overrideProgress(assignmentId, body)` | `PATCH /workouts/assignments/{id}/progress` |

---

## Implementation order

| Step | What | Files |
|---|---|---|
| 0 | Delete dead models and prune imports | program_assignment.py, program_template.py, __init__.py, database.py |
| 1 | WorkoutExerciseLog model | models/workout_exercise_log.py |
| 2 | Extend WorkoutLog, ClientProgramAssignment, ProgramDay, Program | existing model files |
| 3 | DB recreate + alembic stamp | - |
| 4 | assignment_service.py | schedule_program_days(), advance_progress(), self_start_program() |
| 5 | Extend workout_service.py | wire exercise log creation + call advance_progress() |
| 6 | New schemas | workout_exercise_log.py, program_self_start.py |
| 7 | GET /programs/templates + detail (open auth) | programs.py |
| 8 | POST /templates/{id}/preview + /start | programs.py |
| 9 | GET /workouts/assignments/{id}/today | workouts.py |
| 10 | Extended POST /workouts | workouts.py |
| 11 | PATCH /assignments/{id}/progress + /feedback | new assignments.py |
| 12 | Frontend: TemplateLibrary + TemplateDetail | pages/ |
| 13 | Frontend: ProgramDayView | pages/ |
| 14 | Frontend: progress bars in MyPrograms + ClientDetail | pages/ |
| 15 | Frontend: new routes in App.tsx | App.tsx |
