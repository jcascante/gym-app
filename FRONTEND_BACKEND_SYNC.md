## Frontend-Backend Synchronization Strategy

This document explains how we keep frontend preview calculations synchronized with backend saved programs.

---

## The Challenge

**Problem**: We want instant preview feedback in the frontend wizard, but we also need the backend to be the single source of truth for saved programs.

**Requirements**:
1. ✅ **Fast UX**: Instant calculations as user types (no API latency)
2. ✅ **Consistency**: Frontend preview must match backend saved program exactly
3. ✅ **Maintainability**: Single source of truth for algorithm logic
4. ✅ **Versioning**: Track which algorithm version generated each program
5. ✅ **Testability**: Validate frontend calculations against backend

---

## The Solution: Three-Tier Sync Strategy

### Tier 1: Shared Constants (Data Sync)

**Backend exposes calculation constants via API:**

```
GET /api/v1/programs/algorithms/strength_linear_5x5/constants
```

**Returns:**
```json
{
  "version": "v1.0.0",
  "builder_type": "strength_linear_5x5",
  "weekly_jump_table": {
    "1": 5, "2": 5, ..., "20": 2
  },
  "ramp_up_table": {
    "1": 51, "2": 52, ..., "20": 70
  },
  "protocol_by_week": {
    "1": {"sets": 5, "reps": 5},
    "6": {"sets": 3, "reps": 3},
    ...
  }
}
```

**Frontend fetches constants on mount:**

```typescript
// In ProgramBuilder.tsx
useEffect(() => {
  fetchCalculationConstants('strength_linear_5x5');
}, []);
```

**Result**: Frontend uses same lookup tables as backend ✅

---

### Tier 2: Mirrored Logic (Algorithm Sync)

**Backend implements calculation logic:**

```python
# backend/app/services/strength_program_generator.py
class StrengthProgramGenerator:
    @classmethod
    def calculate_weekly_jump(cls, max_reps: int, one_rm: float):
        percent = cls.WEEKLY_JUMP_TABLE.get(max_reps, 5)
        lbs = round((one_rm * percent) / 100)
        return percent, lbs
```

**Frontend mirrors the logic using fetched constants:**

```typescript
// frontend/src/services/programCalculations.ts
export async function calculateWeeklyJump(
  maxRepsAt80: number,
  oneRM: number
) {
  const constants = await getConstants();  // Fetched from backend
  const percent = constants.weekly_jump_table[maxRepsAt80] ?? 5;
  const lbs = Math.round((oneRM * percent) / 100);
  return { percent, lbs };
}
```

**Result**: Frontend calculations match backend exactly ✅

---

### Tier 3: Validation API (Verification)

**Backend provides preview endpoint (calculate without saving):**

```
POST /api/v1/programs/preview
```

**Request:**
```json
{
  "movements": [
    {
      "name": "Squat",
      "one_rm": 315,
      "max_reps_at_80_percent": 12,
      "target_weight": 275
    }
  ]
}
```

**Response:**
```json
{
  "algorithm_version": "v1.0.0",
  "calculated_data": {
    "Squat": {
      "weekly_jump_percent": 3,
      "weekly_jump_lbs": 9,
      "ramp_up_percent": 62,
      "ramp_up_base_lbs": 195
    }
  },
  "weeks": [...full program structure...]
}
```

**Frontend can validate its calculations:**

```typescript
const validation = await validateCalculations(movements);
if (!validation.valid) {
  console.error('Mismatch detected:', validation.errors);
  // Show warning to user
}
```

**Result**: Frontend can verify its preview matches backend ✅

---

## Complete Workflow

### 1. Program Builder Page Loads

```typescript
// ProgramBuilder.tsx
const [constants, setConstants] = useState<CalculationConstants | null>(null);

useEffect(() => {
  // Fetch constants from backend
  fetchCalculationConstants('strength_linear_5x5')
    .then(setConstants)
    .catch(err => {
      console.error('Failed to load constants:', err);
      // Use fallback constants (hardcoded, less ideal)
    });
}, []);
```

### 2. User Enters 1RM

