# TrainGen Engine — API Reference

**Base URL:** `http://localhost:8000`
**All endpoints:** `/api/v1/*`
**Format:** JSON over HTTP — always set `Content-Type: application/json`
**Auth:** None (stateless, no auth required)
**Philosophy:** Every endpoint is **pure and stateless**. The engine never stores anything. You own all persistence.

---

## Table of Contents

1. [Health Check](#1-health-check)
2. [List Program Definitions](#2-list-program-definitions)
3. [Get Program Definition](#3-get-program-definition)
4. [Generate Training Plan](#4-generate-training-plan)
5. [Get Exercise Library](#5-get-exercise-library)
6. [Get Exercise Alternatives](#6-get-exercise-alternatives)
7. [Apply Overrides to Plan](#7-apply-overrides-to-plan)
8. [Validate Definition](#8-validate-definition)
9. [Integration Flow](#9-integration-flow)
10. [Reference: Enum Values](#10-reference-enum-values)
11. [Reference: Prescription Shapes](#11-reference-prescription-shapes)
12. [Error Handling](#12-error-handling)

---

## 1. Health Check

Verify the engine is up and ready.

```
GET /health
```

**Response `200`**
```json
{ "status": "ok" }
```

---

## 2. List Program Definitions

Returns a summary list of every available program template.

```
GET /api/v1/program-definitions
```

**No request body.**

**Response `200`** — array of summaries
```json
[
  {
    "program_id": "strength_ul_4w_v1",
    "version": "1.0.0",
    "name": "UL Strength + Hypertrophy",
    "description": "4-week upper/lower split..."
  }
]
```

| Field | Type | Notes |
|---|---|---|
| `program_id` | `string` | Unique identifier — use this in Generate requests |
| `version` | `string` | Semver string |
| `name` | `string \| null` | Display name |
| `description` | `string \| null` | Short description |

**Available program IDs:**

| `program_id` | Description |
|---|---|
| `strength_ul_4w_v1` | Upper/Lower Strength + Hypertrophy, 4 days/wk |
| `conditioning_4w_v1` | Conditioning engine (run / row / bike / mixed) |
| `hypertrofia_fuerza_4w_v1` | Hypertrophy & strength, Spanish-language |

---

## 3. Get Program Definition

Returns the full definition object — most importantly the `parameter_spec` which tells you what form fields to render before calling Generate.

```
GET /api/v1/program-definitions/{program_id}
```

**Path param:** `program_id` — e.g. `strength_ul_4w_v1`

**Response `200`**
```json
{
  "program_id": "strength_ul_4w_v1",
  "version": "1.0.0",
  "name": "UL Strength + Hypertrophy",
  "description": "...",
  "parameter_spec": {
    "fields": [
      {
        "key": "athlete.level",
        "type": "enum",
        "required": true,
        "enum": ["novice", "intermediate", "advanced"],
        "description": "Training experience level"
      },
      {
        "key": "athlete.equipment",
        "type": "string_array",
        "required": true,
        "description": "Available equipment"
      },
      {
        "key": "athlete.e1rm.squat",
        "type": "number",
        "required_if": "ctx.athlete.level == 'intermediate'",
        "min": 20,
        "max": 400,
        "description": "Squat 1RM in kg"
      }
    ]
  },
  "template": {
    "weeks": { "min": 4, "max": 12 },
    "days_per_week": { "min": 4, "max": 4 }
  }
}
```

### `parameter_spec.fields` — render this as a form

Each field tells you exactly what input to render:

| Field | Type | Notes |
|---|---|---|
| `key` | `string` | Dot-path into the request body (e.g. `athlete.level`) |
| `type` | enum | See field types below |
| `required` | `boolean` | Always required |
| `required_if` | `string \| null` | Conditionally required — evaluate the expression |
| `visible_if` | `string \| null` | Only show when expression is true |
| `default_expr` | `string \| null` | Default value expression (e.g. `'intermediate'`, `[]`, `5`) |
| `min` | `number \| null` | Min value for number fields |
| `max` | `number \| null` | Max value for number fields |
| `enum` | `string[]` | Options list for enum fields |
| `description` | `string \| null` | Label / help text |

**Field types:**

| `type` | Render as |
|---|---|
| `enum` | `<select>` with `field.enum` as options |
| `string` | Text `<input>` |
| `number` | Number `<input>` with min/max |
| `boolean` | `<checkbox>` |
| `string_array` | Multi-select or comma-separated `<input>` |
| `number_array` | Comma-separated numbers |
| `object` | Nested form or JSON textarea |

**Condition expressions** (`visible_if` / `required_if`) use the format:
```
ctx.some.field == 'value'
ctx.athlete.level == 'intermediate' && ctx.rules.main_method == 'HYBRID'
```
Evaluate them by checking your current form values.

**`template`** tells you valid ranges for the schedule inputs:
- `template.weeks.min` / `template.weeks.max` — clamp your weeks slider
- `template.days_per_week.min` / `template.days_per_week.max` — clamp days/week

**Response `404`** — program not found
```json
{ "detail": "Program 'bad_id' not found" }
```

---

## 4. Generate Training Plan

Core endpoint. Sends athlete profile and program parameters; receives a fully-computed multi-week training plan.

```
POST /api/v1/generate
Content-Type: application/json
```

### Request body

```json
{
  "program_id": "strength_ul_4w_v1",
  "program_version": "1.0.0",
  "weeks": 4,
  "days_per_week": 4,
  "athlete": {
    "level": "intermediate",
    "equipment": ["barbell", "rack", "bench", "dumbbells", "cable", "machine", "pullup_bar"],
    "restrictions": [],
    "e1rm": {
      "squat": 160.0,
      "bench": 115.0,
      "deadlift": 190.0,
      "ohp": 70.0
    },
    "time_budget_minutes": 90
  },
  "rules": {
    "rounding_profile": "plate_2p5kg",
    "volume_metric": "hard_sets_weighted",
    "hard_set_rule": "RIR_LE_4",
    "main_method": "HYBRID",
    "accessory_rir_target": 2
  },
  "seed": 42
}
```

### Request fields

| Field | Type | Required | Constraints | Notes |
|---|---|---|---|---|
| `program_id` | `string` | ✅ | min len 1 | From listing |
| `program_version` | `string` | ✅ | min len 1 | From listing |
| `weeks` | `integer` | ✅ | 1–52 | Within definition's `template.weeks` range |
| `days_per_week` | `integer` | ✅ | 1–7 | Within definition's `template.days_per_week` range |
| `athlete` | `object` | ✅ | | Athlete profile |
| `athlete.level` | `enum` | ✅ | | `novice`, `intermediate`, `advanced` |
| `athlete.equipment` | `string[]` | ✅ | | Equipment identifiers — see equipment list below |
| `athlete.restrictions` | `string[]` | ❌ | | Injury/contraindication tags |
| `athlete.e1rm` | `object` | ❌ | values > 0 | Estimated 1-rep maxes in **kg**. Keys: `squat`, `bench`, `deadlift`, `ohp`, `sumo_deadlift`, `kb_press` |
| `athlete.time_budget_minutes` | `float` | ❌ | 10–240 | Session time cap |
| `athlete.modality` | `enum` | ❌ | | For conditioning: `run`, `row`, `bike`, `mixed` |
| `rules` | `object` | ❌ | | Program-specific rules — use values from definition's `parameter_spec` |
| `conditioning` | `object` | ❌ | | Conditioning params (for conditioning programs) |
| `seed` | `integer` | ❌ | ≥ 0 | Deterministic output when set |

**Equipment identifier strings** (use these exactly):
```
barbell, rack, bench, dumbbell, dumbbells, cable, cable_machine, kettlebell,
pullup_bar, pull_up_bar, smith_machine, dip_station, back_raise_bench,
assisted_dip_machine, machine, bands
```

**Rules keys** (program-dependent, from `parameter_spec`):

| Key | Type | Values |
|---|---|---|
| `main_method` | `enum` | `HYBRID`, `PERCENTAGE`, `RPE_ONLY` |
| `rounding_profile` | `enum` | `plate_2p5kg`, `plate_1p25kg`, `dumbbell_2p5`, `none` |
| `volume_metric` | `enum` | `hard_sets_weighted`, `tonnage`, `reps_in_reserve` |
| `hard_set_rule` | `enum` | `RIR_LE_4`, `RPE_GE_6`, `ALL_WORKING` |
| `accessory_rir_target` | `integer` | 0–5 |
| `allow_optional_ohp` | `boolean` | |

**Conditioning keys** (for `conditioning_4w_v1`):

| Key | Type | Notes |
|---|---|---|
| `method` | `enum` | `LISS`, `HIIT`, `TEMPO`, `MIXED` |
| `hr_zone_formula` | `enum` | `KARVONEN`, `MAX_PERCENT` |
| `hr_max` | `integer` | Max heart rate (BPM) |
| `hr_rest` | `integer` | Resting heart rate (BPM) |
| `test_1km_time_seconds` | `integer` | Best 1km time |
| `test_5km_time_seconds` | `integer` | Best 5km time |

---

### Response body `200`

```json
{
  "program_id": "strength_ul_4w_v1",
  "program_version": "1.0.0",
  "generated_at": "2026-03-15T14:32:00.000Z",
  "inputs_echo": { ... },
  "weeks": [
    {
      "week": 1,
      "sessions": [
        {
          "day": 1,
          "tags": ["upper_body", "strength"],
          "blocks": [
            {
              "block_id": "w1d1_d1_main_lift",
              "type": "main_lift",
              "exercise": {
                "id": "bench_press",
                "name": "Bench Press"
              },
              "prescription": { ... }
            }
          ],
          "metrics": {
            "fatigue_score": 7.2,
            "volume_summary": {
              "hard_sets_weighted": { "chest": 3, "triceps": 3 },
              "tonnage": 2250
            }
          }
        }
      ]
    }
  ],
  "warnings": [],
  "repairs": []
}
```

### Response fields

| Field | Type | Notes |
|---|---|---|
| `program_id` | `string` | Echo |
| `program_version` | `string` | Echo |
| `generated_at` | `string` | ISO 8601 datetime |
| `inputs_echo` | `object` | Full inputs echoed back |
| `weeks` | `array` | One entry per week |
| `weeks[].week` | `integer` | Week number (1-based) |
| `weeks[].sessions` | `array` | Sessions in the week |
| `sessions[].day` | `integer` | Day of week (1=Mon … 7=Sun) |
| `sessions[].tags` | `string[]` | Session labels (e.g. `["upper_body"]`) |
| `sessions[].blocks` | `array` | Training blocks |
| `blocks[].block_id` | `string` | Unique across entire plan — use for overrides |
| `blocks[].type` | `string` | Block classification |
| `blocks[].exercise.id` | `string` | Exercise library ID |
| `blocks[].exercise.name` | `string` | Display name |
| `blocks[].prescription` | `object` | Workout prescription — see [Prescription Shapes](#11-reference-prescription-shapes) |
| `sessions[].metrics.fatigue_score` | `float` | 0–10 session fatigue estimate |
| `warnings` | `string[]` | Soft constraint warnings (non-blocking) |
| `repairs` | `string[]` | Log of automated repairs applied |

**`block_id` format:** `w{week}d{day_index}_{block_def_id}` — e.g. `w1d1_d1_main_lift`

**Block types:**

| `type` | Meaning |
|---|---|
| `main_lift` | Primary strength lift |
| `secondary_lift` | Secondary compound movement |
| `accessory` | Accessory exercise |
| `conditioning_steady` | Steady-state cardio block |
| `conditioning_intervals` | Interval cardio block |
| `circuit` | Circuit training block |
| `mobility` | Mobility / flexibility |
| `warmup` | Warm-up block |
| `cooldown` | Cool-down block |

**Response `404`** — unknown program
```json
{ "detail": "Program 'bad_id' not found" }
```

**Response `422`** — validation error on request fields
```json
{
  "detail": [
    { "loc": ["body", "weeks"], "msg": "Input should be greater than or equal to 1", "type": "..." }
  ]
}
```

---

## 5. Get Exercise Library

Full exercise catalog. Use this to build browse UIs, autocomplete, or understand available swap groups.

```
GET /api/v1/exercise-library
```

**No request body.**

**Response `200`**
```json
{
  "version": "1.0.0",
  "exercises": [
    {
      "id": "back_squat",
      "name": "Back Squat",
      "patterns": ["squat"],
      "muscles": {
        "quads": 1.0,
        "glutes": 0.7,
        "erectors": 0.4
      },
      "equipment": ["barbell", "rack"],
      "swap_group": "squat_main",
      "fatigue_cost": 0.9,
      "contraindications": [],
      "tags": ["main", "squat_main", "barbell"]
    }
  ]
}
```

| Field | Type | Notes |
|---|---|---|
| `version` | `string` | Library version |
| `exercises` | `array` | Full exercise list |
| `exercises[].id` | `string` | Stable identifier — use in all other requests |
| `exercises[].name` | `string` | Display name |
| `exercises[].patterns` | `string[]` | Movement patterns (see enum list) |
| `exercises[].muscles` | `object` | Muscle → activation weight (0–1.5) |
| `exercises[].equipment` | `string[]` | Required equipment |
| `exercises[].swap_group` | `string \| null` | Exercises in same group are interchangeable |
| `exercises[].fatigue_cost` | `float` | 0–2; higher = more fatiguing |
| `exercises[].contraindications` | `string[]` | Injury tags that exclude this exercise |
| `exercises[].tags` | `string[]` | Selection tags used internally |

---

## 6. Get Exercise Alternatives

Given an exercise and the athlete's equipment, returns ranked substitute exercises.

```
POST /api/v1/exercises/alternatives
Content-Type: application/json
```

### Request body

```json
{
  "exercise_id": "back_squat",
  "athlete_equipment": ["barbell", "rack"],
  "restrictions": [],
  "exclude_ids": [],
  "limit": 5
}
```

| Field | Type | Required | Constraints |
|---|---|---|---|
| `exercise_id` | `string` | ✅ | Must exist in library |
| `athlete_equipment` | `string[]` | ✅ | |
| `restrictions` | `string[]` | ❌ | Default `[]` — injury tags to exclude |
| `exclude_ids` | `string[]` | ❌ | Default `[]` — exercise IDs to skip |
| `limit` | `integer` | ❌ | 1–20, default `5` |

### Response `200`

```json
{
  "original_exercise_id": "back_squat",
  "alternatives": [
    {
      "id": "front_squat",
      "name": "Front Squat",
      "patterns": ["squat"],
      "tags": ["main", "squat_main", "barbell"],
      "swap_group": "squat_main",
      "fatigue_cost": 0.9,
      "match_reason": "swap_group"
    },
    {
      "id": "goblet_squat",
      "name": "Goblet Squat",
      "patterns": ["squat"],
      "tags": ["accessory", "dumbbell", "kettlebell"],
      "swap_group": null,
      "fatigue_cost": 0.5,
      "match_reason": "pattern_match"
    }
  ]
}
```

**`match_reason` values:**

| Value | Meaning | Priority |
|---|---|---|
| `swap_group` | Same `swap_group` — direct substitute | First in list |
| `pattern_match` | Shares ≥1 movement pattern | After swap_group results |

**Response `404`** — unknown exercise
```json
{ "detail": "Exercise 'bad_id' not found" }
```

---

## 7. Apply Overrides to Plan

Takes a stored `GeneratedPlan` and a list of exercise swaps. Returns the modified plan. **Fully stateless — you must store the result yourself.**

```
POST /api/v1/plans/apply-overrides
Content-Type: application/json
```

### Request body

```json
{
  "plan": { ...GeneratedPlan object from /generate... },
  "overrides": [
    {
      "block_id": "w1d1_d1_main_lift",
      "new_exercise_id": "front_squat"
    }
  ]
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `plan` | `GeneratedPlan` | ✅ | Full plan from `/generate` response |
| `overrides` | `array` | ✅ | Empty array is valid (returns plan unchanged) |
| `overrides[].block_id` | `string` | ✅ | From `blocks[].block_id` in the plan |
| `overrides[].new_exercise_id` | `string` | ✅ | Exercise ID from library |

### Response `200`

```json
{
  "plan": { ...modified GeneratedPlan... },
  "applied": [
    {
      "block_id": "w1d1_d1_main_lift",
      "original_exercise_id": "back_squat",
      "original_exercise_name": "Back Squat",
      "new_exercise_id": "front_squat",
      "new_exercise_name": "Front Squat"
    }
  ],
  "rejected": []
}
```

**`rejected[].reason` values:**

| Reason | Meaning |
|---|---|
| `block_not_found` | `block_id` does not exist in the plan |
| `exercise_not_found` | `new_exercise_id` not in library |
| `incompatible_exercise` | New exercise shares neither `swap_group` nor any pattern with original |

**Compatibility rule:** A swap is accepted if the new exercise either:
- Is in the **same `swap_group`** as the original, OR
- Shares **at least one movement pattern** with the original

**Response `422`** — `plan` object fails GeneratedPlan validation

---

## 8. Validate Definition

Check whether a custom `ProgramDefinition` JSON is structurally valid before using it with Generate.

```
POST /api/v1/validate-definition
Content-Type: application/json
```

### Request body

Send a raw `ProgramDefinition` JSON object:

```json
{
  "program_id": "my_custom_program",
  "version": "1.0.0",
  "name": "My Program",
  "description": "Custom program description",
  "parameter_spec": {
    "fields": [
      {
        "key": "athlete.level",
        "type": "enum",
        "required": true,
        "enum": ["novice", "intermediate", "advanced"]
      }
    ]
  },
  "exercise_library_ref": {
    "type": "file",
    "path": "data/exercise_library_v1.json"
  },
  "template": {
    "weeks": { "min": 4, "max": 12 },
    "days_per_week": { "min": 3, "max": 5 },
    "sessions": [
      {
        "day_index": 1,
        "tags": ["upper_body"],
        "blocks": [
          {
            "id": "d1_main",
            "type": "main_lift",
            "exercise_selector": {
              "count": 1,
              "include_tags": ["horizontal_push", "main"]
            },
            "prescription_ref": "rx_main"
          }
        ]
      }
    ]
  },
  "prescriptions": {
    "rx_main": {
      "mode": "strength",
      "output_mapping": {
        "sets": "5",
        "reps": "5",
        "target_rpe": "8"
      }
    }
  },
  "rules": {},
  "validation": {}
}
```

### Response `200` — valid

```json
{
  "valid": true,
  "errors": []
}
```

### Response `200` — invalid

```json
{
  "valid": false,
  "errors": [
    "template.sessions: List should have at least 1 item after validation, not 0",
    "prescriptions: Field required"
  ]
}
```

| Field | Type | Notes |
|---|---|---|
| `valid` | `boolean` | |
| `errors` | `string[]` | Empty when valid. Each string is `{field.path}: {message}` |

**Response `422`** — request body is not parseable JSON

---

## 9. Integration Flow

Typical sequence for a consumer app to implement the full experience:

```
┌─────────────────────────────────────────────────────────────┐
│  1. SELECT PROGRAM                                          │
│     GET /api/v1/program-definitions                         │
│     → show list to user                                     │
│                                                             │
│  2. BUILD FORM                                              │
│     GET /api/v1/program-definitions/{program_id}           │
│     → render inputs from parameter_spec.fields             │
│     → clamp weeks/days from template.weeks / days_per_week │
│                                                             │
│  3. GENERATE PLAN                                           │
│     POST /api/v1/generate                                   │
│     → store GeneratedPlan in your DB / state               │
│     → render plan to user                                   │
│                                                             │
│  4. EXERCISE SWAP (user requests alternative)              │
│     POST /api/v1/exercises/alternatives                     │
│     → show alternatives list to user                       │
│                                                             │
│  5. APPLY SWAP                                              │
│     POST /api/v1/plans/apply-overrides                      │
│     → store updated plan (replaces old version)            │
│                                                             │
│  6. PERSIST                                                 │
│     Your DB — engine has no storage                        │
│                                                             │
│  7. RE-EDIT (user returns to stored plan)                  │
│     Load plan from your DB                                  │
│     Repeat step 4–5 as needed                              │
└─────────────────────────────────────────────────────────────┘
```

### Minimal integration example (TypeScript)

```typescript
const BASE = process.env.ENGINE_URL ?? 'http://localhost:8000';

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(`API ${res.status}: ${body.detail ?? res.statusText}`);
  }
  return res.json();
}

// 1. List programs
const programs = await apiFetch<ProgramSummary[]>('/api/v1/program-definitions');

// 2. Get full definition (for form rendering)
const def = await apiFetch<ProgramDefinitionFull>(`/api/v1/program-definitions/${programId}`);

// 3. Generate plan
const plan = await apiFetch<GeneratedPlan>('/api/v1/generate', {
  method: 'POST',
  body: JSON.stringify({
    program_id: 'strength_ul_4w_v1',
    program_version: '1.0.0',
    weeks: 4,
    days_per_week: 4,
    athlete: {
      level: 'intermediate',
      equipment: ['barbell', 'rack', 'bench', 'dumbbells'],
      e1rm: { squat: 150, bench: 100, deadlift: 180, ohp: 65 },
    },
    seed: Date.now(), // remove for random
  }),
});

// store plan in your DB here

// 4. Get alternatives for a block's exercise
const alts = await apiFetch('/api/v1/exercises/alternatives', {
  method: 'POST',
  body: JSON.stringify({
    exercise_id: plan.weeks[0].sessions[0].blocks[0].exercise.id,
    athlete_equipment: ['barbell', 'rack', 'bench', 'dumbbells'],
    limit: 5,
  }),
});

// 5. Apply a swap
const updated = await apiFetch('/api/v1/plans/apply-overrides', {
  method: 'POST',
  body: JSON.stringify({
    plan,
    overrides: [
      {
        block_id: plan.weeks[0].sessions[0].blocks[0].block_id,
        new_exercise_id: alts.alternatives[0].id,
      },
    ],
  }),
});

// store updated.plan in your DB
```

---

## 10. Reference: Enum Values

### Athlete Level
```
novice | intermediate | advanced
```

### Athlete Modality (conditioning)
```
run | row | bike | mixed
```

### Movement Patterns
```
squat | hinge | lunge_unilateral |
horizontal_push | horizontal_pull |
vertical_push | vertical_pull |
carry |
core_anti_extension | core_anti_rotation | core_flexion |
rotation |
conditioning_steady | conditioning_intervals
```

### Muscle Groups
```
quads | hamstrings | glutes | adductors | calves | erectors |
lats | upper_back | chest |
delts_anterior | delts_lateral | delts_posterior |
biceps | triceps | forearms_grip |
abs | obliques
```

### Block Types
```
main_lift | secondary_lift | accessory |
conditioning_steady | conditioning_intervals |
circuit | mobility | warmup | cooldown
```

### Rounding Profiles
```
plate_2p5kg | plate_1p25kg | dumbbell_2p5 | none
```

### Rules — Main Method
```
HYBRID | PERCENTAGE | RPE_ONLY
```

### Rules — Volume Metric
```
hard_sets_weighted | tonnage | reps_in_reserve
```

### Rules — Hard Set Rule
```
RIR_LE_4 | RPE_GE_6 | ALL_WORKING
```

### Known Swap Groups
```
squat_main          (back_squat, front_squat, high_bar_squat, low_bar_squat)
hip_hinge_main      (deadlift, sumo_deadlift, trap_bar_deadlift)
horizontal_push_main (bench_press, close_grip_bench_press)
vertical_push_main  (overhead_press, push_press)
horizontal_pull_main (barbell_row, pendlay_row)
```

---

## 11. Reference: Prescription Shapes

The `prescription` field inside each block varies by training type. Use these shapes to render it correctly.

### Strength prescription
```json
{
  "top_set": {
    "sets": 3,
    "reps": 5,
    "target_rpe": 8.0,
    "load_kg": 130.0
  },
  "backoff": [
    {
      "sets": 3,
      "reps": 5,
      "load_kg": 117.0
    }
  ],
  "rounding_profile": "plate_2p5kg"
}
```
Detect with: `"top_set" in prescription`

### Reps-range prescription (hypertrophy accessories)
```json
{
  "sets": 3,
  "reps_range": [8, 12],
  "target_rir": 2,
  "load_note": "moderate weight"
}
```
Detect with: `"reps_range" in prescription`

### Conditioning — steady state
```json
{
  "duration_minutes": 30,
  "intensity": {
    "method": "HR_ZONE",
    "target": "Zone 2 (130–145 BPM)"
  },
  "notes": "Maintain conversational pace"
}
```
Detect with: `"duration_minutes" in prescription && !("work" in prescription)`

### Conditioning — intervals
```json
{
  "warmup_minutes": 5,
  "work": {
    "intervals": 8,
    "seconds_each": 30,
    "intensity": {
      "method": "HR_MAX_PCT",
      "target": "90–95% HR max"
    }
  },
  "rest_seconds": 90,
  "cooldown_minutes": 5,
  "notes": null
}
```
Detect with: `"work" in prescription && "warmup_minutes" in prescription`

---

## 12. Error Handling

All errors follow this structure:

```json
{ "detail": "Human-readable message" }
```

For validation errors (422):
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "athlete", "level"],
      "msg": "Field required"
    }
  ]
}
```

### HTTP status codes used

| Code | Meaning |
|---|---|
| `200` | Success |
| `404` | Resource not found (program or exercise ID unknown) |
| `422` | Request body failed schema validation |
| `500` | Internal server error (generation pipeline failure) |

### Operational notes

- The engine has **no rate limiting** — it's designed for direct internal consumption
- Plan generation is **< 100ms** end-to-end for all supported programs
- The engine is **fully stateless** — restart it without any data loss (it has none)
- `seed` values of `0` and `null` both produce random output; use an explicit positive integer for reproducibility
- A plan's `warnings` array is non-blocking — the plan is usable even with warnings
- If `repairs` is non-empty, the engine had to auto-fix constraint violations during generation — inspect the messages to understand what changed
