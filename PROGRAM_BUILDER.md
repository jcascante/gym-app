# Program Builder Ecosystem - Design Specification

## Overview

The Program Builder Ecosystem is a comprehensive system for creating, managing, assigning, and tracking workout programs. It consists of three main components:

1. **Program Builder Modules** - Wizard-style tools for creating specific types of programs
2. **Template Library** - Repository of saved programs ready for assignment
3. **Assignment & Tracking** - System for assigning programs to clients and monitoring progress

This document defines the architecture, data models, workflows, and analytics for the entire program ecosystem.

---

## Existing Implementation

### Current Program Builder (/program-builder)

**Location**: `frontend/src/pages/ProgramBuilder.tsx`

**Type**: Strength Training / Linear Progression Builder

**Functionality**:
- **Step 1**: Select movements (up to 4 compound lifts)
- **Step 2**: Test 1RM for each movement
- **Step 3**: Test 80% of 1RM for max reps (determines weekly progression rate)
- **Step 4**: Perform 5RM test protocol to establish target weight
- **Step 5**: Generate 8-week linear progression program
  - Weeks 1-5: 5×5 protocol with progressive overload
  - Week 6: 3×3 protocol at higher intensity
  - Week 7: 2×2 protocol at peak intensity
  - Week 8: Testing week (new 1RM test)

**Program Structure**:
- 4 sessions per week (Mon/Wed/Fri/Sat)
- Alternating Heavy-Light-Heavy-Light pattern
- Automatic percentage calculations based on 1RM
- Weekly weight progressions based on rep test results

**Current Status**:
- ✅ UI/UX complete with step-by-step wizard
- ✅ Calculations and progression logic implemented
- ❌ Backend integration pending (save functionality shows "coming soon")
- ❌ Template saving not yet implemented
- ❌ Client assignment not yet implemented

**Next Steps for Existing Builder**:
1. Integrate with backend API to save programs
2. Add option to save as template
3. Add option to assign directly to client
4. Store program data in database according to schema below

---

## Core Concepts

### Program Hierarchy

```
Program (12-Week Strength Builder)
├── Week 1
│   ├── Day 1: Push (Monday)
│   │   ├── Exercise 1: Bench Press (4 sets × 8 reps @ 185 lbs)
│   │   ├── Exercise 2: Overhead Press (3 sets × 10 reps @ 95 lbs)
│   │   └── Exercise 3: Tricep Dips (3 sets × 12 reps)
│   ├── Day 2: Pull (Wednesday)
│   │   └── ...
│   └── Day 3: Legs (Friday)
│       └── ...
├── Week 2
│   └── ... (progressive overload)
└── Week 12
    └── ... (peak performance)
```

### Program Types

1. **Program Templates**
   - Reusable workout program blueprints
   - Created by coaches/admins within a subscription
   - Can be private (subscription-only) or public (marketplace)
   - Not tied to specific clients
   - Can be assigned to multiple clients
   - Versioned for improvements over time

2. **Assigned Programs**
   - Instance of a template assigned to a specific client
   - Has a start date and schedule
   - Tracks actual completion and performance
   - Can be customized after assignment (per-client adjustments)
   - Maintains link to original template for updates

3. **Marketplace Templates** (Future)
   - Public templates created by any coach
   - Available for purchase/download by other subscriptions
   - Rated and reviewed by community
   - Revenue sharing for creators

---

## Database Schema

### Programs Table

```sql
CREATE TABLE programs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id),
    created_by UUID NOT NULL REFERENCES users(id),

    -- Program metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,
    program_type VARCHAR(50) NOT NULL, -- 'strength', 'hypertrophy', 'conditioning', 'sport_specific', 'general_fitness'
    difficulty_level VARCHAR(50), -- 'beginner', 'intermediate', 'advanced', 'elite'
    duration_weeks INT NOT NULL CHECK (duration_weeks > 0 AND duration_weeks <= 52),
    days_per_week INT NOT NULL CHECK (days_per_week > 0 AND days_per_week <= 7),

    -- Template settings
    is_template BOOLEAN DEFAULT FALSE,
    is_public BOOLEAN DEFAULT FALSE, -- marketplace visibility (ENTERPRISE only)
    template_version INT DEFAULT 1,
    parent_template_id UUID REFERENCES programs(id), -- for template versioning

    -- Media and resources
    thumbnail_url VARCHAR(500),
    video_url VARCHAR(500),
    tags JSONB DEFAULT '[]', -- ['strength', 'powerlifting', 'beginner-friendly']

    -- Goals and target audience
    goals JSONB, -- ['build_muscle', 'lose_fat', 'increase_strength']
    target_gender VARCHAR(20), -- 'male', 'female', 'any'
    equipment_required JSONB, -- ['barbell', 'dumbbells', 'bench', 'squat_rack']

    -- Usage tracking (for templates)
    times_assigned INT DEFAULT 0,
    average_completion_rate DECIMAL(5,2), -- percentage
    average_rating DECIMAL(3,2), -- 0.00 to 5.00

    -- Marketplace (ENTERPRISE, future)
    price_cents INT, -- null = free, for marketplace templates
    revenue_share_pct DECIMAL(5,2), -- creator's cut

    -- Soft delete
    is_active BOOLEAN DEFAULT TRUE,
    archived_at TIMESTAMP WITH TIME ZONE,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_programs_subscription ON programs(subscription_id) WHERE is_active = TRUE;
CREATE INDEX idx_programs_template ON programs(is_template, is_public) WHERE is_active = TRUE;
CREATE INDEX idx_programs_creator ON programs(created_by);
```

### Program Weeks Table

```sql
CREATE TABLE program_weeks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    program_id UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
    subscription_id UUID NOT NULL REFERENCES subscriptions(id),

    week_number INT NOT NULL CHECK (week_number > 0),
    name VARCHAR(255), -- 'Accumulation Phase', 'Deload Week', 'Peak Week'
    description TEXT,
    notes TEXT, -- coach notes for this week

    -- Week-level goals/focus
    focus_area VARCHAR(100), -- 'volume', 'intensity', 'technique', 'deload'

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID REFERENCES users(id),

    UNIQUE(program_id, week_number)
);

CREATE INDEX idx_program_weeks_program ON program_weeks(program_id);
```

### Program Days Table

```sql
CREATE TABLE program_days (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    program_week_id UUID NOT NULL REFERENCES program_weeks(id) ON DELETE CASCADE,
    subscription_id UUID NOT NULL REFERENCES subscriptions(id),

    day_number INT NOT NULL CHECK (day_number > 0 AND day_number <= 7),
    name VARCHAR(255) NOT NULL, -- 'Push Day', 'Pull Day', 'Leg Day', 'Upper Body'
    description TEXT,
    day_type VARCHAR(50), -- 'strength', 'conditioning', 'active_recovery', 'rest'

    -- Scheduling hints
    suggested_day_of_week INT, -- 1=Monday, 7=Sunday
    estimated_duration_minutes INT,

    -- Day-level settings
    warm_up_notes TEXT,
    cool_down_notes TEXT,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID REFERENCES users(id),

    UNIQUE(program_week_id, day_number)
);

CREATE INDEX idx_program_days_week ON program_days(program_week_id);
```

### Exercises Library Table

