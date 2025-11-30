# Program Builder - Template-Based Architecture

## Overview

The Program Builder is a **template-based system** for creating, customizing, and assigning workout programs. The core concept is that coaches work with parameterized templates that can be customized with specific inputs (focus, goals, exercises, weights) to generate personalized training programs for clients.

### Key Concepts

1. **Template-Based Workflow** - Programs are created from templates, not wizards
2. **Default Templates** - Platform provides ready-to-use templates available to all coaches
3. **Custom Templates** - Coaches can create and save their own templates
4. **Parameterized Inputs** - Templates require inputs (focus, goals, exercises, weights) to generate programs
5. **Reusability** - Templates can be assigned to multiple clients with different parameters

### Template Architecture

```
Default Templates (Platform-provided)
├── Strength Templates
│   ├── Linear Progression (Focus: Strength, Goal: Increase 1RM)
│   ├── 5/3/1 Progression (Focus: Strength, Goal: Long-term gains)
│   └── Powerlifting Peaking (Focus: Strength, Goal: Competition prep)
├── Conditioning Templates
│   ├── KB Press Conditioning (Focus: Conditioning, Goal: Improve KB press)
│   ├── Endurance Builder (Focus: Conditioning, Goal: Stamina)
│   └── HIIT Protocol (Focus: Conditioning, Goal: Fat loss)
└── Hypertrophy Templates
    ├── PPL Split (Focus: Hypertrophy, Goal: Muscle mass)
    └── Upper/Lower Split (Focus: Hypertrophy, Goal: Balanced growth)

Custom Templates (Coach-created)
├── Coach's Template 1 (private to subscription)
├── Coach's Template 2 (private to subscription)
└── Shared Template (can be made public)
```

---

## Template Parameters

All templates require input parameters when creating a program for a client. These parameters customize the template to the client's specific needs.

### Core Parameters

#### 1. Focus (Required)
The primary training adaptation goal:
- **Strength** - Maximal force production, neural adaptations
- **Hypertrophy** - Muscle growth, volume accumulation
- **Conditioning** - Work capacity, cardiovascular fitness
- **Power** - Rate of force development, explosiveness
- **Sport-Specific** - Athletic performance, movement patterns
- **General Fitness** - Overall health and fitness

#### 2. Goal (Required)
Specific measurable objective within the focus area:

**Strength Examples:**
- "Increase bench press to 400 lbs"
- "Achieve bodyweight back squat"
- "Deadlift 500 lbs by competition"

**Conditioning Examples:**
- "Improve kettlebell press endurance"
- "Complete 5K in under 25 minutes"
- "Increase work capacity for CrossFit"

**Hypertrophy Examples:**
- "Gain 10 lbs lean muscle"
- "Build bigger arms (16-inch biceps)"
- "Develop chest and shoulders"

#### 3. Target Exercises (Optional, template-dependent)
Specific movements to emphasize:
- Compound lifts: Squat, Bench Press, Deadlift, Overhead Press
- Accessory work: Rows, Lunges, Pull-ups, Dips
- Conditioning tools: Kettlebells, Rowers, Assault Bikes
- Sport-specific: Olympic lifts, Plyometrics

#### 4. Starting Weights/Capacity (Optional, template-dependent)
Client's current performance levels:
- 1RM values for main lifts
- RPE ranges for conditioning
- Max reps at specific weights
- Baseline times/distances

#### 5. Schedule Parameters (Required)
Training frequency and duration:
- **Days per week**: 2-7 sessions
- **Program duration**: 4-52 weeks
- **Session length**: 30-120 minutes
- **Preferred training days**: Mon/Wed/Fri, etc.

#### 6. Additional Customization (Optional)
- Equipment availability
- Injury limitations
- Preference for rep ranges
- Volume tolerance

---

## Template Structure

### Template Definition

Each template is a reusable program blueprint with:

```typescript
interface ProgramTemplate {
  id: string;
  name: string;
  description: string;

  // Template categorization
  focus: TemplateFocus; // Strength, Conditioning, Hypertrophy, etc.
  difficulty_level: 'beginner' | 'intermediate' | 'advanced' | 'elite';

  // Template ownership
  created_by: string; // User ID of creator
  subscription_id: string | null; // null for default templates
  is_default: boolean; // Platform-provided templates
  is_public: boolean; // Available in marketplace

  // Required parameters for this template
  required_parameters: TemplateParameter[];
  optional_parameters: TemplateParameter[];

  // Program structure (defined but parameterized)
  duration_weeks: number;
  days_per_week: number;
  program_structure: ProgramStructure; // Weeks, days, exercises

  // Usage and ratings
  times_assigned: number;
  average_rating: number;
  average_completion_rate: number;
}

interface TemplateParameter {
  key: string; // 'goal', 'target_weight', 'focus_lift'
  label: string; // 'Primary Goal', 'Target Bench Press Weight'
  type: 'text' | 'number' | 'select' | 'multi-select';
  required: boolean;
  options?: string[]; // For select types
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
  };
  help_text?: string;
}
```

### Example: Strength - Linear Progression Template

```typescript
{
  id: "default-strength-linear",
  name: "Linear Progression - Compound Lifts",
  description: "Classic 5×5 linear progression for building maximal strength on compound lifts",
  focus: "strength",
  difficulty_level: "beginner",
  is_default: true,
  is_public: true,

  required_parameters: [
    {
      key: "goal",
      label: "Strength Goal",
      type: "text",
      required: true,
      help_text: "Example: Bench press 315 lbs, Squat 405 lbs"
    },
    {
      key: "focus_lifts",
      label: "Primary Lifts",
      type: "multi-select",
      required: true,
      options: ["Squat", "Bench Press", "Deadlift", "Overhead Press"],
      help_text: "Select 3-4 compound movements to focus on"
    },
    {
      key: "current_1rm",
      label: "Current 1RM Values",
      type: "number",
      required: true,
      help_text: "Enter current max for each selected lift"
    }
  ],

  optional_parameters: [
    {
      key: "days_per_week",
      label: "Training Days",
      type: "select",
      required: false,
      options: ["3", "4", "5"],
      help_text: "Number of sessions per week"
    }
  ],

  duration_weeks: 8,
  days_per_week: 4,

  program_structure: {
    // Week-by-week progression defined in the template
    // Uses parameter values to calculate actual weights/reps
  }
}
```

### Example: Conditioning - KB Press Improvement Template

```typescript
{
  id: "default-conditioning-kb-press",
  name: "Kettlebell Press Conditioning",
  description: "Build pressing endurance and work capacity with kettlebells",
  focus: "conditioning",
  difficulty_level: "intermediate",
  is_default: true,
  is_public: true,

  required_parameters: [
    {
      key: "goal",
      label: "Conditioning Goal",
      type: "text",
      required: true,
      help_text: "Example: Improve KB press endurance, 100 presses in 10 minutes"
    },
    {
      key: "kb_weight",
      label: "Kettlebell Weight (lbs)",
      type: "number",
      required: true,
      validation: { min: 8, max: 106 },
      help_text: "Weight you can press for 5-10 reps"
    },
    {
      key: "current_capacity",
      label: "Current Max Reps",
      type: "number",
      required: true,
      help_text: "Maximum consecutive presses per arm"
    }
  ],

  optional_parameters: [
    {
      key: "supplemental_work",
      label: "Include Supplemental Work",
      type: "select",
      options: ["None", "Core only", "Full conditioning"],
      help_text: "Additional work beyond KB pressing"
    }
  ],

  duration_weeks: 6,
  days_per_week: 3,

  program_structure: {
    // Progressive volume and density work
    // EMOM, ladders, intervals based on parameters
  }
}
```

---

## Database Schema

### Programs Table

