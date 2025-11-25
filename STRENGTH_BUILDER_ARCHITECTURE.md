# Strength Builder Architecture Analysis

## Current Implementation Review

### Calculations Currently in Frontend

The existing Strength Builder (`frontend/src/pages/ProgramBuilder.tsx`) performs the following calculations client-side:

1. **80% of 1RM Calculation** (Line 233)
   ```typescript
   const eightyPercent = value > 0 ? Math.round(value * 0.8) : 0;
   ```

2. **Weekly Jump Calculation** (Lines 331-332)
   - Uses lookup table based on max reps at 80%
   - Maps reps (1-20) to weekly progression percentage (2-5%)
   ```typescript
   const weeklyJumpTable: { [key: number]: number } = {
     20: 2, 19: 2, 18: 2, 17: 2, 16: 2,
     15: 3, 14: 3, 13: 3, 12: 3, 11: 3,
     10: 4, 9: 4, 8: 4, 7: 4, 6: 4,
     5: 5, 4: 5, 3: 5, 2: 5, 1: 5
   };
   const weeklyJumpPercent = weeklyJumpTable[value] || 5;
   const weeklyJumpLbs = Math.round((movement.oneRM * weeklyJumpPercent) / 100);
   ```

3. **Ramp Up Calculation** (Lines 333-334)
   - Uses lookup table based on max reps at 80%
   - Maps reps (1-20) to starting percentage (51-70%)
   ```typescript
   const rampUpTable: { [key: number]: number } = {
     20: 70, 19: 69, 18: 68, 17: 67, 16: 66,
     15: 65, 14: 64, 13: 63, 12: 62, 11: 61,
     10: 60, 9: 59, 8: 58, 7: 57, 6: 56,
     5: 55, 4: 54, 3: 53, 2: 52, 1: 51
   };
   const rampUpPercent = rampUpTable[value] || 55;
   const rampUpBaseLbs = Math.round((movement.oneRM * rampUpPercent) / 100);
   ```

4. **Week-by-Week Progression** (Lines 598-606)
   ```typescript
   const weights = [
     movement.targetWeight - (4 * movement.weeklyJumpLbs), // Week 1
     movement.targetWeight - (3 * movement.weeklyJumpLbs), // Week 2
     movement.targetWeight - (2 * movement.weeklyJumpLbs), // Week 3
     movement.targetWeight - movement.weeklyJumpLbs,       // Week 4
     movement.targetWeight,                                 // Week 5
     movement.targetWeight + movement.weeklyJumpLbs,       // Week 6
     movement.targetWeight + (2 * movement.weeklyJumpLbs), // Week 7
   ];
   ```

5. **Heavy/Light Day Split** (Lines 646, 668)
   ```typescript
   const heavyWeight = movement.targetWeight - ((5 - week) * movement.weeklyJumpLbs);
   const lightWeight = Math.round(heavyWeight * 0.8);
   ```

6. **Percentage of 1RM Display** (Line 647)
   ```typescript
   const percentage = Math.round((heavyWeight / movement.oneRM) * 100);
   ```

### Program Structure Generated

- **8 weeks total**
- **4 sessions per week** (Mon/Wed/Fri/Sat)
- **Alternating heavy-light pattern**: Heavy → Light → Heavy → Light
- **Progressive protocols**:
  - Weeks 1-5: 5×5
  - Week 6: 3×3
  - Week 7: 2×2
  - Week 8: Testing week

---

## Architectural Options

### Option 1: Keep Calculations in Frontend (Current Approach)

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│  FRONTEND (React)                                        │
│                                                          │
│  [Wizard UI] → [Calculations] → [Preview] → [Submit]   │
│                                                          │
│  - 80% calc                                             │
│  - Weekly jump calc                                     │
│  - Ramp up calc                                         │
│  - Week progression                                     │
│  - Heavy/light split                                    │
│  - Full program generation                              │
│                                                          │
│  ↓ POST: Final program data (all weeks/days/exercises) │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  BACKEND (FastAPI)                                       │
│                                                          │
│  POST /api/v1/programs                                  │
│  - Validate input data                                  │
│  - Store program as-is in database                      │
│  - No calculations, just CRUD                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Pros:**
✅ **Immediate feedback** - No network latency during wizard steps
✅ **Offline capable** - Can complete wizard without backend
✅ **Simple backend** - Just CRUD operations
✅ **Reduced server load** - No computation on every input change
✅ **Better UX** - Real-time preview updates
✅ **Current code works** - No refactoring needed