```sql
CREATE TABLE exercises_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID REFERENCES subscriptions(id), -- NULL for global exercises
    created_by UUID REFERENCES users(id),

    -- Exercise metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100), -- 'compound', 'isolation', 'cardio', 'mobility'
    muscle_groups JSONB, -- ['chest', 'triceps', 'shoulders']
    equipment JSONB, -- ['barbell', 'bench']

    -- Media
    video_url VARCHAR(500),
    thumbnail_url VARCHAR(500),

    -- Exercise parameters
    is_bilateral BOOLEAN DEFAULT TRUE, -- false for single-leg/single-arm
    is_timed BOOLEAN DEFAULT FALSE, -- true for planks, cardio
    default_rest_seconds INT DEFAULT 90,

    -- Difficulty and progression
    difficulty_level VARCHAR(50),
    progression_exercises JSONB, -- [uuid, uuid] - easier/harder variations

    -- Usage and curation
    is_global BOOLEAN DEFAULT FALSE, -- platform-wide exercises (APPLICATION_SUPPORT only)
    is_verified BOOLEAN DEFAULT FALSE, -- quality-checked by platform

    -- Soft delete
    is_active BOOLEAN DEFAULT TRUE,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_exercises_subscription ON exercises_library(subscription_id) WHERE is_active = TRUE;
CREATE INDEX idx_exercises_global ON exercises_library(is_global) WHERE is_active = TRUE;
CREATE INDEX idx_exercises_category ON exercises_library(category);
```

### Program Day Exercises Table

```sql
CREATE TABLE program_day_exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    program_day_id UUID NOT NULL REFERENCES program_days(id) ON DELETE CASCADE,
    exercise_id UUID NOT NULL REFERENCES exercises_library(id),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id),

    exercise_order INT NOT NULL CHECK (exercise_order > 0),

    -- Exercise prescription
    sets INT NOT NULL CHECK (sets > 0),
    reps_min INT, -- for rep ranges like 8-12
    reps_max INT,
    reps_target INT, -- for fixed reps like 5x5

    -- Load prescription
    load_type VARCHAR(50), -- 'percentage_1rm', 'rpe', 'fixed_weight', 'bodyweight', 'time'
    load_value DECIMAL(10,2), -- 185.5 lbs, or 75% for percentage
    load_unit VARCHAR(20), -- 'lbs', 'kg', 'percentage', 'rpe'

    -- Tempo and timing
    tempo VARCHAR(20), -- '3-0-1-0' (eccentric-pause-concentric-pause)
    rest_seconds INT,
    duration_seconds INT, -- for timed exercises (planks, cardio)

    -- Intensity markers
    rpe_target DECIMAL(3,1), -- Rate of Perceived Exertion (1.0 to 10.0)
    percentage_1rm DECIMAL(5,2), -- for percentage-based programming

    -- Notes and cues
    notes TEXT,
    coaching_cues TEXT, -- form reminders, technique tips

    -- Supersets and circuits
    superset_group INT, -- exercises with same number are supersetted
    circuit_group INT,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID REFERENCES users(id),

    UNIQUE(program_day_id, exercise_order)
);

CREATE INDEX idx_program_day_exercises_day ON program_day_exercises(program_day_id);
CREATE INDEX idx_program_day_exercises_exercise ON program_day_exercises(exercise_id);
```

### Client Program Assignments Table

```sql
CREATE TABLE client_program_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id),

    -- Assignment details
    program_template_id UUID NOT NULL REFERENCES programs(id),
    client_id UUID NOT NULL REFERENCES users(id),
    assigned_by UUID NOT NULL REFERENCES users(id), -- coach or admin

    -- Scheduling
    start_date DATE NOT NULL,
    scheduled_end_date DATE, -- calculated from start_date + duration
    actual_end_date DATE, -- when client actually finished

    -- Customization
    is_customized BOOLEAN DEFAULT FALSE,
    customization_notes TEXT,

    -- Progress tracking
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'paused', 'completed', 'abandoned'
    current_week INT DEFAULT 1,
    current_day INT DEFAULT 1,

    -- Performance metrics
    workouts_completed INT DEFAULT 0,
    workouts_total INT, -- total workouts in program
    completion_percentage DECIMAL(5,2) DEFAULT 0.00,

    -- Satisfaction
    client_rating INT, -- 1-5 stars
    client_feedback TEXT,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID REFERENCES users(id),

    CONSTRAINT client_rating_range CHECK (client_rating >= 1 AND client_rating <= 5)
);

CREATE INDEX idx_client_assignments_client ON client_program_assignments(client_id);
CREATE INDEX idx_client_assignments_program ON client_program_assignments(program_template_id);
CREATE INDEX idx_client_assignments_status ON client_program_assignments(status);
CREATE INDEX idx_client_assignments_subscription ON client_program_assignments(subscription_id);
```

### Workout Logs Table

```sql
CREATE TABLE workout_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id),

    -- Assignment context
    client_assignment_id UUID NOT NULL REFERENCES client_program_assignments(id),
    program_day_id UUID NOT NULL REFERENCES program_days(id),
    client_id UUID NOT NULL REFERENCES users(id),

    -- Workout session details
    scheduled_date DATE,
    actual_date DATE NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INT,

    -- Session quality
    status VARCHAR(50) DEFAULT 'completed', -- 'completed', 'partial', 'skipped'
    overall_rpe DECIMAL(3,1), -- session RPE
    energy_level INT, -- 1-5

    -- Client notes
    notes TEXT,
    how_you_felt TEXT,

    -- Calculated metrics
    total_volume_lbs DECIMAL(12,2), -- sum of (sets × reps × weight) for all exercises
    exercises_completed INT,
    exercises_total INT,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_workout_logs_client ON workout_logs(client_id);
CREATE INDEX idx_workout_logs_assignment ON workout_logs(client_assignment_id);
CREATE INDEX idx_workout_logs_date ON workout_logs(actual_date);
```

### Exercise Logs Table

```sql
CREATE TABLE exercise_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id),

    -- Context
    workout_log_id UUID NOT NULL REFERENCES workout_logs(id) ON DELETE CASCADE,
    program_day_exercise_id UUID NOT NULL REFERENCES program_day_exercises(id),
    exercise_id UUID NOT NULL REFERENCES exercises_library(id),
    client_id UUID NOT NULL REFERENCES users(id),

    exercise_order INT,

    -- Prescribed vs actual
    prescribed_sets INT,
    prescribed_reps INT,
    prescribed_load DECIMAL(10,2),
    prescribed_load_unit VARCHAR(20),

    -- Actual performance (JSONB array for flexibility)
    sets_performed JSONB, -- [
                          --   {"set": 1, "reps": 10, "weight": 185, "rpe": 7, "notes": "felt strong"},
                          --   {"set": 2, "reps": 9, "weight": 185, "rpe": 8, "notes": ""},
                          --   {"set": 3, "reps": 8, "weight": 185, "rpe": 9, "notes": "struggled"}
                          -- ]

    -- Calculated summary
    total_reps INT, -- sum of all reps
    total_volume DECIMAL(12,2), -- sum of (reps × weight) for all sets
    average_rpe DECIMAL(3,1),
    top_set_weight DECIMAL(10,2), -- heaviest weight used
    top_set_reps INT, -- reps at heaviest weight

    -- Performance indicators
    is_personal_record BOOLEAN DEFAULT FALSE,
    pr_type VARCHAR(50), -- '1rm', 'volume', 'reps_at_weight', 'time'

    -- Client feedback
    notes TEXT,
    difficulty_rating INT, -- 1-5
    form_quality INT, -- 1-5, self-assessed

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_exercise_logs_workout ON exercise_logs(workout_log_id);
CREATE INDEX idx_exercise_logs_client ON exercise_logs(client_id);
CREATE INDEX idx_exercise_logs_exercise ON exercise_logs(exercise_id);
CREATE INDEX idx_exercise_logs_pr ON exercise_logs(is_personal_record) WHERE is_personal_record = TRUE;
```