```typescript
const handleOneRMChange = async (movementId: string, oneRM: number) => {
  // Calculate 80% (always the same)
  const eightyPercent = calculate80Percent(oneRM);

  // Update movement
  updateMovement(movementId, {
    oneRM,
    eightyPercentRM: eightyPercent
  });
};
```

### 3. User Enters Max Reps at 80%

```typescript
const handleMaxRepsChange = async (movementId: string, maxReps: number, oneRM: number) => {
  // Calculate using backend constants
  const { percent: weeklyJumpPercent, lbs: weeklyJumpLbs } =
    await calculateWeeklyJump(maxReps, oneRM);

  const { percent: rampUpPercent, baseLbs: rampUpBaseLbs } =
    await calculateRampUp(maxReps, oneRM);

  // Update movement
  updateMovement(movementId, {
    maxRepsAt80: maxReps,
    weeklyJumpPercent,
    weeklyJumpLbs,
    rampUpPercent,
    rampUpBaseLbs
  });
};
```

### 4. Frontend Shows Preview (Final Step)

```typescript
// Calculate weights for each week using backend constants
const week1Weight = calculateWeightForWeek(
  movement.targetWeight,
  1,  // week number
  movement.weeklyJumpLbs,
  true  // is heavy day
);

// Display preview to user
```

### 5. (Optional) Validate Before Saving

```typescript
const handleSaveClick = async () => {
  // Validate calculations against backend
  const validation = await validateCalculations(movements);

  if (!validation.valid) {
    // Show warning dialog
    const proceed = confirm(
      'Frontend calculations differ from backend. ' +
      'Backend will be used as source of truth. Continue?'
    );
    if (!proceed) return;
  }

  // Save program
  await saveProgram();
};
```

### 6. Save Program

```typescript
const saveProgram = async () => {
  // Send INPUTS (not calculated program) to backend
  const response = await fetch('/api/v1/programs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      builder_type: 'strength_linear_5x5',
      name: programName,
      movements: movements.map(m => ({
        name: m.name,
        one_rm: m.oneRM,
        max_reps_at_80_percent: m.maxRepsAt80,
        target_weight: m.targetWeight
      })),
      is_template: true
    })
  });

  // Backend will:
  // 1. Re-calculate using its algorithm (source of truth)
  // 2. Generate full program structure
  // 3. Save to database with algorithm version
  // 4. Return saved program

  const savedProgram = await response.json();

  // Redirect to template library or assignment flow
  navigate(`/templates/${savedProgram.id}`);
};
```

---

## What Gets Stored in Database

When backend saves a program, it stores:

```json
{
  "id": "uuid",
  "name": "8-Week Linear Strength",
  "algorithm_version": "v1.0.0",  // ← Track which version was used
  "input_data": {  // ← Original inputs (reproducible)
    "movements": [
      {
        "name": "Squat",
        "one_rm": 315,
        "max_reps_at_80_percent": 12,
        "target_weight": 275
      }
    ]
  },
  "calculated_data": {  // ← Calculated values (for analytics)
    "Squat": {
      "weekly_jump_percent": 3,
      "weekly_jump_lbs": 9,
      "ramp_up_percent": 62,
      "ramp_up_base_lbs": 195
    }
  },
  "weeks": [...]  // ← Full program structure
}
```

---

## Benefits of This Approach

### ✅ Fast User Experience
- Frontend uses cached constants for instant calculations
- No API calls during wizard (except initial constant fetch)
- User sees preview update in real-time

### ✅ Backend is Source of Truth
- Backend recalculates on save
- Database stores algorithm version used
- Can regenerate program from inputs if algorithm changes

### ✅ Consistency Guaranteed
- Frontend fetches constants from backend (data sync)
- Frontend mirrors backend logic (algorithm sync)
- Frontend can validate preview (verification)

### ✅ Easy to Update Algorithm
- Update backend constants/logic
- Frontend automatically uses new constants on next fetch
- Old programs tracked with algorithm version

### ✅ Testable and Debuggable
- Can compare frontend vs backend calculations
- Validation API catches mismatches
- Algorithm version tracking for debugging