**Cons:**
❌ **Logic duplication** - Need to replicate in mobile apps, other clients
❌ **Hard to update** - Algorithm changes require frontend redeployment
❌ **No A/B testing** - Can't test different calculation methods easily
❌ **No versioning** - Can't track which algorithm version generated a program
❌ **Potential inconsistency** - Frontend and backend could drift
❌ **Limited analytics** - Can't log which inputs produce best results

---

### Option 2: Move All Calculations to Backend

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│  FRONTEND (React)                                        │
│                                                          │
│  [Wizard UI] → [Input Collection] → [Preview Request]  │
│                                                          │
│  ↓ POST: Input data (movements, 1RMs, reps, target)    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  BACKEND (FastAPI)                                       │
│                                                          │
│  POST /api/v1/programs/generate                         │
│  - Perform all calculations                             │
│  - Apply weekly jump algorithm                          │
│  - Apply ramp up algorithm                              │
│  - Generate full 8-week program                         │
│  - Return complete program structure                     │
│                                                          │
│  Program Generator Service:                             │
│  class StrengthProgramGenerator:                        │
│    - calculate_weekly_jump()                            │
│    - calculate_ramp_up()                                │
│    - generate_week_progression()                        │
│    - generate_sessions()                                │
│                                                          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                    [Database]
```

**Pros:**
✅ **Single source of truth** - Algorithm lives in one place
✅ **Easy to update** - Backend-only deployment for algorithm changes
✅ **Versioning** - Track which algorithm version was used
✅ **A/B testing** - Easy to test different calculation methods
✅ **Analytics** - Log inputs/outputs, analyze success rates
✅ **Reusable** - Mobile apps, API clients use same logic
✅ **Testable** - Unit tests for calculation logic
✅ **Auditable** - Know exactly what was calculated and when

**Cons:**
❌ **Network dependency** - Requires API calls for preview
❌ **Latency** - User waits for calculation on each step
❌ **More complex backend** - Need to implement generator service
❌ **Server load** - Calculations on every preview request
❌ **Worse UX** - Delayed feedback, loading states
❌ **Refactoring required** - Significant frontend changes

---

### Option 3: Hybrid Approach (RECOMMENDED)

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│  FRONTEND (React)                                        │
│                                                          │
│  [Wizard UI] → [Client-side Preview] → [Submit]        │
│                                                          │
│  - Keep calculations for real-time preview              │
│  - Show immediate feedback to user                      │
│  - Mirror backend algorithm (shared constants)          │
│                                                          │
│  ↓ POST: Input data (movements, 1RMs, reps, target)    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  BACKEND (FastAPI)                                       │
│                                                          │
│  POST /api/v1/programs                                  │
│  - Receive input data (NOT pre-calculated program)      │
│  - Re-calculate using backend algorithm (source of truth)│
│  - Generate full program structure                       │
│  - Store in database with metadata:                      │
│    • algorithm_version: "linear_5x5_v1"                 │
│    • input_data: {1RMs, reps, etc.}                     │
│    • calculated_data: {weekly jumps, etc.}              │
│                                                          │
│  Program Generator Service:                             │
│  class StrengthProgramGenerator:                        │
│    VERSION = "v1.0.0"                                   │
│    WEEKLY_JUMP_TABLE = {...}  # Source of truth         │
│    RAMP_UP_TABLE = {...}      # Source of truth         │
│                                                          │
│    def generate(inputs: ProgramInputs) -> Program:      │
│      # Calculate and return full program                │
│                                                          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                    [Database]
                    - Stores inputs
                    - Stores generated program
                    - Stores algorithm version
```

**Frontend sends:**
```json
{
  "builder_type": "strength_linear_5x5",
  "movements": [
    {
      "name": "Squat",
      "one_rm": 315,
      "max_reps_at_80_percent": 12,
      "target_weight": 275
    },
    // ... more movements
  ]
}
```

**Backend generates and stores:**
```json
{
  "id": "uuid",
  "builder_type": "strength_linear_5x5",
  "algorithm_version": "v1.0.0",
  "input_data": {
    "movements": [...]  // Original inputs
  },
  "calculated_data": {
    "squat": {
      "weekly_jump_percent": 3,
      "weekly_jump_lbs": 9,
      "ramp_up_percent": 62,
      "ramp_up_base_lbs": 195
    }
  },
  "weeks": [
    {
      "week_number": 1,
      "days": [
        {
          "day_number": 1,
          "exercises": [
            {
              "exercise_name": "Squat",
              "sets": 5,
              "reps": 5,
              "weight_lbs": 239,
              "percentage_1rm": 76
            }
          ]
        }
      ]
    }
  ]
}
```