---

## Program Ecosystem Architecture

### Three-Layer System

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 1: PROGRAM BUILDERS                     │
│  Wizard-style tools for creating specific types of programs     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Strength Builder]  [Hypertrophy]  [Conditioning]  [Custom]   │
│   (Existing 5x5)     (Future)        (Future)        (Future)   │
│                                                                  │
│  Each builder outputs → Program Template                         │
│                                                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LAYER 2: TEMPLATE LIBRARY                      │
│     Repository of saved programs ready for assignment           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📁 My Templates (Private)                                      │
│     ├─ "8-Week Linear Strength" (from Strength Builder)        │
│     ├─ "12-Week Hypertrophy" (from Hypertrophy Builder)       │
│     └─ "4-Week Peaking Cycle" (Custom)                         │
│                                                                  │
│  📁 Subscription Templates (Shared within gym)                  │
│     └─ Templates created by other coaches in gym               │
│                                                                  │
│  🏪 Marketplace Templates (Public - ENTERPRISE, Future)         │
│     └─ Templates from coaches worldwide                        │
│                                                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              LAYER 3: ASSIGNMENT & TRACKING                      │
│         Programs assigned to specific clients                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Client: John Doe                                               │
│  Assigned Program: "8-Week Linear Strength"                     │
│  Start Date: Jan 15, 2025                                       │
│  Current Progress: Week 2, Day 3 (25% complete)                │
│  Status: Active                                                  │
│                                                                  │
│  [Workout Log] → Exercise Performance → Analytics               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Workflow: Builder → Template → Assignment

#### Path 1: Direct Assignment (Quick Path)
```
Coach → Program Builder → Configure Program → "Assign to Client"
  ↓
Select Client → Set Start Date → Confirm
  ↓
Client receives notification → Program appears in their app
```

#### Path 2: Save as Template First (Reusable Path)
```
Coach → Program Builder → Configure Program → "Save as Template"
  ↓
Enter Template Details (name, description, tags, visibility)
  ↓
Template saved to library
  ↓
[Later] Coach → Template Library → Select Template → "Assign to Client"
  ↓
Select Client → Set Start Date → Optional Customization → Confirm
  ↓
Client receives notification → Program appears in their app
```

#### Path 3: Use Existing Template
```
Coach → Template Library → Browse/Search Templates
  ↓
Preview Template → "Assign to Client"
  ↓
Select Client → Set Start Date → Optional Customization → Confirm
  ↓
Client receives notification → Program appears in their app
```

### Builder Types (Current + Future)

#### 1. Strength Builder (EXISTING - Current Implementation)
**Target**: Linear progression for compound lifts
**Output**: 8-week 5×5 program with heavy/light alternation
**Inputs**:
- Movements selection
- 1RM tests
- 80% max rep test
- 5RM test protocol
**Features**:
- Auto-calculated progression rates
- Percentage-based loading
- Deload and test week built-in

#### 2. Hypertrophy Builder (FUTURE)
**Target**: Muscle building programs with volume focus
**Output**: 8-12 week program with varied rep ranges
**Inputs**:
- Muscle group split selection (PPL, Upper/Lower, Bro Split)
- Training frequency (3-6 days/week)
- Exercise selection per muscle group
- Volume preferences (sets per week per muscle)
**Features**:
- 8-12 rep range focus
- Progressive overload via volume or weight
- Deload weeks every 4-6 weeks
- Exercise variety and rotation

#### 3. Conditioning Builder (FUTURE)
**Target**: Cardio, HIIT, metabolic conditioning
**Output**: 4-8 week conditioning program
**Inputs**:
- Goal (fat loss, endurance, general fitness)
- Available equipment (bike, rower, running, bodyweight)
- Training frequency
- Session duration
**Features**:
- Interval protocols (Tabata, EMOM, AMRAP)
- Progressive duration/intensity
- Recovery day planning
- Heart rate zone guidance

#### 4. Custom Builder (FUTURE)
**Target**: Fully customizable programs for advanced coaches
**Output**: Any program structure coach designs
**Features**:
- Drag-and-drop week/day/exercise builder
- Manual set/rep/load prescription
- Custom progression schemes
- Blank canvas approach
- Most flexible, requires most expertise

---

## Program Management Workflows

### Creating a Program Template

**Who Can Create:**
- SUBSCRIPTION_ADMIN (all subscription types)
- COACH (GYM and ENTERPRISE subscriptions only)

**Creation Flow:**

1. **Initialize Program**
   - Name, description, type, difficulty
   - Duration (weeks), frequency (days/week)
   - Goals, equipment requirements
   - Upload thumbnail/video (optional)

2. **Define Program Structure**
   - Create weeks (auto-generated based on duration, or manual)
   - Name each week (optional)
   - Set week-level focus/notes

3. **Build Workout Days**
   - For each week, create training days
   - Name day (Push, Pull, Legs, etc.)
   - Set suggested day of week
   - Estimate duration

4. **Add Exercises**
   - Search/select from exercise library
   - Set order, sets, reps, load
   - Configure rest periods, tempo, RPE
   - Add coaching cues and notes
   - Create supersets/circuits

5. **Review and Publish**
   - Preview full program
   - Mark as template
   - Set visibility (private/public)
   - Save and make available for assignment

**Template Versioning:**
- When editing a template that's already assigned to clients:
  - Option 1: Create new version (original assignments unchanged)
  - Option 2: Update in place (affects future assignments only, not current)
  - Option 3: Update and migrate (update current assignments with approval)

### Assigning a Program to a Client

**Who Can Assign:**
- SUBSCRIPTION_ADMIN: Can assign to any client in subscription
- COACH: Can assign to their assigned clients only

**Assignment Sources:**
1. **From Program Builder** (Path 1: Direct Assignment)
   - Complete builder wizard
   - At final step: "Assign to Client" button
   - Optionally save as template for future reuse

2. **From Template Library** (Path 3: Use Existing)
   - Navigate to Templates page
   - Browse/search/filter templates
   - Click "Assign" on template card

**Assignment Flow:**

1. **Select Template/Program**
   - Browse subscription's template library
   - Filter by:
     - Program type (strength, hypertrophy, conditioning)
     - Difficulty level (beginner, intermediate, advanced)
     - Duration (4-week, 8-week, 12-week)
     - Equipment requirements
     - Creator (me, my gym, marketplace)
   - Preview program details with full week/day/exercise breakdown

2. **Select Client**
   - Choose from available clients
   - View client profile:
     - Current program status (if any)
     - Training history
     - Recent progress
     - Goals and preferences
   - Check for conflicts:
     - Warning if client has active program
     - Option to replace or schedule after current program ends

3. **Configure Assignment**
   - **Start Date Selection**:
     - Choose immediate start or future date
     - Calendar view with client's current schedule
     - Auto-calculate end date (start + duration)

   - **Customization Options** (optional):
     - Adjust exercises (swap, add, remove)
     - Modify sets/reps/load prescriptions
     - Add client-specific notes and cues
     - Set customization flag (tracks divergence from template)

   - **Assignment Notes**:
     - Coach notes visible to client
     - Program expectations and goals
     - Special instructions