```sql
CREATE TABLE programs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID REFERENCES subscriptions(id), -- NULL for default templates
    created_by UUID NOT NULL REFERENCES users(id),

    -- Program metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,
    program_type VARCHAR(50) NOT NULL, -- 'strength', 'hypertrophy', 'conditioning', 'power', 'sport_specific'
    difficulty_level VARCHAR(50), -- 'beginner', 'intermediate', 'advanced', 'elite'
    duration_weeks INT NOT NULL CHECK (duration_weeks > 0 AND duration_weeks <= 52),
    days_per_week INT NOT NULL CHECK (days_per_week > 0 AND days_per_week <= 7),

    -- Template settings
    is_template BOOLEAN DEFAULT FALSE,
    is_default BOOLEAN DEFAULT FALSE, -- Platform-provided default templates
    is_public BOOLEAN DEFAULT FALSE, -- Available to other subscriptions
    template_version INT DEFAULT 1,
    parent_template_id UUID REFERENCES programs(id), -- for template versioning/forking

    -- Template parameters (JSON schema)
    required_parameters JSONB DEFAULT '[]', -- Array of parameter definitions
    optional_parameters JSONB DEFAULT '[]', -- Array of parameter definitions

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

    -- Marketplace (future)
    price_cents INT, -- null = free
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
CREATE INDEX idx_programs_template ON programs(is_template, is_default, is_public) WHERE is_active = TRUE;
CREATE INDEX idx_programs_type ON programs(program_type);
CREATE INDEX idx_programs_creator ON programs(created_by);
```

### Program Assignments Table