**Pros:**
✅ **Best UX** - Immediate frontend preview feedback
✅ **Single source of truth** - Backend validates and regenerates
✅ **Versioning** - Track which algorithm was used
✅ **Analytics** - Store inputs and calculated outputs
✅ **Reproducible** - Can regenerate program from inputs
✅ **Testable** - Backend logic is unit tested
✅ **Updateable** - Can improve algorithm over time
✅ **A/B testable** - Backend can apply different algorithms
✅ **Debuggable** - Know if frontend/backend calculations diverge

**Cons:**
⚠️ **Need to maintain sync** - Frontend mirrors backend constants
⚠️ **Two implementations** - But backend is authoritative

---

## Recommendation: Hybrid Approach

### Implementation Strategy

#### Phase 1: Extract Backend Program Generator

1. **Create backend service** (`backend/app/services/strength_program_generator.py`):
```python
from typing import List, Dict
from pydantic import BaseModel

class MovementInput(BaseModel):
    name: str
    one_rm: float
    max_reps_at_80_percent: int
    target_weight: float

class ProgramInputs(BaseModel):
    movements: List[MovementInput]
    duration_weeks: int = 8
    days_per_week: int = 4

class StrengthProgramGenerator:
    VERSION = "v1.0.0"

    # Source of truth for calculation tables
    WEEKLY_JUMP_TABLE = {
        20: 2, 19: 2, 18: 2, 17: 2, 16: 2,
        15: 3, 14: 3, 13: 3, 12: 3, 11: 3,
        10: 4, 9: 4, 8: 4, 7: 4, 6: 4,
        5: 5, 4: 5, 3: 5, 2: 5, 1: 5
    }

    RAMP_UP_TABLE = {
        20: 70, 19: 69, 18: 68, 17: 67, 16: 66,
        15: 65, 14: 64, 13: 63, 12: 62, 11: 61,
        10: 60, 9: 59, 8: 58, 7: 57, 6: 56,
        5: 55, 4: 54, 3: 53, 2: 52, 1: 51
    }

    def calculate_weekly_jump(self, max_reps: int, one_rm: float) -> tuple[int, float]:
        """Calculate weekly progression percentage and pounds."""
        percent = self.WEEKLY_JUMP_TABLE.get(max_reps, 5)
        pounds = round((one_rm * percent) / 100)
        return percent, pounds

    def calculate_ramp_up(self, max_reps: int, one_rm: float) -> tuple[int, float]:
        """Calculate ramp-up starting percentage and base weight."""
        percent = self.RAMP_UP_TABLE.get(max_reps, 55)
        base_lbs = round((one_rm * percent) / 100)
        return percent, base_lbs

    def generate_program(self, inputs: ProgramInputs) -> Dict:
        """Generate complete 8-week strength program."""
        program = {
            "algorithm_version": self.VERSION,
            "input_data": inputs.dict(),
            "calculated_data": {},
            "weeks": []
        }

        # Calculate movement-specific data
        for movement in inputs.movements:
            weekly_jump_pct, weekly_jump_lbs = self.calculate_weekly_jump(
                movement.max_reps_at_80_percent,
                movement.one_rm
            )
            ramp_up_pct, ramp_up_base = self.calculate_ramp_up(
                movement.max_reps_at_80_percent,
                movement.one_rm
            )

            program["calculated_data"][movement.name] = {
                "weekly_jump_percent": weekly_jump_pct,
                "weekly_jump_lbs": weekly_jump_lbs,
                "ramp_up_percent": ramp_up_pct,
                "ramp_up_base_lbs": ramp_up_base
            }

        # Generate weeks 1-8
        for week_num in range(1, 9):
            week = self._generate_week(week_num, inputs, program["calculated_data"])
            program["weeks"].append(week)

        return program

    def _generate_week(self, week_num: int, inputs: ProgramInputs, calc_data: Dict) -> Dict:
        """Generate a single week of training."""
        week = {
            "week_number": week_num,
            "name": self._get_week_name(week_num),
            "days": []
        }

        # Week 8 is testing week (different structure)
        if week_num == 8:
            week["days"].append(self._generate_test_day(inputs))
            return week

        # Determine protocol (5x5, 3x3, 2x2)
        sets, reps = self._get_protocol_for_week(week_num)

        # Generate 4 sessions: Heavy, Light, Heavy, Light
        for day_num in range(1, 5):
            is_heavy = day_num % 2 == 1  # Days 1,3 are heavy; 2,4 are light
            day = self._generate_day(
                day_num,
                week_num,
                inputs,
                calc_data,
                sets,
                reps,
                is_heavy
            )
            week["days"].append(day)

        return week

    def _generate_day(
        self,
        day_num: int,
        week_num: int,
        inputs: ProgramInputs,
        calc_data: Dict,
        sets: int,
        reps: int,
        is_heavy: bool
    ) -> Dict:
        """Generate a single training day."""
        day_names = {
            1: "Monday",
            2: "Wednesday",
            3: "Friday",
            4: "Saturday"
        }

        day = {
            "day_number": day_num,
            "name": f"Session {day_num} - {'Heavy' if is_heavy else 'Light'} Day",
            "suggested_day_of_week": day_names[day_num],
            "exercises": []
        }

        # Add exercises for all movements
        for movement in inputs.movements:
            exercise = self._calculate_exercise(
                movement,
                week_num,
                calc_data[movement.name],
                sets,
                reps,
                is_heavy
            )
            day["exercises"].append(exercise)

        return day

    def _calculate_exercise(
        self,
        movement: MovementInput,
        week_num: int,
        calc_data: Dict,
        sets: int,
        reps: int,
        is_heavy: bool
    ) -> Dict:
        """Calculate weight for a specific exercise."""
        # Calculate heavy weight for this week
        # Weeks 1-5: linear progression toward target
        # Week 6: target + 1 jump
        # Week 7: target + 2 jumps
        if week_num <= 5:
            heavy_weight = movement.target_weight - ((5 - week_num) * calc_data["weekly_jump_lbs"])
        elif week_num == 6:
            heavy_weight = movement.target_weight + calc_data["weekly_jump_lbs"]
        else:  # week 7
            heavy_weight = movement.target_weight + (2 * calc_data["weekly_jump_lbs"])

        # Light weight is 80% of heavy
        weight = heavy_weight if is_heavy else round(heavy_weight * 0.8)
        percentage_1rm = round((weight / movement.one_rm) * 100)

        return {
            "exercise_name": movement.name.upper() if is_heavy else movement.name.lower(),
            "sets": sets,
            "reps": reps,
            "weight_lbs": weight,
            "percentage_1rm": percentage_1rm,
            "notes": ""
        }

    def _get_protocol_for_week(self, week_num: int) -> tuple[int, int]:
        """Get sets and reps for the week."""
        if week_num <= 5:
            return 5, 5  # 5x5
        elif week_num == 6:
            return 3, 3  # 3x3
        else:  # week 7
            return 2, 2  # 2x2

    def _get_week_name(self, week_num: int) -> str:
        """Get descriptive name for the week."""
        if week_num == 1:
            return "Foundation Phase"
        elif week_num <= 5:
            return f"Building Phase - Week {week_num}"
        elif week_num == 6:
            return "Intensification Phase"
        elif week_num == 7:
            return "Peak Phase"
        else:
            return "Testing Week"

    def _generate_test_day(self, inputs: ProgramInputs) -> Dict:
        """Generate testing week day."""
        return {
            "day_number": 1,
            "name": "1RM Test Day",
            "suggested_day_of_week": "Wednesday",
            "exercises": [
                {
                    "exercise_name": movement.name.upper(),
                    "sets": 1,
                    "reps": 1,
                    "weight_lbs": None,  # To be determined
                    "percentage_1rm": 100,
                    "notes": "Test new 1RM. Previous: {movement.one_rm} lbs"
                }
                for movement in inputs.movements
            ]
        }
```

