# Coach Workflow: Client Management and Program Assignment

## Overview

This document defines the coach-centric workflow for managing clients and assigning programs. The flow prioritizes simplicity and speed for coaches while capturing essential client data.

---

## Complete Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Coach Views Client List                            │
│  - See all assigned clients                                  │
│  - Search/filter clients                                     │
│  - Click "Add New Client" or select existing client          │
└─────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌─────────────────────┐      ┌─────────────────────────┐
│  New Client         │      │  Existing Client        │
│                     │      │                         │
│  - Enter email      │      │  - Load profile         │
│  - Check if exists  │      │  - View history         │
│  - Create account   │      │  - See current programs │
│  - Minimal profile  │      │                         │
└─────────────────────┘      └─────────────────────────┘
          │                               │
          └───────────────┬───────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Coach Builds Program                               │
│  - Select program builder type (Strength, Hypertrophy, etc) │
│  - Fill in program parameters                                │
│  - Use client data if available (1RMs, preferences)          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Generate Preview                                    │
│  - Backend generates full program                            │
│  - Shows all weeks, days, exercises                          │
│  - Displays calculated weights, sets, reps                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: Coach Reviews and Adjusts                          │
│  - Preview full 8-week program                               │
│  - Make adjustments:                                         │
│    • Modify exercise weights                                 │
│    • Change exercise selection                               │
│    • Adjust sets/reps                                        │
│    • Add notes/cues                                          │
│  - Approve program                                           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: Assign Program to Client                           │
│  - Set start date                                            │
│  - Add assignment notes                                      │
│  - Confirm assignment                                        │
│  - Client receives notification                              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  RESULT: Client has active program                           │
│  - Client can view program in their dashboard                │
│  - Client can start logging workouts                         │
│  - Coach can monitor progress                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Client Selection/Creation

### Coach Dashboard - Client List View

```typescript
interface ClientListView {
  // Coach sees their assigned clients
  clients: Array<{
    id: string;
    name: string;
    email: string;
    profilePhoto?: string;
    activePrograms: number;
    lastWorkout?: Date;
    status: 'active' | 'inactive' | 'new';
  }>;

  actions: {
    addNewClient: () => void;
    selectClient: (clientId: string) => void;
    searchClients: (query: string) => void;
  };
}
```

**UI Layout:**

```
┌────────────────────────────────────────────────────────┐
│  My Clients                          [+ Add New Client]│
├────────────────────────────────────────────────────────┤
│                                                         │
│  🔍 Search clients...                                  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │ 👤 John Doe (john@email.com)                    │  │
│  │    Active: "8-Week Strength" - Week 3/8         │  │
│  │    Last workout: 2 days ago                     │  │
│  │    [View Progress] [Build New Program]          │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │ 👤 Jane Smith (jane@email.com)                  │  │
│  │    No active program                             │  │
│  │    Last workout: 1 week ago                     │  │
│  │    [View Profile] [Build Program]               │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │ 👤 Mike Johnson (mike@email.com) 🆕            │  │
│  │    Just added - No program yet                   │  │
│  │    [Complete Profile] [Build Program]           │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
└────────────────────────────────────────────────────────┘
```

### Add New Client Flow

**Option A: Client Already Exists (Invitation Flow)**

```
┌────────────────────────────────────────┐
│  Add New Client                         │
├────────────────────────────────────────┤
│                                         │
│  Email: [________________]  [Check]    │
│                                         │
│  ✅ Found: John Doe (john@email.com)   │
│  Currently working with Coach Sarah     │
│                                         │
│  [Send Connection Request]              │
│                                         │
└────────────────────────────────────────┘
```

**Option B: New Client (Create Account)**

