# Client and Program Parameters Architecture

## Overview

This document defines the parameter system for client profiles and program generation. The system has two main components:

1. **Client Parameters**: Data captured about the client (anthropometric, experience, goals)
2. **Program Parameters**: Configurable options that adapt programs to client needs

Together, these parameters enable personalized program generation where **Client Data + Program Config = Customized Program**.

---

## Client Profile Parameters

### Current Implementation

The `User` model has a flexible `profile` JSONB field that can store arbitrary profile data. We'll define a structured schema for client profiles.

### Client Profile Schema

```typescript
interface ClientProfile {
  // Basic Information
  basicInfo: {
    firstName: string;
    lastName: string;
    dateOfBirth: string;  // ISO date string
    gender: 'male' | 'female' | 'other' | 'prefer_not_to_say';
    phoneNumber?: string;
    emergencyContact?: {
      name: string;
      relationship: string;
      phoneNumber: string;
    };
  };

  // Anthropometric Data
  anthropometrics: {
    // Current measurements
    currentWeight: number;  // in lbs or kg
    currentHeight: number;  // in inches or cm
    weightUnit: 'lbs' | 'kg';
    heightUnit: 'inches' | 'cm';

    // Body composition (optional)
    bodyFatPercentage?: number;
    leanBodyMass?: number;

    // History (for tracking)
    weightHistory?: Array<{
      date: string;
      weight: number;
      unit: 'lbs' | 'kg';
    }>;

    // Goal weight
    goalWeight?: number;
    goalBodyFatPercentage?: number;
  };

  // Training Experience
  trainingExperience: {
    // Overall experience
    overallExperienceLevel: 'beginner' | 'novice' | 'intermediate' | 'advanced' | 'elite';
    yearsTraining?: number;

    // Strength training specific
    strengthTrainingExperience: 'none' | 'less_than_6_months' | '6_to_12_months' | '1_to_2_years' | '2_to_5_years' | '5_plus_years';

    // Current maxes (for strength training)
    oneRepMaxes?: {
      [exerciseName: string]: {
        weight: number;
        unit: 'lbs' | 'kg';
        testedDate: string;
        verified: boolean;  // Whether coach verified this
      };
    };

    // Training history
    previousPrograms?: string[];  // Program IDs or names
    currentTrainingFrequency?: number;  // Days per week
  };

  // Fitness Goals
  fitnessGoals: {
    primaryGoal: 'strength' | 'hypertrophy' | 'fat_loss' | 'athletic_performance' | 'general_fitness' | 'rehabilitation';
    secondaryGoals?: Array<'strength' | 'hypertrophy' | 'fat_loss' | 'endurance' | 'mobility' | 'sport_specific'>;
    specificGoals?: string;  // Free text for specific goals
    targetDate?: string;  // When they want to achieve goal
    motivation?: string;  // What drives them
  };

  // Health and Medical
  healthInfo: {
    // Medical conditions
    medicalConditions?: Array<{
      condition: string;
      diagnosedDate?: string;
      notes?: string;
    }>;

    // Injuries
    injuries?: Array<{
      injury: string;
      injuryDate?: string;
      recoveryStatus: 'fully_recovered' | 'recovering' | 'chronic' | 'requires_modification';
      affectedMovements?: string[];  // Exercises to avoid
      notes?: string;
    }>;

    // Medications
    medications?: Array<{
      name: string;
      dosage?: string;
      relevantSideEffects?: string;
    }>;

    // Allergies
    allergies?: string[];

    // Cleared for training
    medicalClearance: boolean;
    clearanceDate?: string;
    clearanceNotes?: string;
  };

  // Availability and Preferences
  trainingPreferences: {
    // Schedule
    availableDaysPerWeek: number;
    preferredTrainingDays?: Array<'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday'>;
    sessionDuration?: number;  // Preferred session length in minutes
    timeOfDay?: 'early_morning' | 'morning' | 'midday' | 'afternoon' | 'evening' | 'night';

    // Equipment access
    gymAccess: 'full_gym' | 'home_gym' | 'minimal_equipment' | 'bodyweight_only';
    availableEquipment?: string[];  // List of equipment they have access to

    // Exercise preferences
    preferredExercises?: string[];
    dislikedExercises?: string[];
    exerciseRestrictions?: Array<{
      exercise: string;
      reason: string;
    }>;

    // Training style preferences
    preferredTrainingStyle?: 'powerlifting' | 'bodybuilding' | 'crossfit' | 'functional' | 'hybrid';
    intensityPreference?: 'low' | 'moderate' | 'high' | 'very_high';
  };

  // Movement Assessment (Optional - Coach fills out)
  movementAssessment?: {
    assessmentDate: string;
    assessedBy: string;  // Coach ID

    // Mobility scores (1-5 scale)
    shoulderMobility?: number;
    hipMobility?: number;
    ankleMobility?: number;
    thoracicMobility?: number;

    // Stability scores
    coreStability?: number;
    shoulderStability?: number;

    // Movement patterns
    squatPattern?: 'excellent' | 'good' | 'needs_work' | 'restricted';
    hingePattern?: 'excellent' | 'good' | 'needs_work' | 'restricted';
    pushPattern?: 'excellent' | 'good' | 'needs_work' | 'restricted';
    pullPattern?: 'excellent' | 'good' | 'needs_work' | 'restricted';

    // Notes
    assessmentNotes?: string;
    recommendations?: string[];
  };

  // Lifestyle Factors
  lifestyle?: {
    occupation?: string;
    occupationType?: 'sedentary' | 'lightly_active' | 'moderately_active' | 'very_active' | 'extremely_active';
    sleepQuality?: 'poor' | 'fair' | 'good' | 'excellent';
    averageSleepHours?: number;
    stressLevel?: 'low' | 'moderate' | 'high' | 'very_high';
    nutritionQuality?: 'poor' | 'fair' | 'good' | 'excellent';
    hydration?: 'poor' | 'fair' | 'good' | 'excellent';
  };

  // Notes
  notes?: {
    coachNotes?: string;  // Coach's private notes
    clientNotes?: string;  // Client's own notes
  };
}
```