```sql
CREATE TABLE program_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id),

    -- Template and client
    template_id UUID NOT NULL REFERENCES programs(id), -- Source template
    client_id UUID NOT NULL REFERENCES users(id), -- Assigned to
    assigned_by UUID NOT NULL REFERENCES users(id), -- Coach who assigned

    -- Program instance (can be customized after assignment)
    program_id UUID NOT NULL REFERENCES programs(id), -- Actual program instance (copy of template)

    -- Assignment parameters (values provided when creating from template)
    assignment_parameters JSONB NOT NULL, -- { "goal": "Bench 315 lbs", "focus_lifts": [...], "current_1rm": {...} }

    -- Scheduling
    start_date DATE NOT NULL,
    end_date DATE, -- Calculated from template duration
    actual_end_date DATE, -- When client actually completed

    -- Status
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'paused', 'completed', 'cancelled'
    completion_percentage DECIMAL(5,2) DEFAULT 0.00,

    -- Progress tracking
    workouts_completed INT DEFAULT 0,
    workouts_total INT NOT NULL,
    current_week INT DEFAULT 1,
    current_day INT DEFAULT 1,

    -- Client feedback
    client_rating DECIMAL(3,2), -- 0.00 to 5.00
    client_feedback TEXT,

    -- Coach notes
    coach_notes TEXT,

    -- Soft delete
    is_active BOOLEAN DEFAULT TRUE,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_assignments_client ON program_assignments(client_id) WHERE is_active = TRUE;
CREATE INDEX idx_assignments_template ON program_assignments(template_id);
CREATE INDEX idx_assignments_subscription ON program_assignments(subscription_id);
CREATE INDEX idx_assignments_status ON program_assignments(status) WHERE is_active = TRUE;
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

    -- Progression tracking (for assigned programs)
    is_completed BOOLEAN DEFAULT FALSE,
    actual_sets INT,
    actual_reps INT,
    actual_weight DECIMAL(10,2),
    actual_rpe DECIMAL(3,1),
    completion_date TIMESTAMP WITH TIME ZONE,

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

---

## User Workflows

### Workflow 1: Coach Assigns Default Template to Client

**Scenario**: Coach wants to use a platform-provided Strength template for a client who wants to bench 400 lbs.

1. **Browse Templates**
   - Coach navigates to "Program Templates"
   - Filters by Focus: "Strength"
   - Finds "Linear Progression - Compound Lifts" (default template)

2. **Select Client**
   - Coach clicks "Assign to Client"
   - Selects client from their roster

3. **Provide Parameters**
   - **Goal**: "Bench press 400 lbs by June 2026"
   - **Focus Lifts**: Bench Press, Squat, Overhead Press
   - **Current 1RM**: Bench 315 lbs, Squat 405 lbs, OHP 185 lbs
   - **Days per Week**: 4
   - **Start Date**: Monday, December 2, 2025

4. **Generate Program**
   - System creates program instance from template
   - Calculates all weights based on current 1RM and progression
   - Creates 8-week schedule with 4 sessions/week

5. **Review & Assign**
   - Coach reviews generated program
   - Can make adjustments to specific exercises/weights
   - Clicks "Assign Program"

6. **Client Notification**
   - Client receives notification
   - Can view program in their dashboard
   - Begins tracking workouts

### Workflow 2: Coach Creates Custom Template

**Scenario**: Coach has a unique conditioning protocol they use for multiple clients.

1. **Create New Template**
   - Coach navigates to "My Templates"
   - Clicks "Create New Template"

2. **Template Setup**
   - **Name**: "KB Complex Conditioning"
   - **Focus**: Conditioning
   - **Difficulty**: Intermediate
   - **Duration**: 6 weeks
   - **Days/Week**: 3

3. **Define Parameters**
   - Add required parameter: "Goal" (text)
   - Add required parameter: "KB Weight" (number, 8-106 lbs)
   - Add required parameter: "Current Max Reps" (number)
   - Add optional parameter: "Supplemental Work" (select)

4. **Build Program Structure**
   - Week 1: Foundation
     - Day 1: KB Complex A (3 rounds)
     - Day 2: KB Complex B (4 rounds)
     - Day 3: KB Complex C (3 rounds)
   - Week 2-6: Progressive volume/intensity
   - For each exercise, specify sets/reps/rest

5. **Save Template**
   - Template saved to coach's subscription
   - Private by default (only coach can use)
   - Can optionally share with other coaches in subscription

6. **Assign to Multiple Clients**
   - Coach can now assign this template to any client
   - Each assignment gets customized parameters

### Workflow 3: Client Follows Assigned Program

**Scenario**: Client has been assigned "Linear Progression" template focused on bench press.

1. **View Program**
   - Client logs in
   - Dashboard shows "Active Program: Linear Progression"
   - Can see current week and upcoming workouts

2. **Start Workout**
   - Monday: "Push Day - Week 1"
   - Warm-up instructions displayed
   - Exercise list with prescribed sets/reps/weights

3. **Log Performance**
   - Exercise 1: Bench Press 5×5 @ 225 lbs
   - Client logs each set (weight, reps, RPE)
   - Can add notes: "Felt strong, bar speed good"

4. **Complete Workout**
   - All exercises logged
   - System marks workout as complete
   - Updates progress: "3/32 workouts complete (9%)"

5. **Progress Tracking**
   - Client can view progression over weeks
   - Graphs show weight increases
   - Completion percentage shown

6. **Coach Monitoring**
   - Coach can view client's logged workouts
   - Can provide feedback on performance
   - Can adjust future weeks if needed

### Workflow 4: Browse and Use Community Templates (Future)

**Scenario**: Coach wants to find a proven hypertrophy template from the marketplace.

1. **Browse Marketplace**
   - Navigate to "Template Marketplace"
   - Filter: Focus = Hypertrophy, Rating > 4.5 stars

2. **Review Template**
   - Click on "PPL Hypertrophy - 12 Weeks"
   - See description, required parameters, sample week
   - Read reviews from other coaches
   - View creator's profile and other templates

3. **Purchase/Download**
   - Free templates: Click "Add to My Templates"
   - Paid templates: Purchase for $X.XX
   - Template now available in coach's library

4. **Customize and Assign**
   - Follow standard assignment workflow
   - Can further customize after download
   - Can save customizations as own template variant

---

## Default Platform Templates

### Template Library v1.0

The platform will launch with the following default templates available to all coaches:

#### Strength Focus

1. **Linear Progression - Classic 5×5**
   - Difficulty: Beginner
   - Duration: 8 weeks
   - Days/Week: 3-4
   - Goal Examples: "Squat 315 lbs", "Bench 225 lbs"
   - Parameters: Focus lifts (3-4), Current 1RM, Days/week

2. **Intermediate Strength Builder**
   - Difficulty: Intermediate
   - Duration: 12 weeks
   - Days/Week: 4
   - Goal Examples: "400 lb bench press", "500 lb deadlift"
   - Parameters: Primary goal lift, Current 1RM, Weak points

3. **Powerlifting Peaking Protocol**
   - Difficulty: Advanced
   - Duration: 16 weeks (12 weeks + 4 week peak)
   - Days/Week: 4-5
   - Goal Examples: "Competition prep", "Test new maxes"
   - Parameters: Meet date, Current 1RM (SBD), Weight class

#### Conditioning Focus

4. **KB Press Conditioning**
   - Difficulty: Intermediate
   - Duration: 6 weeks
   - Days/Week: 3
   - Goal Examples: "Improve KB press endurance", "100 presses in 10 min"
   - Parameters: KB weight, Current max reps, Supplemental work preference

5. **General Conditioning Builder**
   - Difficulty: Beginner to Intermediate
   - Duration: 8 weeks
   - Days/Week: 3-4
   - Goal Examples: "Improve work capacity", "Better cardiovascular fitness"
   - Parameters: Equipment available, Session length, Intensity preference

6. **CrossFit-Style Conditioning**
   - Difficulty: Intermediate to Advanced
   - Duration: 10 weeks
   - Days/Week: 5
   - Goal Examples: "Improve CrossFit performance", "Increase engine"
   - Parameters: Weaknesses (gymnastics/weightlifting/cardio), Equipment

#### Hypertrophy Focus

7. **Push/Pull/Legs Split**
   - Difficulty: Intermediate
   - Duration: 12 weeks
   - Days/Week: 6 (2x per muscle group)
   - Goal Examples: "Build muscle mass", "Gain 10 lbs lean mass"
   - Parameters: Weak body parts, Rep range preference, Volume tolerance

8. **Upper/Lower Split**
   - Difficulty: Beginner to Intermediate
   - Duration: 10 weeks
   - Days/Week: 4
   - Goal Examples: "Balanced muscle growth", "Build strength and size"
   - Parameters: Focus areas (upper/lower priority), Equipment, Session length

#### General Fitness

9. **Beginner Full Body**
   - Difficulty: Beginner
   - Duration: 8 weeks
   - Days/Week: 3
   - Goal Examples: "Get stronger and fitter", "Build foundation"
   - Parameters: Equipment available, Limitations/injuries, Session length

10. **Athletic Development**
    - Difficulty: Intermediate
    - Duration: 12 weeks
    - Days/Week: 4-5
    - Goal Examples: "Improve athleticism", "Sport-specific training"
    - Parameters: Sport, Weaknesses, Competition schedule

---

## Technical Implementation

### Backend API Endpoints

#### Template Management

```
GET    /api/v1/programs/templates              # List all templates (default + coach's custom)
GET    /api/v1/programs/templates/default      # List only default templates
GET    /api/v1/programs/templates/my-templates # List coach's custom templates
GET    /api/v1/programs/templates/{id}         # Get template details
POST   /api/v1/programs/templates              # Create new custom template
PUT    /api/v1/programs/templates/{id}         # Update custom template
DELETE /api/v1/programs/templates/{id}         # Delete custom template (soft delete)