```
┌────────────────────────────────────────┐
│  Add New Client                         │
├────────────────────────────────────────┤
│                                         │
│  Email: [________________]  [Check]    │
│                                         │
│  ℹ️  No account found. Create new      │
│                                         │
│  First Name: [__________]              │
│  Last Name:  [__________]              │
│                                         │
│  ☐ Send welcome email with login       │
│                                         │
│  [Create Client]                        │
│                                         │
└────────────────────────────────────────┘
```

### Minimal Client Data at Creation

When creating a new client, only require **essential** information:

```typescript
interface MinimalClientCreation {
  // Required
  email: string;
  firstName: string;
  lastName: string;

  // Optional (can be filled later)
  phoneNumber?: string;
  sendWelcomeEmail?: boolean;
}
```

**Backend API:**

```python
# POST /api/v1/coaches/me/clients
class CreateClientRequest(BaseModel):
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone_number: Optional[str] = None
    send_welcome_email: bool = True

class CreateClientResponse(BaseModel):
    client_id: str
    email: str
    name: str
    is_new: bool  # True if newly created, False if existing user
    profile_complete: bool  # Whether client has filled out full profile
```

---

## Step 2: Program Builder Parameters

### Program Builder Entry

After selecting a client, coach starts program builder:

```
┌────────────────────────────────────────────────────────┐
│  Build Program for John Doe                             │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Select Program Type:                                   │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ 💪 STRENGTH  │  │ 🏋️ HYPERTROPHY│  │ 🏃 CARDIO   │ │
│  │ Linear 5x5   │  │ Coming Soon   │  │ Coming Soon │ │
│  │ [Select] →   │  │               │  │             │ │
│  └──────────────┘  └──────────────┘  └─────────────┘ │
│                                                         │
└────────────────────────────────────────────────────────┘
```

### Strength Builder Parameters (Simplified)

Focus on **essential parameters** that coach needs to provide:

```typescript
interface StrengthBuilderInputs {
  // Client reference
  clientId: string;

  // Program basic info
  programName?: string;  // Auto-generated if not provided
  startDate?: Date;  // Can be set now or at assignment

  // Movement selection (1-4 exercises)
  movements: Array<{
    exerciseName: string;  // "Squat", "Bench Press", "Deadlift", "Overhead Press"

    // Testing/baseline data
    oneRepMax: number;  // lbs or kg
    maxRepsAt80Percent: number;  // Result of 80% test
    targetWeight: number;  // 5x5 target weight

    // Optional customization
    notes?: string;
  }>;

  // Optional client context (if available)
  clientContext?: {
    experienceLevel?: 'beginner' | 'intermediate' | 'advanced';
    injuries?: string[];  // Simple list of injury notes
    equipmentRestrictions?: string[];
  };
}
```

### Program Builder UI Flow

**Step 1: Movement Selection**

```
┌────────────────────────────────────────────────────────┐
│  Step 1: Select Movements (1-4)                         │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ✅ Squat                      [Remove]                │
│  ✅ Bench Press                [Remove]                │
│  ✅ Deadlift                   [Remove]                │
│  ✅ Overhead Press             [Remove]                │
│                                                         │
│  [+ Add Movement] (Max 4)                              │
│                                                         │
│  [Cancel]                            [Next: Test 1RM]→ │
└────────────────────────────────────────────────────────┘
```

**Step 2: Enter 1RM for Each Movement**

```
┌────────────────────────────────────────────────────────┐
│  Step 2: Test 1RM - Squat                              │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Enter client's 1 Rep Max for Squat:                   │
│                                                         │
│  1RM: [315] lbs                                        │
│                                                         │
│  ℹ️  This is the maximum weight the client can lift    │
│     for a single rep with good form.                    │
│                                                         │
│  💾 Save to client profile: ☑️                         │
│                                                         │
│  [← Back]                           [Next: Bench] →    │
└────────────────────────────────────────────────────────┘
```

**Step 3: Test 80% for Max Reps**