---

## Testing Strategy

### 1. Unit Tests (Backend)

```python
# backend/tests/test_strength_generator.py
def test_weekly_jump_calculation():
    """Test weekly jump calculation matches expected values."""
    gen = StrengthProgramGenerator()

    # 12 reps at 80% should give 3% weekly jump
    percent, lbs = gen.calculate_weekly_jump(
        max_reps=12,
        one_rm=300
    )

    assert percent == 3
    assert lbs == 9  # 300 * 0.03 = 9
```

### 2. Integration Tests (Frontend vs Backend)

```typescript
// frontend/src/services/__tests__/programCalculations.test.ts
test('frontend calculations match backend', async () => {
  const movements = [
    {
      name: 'Squat',
      oneRM: 315,
      maxRepsAt80: 12,
      targetWeight: 275
    }
  ];

  const validation = await validateCalculations(movements);

  expect(validation.valid).toBe(true);
  expect(validation.errors).toHaveLength(0);
});
```

### 3. Manual Validation (During Development)

```typescript
// In browser console during testing
const movements = getMovementsFromState();
const validation = await validateCalculations(movements);
console.table(validation.errors);
```

---

## Updating the Algorithm

When you need to change calculation logic:

### Step 1: Update Backend
```python
# backend/app/services/strength_program_generator.py
class StrengthProgramGenerator:
    VERSION = "v1.1.0"  # ← Bump version

    WEEKLY_JUMP_TABLE = {
        # Updated table
        20: 1.5, 19: 1.5, ...  # ← Changed values
    }
```

### Step 2: Frontend Automatically Syncs
```typescript
// Frontend will fetch new constants automatically
// No code changes needed if logic structure is the same
```

### Step 3: Old Programs Unaffected
```sql
-- Old programs keep their version
SELECT name, algorithm_version FROM programs;
-- "Program A", "v1.0.0"  ← Still uses old algorithm
-- "Program B", "v1.1.0"  ← Uses new algorithm
```

### Step 4: (Optional) Migrate Old Programs
```python
# Migration script to regenerate old programs with new algorithm
async def migrate_programs_to_v1_1():
    old_programs = await db.query(Program).filter(
        Program.algorithm_version == "v1.0.0"
    ).all()

    for program in old_programs:
        # Regenerate from input_data
        new_program = StrengthProgramGenerator.generate_preview(
            program.input_data
        )

        # Update program with new calculations
        program.algorithm_version = new_program.algorithm_version
        program.calculated_data = new_program.calculated_data
        program.weeks = new_program.weeks

    await db.commit()
```

---

## Troubleshooting

### Frontend Preview Doesn't Match Backend

**Symptoms**: Validation fails, errors in console

**Causes**:
1. Frontend didn't fetch latest constants
2. Frontend logic doesn't mirror backend
3. Rounding differences

**Solution**:
```typescript
// Force refetch constants
await fetchCalculationConstants('strength_linear_5x5');

// Validate again
const validation = await validateCalculations(movements);
console.log(validation.errors);
```

### Constants API Fails

**Symptoms**: Frontend falls back to hardcoded constants

**Solution**:
1. Check backend is running
2. Check authentication token is valid
3. Update fallback constants to match backend

```typescript
// frontend/src/services/programCalculations.ts
function getFallbackConstants() {
  // Update these to match backend exactly
  return {
    version: 'v1.0.0-fallback',
    weekly_jump_table: {...},  // ← Keep in sync
    ramp_up_table: {...}
  };
}
```

---

## Summary

**Three tiers keep frontend and backend in sync:**

1. **Shared Constants** (API) - Frontend fetches lookup tables from backend
2. **Mirrored Logic** (Code) - Frontend implements same calculations as backend
3. **Validation API** (Verification) - Frontend can verify preview matches backend

**Workflow:**
1. Load constants → 2. Calculate preview → 3. Validate (optional) → 4. Save

**Result:**
- ✅ Fast, instant preview for user
- ✅ Backend is always source of truth
- ✅ Calculations guaranteed to match
- ✅ Easy to update algorithm
- ✅ Versioned and traceable