4. **Review & Confirm**
   - Summary of assignment:
     - Client name
     - Program name
     - Start/end dates
     - Customizations (if any)
   - Click "Assign Program"

5. **Notification & Client Access**
   - **Automatic Notifications**:
     - Email: "New program assigned: [Program Name]"
     - In-app notification
     - Push notification (mobile app)

   - **Client View**:
     - Program appears in client dashboard
     - "Today's Workout" shows current day
     - Full program preview available
     - Start workout button activates on start date

6. **Coach Monitoring**
   - Assignment appears in coach's "Active Assignments" list
   - Real-time progress tracking:
     - Completion percentage
     - Adherence rate
     - Workout logs
     - Performance trends
   - Option to adjust program mid-cycle if needed

### Customizing an Assigned Program

After assignment, coaches can customize the program for a specific client:

**Customization Options:**
- Adjust sets, reps, load for any exercise
- Add or remove exercises
- Modify rest periods, tempo
- Add client-specific notes
- Swap exercises (e.g., replace barbell with dumbbells due to injury)

**Customization Tracking:**
- `is_customized` flag set to TRUE
- Changes logged in `customization_notes`
- Customizations only affect this client's assignment
- Original template remains unchanged

---

## Template Library Interface

### Navigation & Access

**URL Routes:**
- `/templates` - Main template library page (coaches/admins)
- `/templates/:id` - Template detail/preview page
- `/templates/new` - Create new template (redirects to builder selection)
- `/templates/:id/edit` - Edit existing template

**Access from Dashboard:**
- Coach Dashboard: "My Programs" → "Templates" tab
- Quick action: "Create Program" → Choose builder type
- Quick action: "Browse Templates" → Template library

### Template Library Page (`/templates`)

**Page Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  Templates                                    [+ Create]    │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  🔍 Search templates...                                    │
│                                                             │
│  Filters:                                                  │
│  [Type ▾] [Difficulty ▾] [Duration ▾] [Equipment ▾]      │
│                                                             │
│  Tabs: [📁 My Templates] [👥 Shared] [🏪 Marketplace]    │
│                                                             │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ 📸 Thumbnail │  │ 📸 Thumbnail │  │ 📸 Thumbnail │    │
│  │              │  │              │  │              │    │
│  │ Linear 5x5   │  │ PPL Builder  │  │ Conditioning │    │
│  │ Strength     │  │ Hypertrophy  │  │ HIIT         │    │
│  │              │  │              │  │              │    │
│  │ 8 weeks      │  │ 12 weeks     │  │ 6 weeks      │    │
│  │ 4 days/week  │  │ 6 days/week  │  │ 4 days/week  │    │
│  │              │  │              │  │              │    │
│  │ ⭐ 4.8 (23)  │  │ ⭐ 4.6 (15)  │  │ ⭐ 4.9 (8)   │    │
│  │ 📊 87% comp  │  │ 📊 78% comp  │  │ 📊 92% comp  │    │
│  │              │  │              │  │              │    │
│  │ [Preview]    │  │ [Preview]    │  │ [Preview]    │    │
│  │ [Assign]     │  │ [Assign]     │  │ [Assign]     │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

**Filter Options:**

1. **Type Filter**
   - Strength
   - Hypertrophy
   - Conditioning
   - Sport-Specific
   - General Fitness
   - All

2. **Difficulty Filter**
   - Beginner
   - Intermediate
   - Advanced
   - Elite
   - All

3. **Duration Filter**
   - 4 weeks
   - 6 weeks
   - 8 weeks
   - 12 weeks
   - 16+ weeks
   - Custom

4. **Equipment Filter**
   - Minimal (bodyweight, dumbbells)
   - Standard (barbell, rack, bench)
   - Full gym
   - Home gym
   - No equipment

5. **Creator Filter** (My Templates tab only)
   - Created by me
   - Created by others in gym

**Template Card Components:**

```jsx
<TemplateCard>
  <Thumbnail /> {/* Image or default based on type */}
  <TemplateHeader>
    <Name>8-Week Linear Strength</Name>
    <Type badge>Strength</Type>
    <Difficulty badge>Intermediate</Difficulty>
  </TemplateHeader>
  <TemplateStats>
    <Duration>8 weeks • 4 days/week</Duration>
    <Assigned>23 times assigned</Assigned>
    <Rating>⭐ 4.8 (23 ratings)</Rating>
    <Completion>87% avg completion</Completion>
  </TemplateStats>
  <EquipmentTags>
    <Tag>Barbell</Tag>
    <Tag>Rack</Tag>
    <Tag>Bench</Tag>
  </EquipmentTags>
  <Actions>
    <Button variant="secondary" onClick={handlePreview}>
      Preview
    </Button>
    <Button variant="primary" onClick={handleAssign}>
      Assign to Client
    </Button>
    {isCreator && (
      <Menu>
        <MenuItem>Edit</MenuItem>
        <MenuItem>Duplicate</MenuItem>
        <MenuItem>Archive</MenuItem>
      </Menu>
    )}
  </Actions>
</TemplateCard>
```

### Template Detail/Preview Page (`/templates/:id`)

**Full Program View:**