```
┌────────────────────────────────────────────────────────┐
│  Step 3: Test 80% - Squat                              │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Calculated 80% of 1RM: 252 lbs                        │
│                                                         │
│  How many reps can client do at 252 lbs?               │
│                                                         │
│  Reps: [12]                                            │
│                                                         │
│  ℹ️  This determines weekly progression rate:          │
│     12 reps = 3% weekly increase                        │
│                                                         │
│  [← Back]                           [Next: Target] →   │
└────────────────────────────────────────────────────────┘
```

**Step 4: Set Target 5x5 Weight**

```
┌────────────────────────────────────────────────────────┐
│  Step 4: Set Target - Squat                            │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Client will work towards 5 sets of 5 reps at:        │
│                                                         │
│  Target Weight: [275] lbs                              │
│                                                         │
│  ℹ️  Recommended: 195 lbs (62% of 1RM)                 │
│     Program will build from 239 to 284 lbs            │
│                                                         │
│  [Use Recommended] [Manual Entry]                      │
│                                                         │
│  [← Back]                      [Generate Program] →    │
└────────────────────────────────────────────────────────┘
```

**Backend Submission:**

```typescript
// POST /api/v1/programs/generate-preview
const programInputs = {
  clientId: "uuid-123",
  builderType: "strength_linear_5x5",
  movements: [
    {
      exerciseName: "Squat",
      oneRepMax: 315,
      maxRepsAt80Percent: 12,
      targetWeight: 275,
    },
    {
      exerciseName: "Bench Press",
      oneRepMax: 225,
      maxRepsAt80Percent: 10,
      targetWeight: 185,
    },
    // ... more movements
  ],
};

// Response includes full generated program
const preview: ProgramPreview = await generatePreview(programInputs);
```

---

## Step 3: Program Preview Generation

### Backend Generates Full Program

```python
# POST /api/v1/programs/generate-preview
@router.post("/programs/generate-preview")
async def generate_program_preview(
    inputs: ProgramInputs,
    current_user: User = Depends(get_current_coach)
):
    """
    Generate program preview without saving to database.
    Coach can review before final assignment.
    """
    # 1. Validate coach has access to this client
    await validate_coach_client_relationship(current_user.id, inputs.client_id)

    # 2. Fetch client data if available
    client = await get_client(inputs.client_id)
    client_profile = client.profile if client else {}

    # 3. Generate program using backend algorithm
    generator = StrengthProgramGenerator()
    program = generator.generate_program(inputs)

    # 4. Apply client-specific adjustments if data available
    if client_profile.get('health_info', {}).get('injuries'):
        program = apply_injury_modifications(program, client_profile)

    # 5. Return preview with metadata
    return {
        "preview": program,
        "metadata": {
            "total_weeks": 8,
            "total_sessions": 32,
            "exercises": [m.exercise_name for m in inputs.movements],
            "adjustments_applied": get_applied_adjustments(),
        },
        "warnings": get_warnings(client_profile),
    }
```

### Preview Response Structure

```typescript
interface ProgramPreview {
  // Generated program structure
  weeks: Array<{
    weekNumber: number;
    name: string;  // "Foundation Phase", "Building Phase", etc.
    days: Array<{
      dayNumber: number;
      name: string;  // "Session 1 - Heavy Day"
      suggestedDay: string;  // "Monday"
      exercises: Array<{
        exerciseName: string;  // "SQUAT" (uppercase = heavy)
        sets: number;
        reps: number;
        weightLbs: number;
        percentageOf1RM: number;
        notes?: string;
      }>;
    }>;
  }>;

  // Metadata
  metadata: {
    totalWeeks: number;
    totalSessions: number;
    exercises: string[];
    algorithmVersion: string;
    adjustmentsApplied: string[];
  };

  // Warnings for coach
  warnings?: string[];  // e.g., "Client profile incomplete", "No injury data"
}
```

---

## Step 4: Coach Reviews and Adjusts Program

### Program Preview UI