### Client Profile Storage

**Database Implementation:**

```python
# In User model (existing)
class User(BaseModel):
    # ... existing fields ...

    profile = Column(
        JSONBType,
        nullable=True,
        default=dict,
        doc="User profile data (ClientProfile schema for clients)"
    )
```

**Pydantic Schema for Validation:**

```python
# backend/app/schemas/client.py

from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import date

class EmergencyContact(BaseModel):
    name: str
    relationship: str
    phone_number: str

class BasicInfo(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str = Field(..., regex="^(male|female|other|prefer_not_to_say)$")
    phone_number: Optional[str] = None
    emergency_contact: Optional[EmergencyContact] = None

class Anthropometrics(BaseModel):
    current_weight: float
    current_height: float
    weight_unit: str = Field(default="lbs", regex="^(lbs|kg)$")
    height_unit: str = Field(default="inches", regex="^(inches|cm)$")
    body_fat_percentage: Optional[float] = None
    lean_body_mass: Optional[float] = None
    goal_weight: Optional[float] = None
    goal_body_fat_percentage: Optional[float] = None

class OneRepMax(BaseModel):
    weight: float
    unit: str = Field(..., regex="^(lbs|kg)$")
    tested_date: date
    verified: bool = False

class TrainingExperience(BaseModel):
    overall_experience_level: str = Field(
        ...,
        regex="^(beginner|novice|intermediate|advanced|elite)$"
    )
    years_training: Optional[float] = None
    strength_training_experience: str
    one_rep_maxes: Optional[Dict[str, OneRepMax]] = {}
    current_training_frequency: Optional[int] = None

class FitnessGoals(BaseModel):
    primary_goal: str
    secondary_goals: Optional[List[str]] = []
    specific_goals: Optional[str] = None
    target_date: Optional[date] = None
    motivation: Optional[str] = None

class Injury(BaseModel):
    injury: str
    injury_date: Optional[date] = None
    recovery_status: str
    affected_movements: Optional[List[str]] = []
    notes: Optional[str] = None

class HealthInfo(BaseModel):
    medical_conditions: Optional[List[Dict]] = []
    injuries: Optional[List[Injury]] = []
    medications: Optional[List[Dict]] = []
    allergies: Optional[List[str]] = []
    medical_clearance: bool
    clearance_date: Optional[date] = None
    clearance_notes: Optional[str] = None

class TrainingPreferences(BaseModel):
    available_days_per_week: int = Field(..., ge=1, le=7)
    preferred_training_days: Optional[List[str]] = []
    session_duration: Optional[int] = None
    time_of_day: Optional[str] = None
    gym_access: str
    available_equipment: Optional[List[str]] = []
    preferred_exercises: Optional[List[str]] = []
    disliked_exercises: Optional[List[str]] = []
    intensity_preference: Optional[str] = None

class MovementAssessment(BaseModel):
    assessment_date: date
    assessed_by: str  # User ID of coach
    shoulder_mobility: Optional[int] = Field(None, ge=1, le=5)
    hip_mobility: Optional[int] = Field(None, ge=1, le=5)
    ankle_mobility: Optional[int] = Field(None, ge=1, le=5)
    squat_pattern: Optional[str] = None
    hinge_pattern: Optional[str] = None
    push_pattern: Optional[str] = None
    pull_pattern: Optional[str] = None
    assessment_notes: Optional[str] = None
    recommendations: Optional[List[str]] = []

class Lifestyle(BaseModel):
    occupation: Optional[str] = None
    occupation_type: Optional[str] = None
    sleep_quality: Optional[str] = None
    average_sleep_hours: Optional[float] = None
    stress_level: Optional[str] = None

class ClientProfile(BaseModel):
    """Complete client profile schema."""
    basic_info: BasicInfo
    anthropometrics: Anthropometrics
    training_experience: TrainingExperience
    fitness_goals: FitnessGoals
    health_info: HealthInfo
    training_preferences: TrainingPreferences
    movement_assessment: Optional[MovementAssessment] = None
    lifestyle: Optional[Lifestyle] = None
    notes: Optional[Dict[str, str]] = {}

class ClientProfileUpdate(BaseModel):
    """Partial update schema - all fields optional."""
    basic_info: Optional[BasicInfo] = None
    anthropometrics: Optional[Anthropometrics] = None
    training_experience: Optional[TrainingExperience] = None
    fitness_goals: Optional[FitnessGoals] = None
    health_info: Optional[HealthInfo] = None
    training_preferences: Optional[TrainingPreferences] = None
    movement_assessment: Optional[MovementAssessment] = None
    lifestyle: Optional[Lifestyle] = None
    notes: Optional[Dict[str, str]] = None
```