# Template assignment workflow
POST   /api/v1/programs/templates/{id}/preview # Preview program with parameters (doesn't save)
POST   /api/v1/programs/templates/{id}/assign  # Create program instance and assign to client
```

#### Program Assignment Management

```
GET    /api/v1/coaches/me/assignments          # Coach's view of all program assignments
GET    /api/v1/clients/me/assignments          # Client's active programs
GET    /api/v1/assignments/{id}                # Get assignment details
PUT    /api/v1/assignments/{id}                # Update assignment (status, notes)
DELETE /api/v1/assignments/{id}                # Cancel assignment

# Progress tracking
GET    /api/v1/assignments/{id}/progress       # Get detailed progress
POST   /api/v1/assignments/{id}/workouts/{workout_id}/log  # Log workout completion
PUT    /api/v1/assignments/{id}/workouts/{workout_id}      # Update logged workout
```

#### Exercise Library

```
GET    /api/v1/exercises                       # List exercises (global + subscription's)
GET    /api/v1/exercises/{id}                  # Get exercise details
POST   /api/v1/exercises                       # Create custom exercise
PUT    /api/v1/exercises/{id}                  # Update exercise
DELETE /api/v1/exercises/{id}                  # Delete exercise
```

### Frontend Components

#### Coach View

```
/program-templates              # Browse all templates
/program-templates/default      # Default template library
/program-templates/my-templates # Coach's custom templates
/program-templates/create       # Create new template
/program-templates/{id}         # View/edit template
/program-templates/{id}/assign  # Assign template to client (parameter form)