```
┌────────────────────────────────────────────────────────────┐
│  ← Back to Templates                                        │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  8-Week Linear Strength Program                [Assign]    │
│  By: Coach Mike Johnson                                     │
│                                                             │
│  Type: Strength | Difficulty: Intermediate | 8 weeks       │
│                                                             │
│  Description:                                              │
│  Classic linear progression strength program based on      │
│  5x5 protocol. Suitable for intermediate lifters...       │
│                                                             │
│  ⭐ 4.8 (23 ratings) | 📊 87% completion | 23 assignments │
│                                                             │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  [Week 1] [Week 2] [Week 3] ... [Week 8]                  │
│                                                             │
│  Week 1: Foundation Phase                                  │
│  ├─ Day 1: Full Body Heavy (Monday)                       │
│  │  └─ Squat: 5x5 @ calculated weight                    │
│  │  └─ Bench Press: 5x5                                   │
│  │  └─ Rows: 5x5                                          │
│  │  └─ Overhead Press: 5x5                                │
│  │                                                          │
│  ├─ Day 2: Full Body Light (Wednesday)                    │
│  │  └─ squat: 5x5 @ 80% of heavy                         │
│  │  └─ bench press: 5x5 @ 80%                            │
│  │  └─ ...                                                 │
│  │                                                          │
│  └─ Day 3: Full Body Heavy (Friday)                       │
│      └─ ...                                                 │
│                                                             │
│  [Expand All] [Collapse All]                              │
│                                                             │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Equipment Required:                                       │
│  • Barbell • Squat Rack • Bench • Weights                 │
│                                                             │
│  Target Audience:                                          │
│  Intermediate lifters with 1+ year experience              │
│                                                             │
│  Goals:                                                    │
│  • Increase absolute strength                              │
│  • Build muscle mass                                       │
│  • Improve 1RM on compound lifts                           │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### Subscription Template Library

Each subscription has its own library of program templates:

**Library Categories:**

1. **My Templates** (Private to creator)
   - Templates created by the current user
   - Full edit/delete permissions
   - Can be shared with subscription or made public

2. **Subscription Templates** (Shared within gym)
   - Templates created by other coaches in the subscription
   - Read-only (can duplicate to customize)
   - Visible to all coaches/admins in subscription

3. **Marketplace Templates** (ENTERPRISE only - Future)
   - Public templates from coaches worldwide
   - Purchase/download to copy to subscription
   - Read-only originals with local customization copies

**Template Visibility Settings:**

```typescript
enum TemplateVisibility {
  PRIVATE = 'private',        // Only creator can see
  SUBSCRIPTION = 'subscription', // All coaches in subscription can see
  PUBLIC = 'public'           // Marketplace (ENTERPRISE only)
}
```

When creating/editing a template:
- **INDIVIDUAL subscriptions**: Can only set PRIVATE
- **GYM subscriptions**: Can set PRIVATE or SUBSCRIPTION
- **ENTERPRISE subscriptions**: Can set PRIVATE, SUBSCRIPTION, or PUBLIC (marketplace)

### Global Exercise Library

Platform-wide exercise database:

**Exercise Categories:**
- Compound movements (squat, deadlift, bench press)
- Isolation exercises (bicep curl, leg extension)
- Cardio (running, rowing, cycling)
- Bodyweight (push-ups, pull-ups, planks)
- Olympic lifts (clean, snatch, jerk)
- Mobility and stretching

**Exercise Data:**
- Name, description, instructions
- Video demonstration
- Muscle groups targeted
- Equipment needed
- Difficulty level
- Progression/regression variants
- Common mistakes and cues

**Custom Exercises:**
- Subscription admins and coaches can create custom exercises
- Stored in subscription's private library
- Can be marked for inclusion in global library (review process)

### Marketplace (ENTERPRISE - Future)

Public template marketplace for buying/selling programs:

**Features:**
- Browse templates from coaches worldwide
- Ratings and reviews
- Preview before purchase
- One-time purchase or subscription
- Revenue sharing (70% creator, 30% platform)
- Featured templates and collections

**Quality Control:**
- Verification process for marketplace templates
- Minimum quality standards
- User reports for inappropriate content
- Platform moderation

---

## Tracking and Analytics

### Client-Level Tracking

**Program Progress:**
- Current week and day
- Workouts completed vs scheduled
- Completion percentage
- Estimated completion date
- Adherence rate (workouts completed on time)

**Performance Metrics:**
- Total volume (lbs/kg lifted)
- Personal records achieved
- Average session RPE
- Average workout duration
- Energy levels trend
- Exercise-specific progression

**Progress Dashboard:**
```
Current Program: 12-Week Hypertrophy Builder
Progress: Week 4 of 12 (33% complete)
Adherence: 11/12 workouts (92%)
Total Volume: 145,230 lbs
Personal Records: 5
Average RPE: 7.8
```

### Coach Analytics

**Program Performance:**
- Templates created
- Times each template assigned
- Average completion rate per template
- Average client satisfaction rating
- Most/least successful programs

**Client Overview:**
- Active programs count
- Client adherence rates
- Clients at risk (low adherence)
- Recent personal records
- Clients needing check-in

**Coach Dashboard:**
```
Active Clients: 18
Active Programs: 18
Avg Completion Rate: 78%
Avg Client Rating: 4.6/5.0
Programs Created: 12
Most Assigned: "Beginner Strength Foundations" (8 times)
```

### Admin Analytics (Subscription-Level)

**Subscription Metrics:**
- Total programs created
- Total assignments (all-time, monthly)
- Overall completion rate
- Most popular program types
- Coach performance comparison
- Client engagement metrics

**Retention Insights:**
- Correlation between program completion and client retention
- Average client lifetime (days active)
- Churn risk indicators

**Revenue Impact (GYM/ENTERPRISE):**
- Clients with active programs vs those without
- Retention rate difference
- Upsell opportunities (clients ready for advanced programs)

---

## API Endpoints

### Program Template Endpoints

```
POST   /api/v1/programs/templates
GET    /api/v1/programs/templates
GET    /api/v1/programs/templates/{id}
PUT    /api/v1/programs/templates/{id}
DELETE /api/v1/programs/templates/{id}
POST   /api/v1/programs/templates/{id}/duplicate
POST   /api/v1/programs/templates/{id}/publish
```

### Program Structure Endpoints

```
POST   /api/v1/programs/{program_id}/weeks
PUT    /api/v1/programs/weeks/{week_id}
DELETE /api/v1/programs/weeks/{week_id}

POST   /api/v1/programs/weeks/{week_id}/days
PUT    /api/v1/programs/days/{day_id}
DELETE /api/v1/programs/days/{day_id}

POST   /api/v1/programs/days/{day_id}/exercises
PUT    /api/v1/programs/exercises/{exercise_id}
DELETE /api/v1/programs/exercises/{exercise_id}
POST   /api/v1/programs/exercises/{exercise_id}/reorder
```

### Exercise Library Endpoints

```
GET    /api/v1/exercises
POST   /api/v1/exercises
GET    /api/v1/exercises/{id}
PUT    /api/v1/exercises/{id}
DELETE /api/v1/exercises/{id}
GET    /api/v1/exercises/categories
GET    /api/v1/exercises/search?q=bench&category=compound
```

### Assignment Endpoints

```
POST   /api/v1/assignments
GET    /api/v1/assignments
GET    /api/v1/assignments/{id}
PUT    /api/v1/assignments/{id}
DELETE /api/v1/assignments/{id}
POST   /api/v1/assignments/{id}/customize
PATCH  /api/v1/assignments/{id}/status
GET    /api/v1/assignments/{id}/progress
```

### Workout Logging Endpoints

```
POST   /api/v1/workouts/log
GET    /api/v1/workouts/log/{id}
PUT    /api/v1/workouts/log/{id}
GET    /api/v1/workouts/history?client_id={id}&date_from={date}

POST   /api/v1/workouts/log/{workout_id}/exercises
PUT    /api/v1/workouts/log/exercises/{exercise_log_id}
POST   /api/v1/workouts/log/exercises/{exercise_log_id}/set
```

### Analytics Endpoints

```
GET    /api/v1/analytics/client/{client_id}/progress
GET    /api/v1/analytics/client/{client_id}/personal-records
GET    /api/v1/analytics/coach/{coach_id}/overview
GET    /api/v1/analytics/subscription/overview
GET    /api/v1/analytics/programs/{program_id}/performance
```

---

## Multi-Tenant Considerations

### Data Isolation

All program data is scoped by `subscription_id`:

```python
# Example: Fetching programs for a subscription
@router.get("/programs/templates")
async def get_program_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Automatic subscription filtering
    query = select(Program).where(
        Program.subscription_id == current_user.subscription_id,
        Program.is_template == True,
        Program.is_active == True
    )
    result = await db.execute(query)
    return result.scalars().all()