```
┌────────────────────────────────────────────────────────────────┐
│  Program Preview: 8-Week Linear Strength                       │
│  For: John Doe                                      [Edit Info]│
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ⚠️  Client profile incomplete - Add injury information        │
│                                                                 │
│  [Week 1] [Week 2] [Week 3] [Week 4] [Week 5] [Week 6] ...   │
│  ▼ Week 1: Foundation Phase                                    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ 📅 Day 1 - Monday - Heavy Day               [Edit Day] │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ 1. SQUAT                                     [Edit]     │  │
│  │    5 sets × 5 reps @ 239 lbs (76% of 1RM)             │  │
│  │    Rest: 3 min                                          │  │
│  │                                                          │  │
│  │ 2. BENCH PRESS                               [Edit]     │  │
│  │    5 sets × 5 reps @ 157 lbs (70% of 1RM)             │  │
│  │    Rest: 3 min                                          │  │
│  │                                                          │  │
│  │ 3. DEADLIFT                                  [Edit]     │  │
│  │    5 sets × 5 reps @ 275 lbs (73% of 1RM)             │  │
│  │    Rest: 3 min                                          │  │
│  │                                                          │  │
│  │ 4. OVERHEAD PRESS                            [Edit]     │  │
│  │    5 sets × 5 reps @ 99 lbs (68% of 1RM)              │  │
│  │    Rest: 3 min                                          │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ 📅 Day 2 - Wednesday - Light Day            [Edit Day] │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ 1. squat                                     [Edit]     │  │
│  │    5 sets × 5 reps @ 191 lbs (80% of heavy day)       │  │
│  │    ...                                                   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  [< Previous Week] [Next Week >]                               │
│                                                                 │
│  [Cancel]  [Regenerate]  [Save as Template]  [Assign to Client]│
└────────────────────────────────────────────────────────────────┘
```

### Adjustment Capabilities

**Exercise-Level Adjustments:**

```
┌────────────────────────────────────────┐
│  Edit Exercise: Squat (Week 1, Day 1)  │
├────────────────────────────────────────┤
│                                         │
│  Exercise: [Squat ▾]                   │
│    ↳ Replace with: Back Squat, Front  │
│      Squat, Leg Press                  │
│                                         │
│  Sets: [5]   Reps: [5]                 │
│                                         │
│  Weight: [239] lbs                     │
│  (76% of 1RM)                          │
│                                         │
│  Rest: [180] seconds                   │
│                                         │
│  Tempo: [3-0-1-0]  (optional)          │
│  RPE: [7-8]        (optional)          │
│                                         │
│  Notes/Cues:                            │
│  ┌────────────────────────────────┐   │
│  │ Focus on depth and bar path    │   │
│  └────────────────────────────────┘   │
│                                         │
│  [Cancel]              [Save Changes]  │
└────────────────────────────────────────┘
```

**Day-Level Adjustments:**

```
┌────────────────────────────────────────┐
│  Edit Day: Week 1, Day 1 (Monday)      │
├────────────────────────────────────────┤
│                                         │
│  Day Name: [Session 1 - Heavy Day]    │
│                                         │
│  Suggested Day: [Monday ▾]             │
│                                         │
│  Add Exercise: [+ Add Exercise]        │
│                                         │
│  Current Exercises:                     │
│  1. ☰ Squat (5x5 @ 239 lbs) [Edit][×] │
│  2. ☰ Bench (5x5 @ 157 lbs) [Edit][×] │
│  3. ☰ Deadlift (5x5 @ 275)[Edit][×]   │
│  4. ☰ OHP (5x5 @ 99 lbs)   [Edit][×]  │
│                                         │
│  ℹ️  Drag to reorder                    │
│                                         │
│  Warm-up Notes:                         │
│  ┌────────────────────────────────┐   │
│  │ 5 min bike, dynamic stretches  │   │
│  └────────────────────────────────┘   │
│                                         │
│  [Cancel]              [Save Changes]  │
└────────────────────────────────────────┘
```