---

## Program Parameters

### Program Builder Configuration

Programs are generated based on **client data** + **program configuration**. Different builders will have different parameters.

### Strength Builder Parameters (Current + Enhanced)

```typescript
interface StrengthProgramInputs {
  // Basic Program Info
  programInfo: {
    name?: string;  // Auto-generated if not provided
    description?: string;
    durationWeeks: number;  // Default: 8
    daysPerWeek: number;  // Default: 4
  };

  // Client Context (pulled from client profile)
  clientContext: {
    clientId: string;
    experienceLevel: 'beginner' | 'intermediate' | 'advanced';
    availableDays: number;
    sessionDuration?: number;  // minutes
    availableEquipment: string[];
    injuries?: Array<{
      injury: string;
      affectedMovements: string[];
    }>;
  };

  // Movement Selection
  movements: Array<{
    name: string;
    exerciseId?: string;  // Reference to exercise library
    oneRM: number;
    maxRepsAt80Percent: number;
    targetWeight: number;

    // Customization per movement
    progressionType?: 'linear' | 'undulating' | 'custom';
    deloadFrequency?: number;  // Every N weeks
    exerciseVariations?: string[];  // Alternative exercises
  }>;

  // Program Customization
  customization: {
    // Periodization
    periodizationModel: 'linear' | 'undulating' | 'block' | 'conjugate';

    // Progression strategy
    progressionStrategy: 'percentage_based' | 'rpe_based' | 'weight_based';

    // Intensity distribution
    heavyDays: number;  // How many heavy days per week
    lightDays: number;  // How many light days per week

    // Volume
    volumeLevel: 'low' | 'moderate' | 'high';

    // Accessory work
    includeAccessories: boolean;
    accessoryFocus?: Array<'hypertrophy' | 'technique' | 'weak_points' | 'mobility'>;

    // Deload
    deloadStrategy: 'scheduled' | 'auto_regulated' | 'none';
    deloadFrequencyWeeks?: number;

    // Testing
    includeTestingWeeks: boolean;
    testingFrequency?: number;  // Every N weeks
  };

  // Advanced Options
  advanced?: {
    // Warm-up structure
    warmUpProtocol?: 'standard' | 'ramping' | 'dynamic' | 'custom';

    // Rest periods
    restPeriods?: {
      mainLifts: number;  // seconds
      accessories: number;
    };

    // Tempo prescriptions
    includeTempo: boolean;

    // RPE targets
    includeRPE: boolean;
    rpeRange?: { min: number; max: number };

    // Exercise order
    exerciseOrder?: 'strength_first' | 'weak_points_first' | 'custom';
  };
}
```