/clients/{id}/programs          # Client's program history
/assignments/{id}               # Monitor client's progress on assignment
```

#### Client View

```
/my-programs                    # Active and past programs
/my-programs/{id}               # View program details
/my-programs/{id}/week/{week}   # Current week view
/workout/{id}                   # Today's workout (log performance)
/workout/{id}/history           # Past workout logs for same exercises
```

### Data Flow: Template Assignment

```
1. Coach selects template
   ↓
2. Coach selects client
   ↓
3. Frontend displays parameter form
   (based on template.required_parameters and template.optional_parameters)
   ↓
4. Coach fills in parameters:
   - Goal: "Bench press 400 lbs"
   - Focus lifts: [Bench Press, Squat, OHP]
   - Current 1RM: {bench: 315, squat: 405, ohp: 185}
   - Days/week: 4
   ↓
5. Frontend calls POST /api/v1/programs/templates/{id}/preview
   Backend generates program instance (not saved yet)
   Returns full program structure for review
   ↓
6. Coach reviews generated program
   Can make manual adjustments
   ↓
7. Coach clicks "Assign Program"
   Frontend calls POST /api/v1/programs/templates/{id}/assign
   ↓
8. Backend:
   a. Creates program instance (copy of template structure)
   b. Applies parameters to calculate all weights/reps
   c. Creates program_weeks, program_days, program_day_exercises
   d. Creates program_assignment record
   e. Links assignment to client
   ↓
9. Client receives notification
   Program appears in client dashboard