**Bulk Adjustments:**

```
┌────────────────────────────────────────┐
│  Bulk Adjustments                       │
├────────────────────────────────────────┤
│                                         │
│  Apply to: ☑️ All Weeks                │
│                                         │
│  Adjustment Type:                       │
│  ⚪ Increase all weights by [5] lbs    │
│  ⚪ Decrease all weights by [5] lbs    │
│  ⚪ Scale all weights by [90]%         │
│  ⚫ Add exercise to all heavy days     │
│                                         │
│  Exercise: [Pull-ups ▾]                │
│  Sets: [3]  Reps: [8-10]               │
│  Weight: [Bodyweight]                   │
│                                         │
│  [Cancel]                     [Apply]  │
└────────────────────────────────────────┘
```

### Adjustment Tracking

Track what coach changed from original generated program:

```typescript
interface ProgramAdjustments {
  programId: string;
  originalGenerated: ProgramPreview;  // Store original
  adjustments: Array<{
    timestamp: Date;
    adjustedBy: string;  // Coach ID
    adjustmentType: 'exercise_modified' | 'exercise_added' | 'exercise_removed' | 'weight_changed' | 'sets_reps_changed';
    location: {
      weekNumber: number;
      dayNumber: number;
      exerciseIndex?: number;
    };
    before: any;
    after: any;
    reason?: string;  // Optional note from coach
  }>;
}
```

---

## Step 5: Assign Program to Client

### Assignment Modal

After coach approves the program:

```
┌────────────────────────────────────────────────────────┐
│  Assign Program to John Doe                             │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Program: 8-Week Linear Strength                       │
│  Duration: 8 weeks, 4 sessions/week                    │
│                                                         │
│  ⚠️  Client has active program: "Beginner Program"     │
│     ⚪ Replace active program                          │
│     ⚫ Schedule after current program ends (Mar 15)    │
│                                                         │
│  Start Date: [2025-03-15 ▾]                           │
│  End Date: May 10, 2025 (calculated)                   │
│                                                         │
│  Assignment Notes (visible to client):                 │
│  ┌────────────────────────────────────────────────┐   │
│  │ Focus on form over weight. Don't rush the     │   │
│  │ progression. Take rest days seriously!         │   │
│  └────────────────────────────────────────────────┘   │
│                                                         │
│  Notification:                                          │
│  ☑️ Send email to client                               │
│  ☑️ Send in-app notification                           │
│                                                         │
│  [Cancel]  [Save as Template]  [Assign Program] →     │
└────────────────────────────────────────────────────────┘
```

### Assignment API

```python
# POST /api/v1/programs/{programId}/assign
class AssignProgramRequest(BaseModel):
    client_id: str
    start_date: date
    replace_active: bool = False  # Replace existing active program
    assignment_notes: Optional[str] = None
    send_notification: bool = True

class AssignProgramResponse(BaseModel):
    assignment_id: str
    program_id: str
    client_id: str
    start_date: date
    end_date: date  # Calculated
    status: str  # "scheduled" or "active"
    notification_sent: bool

@router.post("/programs/{program_id}/assign")
async def assign_program_to_client(
    program_id: str,
    request: AssignProgramRequest,
    current_user: User = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db)
):
    """Assign generated program to client."""

    # 1. Validate coach-client relationship
    await validate_coach_client_relationship(current_user.id, request.client_id)

    # 2. Get program (must be owned by this coach)
    program = await get_program(program_id)
    if program.created_by_user_id != current_user.id:
        raise HTTPException(403, "Not your program")

    # 3. Check for existing active program
    if request.replace_active:
        await deactivate_client_programs(request.client_id)

    # 4. Create assignment
    assignment = ClientProgramAssignment(
        subscription_id=current_user.subscription_id,
        program_id=program_id,
        client_id=request.client_id,
        assigned_by=current_user.id,
        start_date=request.start_date,
        scheduled_end_date=request.start_date + timedelta(weeks=program.duration_weeks),
        status='active' if request.start_date <= date.today() else 'scheduled',
        assignment_notes=request.assignment_notes,
    )
    db.add(assignment)
    await db.commit()

    # 5. Send notifications
    if request.send_notification:
        await send_program_assignment_notification(
            client_id=request.client_id,
            program_name=program.name,
            coach_name=current_user.profile.get('first_name'),
            start_date=request.start_date,
            notes=request.assignment_notes,
        )

    return AssignProgramResponse(
        assignment_id=str(assignment.id),
        program_id=str(program_id),
        client_id=request.client_id,
        start_date=request.start_date,
        end_date=assignment.scheduled_end_date,
        status=assignment.status,
        notification_sent=request.send_notification,
    )
```

