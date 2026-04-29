export type ProgramType = "strength" | "hypertrophy" | "conditioning";
export type DurationWeeks = 4 | 6 | 8 | 12;
export type FrequencyDays = 3 | 4 | 5;
export type SessionType =
  | "upper_body"
  | "lower_body"
  | "push"
  | "pull"
  | "full_body"
  | "conditioning";
export type BlockType = "main_lift" | "accessory" | "conditioning";
export type ExerciseCategory =
  | "squat"
  | "hip_hinge"
  | "horizontal_push"
  | "horizontal_pull"
  | "vertical_push"
  | "vertical_pull"
  | "core"
  | "conditioning";
export type TrainingStyle =
  | "top_set_plus_backoff"
  | "reps_range_rir"
  | "steady_state";
export type RepRange = "light" | "moderate" | "heavy" | "custom";
export type IntensityLevel = "easy" | "moderate" | "hard";
export type ProgressionPattern = "linear" | "undulating" | "fixed";

export interface Step1Data {
  name: string;
  description: string;
  programType: ProgramType;
  durationWeeks: DurationWeeks;
  frequencyDays: FrequencyDays;
}

export interface ScheduledDay {
  dayIndex: number; // 0-6 (Mon-Sun)
  sessionType: SessionType;
}

export interface Step2Data {
  activeDays: ScheduledDay[];
}

export interface Block {
  id: string;
  blockType: BlockType;
  exerciseCategory: ExerciseCategory;
}

export interface SessionDef {
  dayIndex: number; // matches ScheduledDay.dayIndex
  sessionType: SessionType;
  blocks: Block[];
}

export interface Step3Data {
  sessions: SessionDef[];
}

export interface BlockPrescription {
  blockId: string;
  trainingStyle: TrainingStyle;
  sets: number;
  repRange: RepRange;
  customRepsMin?: number;
  customRepsMax?: number;
  intensityLevel: IntensityLevel;
  progression: ProgressionPattern;
}

export interface Step4Data {
  prescriptions: BlockPrescription[];
}

export interface WizardState {
  currentStep: 1 | 2 | 3 | 4 | 5;
  step1: Step1Data;
  step2: Step2Data;
  step3: Step3Data;
  step4: Step4Data;
}

export const DEFAULT_STEP1: Step1Data = {
  name: "",
  description: "",
  programType: "strength",
  durationWeeks: 4,
  frequencyDays: 4,
};

export const DEFAULT_STEP2: Step2Data = {
  activeDays: [],
};

export const DEFAULT_STEP3: Step3Data = {
  sessions: [],
};

export const DEFAULT_STEP4: Step4Data = {
  prescriptions: [],
};

export function defaultPrescription(blockId: string, blockType: BlockType): BlockPrescription {
  const styleMap: Record<BlockType, TrainingStyle> = {
    main_lift: "top_set_plus_backoff",
    accessory: "reps_range_rir",
    conditioning: "steady_state",
  };
  return {
    blockId,
    trainingStyle: styleMap[blockType],
    sets: 3,
    repRange: blockType === "main_lift" ? "heavy" : "moderate",
    intensityLevel: "moderate",
    progression: "linear",
  };
}