```

### Permission Enforcement

**SUBSCRIPTION_ADMIN:**
- Create, edit, delete any program in subscription
- Assign programs to any client
- View all program analytics
- Manage exercise library

**COACH (GYM/ENTERPRISE):**
- Create, edit, delete own programs
- Assign programs to assigned clients only
- View analytics for assigned clients
- Add to exercise library

**CLIENT:**
- View assigned programs only
- Log workouts
- View own progress and history
- Cannot create or edit programs

### Cross-Subscription Features

**Global Exercise Library:**
- `is_global = TRUE` exercises visible to all subscriptions
- Created by APPLICATION_SUPPORT
- Read-only for all other users
- Subscriptions can add custom exercises to own library

**Marketplace Templates (ENTERPRISE - Future):**
- `is_public = TRUE` templates visible across subscriptions
- Purchasing copies template to buyer's subscription
- Original creator retains ownership
- Platform revenue sharing

---

## User Experience Flows

### Coach: Creating a Program

1. Navigate to "Programs" tab
2. Click "Create New Program"
3. Fill out program details form
4. Click "Build Program" to enter builder interface
5. Add weeks (or use auto-generate)
6. For each week, add training days
7. For each day, search and add exercises from library
8. Configure sets, reps, load for each exercise
9. Preview full program
10. Save as template
11. Assign to clients or save for later

### Coach: Assigning a Program

1. Navigate to "Clients" tab
2. Select a client
3. Click "Assign Program"
4. Browse template library or search
5. Select template and preview
6. Set start date
7. Optionally customize exercises
8. Add assignment notes
9. Confirm assignment
10. Client receives notification

### Client: Logging a Workout

1. Open mobile app or web dashboard
2. View "Today's Workout"
3. See list of exercises with prescribed sets/reps/load
4. Complete first exercise
5. For each set:
   - Enter actual reps
   - Enter actual weight
   - Enter RPE (optional)
   - Add notes (optional)
6. Submit set
7. Rest timer starts automatically
8. Repeat for all sets
9. Move to next exercise
10. After all exercises, mark workout complete
11. Add session notes and overall rating
12. Submit workout log

### Client: Viewing Progress

1. Navigate to "Progress" tab
2. See current program overview
   - Completion percentage
   - Current week/day
   - Adherence rate
3. View recent workout history
4. See personal records achieved
5. View exercise-specific progression charts
6. Filter by date range, exercise, or muscle group

---

## Client Program Experience

### Client Dashboard - Program View

**When Client Has Active Program:**

```
┌────────────────────────────────────────────────────────────┐
│  Welcome back, John!                                        │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Current Program: 8-Week Linear Strength                   │
│  Week 2 of 8 • Day 3 (Friday)                              │
│  Progress: ████████░░░░░░░░░░ 25%                         │
│  Adherence: 11/12 workouts (92%)                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  TODAY'S WORKOUT - Heavy Day                         │  │
│  │                                                       │  │
│  │  Session 3: Full Body Heavy                          │  │
│  │  Estimated time: 60 minutes                          │  │
│  │                                                       │  │
│  │  Exercises:                                          │  │
│  │  • Squat: 5×5 @ 225 lbs                             │  │
│  │  • Bench Press: 5×5 @ 185 lbs                       │  │
│  │  • Barbell Row: 5×5 @ 165 lbs                       │  │
│  │  • Overhead Press: 5×5 @ 115 lbs                    │  │
│  │                                                       │  │
│  │  [Start Workout] →                                   │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Quick Stats:                                              │
│  • Next workout: Saturday (Light Day)                      │
│  • Personal Records this program: 3                        │
│  • Total volume lifted: 145,230 lbs                        │
│                                                             │
│  [View Full Program] [Progress Details]                   │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

**When Client Has NO Active Program:**

```
┌────────────────────────────────────────────────────────────┐
│  Welcome back, John!                                        │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  📋 No Active Program                                      │
│                                                             │
│  You don't have an active training program yet.            │
│  Your coach will assign one soon!                          │
│                                                             │
│  In the meantime:                                          │
│  • [View Program History]                                  │
│  • [Browse Workout Library]                                │
│  • [Log Custom Workout]                                    │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### Client Program Details Page

**Full Program View (Read-Only):**

```
┌────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard                                        │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  8-Week Linear Strength Program                            │
│  Assigned by: Coach Mike                                    │
│  Started: Jan 15, 2025 • Ends: Mar 10, 2025               │
│                                                             │
│  Coach Notes:                                              │
│  "Focus on form over weight. Take the rest days seriously. │
│   You've got this! 💪"                                     │
│                                                             │
│  Progress: Week 2 of 8 (25% complete)                      │
│  ████████░░░░░░░░░░░░░░░░░░                               │
│                                                             │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  [Week 1✓] [Week 2 ◐] [Week 3] [Week 4] ... [Week 8]     │
│                                                             │
│  Week 2: Building Phase                                    │
│  ├─ ✅ Day 1: Heavy (Completed Mon, Jan 22)              │
│  ├─ ✅ Day 2: Light (Completed Wed, Jan 24)              │
│  ├─ 🎯 Day 3: Heavy (Today - Friday)                      │
│  │   └─ Squat: 5×5 @ 225 lbs                             │
│  │   └─ Bench Press: 5×5 @ 185 lbs                       │
│  │   └─ Barbell Row: 5×5 @ 165 lbs                       │
│  │   └─ Overhead Press: 5×5 @ 115 lbs                    │
│  │   [Start Workout] →                                    │
│  │                                                          │
│  └─ ⏸️  Day 4: Light (Scheduled Sat, Jan 27)              │
│      └─ Preview exercises...                               │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### Workout Execution Flow (Client Mobile App)

**Pre-Workout Screen:**

```
┌──────────────────────┐
│  Today's Workout     │
│  Heavy Day           │
│                      │
│  📊 Session 3/32     │
│  ⏱️  ~60 minutes     │
│  🏋️  4 exercises     │
│                      │
│  Squat               │
│  Bench Press         │
│  Barbell Row         │
│  Overhead Press      │
│                      │
│  Ready?              │
│                      │
│  [Start Workout] →   │
│                      │
│  Warm-up tips:       │
│  • 5-10 min cardio   │
│  • Dynamic stretches │
│  • Empty bar sets    │
└──────────────────────┘
```

**During Workout - Exercise View:**

```
┌──────────────────────┐
│  Exercise 1 of 4     │
│  ━━━━━━━━━░░░░       │
│                      │
│  SQUAT               │
│  🎯 Target: 5×5      │
│  ⚖️  Weight: 225 lbs  │
│                      │
│  Set 1 of 5          │
│  ┌────────────────┐  │
│  │ Reps: [ 5  ]   │  │
│  │ Weight: [225]  │  │
│  │ RPE: [●●●●●○○] │  │
│  │               │  │
│  │ [✓ Log Set]   │  │
│  └────────────────┘  │
│                      │
│  Rest Timer: 3:00    │
│  ⏱️  2:45 remaining   │
│  [Skip Rest]         │
│                      │
│  Sets Completed:     │
│  ✅ Set 1: 5 @ 225   │
│  ⏳ Set 2            │
│  ⏳ Set 3            │
│  ⏳ Set 4            │
│  ⏳ Set 5            │
│                      │
│  Video Guide ▶️       │
│  Form Tips 💡        │
└──────────────────────┘
```

**Post-Workout Summary:**

```
┌──────────────────────┐
│  Workout Complete!   │
│  🎉 Great job!       │
│                      │
│  Session Summary     │
│  ⏱️  Duration: 58min  │
│  🏋️  Exercises: 4/4   │
│  📊 Total Volume:    │
│     12,450 lbs       │
│                      │
│  🏆 New PR!          │
│  Squat: 225×5        │
│  (prev: 220×5)       │
│                      │
│  How did you feel?   │
│  Energy: ●●●●○       │
│  Difficulty: ●●●○○   │
│                      │
│  Notes (optional):   │
│  ┌────────────────┐  │
│  │ Felt strong    │  │
│  │ today!         │  │
│  └────────────────┘  │
│                      │
│  [Save & Finish]     │
│                      │
│  Next workout:       │
│  Saturday - Light    │
└──────────────────────┘
```

### Client Program Progress Dashboard

**Progress Analytics View:**