### Hypertrophy Builder Parameters (Future)

```typescript
interface HypertrophyProgramInputs {
  programInfo: {
    name?: string;
    description?: string;
    durationWeeks: number;  // Default: 12
    daysPerWeek: number;  // 3-6 days
  };

  clientContext: {
    clientId: string;
    experienceLevel: string;
    availableDays: number;
    sessionDuration?: number;
    gymAccess: string;
  };

  // Training Split
  split: {
    splitType: 'push_pull_legs' | 'upper_lower' | 'bro_split' | 'full_body' | 'custom';
    customSplit?: Array<{
      dayName: string;
      muscleGroups: string[];
    }>;
  };

  // Volume Configuration
  volumeConfig: {
    // Sets per muscle group per week
    setsPerMuscleGroup: {
      chest: number;
      back: number;
      shoulders: number;
      biceps: number;
      triceps: number;
      quads: number;
      hamstrings: number;
      glutes: number;
      calves: number;
    };

    // Rep ranges
    repRanges: {
      compounds: { min: number; max: number };  // e.g., 6-10
      isolations: { min: number; max: number };  // e.g., 10-15
    };
  };

  // Exercise Selection
  exercisePreferences: {
    compoundExercises: string[];  // Primary movements
    isolationExercises: string[];  // Accessory work
    avoidExercises?: string[];  // Due to injury or preference
    equipmentAvailable: string[];
  };

  // Progression
  progression: {
    progressionMethod: 'weight' | 'volume' | 'combined';
    incrementPerWeek: number | 'auto';  // lbs or percentage
    deloadEveryNWeeks: number;
  };

  // Intensity Techniques
  intensityTechniques?: {
    dropSets: boolean;
    superSets: boolean;
    giantSets: boolean;
    restPause: boolean;
    tempoWork: boolean;
  };
}
```

### Conditioning Builder Parameters (Future)