2. **Create API endpoint** (`backend/app/api/programs.py`):
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.strength_program_generator import (
    StrengthProgramGenerator,
    ProgramInputs
)
from app.core.database import get_db
from app.models import Program, ProgramWeek, ProgramDay, ProgramDayExercise

router = APIRouter()

@router.post("/programs")
async def create_program(
    inputs: ProgramInputs,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new strength program from inputs.
    Backend re-calculates everything to be source of truth.
    """
    # Generate program using backend algorithm
    generator = StrengthProgramGenerator()
    generated = generator.generate_program(inputs)

    # Store in database
    program = Program(
        subscription_id=current_user.subscription_id,
        created_by=current_user.id,
        name=f"8-Week Linear Strength",  # TODO: Allow custom name
        program_type="strength",
        difficulty_level="intermediate",
        duration_weeks=8,
        days_per_week=4,
        is_template=True,
        algorithm_version=generated["algorithm_version"],
        input_data=generated["input_data"],
        calculated_data=generated["calculated_data"]
    )
    db.add(program)
    await db.flush()  # Get program.id

    # Create weeks, days, exercises from generated data
    for week_data in generated["weeks"]:
        week = ProgramWeek(
            program_id=program.id,
            week_number=week_data["week_number"],
            name=week_data["name"]
        )
        db.add(week)
        await db.flush()

        for day_data in week_data["days"]:
            day = ProgramDay(
                program_week_id=week.id,
                day_number=day_data["day_number"],
                name=day_data["name"],
                suggested_day_of_week=day_data.get("suggested_day_of_week")
            )
            db.add(day)
            await db.flush()

            for i, ex_data in enumerate(day_data["exercises"], 1):
                exercise = ProgramDayExercise(
                    program_day_id=day.id,
                    exercise_order=i,
                    exercise_name=ex_data["exercise_name"],
                    sets=ex_data["sets"],
                    reps_target=ex_data["reps"],
                    load_value=ex_data["weight_lbs"],
                    load_unit="lbs",
                    notes=ex_data["notes"]
                )
                db.add(exercise)

    await db.commit()
    await db.refresh(program)

    return program
```

#### Phase 2: Update Frontend to Send Inputs

Modify `ProgramBuilder.tsx` to submit inputs instead of pre-calculated program:

```typescript
const handleSaveProgram = async () => {
  const programInputs = {
    builder_type: "strength_linear_5x5",
    movements: movements.map(m => ({
      name: m.name,
      one_rm: m.oneRM,
      max_reps_at_80_percent: m.maxRepsAt80,
      target_weight: m.targetWeight
    }))
  };

  try {
    const response = await fetch('/api/v1/programs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(programInputs)
    });

    const program = await response.json();
    // Redirect to template library or assignment flow
  } catch (error) {
    console.error('Failed to save program:', error);
  }
};
```

#### Phase 3: Shared Constants (Future Enhancement)

To keep frontend/backend in sync, consider:

1. **API endpoint to fetch calculation constants**:
   ```
   GET /api/v1/programs/algorithms/strength_linear_5x5/constants
   ```
   Returns:
   ```json
   {
     "version": "v1.0.0",
     "weekly_jump_table": {...},
     "ramp_up_table": {...}
   }
   ```

2. **Frontend fetches constants on mount**:
   - Ensures frontend preview matches backend
   - Allows backend to update constants without frontend deploy

---

## Migration Plan

### Week 1: Backend Implementation
- [ ] Create `StrengthProgramGenerator` service
- [ ] Add unit tests for calculations
- [ ] Create `POST /api/v1/programs` endpoint
- [ ] Test program generation end-to-end

### Week 2: Frontend Integration
- [ ] Update ProgramBuilder.tsx to submit inputs
- [ ] Update final step to call API
- [ ] Add loading states
- [ ] Handle success/error cases
- [ ] Add "Save as Template" vs "Assign to Client" options

### Week 3: Validation & Testing
- [ ] Compare frontend preview vs backend generated programs
- [ ] Add integration tests
- [ ] Test with various input combinations
- [ ] Document any discrepancies and fix

### Week 4: Enhancement (Optional)
- [ ] Add constants API endpoint
- [ ] Frontend fetches constants dynamically
- [ ] Add algorithm version display in UI

---

## Summary

**Recommended Architecture: Hybrid Approach**

- ✅ **Frontend**: Keep calculations for immediate preview feedback (best UX)
- ✅ **Backend**: Re-calculate on submit as source of truth (best architecture)
- ✅ **Database**: Store both inputs and calculated data for reproducibility
- ✅ **Versioning**: Track algorithm version for future improvements
- ✅ **Analytics**: Understand which inputs produce successful programs

This gives you the best of both worlds: great user experience with frontend previews, and reliable, versioned, testable backend logic that serves as the single source of truth.