```
┌────────────────────────────────────────────────────────────┐
│  Program Progress - 8-Week Linear Strength                 │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Overall Progress                                          │
│  Week 2 of 8 • 25% Complete                                │
│  ████████░░░░░░░░░░░░░░░░░░                               │
│                                                             │
│  Adherence: 11/12 workouts (92%)                           │
│  On track to finish: March 10, 2025                        │
│                                                             │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Performance Trends                                         │
│                                                             │
│  Squat Progression                                         │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 240│                                            ●    │  │
│  │ 230│                                      ●          │  │
│  │ 220│                                ●                │  │
│  │ 210│                          ●                      │  │
│  │ 200│                    ●                            │  │
│  │    └───────────────────────────────────────────────  │  │
│  │      W1   W2   W3   W4   W5   W6   W7   W8          │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Volume Per Week                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 60K│     █                                           │  │
│  │ 50K│     █  █                                        │  │
│  │ 40K│  █  █  █                                        │  │
│  │ 30K│  █  █  █                                        │  │
│  │    └───────────────────────────────────────────────  │  │
│  │      W1  W2 W3  W4  W5  W6  W7  W8                  │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Personal Records This Program: 3                          │
│  • Squat: 225×5 (Jan 26)                                  │
│  • Bench: 185×5 (Jan 24)                                  │
│  • Row: 165×5 (Jan 22)                                    │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### Client Notifications

**Program Assignment Notification:**
```
📧 Email: "New Training Program Assigned"

Hi John,

Coach Mike has assigned you a new training program!

Program: 8-Week Linear Strength
Start Date: January 15, 2025
Duration: 8 weeks
Frequency: 4 workouts per week

Coach's Message:
"Focus on form over weight. Take the rest days seriously. You've got this! 💪"

[View Program in App] [Log in to Web Dashboard]

Questions? Reply to this email or message Coach Mike in the app.
```

**Workout Reminder Notification:**
```
🔔 Push Notification (Mobile):

"Today's Workout Ready!"
Heavy Day - Session 3
Squat, Bench, Row, OHP
Tap to start →
```

**Milestone Achievement:**
```
🎉 Push Notification:

"New Personal Record! 🏆"
Squat: 225 lbs × 5 reps
Previous: 220 lbs × 5 reps
Keep crushing it!
```

---

## Progressive Overload Strategies

### Built-in Progression Models

**Linear Progression:**
- Increase weight by fixed amount each week (e.g., +5 lbs)
- Suitable for beginners
- Example: Week 1: 135 lbs → Week 2: 140 lbs → Week 3: 145 lbs

**Percentage-Based Progression:**
- Sets prescribed as % of 1RM
- Week 1: 70% × 5 reps
- Week 2: 75% × 5 reps
- Week 3: 80% × 3 reps

**RPE-Based Progression:**
- Maintain RPE while increasing weight
- Week 1: RPE 7 @ 185 lbs
- Week 2: RPE 7 @ 190 lbs (client naturally progressed)

**Volume Progression:**
- Increase total sets or reps
- Week 1: 3×8
- Week 2: 4×8
- Week 3: 4×10

**Undulating Periodization:**
- Vary intensity and volume within week
- Monday: 4×10 @ 70%
- Wednesday: 5×5 @ 85%
- Friday: 3×8 @ 75%

### Auto-Regulation Features

**RPE-Based Auto-Regulation:**
- Client logs actual RPE for each set
- System suggests weight adjustments based on RPE trends
- If consistently hitting RPE 8 when prescribed RPE 7, suggest +5 lbs

**Performance-Based Suggestions:**
- Track exercise performance over time
- Identify plateaus or regression
- Suggest deload weeks or program changes
- Alert coach when client exceeds expected progression (potential PR)

---

## Mobile App Integration

### Workout Mode

**Features:**
- Offline-first (sync when connected)
- Rest timers with notifications
- Exercise video demonstrations
- Form tracking (front camera, AI form analysis - future)
- Voice logging (say reps/weight instead of typing)
- Playlist integration (Spotify, Apple Music)

**Workout Flow:**
- Pre-workout warm-up reminders
- Exercise-by-exercise guided flow
- Visual progress bar (X of Y exercises complete)
- Superset grouping (perform both, then rest)
- Post-workout summary and rating

### Progress Tracking

**Features:**
- Visual charts and graphs (weight progression, volume trends)
- Personal record celebrations (confetti animation!)
- Body weight and measurements tracking
- Progress photos with before/after comparison
- Share achievements on social media (optional)

---

## Technical Implementation Notes

### Performance Considerations

**Database Indexing:**
- Index on `subscription_id` for all tables (multi-tenant queries)
- Index on `client_id` for workout logs (client history queries)
- Index on `program_template_id` for assignments (template usage stats)
- Composite index on `(client_id, actual_date)` for workout history

**Query Optimization:**
- Use eager loading for nested relationships (programs → weeks → days → exercises)
- Paginate program library (50 templates per page)
- Cache global exercise library (rarely changes)
- Denormalize completion stats on `client_program_assignments` (avoid complex aggregations)

**Data Volume:**
- Exercise logs grow rapidly (sets × exercises × workouts × clients)
- Archive completed programs after 1 year
- Implement partitioning on `workout_logs` by date (monthly partitions)

### Caching Strategy

**Redis Cache:**
- Global exercise library (TTL: 24 hours)
- Program template previews (TTL: 1 hour)
- User's active assignments (TTL: 5 minutes)
- Analytics dashboard data (TTL: 15 minutes)

**Cache Invalidation:**
- On program template edit: invalidate template cache
- On assignment creation: invalidate user's active assignments
- On workout log: invalidate client progress cache

### Real-Time Features (Future)

**WebSocket Updates:**
- Coach sees live workout progress as client logs sets
- Real-time notifications for PR achievements
- Live leaderboard for group challenges

---

## Future Enhancements

### Advanced Features

**AI-Powered Program Generation:**
- Input: Client goals, experience level, equipment, schedule
- Output: Fully generated program tailored to client
- Uses ML trained on successful programs

**Form Analysis:**
- Use device camera + AI to analyze exercise form
- Provide real-time feedback on depth, bar path, tempo
- Flag potential injury risk (excessive rounding, knee valgus)

**Nutrition Integration:**
- Macro tracking integrated with workout programs
- Periodized nutrition (high carb on training days, lower on rest days)
- Meal planning based on training phase

**Wearable Integration:**
- Import heart rate data from Apple Watch, Fitbit, Garmin
- Track recovery metrics (HRV, sleep quality, resting HR)
- Auto-suggest deload weeks based on recovery scores

**Social Features:**
- Client can share workouts with friends
- Group challenges (total volume lifted, workouts completed)
- Leaderboards within subscription
- Community feed of achievements

**Voice Assistant:**
- "Hey Gym App, log 10 reps at 185 pounds, RPE 8"
- "What's my next exercise?"
- "Start rest timer"

### Business Features

**Program Marketplace:**
- Buy/sell program templates
- Revenue sharing for creators
- Ratings and reviews
- Featured programs

**Certification Integration:**
- NASM, ACE, NSCA program templates
- CEU credits for creating programs
- Verified coach badges

**API for Third-Party Apps:**
- Allow fitness apps to integrate with Gym App
- Export workout data to MyFitnessPal, Strava
- Import programs from Training Peaks, TrainHeroic

---

## Implementation Roadmap

### Phase 1: Core Backend Integration (Weeks 1-3)

**Goal**: Connect existing Strength Builder to backend and enable saving programs

**Tasks:**
1. **Database Setup**
   - Create all tables from schema (programs, program_weeks, program_days, program_day_exercises, etc.)
   - Set up migrations using Alembic
   - Add indexes and foreign key constraints
   - Implement audit fields (created_at/by, updated_at/by)

2. **Backend API - Program CRUD**
   - POST `/api/v1/programs` - Create program from builder
   - GET `/api/v1/programs` - List programs (filtered by subscription)
   - GET `/api/v1/programs/:id` - Get program details with full hierarchy
   - PUT `/api/v1/programs/:id` - Update program
   - DELETE `/api/v1/programs/:id` - Soft delete program

3. **Frontend Integration**
   - Update ProgramBuilder.tsx final step to save via API
   - Add "Save as Template" option with metadata form
   - Add "Assign to Client" option (basic version)
   - Handle success/error states

4. **Exercise Library**
   - Seed global exercise library with common movements
   - API endpoints for exercise CRUD
   - Frontend exercise selector component

**Deliverables:**
- Coaches can create and save programs from existing Strength Builder
- Programs stored in database with proper multi-tenant isolation
- Basic exercise library available

---

### Phase 2: Template Library & Assignment (Weeks 4-6)

**Goal**: Build template browsing and enable assignment to clients

**Tasks:**
1. **Template Library Page**
   - Create `/templates` route in frontend
   - Build template card grid with filters
   - Implement search functionality
   - Template detail/preview page
   - "My Templates" vs "Subscription Templates" tabs

2. **Assignment System**
   - Assignment modal/wizard component
   - Client selection dropdown
   - Start date picker
   - Assignment notes textarea
   - POST `/api/v1/assignments` endpoint
   - GET `/api/v1/assignments` endpoint (for coach view)

3. **Client View - Assigned Programs**
   - Update client dashboard to show active program
   - Display "Today's Workout" card
   - Program detail page (read-only view)
   - Week/day navigation

4. **Notifications**
   - Email notification on assignment
   - In-app notification system (basic)

**Deliverables:**
- Template library fully functional
- Coaches can assign programs to clients
- Clients can view assigned programs

---

### Phase 3: Workout Logging & Tracking (Weeks 7-10)

**Goal**: Enable clients to log workouts and track progress

**Tasks:**
1. **Workout Logging Interface**
   - "Start Workout" flow in client app
   - Exercise-by-exercise logging
   - Set/rep/weight input
   - RPE tracking
   - Rest timer
   - Workout completion summary

2. **Workout Log API**
   - POST `/api/v1/workouts/log` - Create workout log
   - POST `/api/v1/workouts/log/:id/exercises` - Log exercise sets
   - GET `/api/v1/workouts/history` - Client workout history

3. **Progress Tracking**
   - Client progress dashboard
   - Exercise progression charts
   - Volume tracking
   - Personal record detection and celebration
   - Adherence calculations

4. **Coach Monitoring**
   - View client's workout logs
   - Assignment progress overview
   - Adherence metrics
   - Performance trends

**Deliverables:**
- Clients can log workouts from assigned programs
- Progress tracking with analytics
- Coaches can monitor client progress

---

### Phase 4: Advanced Features (Weeks 11-14)

**Goal**: Polish and add customization features

**Tasks:**
1. **Program Customization**
   - Mid-assignment program editing
   - Exercise substitution
   - Load/volume adjustments
   - Custom notes per client

2. **Template Versioning**
   - Version tracking for templates
   - Update propagation options
   - Change history

3. **Analytics Dashboard**
   - Subscription-level program analytics
   - Template performance metrics
   - Client retention correlation
   - Coach performance comparison (GYM/ENTERPRISE)

4. **Mobile App Enhancement**
   - Offline-first workout logging
   - Push notifications
   - Video exercise demonstrations
   - Form timer and audio cues

**Deliverables:**
- Full customization capabilities
- Comprehensive analytics
- Enhanced mobile experience

---

### Phase 5: Additional Builders (Weeks 15-20)

**Goal**: Add Hypertrophy and Conditioning builders

**Tasks:**
1. **Builder Selection Page**
   - `/program-builder/select` route
   - Cards for each builder type
   - Builder descriptions and use cases

2. **Hypertrophy Builder**
   - Wizard interface for muscle group splits
   - Volume calculator
   - Exercise selection per muscle group
   - Rep range configuration
   - Generate 8-12 week program

3. **Conditioning Builder**
   - HIIT/cardio program wizard
   - Interval protocol selection
   - Duration and intensity progression
   - Generate conditioning program

4. **Custom Builder** (Blank Canvas)
   - Drag-and-drop week/day/exercise interface
   - Manual prescription fields
   - Free-form program creation

**Deliverables:**
- Multiple builder types available
- Coaches can choose appropriate builder for client goals

---

### Phase 6: Marketplace (Future - Weeks 21+)

**Goal**: ENTERPRISE feature for public template sharing

**Tasks:**
1. **Marketplace Infrastructure**
   - Public template discovery
   - Purchase/download flow
   - Revenue sharing system
   - Payment processing integration

2. **Quality Control**
   - Template review system
   - Rating and reviews
   - Content moderation
   - Featured templates

3. **Creator Tools**
   - Template publishing wizard
   - Pricing configuration
   - Sales analytics
   - Payout management

**Deliverables:**
- Public marketplace for templates
- Revenue sharing for creators
- Community-driven content

---

## Summary

The Program Builder Ecosystem is a comprehensive three-layer system:

### Architecture Layers

1. **LAYER 1: Program Builders**
   - ✅ Strength Builder (Existing - needs backend integration)
   - ⏳ Hypertrophy Builder (Phase 5)
   - ⏳ Conditioning Builder (Phase 5)
   - ⏳ Custom Builder (Phase 5)

2. **LAYER 2: Template Library**
   - ⏳ Template browsing and filtering (Phase 2)
   - ⏳ Template preview and detail pages (Phase 2)
   - ⏳ Visibility controls (private/subscription/public) (Phase 2)
   - ⏳ Version management (Phase 4)

3. **LAYER 3: Assignment & Tracking**
   - ⏳ Assignment workflow (Phase 2)
   - ⏳ Client program view (Phase 2)
   - ⏳ Workout logging (Phase 3)
   - ⏳ Progress analytics (Phase 3)
   - ⏳ Customization (Phase 4)

### Key Design Principles

1. **Flexibility**: Support diverse training methodologies (strength, hypertrophy, conditioning)
2. **Scalability**: Handle thousands of concurrent assignments and workout logs
3. **Multi-Tenancy**: Strict data isolation by subscription
4. **Progressive Overload**: Built-in support for periodization and progression
5. **User Experience**: Intuitive flows for coaches and clients
6. **Analytics**: Data-driven insights for coaches and admins
7. **Modularity**: Separate builders, templates, and assignments for clean architecture

### Success Metrics

**Coach Metrics:**
- Time to create first program: < 15 minutes
- Programs created per coach: 5+ in first month
- Template reuse rate: 60%+

**Client Metrics:**
- Workout completion rate: 75%+
- Client satisfaction rating: 4.5+ / 5.0
- Adherence to program: 80%+

**Business Metrics:**
- Feature adoption: 70%+ of active subscriptions use program builder
- Client retention: 15% improvement for clients with active programs
- Upgrade driver: 30% of Individual → Gym upgrades cite program features

This design provides a strong foundation for the core Program Builder MVP (Phases 1-3), with clear pathways for advanced features (Phase 4), additional builders (Phase 5), and marketplace expansion (Phase 6).