---

## Additional Flows

### Save as Template (Optional)

Before or after assignment, coach can save as reusable template:

```
┌────────────────────────────────────────┐
│  Save as Template                       │
├────────────────────────────────────────┤
│                                         │
│  Template Name:                         │
│  [8-Week Linear Strength - Custom]     │
│                                         │
│  Description (optional):                │
│  ┌────────────────────────────────┐   │
│  │ Modified version with extra    │   │
│  │ accessory work for hypertrophy │   │
│  └────────────────────────────────┘   │
│                                         │
│  Visibility:                            │
│  ⚫ Private (only me)                   │
│  ⚪ Shared (all coaches in gym)        │
│                                         │
│  Tags:                                  │
│  [strength] [intermediate] [custom]    │
│  [+ Add tag]                            │
│                                         │
│  [Cancel]              [Save Template] │
└────────────────────────────────────────┘
```

### Client Receives Notification

**Email:**
```
Subject: New Training Program Assigned! 💪

Hi John,

Coach Mike has assigned you a new training program:

Program: 8-Week Linear Strength
Start Date: March 15, 2025
Duration: 8 weeks
Frequency: 4 workouts per week

Coach's Message:
"Focus on form over weight. Don't rush the progression.
Take rest days seriously!"

[View Program] [Download PDF]

Questions? Reply to this email or message Coach Mike in the app.

Train hard!
```

**In-App Notification:**
```
┌────────────────────────────────────────┐
│  🔔 New Program Assigned                │
├────────────────────────────────────────┤
│                                         │
│  Coach Mike assigned:                   │
│  "8-Week Linear Strength"              │
│                                         │
│  Starts: March 15, 2025                │
│  4 workouts/week                        │
│                                         │
│  [View Program] [Dismiss]              │
└────────────────────────────────────────┘
```

---

## Summary of Updated Flow

### Simplified Workflow

1. **Coach selects/creates client** (minimal info: email, name)
2. **Coach builds program** (enters movement data and parameters)
3. **System generates preview** (full 8-week program calculated)
4. **Coach reviews and adjusts** (modify exercises, weights, notes)
5. **Coach assigns to client** (set start date, add notes)
6. **Client receives program** (notification + access in their app)

### Key Design Principles

✅ **Coach-centric**: Coach drives the entire flow
✅ **Minimal friction**: Don't require full client profile upfront
✅ **Preview first**: Always show coach what will be assigned
✅ **Flexible adjustments**: Coach can modify anything in preview
✅ **Progressive enhancement**: Can add more client data later for better personalization
✅ **Clear state management**: Track original vs adjusted program

### Data Requirements

**At Client Creation** (minimal):
- Email (required)
- First Name (required)
- Last Name (required)

**At Program Building** (coach provides):
- Movement selection
- 1RMs
- 80% rep test results
- Target weights

**Enhanced Later** (optional, improves future programs):
- Client injuries
- Equipment restrictions
- Training preferences
- Full anthropometric data

This flow prioritizes speed and simplicity while maintaining the ability to add more sophisticated personalization as the coach-client relationship develops.