```typescript
interface ConditioningProgramInputs {
  programInfo: {
    name?: string;
    description?: string;
    durationWeeks: number;  // Default: 6
    sessionsPerWeek: number;  // 3-5 sessions
  };

  clientContext: {
    clientId: string;
    currentFitnessLevel: string;
    cardioExperience: string;
    availableEquipment: string[];
  };

  // Goal-specific configuration
  goal: {
    primaryGoal: 'fat_loss' | 'endurance' | 'general_fitness' | 'athletic_performance';
    targetHeartRateZones?: Array<{ zone: number; percentage: number }>;
  };

  // Modality Selection
  modalities: Array<{
    type: 'running' | 'cycling' | 'rowing' | 'swimming' | 'jump_rope' | 'bodyweight_circuits';
    preference: 'high' | 'medium' | 'low';
  }>;

  // Workout Types
  workoutTypes: {
    hiit: boolean;
    liss: boolean;  // Low Intensity Steady State
    emom: boolean;  // Every Minute On the Minute
    tabata: boolean;
    circuits: boolean;
    customIntervals: boolean;
  };

  // Intensity and Volume
  intensityConfig: {
    highIntensityDays: number;
    lowIntensityDays: number;
    avgSessionDuration: number;  // minutes
    intensityLevel: 'moderate' | 'high' | 'very_high';
  };

  // Progression
  progression: {
    progressionMetric: 'duration' | 'intensity' | 'distance' | 'work_capacity';
    startingLevel: number;  // Baseline
    progressionRate: 'conservative' | 'moderate' | 'aggressive';
  };
}
```

---

## Parameter Interaction: How Client Data Influences Programs

### Automatic Adjustments Based on Client Profile

When generating a program, the system automatically adjusts parameters based on client data:

#### 1. Experience Level Adjustments

```typescript
function adjustForExperience(
  clientProfile: ClientProfile,
  programInputs: ProgramInputs
): ProgramInputs {
  const experience = clientProfile.trainingExperience.overallExperienceLevel;

  switch (experience) {
    case 'beginner':
      return {
        ...programInputs,
        customization: {
          ...programInputs.customization,
          volumeLevel: 'moderate',  // Lower volume for beginners
          progressionStrategy: 'linear',  // Simpler progression
          deloadFrequencyWeeks: 4,  // More frequent deloads
        }
      };

    case 'intermediate':
      return {
        ...programInputs,
        customization: {
          ...programInputs.customization,
          volumeLevel: 'moderate_to_high',
          periodizationModel: 'undulating',  // More variety
          deloadFrequencyWeeks: 6,
        }
      };

    case 'advanced':
      return {
        ...programInputs,
        customization: {
          ...programInputs.customization,
          volumeLevel: 'high',
          periodizationModel: 'block',  // More sophisticated
          includeAccessories: true,
          deloadFrequencyWeeks: 8,  // Can handle more volume before deload
        }
      };
  }
}
```

#### 2. Injury Modifications

```typescript
function modifyForInjuries(
  clientProfile: ClientProfile,
  programExercises: Exercise[]
): Exercise[] {
  const injuries = clientProfile.healthInfo.injuries || [];

  return programExercises.map(exercise => {
    // Check if this exercise affects any injured areas
    const relevantInjury = injuries.find(injury =>
      injury.affectedMovements?.includes(exercise.name)
    );

    if (relevantInjury) {
      if (relevantInjury.recoveryStatus === 'requires_modification') {
        // Substitute with safer alternative
        return {
          ...exercise,
          name: findSafeAlternative(exercise.name, relevantInjury),
          notes: `Modified due to ${relevantInjury.injury}`,
          loadModification: 0.8,  // Reduce weight by 20%
        };
      } else if (relevantInjury.recoveryStatus === 'recovering') {
        // Keep exercise but reduce intensity
        return {
          ...exercise,
          loadModification: 0.85,
          notes: `Reduced intensity due to recovering ${relevantInjury.injury}`,
        };
      }
    }

    return exercise;
  });
}
```

#### 3. Equipment Availability

```typescript
function filterByEquipment(
  clientProfile: ClientProfile,
  proposedExercises: Exercise[]
): Exercise[] {
  const availableEquipment = clientProfile.trainingPreferences.availableEquipment || [];

  return proposedExercises.map(exercise => {
    const requiredEquipment = exercise.equipmentRequired;

    // Check if client has all required equipment
    const hasEquipment = requiredEquipment.every(eq =>
      availableEquipment.includes(eq)
    );

    if (!hasEquipment) {
      // Find alternative with available equipment
      return findEquipmentAlternative(exercise, availableEquipment);
    }

    return exercise;
  });
}
```

#### 4. Goal-Based Customization