```

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
**Goal**: Core template system and database

- [ ] Database migrations
  - [ ] Update `programs` table with template fields
  - [ ] Create `program_assignments` table
  - [ ] Create `program_weeks`, `program_days`, `program_day_exercises` tables
  - [ ] Create `exercises_library` table
- [ ] Seed default exercises library
  - [ ] Compound lifts (Squat, Bench, Deadlift, OHP, Row)
  - [ ] Accessory exercises (50+ exercises)
  - [ ] Conditioning movements (KB, rowing, running, etc.)
- [ ] Backend models and schemas
  - [ ] ProgramTemplate model
  - [ ] ProgramAssignment model
  - [ ] Exercise model
  - [ ] Pydantic schemas for all models

**Deliverable**: Database ready, basic models in place

### Phase 2: Template Management API (Weeks 3-4)
**Goal**: CRUD operations for templates

- [ ] Template endpoints
  - [ ] GET /api/v1/programs/templates (list with filters)
  - [ ] GET /api/v1/programs/templates/{id}
  - [ ] POST /api/v1/programs/templates (create custom template)
  - [ ] PUT /api/v1/programs/templates/{id}
  - [ ] DELETE /api/v1/programs/templates/{id}
- [ ] Exercise library endpoints
  - [ ] GET /api/v1/exercises
  - [ ] POST /api/v1/exercises (custom exercises)
- [ ] Authorization
  - [ ] Coaches can create templates in their subscription
  - [ ] APPLICATION_SUPPORT can create default templates
  - [ ] Template visibility rules (default/public/private)

**Deliverable**: Full template CRUD API with authorization

### Phase 3: Default Templates Creation (Weeks 5-6)
**Goal**: Seed 10 default platform templates

- [ ] Create 10 default templates (see "Default Platform Templates" section)
  - [ ] 3 Strength templates
  - [ ] 3 Conditioning templates
  - [ ] 2 Hypertrophy templates
  - [ ] 2 General Fitness templates
- [ ] Define required_parameters for each template
- [ ] Build week-by-week structure for each
- [ ] Create seed script to populate database
- [ ] Test each template with sample parameters

**Deliverable**: 10 production-ready default templates

### Phase 4: Assignment Workflow API (Weeks 7-8)
**Goal**: Assign templates to clients with parameters

- [ ] Preview endpoint
  - [ ] POST /api/v1/programs/templates/{id}/preview
  - [ ] Accept parameters, return generated program (not saved)
  - [ ] Calculate all weights based on 1RM and parameters
- [ ] Assignment endpoint
  - [ ] POST /api/v1/programs/templates/{id}/assign
  - [ ] Create program instance from template
  - [ ] Apply parameters to generate weeks/days/exercises
  - [ ] Create assignment record
  - [ ] Link to client
- [ ] Assignment management
  - [ ] GET /api/v1/assignments (coach view)
  - [ ] GET /api/v1/clients/me/assignments (client view)
  - [ ] PUT /api/v1/assignments/{id} (update status, notes)

**Deliverable**: Full template-to-assignment workflow backend

### Phase 5: Coach Frontend (Weeks 9-11)
**Goal**: UI for coaches to manage and assign templates

- [ ] Template browsing
  - [ ] /program-templates page (list view with filters)
  - [ ] Template cards showing focus, difficulty, rating
  - [ ] Filter by focus, difficulty, default/custom
- [ ] Template details
  - [ ] /program-templates/{id} page
  - [ ] Show full template structure
  - [ ] Display required/optional parameters
  - [ ] Sample week view
- [ ] Assignment workflow
  - [ ] "Assign to Client" button
  - [ ] Client selection modal
  - [ ] Parameter form (dynamic based on template)
  - [ ] Preview generated program
  - [ ] Confirm and assign
- [ ] My Templates
  - [ ] /program-templates/my-templates
  - [ ] List custom templates
  - [ ] Create new template UI (Phase 6)

**Deliverable**: Coach can browse and assign default templates

### Phase 6: Template Builder UI (Weeks 12-14)
**Goal**: UI for coaches to create custom templates

- [ ] Template creation wizard
  - [ ] Step 1: Basic info (name, focus, difficulty, duration)
  - [ ] Step 2: Define parameters (add required/optional inputs)
  - [ ] Step 3: Build week structure (add weeks, name them)
  - [ ] Step 4: Build day structure (add days per week, name/type)
  - [ ] Step 5: Add exercises (search exercise library, add to days)
  - [ ] Step 6: Set prescriptions (sets, reps, load, rest)
  - [ ] Step 7: Review and save
- [ ] Exercise selection
  - [ ] Searchable exercise library
  - [ ] Filter by muscle group, equipment, category
  - [ ] Add custom exercises on-the-fly
- [ ] Template editing
  - [ ] Edit existing custom templates
  - [ ] Version control (create new version)
  - [ ] Duplicate template (fork from default or other custom)

**Deliverable**: Full template builder for coaches

### Phase 7: Client Frontend (Weeks 15-16)
**Goal**: UI for clients to view and track programs

- [ ] Program dashboard
  - [ ] /my-programs page
  - [ ] Show active program(s)
  - [ ] Show past programs
  - [ ] Progress indicators
- [ ] Program details
  - [ ] /my-programs/{id} page
  - [ ] Current week highlighted
  - [ ] Upcoming workouts
  - [ ] Completion statistics
- [ ] Workout logging
  - [ ] /workout/{id} page
  - [ ] Exercise list with prescribed sets/reps/weight
  - [ ] Log actual performance
  - [ ] RPE tracking
  - [ ] Notes field
  - [ ] Mark workout complete
- [ ] Progress visualization
  - [ ] Graphs showing weight progression
  - [ ] Completion percentage
  - [ ] Week-by-week summary

**Deliverable**: Full client program experience

### Phase 8: Analytics & Refinement (Weeks 17-18)
**Goal**: Insights and optimizations

- [ ] Template analytics
  - [ ] Times assigned
  - [ ] Average completion rate
  - [ ] Average rating
  - [ ] Client feedback
- [ ] Coach dashboard insights
  - [ ] Client progress summaries
  - [ ] Alerts for missed workouts
  - [ ] Adherence rates
- [ ] Performance optimizations
  - [ ] Caching for template queries
  - [ ] Optimize assignment preview generation
- [ ] UX improvements based on feedback

**Deliverable**: Production-ready, analytics-enabled system

---

## Future Enhancements

### Marketplace Templates (Phase 9)
- Public template marketplace
- Template ratings and reviews
- Purchase/download paid templates
- Revenue sharing for creators
- Featured templates and creators

### AI-Assisted Programming (Phase 10)
- AI suggests templates based on client goals
- Auto-adjusts parameters based on client progress
- Generates new template variations
- Personalized recommendations

### Advanced Features (Phase 11+)
- Autoregulation (adjust based on readiness)
- Video form analysis integration
- Social features (share workouts, compare with friends)
- Program challenges and competitions
- Mobile app for workout logging
- Wearable integration (track HR, HRV, recovery)

---

## Success Metrics

### Template Usage
- Number of default templates used per month
- Number of custom templates created per subscription
- Average templates per coach
- Most popular templates

### Assignment & Completion
- Programs assigned per month
- Active programs per client
- Average program completion rate
- Time to first assignment (coach onboarding)

### Client Engagement
- Workout logging frequency
- Average workouts per week
- Program adherence rate (workouts completed / planned)
- Client ratings of programs

### Coach Efficiency
- Time to assign program (template-based vs manual)
- Number of clients per program template
- Template reuse rate

---

## Technical Considerations

### Performance
- Template preview generation must be fast (<2 seconds)
- Cache template structures
- Optimize queries with proper indexes
- Consider read replicas for template browsing

### Scalability
- Millions of potential template assignments
- Partition program_day_exercises table by subscription_id
- Archive old completed assignments
- Efficient JSONB queries for parameters

### Security
- Multi-tenant isolation (subscription_id everywhere)
- Template visibility rules strictly enforced
- Prevent cross-subscription template access
- Validate all parameter inputs (XSS, injection)

### Data Integrity
- Cascading deletes for program hierarchy
- Soft deletes for templates (preserve assignment history)
- Audit trails for template modifications
- Version control for template updates

---

## Summary

The new **Template-Based Program Builder** architecture shifts from wizard-driven program creation to a reusable, parameterized template system. Coaches leverage default platform templates or create custom templates that can be assigned to multiple clients with personalized parameters (focus, goals, exercises, weights).

**Key Benefits:**
- **Efficiency**: Assign proven programs in minutes
- **Consistency**: Reuse successful templates across clients
- **Flexibility**: Customize templates with parameters for each client
- **Quality**: Default templates provide best practices
- **Scalability**: Templates enable coaches to manage more clients

**Implementation Timeline**: 18 weeks (4.5 months) for full v1.0 with coach template builder and client tracking.

---

**Status**: 🚧 Planning Complete - Ready for Implementation

**Last Updated**: 2025-11-29

**Document Owner**: Development Team