```typescript
function customizeForGoal(
  clientProfile: ClientProfile,
  programTemplate: Program
): Program {
  const primaryGoal = clientProfile.fitnessGoals.primaryGoal;

  switch (primaryGoal) {
    case 'strength':
      return {
        ...programTemplate,
        repRanges: { min: 1, max: 5 },  // Low rep ranges
        restPeriods: { main: 180, accessory: 120 },  // Longer rest
        intensityLevel: 'high',
      };

    case 'hypertrophy':
      return {
        ...programTemplate,
        repRanges: { min: 6, max: 12 },  // Moderate rep ranges
        restPeriods: { main: 90, accessory: 60 },  // Moderate rest
        volumeMultiplier: 1.2,  // More volume
      };

    case 'fat_loss':
      return {
        ...programTemplate,
        repRanges: { min: 10, max: 15 },  // Higher reps
        restPeriods: { main: 60, accessory: 45 },  // Shorter rest
        includeCardio: true,
        circuitStyle: true,  // Keep heart rate elevated
      };

    case 'general_fitness':
      return {
        ...programTemplate,
        repRanges: { min: 8, max: 12 },  // Balanced
        varietyLevel: 'high',  // More exercise variety
        includeCardio: true,
        includeMobility: true,
      };
  }
}
```

#### 5. Time Availability

```typescript
function adjustForTimeAvailability(
  clientProfile: ClientProfile,
  program: Program
): Program {
  const availableDays = clientProfile.trainingPreferences.availableDaysPerWeek;
  const sessionDuration = clientProfile.trainingPreferences.sessionDuration || 60;

  if (sessionDuration < 45) {
    // Short sessions - focus on main lifts only
    return {
      ...program,
      exercisesPerSession: 3,  // Reduced
      accessoryWork: 'minimal',
      supersets: true,  // Save time
    };
  } else if (sessionDuration > 90) {
    // Long sessions - can include more volume
    return {
      ...program,
      exercisesPerSession: 6,  // More exercises
      accessoryWork: 'comprehensive',
      includeConditioningFinisher: true,
    };
  }

  return program;
}
```

---

## Program Generation Workflow

### Complete Flow: Client Profile → Program Generation

```typescript
async function generatePersonalizedProgram(
  clientId: string,
  builderType: 'strength' | 'hypertrophy' | 'conditioning',
  baseInputs: ProgramInputs
): Promise<Program> {

  // 1. Fetch client profile
  const clientProfile = await getClientProfile(clientId);

  // 2. Validate client has required data
  validateClientDataForBuilder(clientProfile, builderType);

  // 3. Auto-populate client context from profile
  const clientContext = {
    clientId,
    experienceLevel: clientProfile.trainingExperience.overallExperienceLevel,
    availableDays: clientProfile.trainingPreferences.availableDaysPerWeek,
    sessionDuration: clientProfile.trainingPreferences.sessionDuration,
    availableEquipment: clientProfile.trainingPreferences.availableEquipment,
    injuries: clientProfile.healthInfo.injuries,
    oneRepMaxes: clientProfile.trainingExperience.oneRepMaxes,
  };

  // 4. Merge client context with manual inputs
  const enrichedInputs = {
    ...baseInputs,
    clientContext,
  };

  // 5. Apply automatic adjustments
  let adjustedInputs = adjustForExperience(clientProfile, enrichedInputs);
  adjustedInputs = adjustForGoal(clientProfile, adjustedInputs);
  adjustedInputs = adjustForTimeAvailability(clientProfile, adjustedInputs);

  // 6. Generate program structure
  const program = await programGenerator.generate(adjustedInputs);

  // 7. Modify exercises based on injuries and equipment
  program.weeks = program.weeks.map(week => ({
    ...week,
    days: week.days.map(day => ({
      ...day,
      exercises: modifyForInjuries(
        clientProfile,
        filterByEquipment(clientProfile, day.exercises)
      ),
    })),
  }));

  // 8. Calculate personalized loading
  program.weeks = calculatePersonalizedLoading(
    program.weeks,
    clientContext.oneRepMaxes,
    adjustedInputs.customization.progressionStrategy
  );

  // 9. Store program with full metadata
  return await saveProgram({
    ...program,
    clientId,
    generatedFrom: {
      clientProfile: sanitizeForStorage(clientProfile),
      inputs: adjustedInputs,
      adjustments: getAppliedAdjustments(),
    },
  });
}
```

---

## API Endpoints for Client and Program Parameters

### Client Profile Endpoints

```typescript
// Create or update client profile
POST /api/v1/clients/{clientId}/profile
PUT /api/v1/clients/{clientId}/profile

// Get client profile
GET /api/v1/clients/{clientId}/profile

// Update specific sections
PATCH /api/v1/clients/{clientId}/profile/anthropometrics
PATCH /api/v1/clients/{clientId}/profile/training-experience
PATCH /api/v1/clients/{clientId}/profile/fitness-goals
PATCH /api/v1/clients/{clientId}/profile/health-info

// Movement assessment (coach only)
POST /api/v1/clients/{clientId}/movement-assessment
GET /api/v1/clients/{clientId}/movement-assessment

// Update 1RM (can be done by client during workout or coach)
POST /api/v1/clients/{clientId}/one-rep-max
PUT /api/v1/clients/{clientId}/one-rep-max/{exerciseName}
```

### Program Generation Endpoints

```typescript
// Generate program preview (doesn't save)
POST /api/v1/programs/generate-preview
Body: {
  builderType: 'strength',
  clientId: 'uuid',
  movements: [...],
  customization: {...}
}
Response: {
  preview: ProgramPreview,
  adjustmentsApplied: string[],
  warnings: string[]  // e.g., "Client has knee injury, modified squats"
}

// Generate and save program
POST /api/v1/programs/generate
Body: { ... same as preview ... }
Response: {
  program: Program,
  programId: 'uuid',
  adjustmentsApplied: string[]
}

// Get program builder constants (for frontend calculations)
GET /api/v1/programs/builders/{builderType}/constants
Response: CalculationConstants
```

---

## Frontend Implementation

### Client Onboarding Flow

When a client is first created or onboarded:

```typescript
// Step 1: Basic Info
<ClientOnboardingForm step="basic">
  <Input name="firstName" />
  <Input name="lastName" />
  <DatePicker name="dateOfBirth" />
  <Select name="gender" />
</ClientOnboardingForm>

// Step 2: Anthropometrics
<ClientOnboardingForm step="anthropometrics">
  <NumberInput name="currentWeight" unit="lbs" />
  <NumberInput name="currentHeight" unit="inches" />
  <NumberInput name="goalWeight" optional />
</ClientOnboardingForm>

// Step 3: Training Experience
<ClientOnboardingForm step="experience">
  <Select name="overallExperienceLevel" />
  <NumberInput name="yearsTraining" optional />
  <Select name="strengthTrainingExperience" />
</ClientOnboardingForm>

// Step 4: Fitness Goals
<ClientOnboardingForm step="goals">
  <Select name="primaryGoal" />
  <MultiSelect name="secondaryGoals" />
  <TextArea name="specificGoals" />
</ClientOnboardingForm>

// Step 5: Health Screening
<ClientOnboardingForm step="health">
  <Checkbox name="medicalClearance" required />
  <RepeaterField name="injuries">
    <Input name="injury" />
    <Select name="recoveryStatus" />
    <MultiSelect name="affectedMovements" />
  </RepeaterField>
</ClientOnboardingForm>

// Step 6: Training Preferences
<ClientOnboardingForm step="preferences">
  <NumberInput name="availableDaysPerWeek" min={1} max={7} />
  <MultiSelect name="preferredTrainingDays" />
  <Select name="gymAccess" />
  <MultiSelect name="availableEquipment" />
</ClientOnboardingForm>
```

### Program Builder with Client Context

When coach builds a program for a client:

```typescript
// Program Builder automatically loads client data
const ProgramBuilder = ({ clientId }: { clientId: string }) => {
  const { data: clientProfile } = useClientProfile(clientId);

  // Auto-populate from client profile
  const [inputs, setInputs] = useState<ProgramInputs>({
    clientContext: {
      clientId,
      experienceLevel: clientProfile?.trainingExperience.overallExperienceLevel,
      availableDays: clientProfile?.trainingPreferences.availableDaysPerWeek,
      // ... other auto-populated fields
    },
    movements: clientProfile?.trainingExperience.oneRepMaxes
      ? Object.entries(clientProfile.trainingExperience.oneRepMaxes).map(([name, data]) => ({
          name,
          oneRM: data.weight,
          // Other fields to be filled by coach
        }))
      : [],
  });

  // Show warnings if client data is incomplete or concerning
  const warnings = useMemo(() => {
    const w = [];
    if (clientProfile?.healthInfo.injuries?.length > 0) {
      w.push(`Client has ${clientProfile.healthInfo.injuries.length} active injuries`);
    }
    if (!clientProfile?.healthInfo.medicalClearance) {
      w.push('Client has not provided medical clearance');
    }
    return w;
  }, [clientProfile]);

  return (
    <div>
      {warnings.length > 0 && (
        <WarningBanner warnings={warnings} />
      )}

      <ProgramBuilderWizard
        clientProfile={clientProfile}
        initialInputs={inputs}
        onGenerate={handleGenerate}
      />
    </div>
  );
};
```

---

## Database Schema Updates

### Add Client Profile Validation

```sql
-- Add constraint to validate profile structure (PostgreSQL)
ALTER TABLE users
ADD CONSTRAINT check_client_profile_structure
CHECK (
  role != 'CLIENT' OR (
    profile ? 'basic_info' AND
    profile ? 'anthropometrics' AND
    profile ? 'training_experience' AND
    profile ? 'fitness_goals' AND
    profile ? 'health_info' AND
    profile ? 'training_preferences'
  )
);

-- Index for querying by experience level
CREATE INDEX idx_users_experience_level
ON users ((profile->'training_experience'->>'overall_experience_level'))
WHERE role = 'CLIENT';

-- Index for querying by primary goal
CREATE INDEX idx_users_primary_goal
ON users ((profile->'fitness_goals'->>'primary_goal'))
WHERE role = 'CLIENT';
```

---

## Summary

### Client Parameters

**Purpose**: Capture comprehensive information about the client to enable personalized program generation.

**Key Sections**:
1. Basic Info (name, DOB, contact)
2. Anthropometrics (weight, height, body composition)
3. Training Experience (level, history, 1RMs)
4. Fitness Goals (primary/secondary goals, motivation)
5. Health Info (injuries, conditions, clearance)
6. Training Preferences (schedule, equipment, preferences)
7. Movement Assessment (mobility, stability, patterns)
8. Lifestyle (occupation, sleep, stress, nutrition)

**Storage**: User.profile JSONB field with structured schema

### Program Parameters

**Purpose**: Configurable options that determine how a program is structured and progresses.

**Key Categories**:
1. Program Info (name, duration, frequency)
2. Client Context (experience, availability, equipment)
3. Movement Selection (exercises, 1RMs, targets)
4. Customization (periodization, progression, volume, intensity)
5. Advanced Options (warm-up, rest, tempo, RPE)

### Parameter Interaction

**Client Data → Program Adjustments**:
- Experience level → Volume, complexity, progression rate
- Injuries → Exercise modifications, load reductions
- Equipment → Exercise alternatives
- Goals → Rep ranges, intensity, rest periods, exercise selection
- Time availability → Exercise count, supersets, session structure

**Result**: Highly personalized programs that adapt to each client's unique situation while maintaining evidence-based training principles.

---

## Next Steps

1. ✅ Review and approve parameter schemas
2. Implement ClientProfile Pydantic schemas
3. Create client onboarding UI flow
4. Enhance program generator with client context logic
5. Build parameter interaction/adjustment system
6. Create API endpoints for profile management
7. Update program builder UI to show client context
8. Add validation and warnings for incomplete/concerning data
