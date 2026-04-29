import type { WizardState, BlockPrescription } from "./types";
import { CATEGORY_TAGS, PROGRAM_PRESETS } from "./presets";
import {
  buildRepsRangeOutputMapping,
  buildTopSetOutputMapping,
  buildSteadyStateOutputMapping,
} from "./expressionGenerators";

function slugify(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s_]/g, "")
    .replace(/\s+/g, "_");
}

function buildOutputMapping(
  rx: BlockPrescription,
  weeks: number
): Record<string, string> {
  if (rx.trainingStyle === "top_set_plus_backoff") {
    return buildTopSetOutputMapping({
      sets: rx.sets,
      repRange: rx.repRange,
      customRepsMin: rx.customRepsMin,
      customRepsMax: rx.customRepsMax,
      intensityLevel: rx.intensityLevel,
      progression: rx.progression,
      weeks,
    });
  }
  if (rx.trainingStyle === "steady_state") {
    return buildSteadyStateOutputMapping({ sets: rx.sets });
  }
  return buildRepsRangeOutputMapping({
    sets: rx.sets,
    repRange: rx.repRange,
    customRepsMin: rx.customRepsMin,
    customRepsMax: rx.customRepsMax,
    intensityLevel: rx.intensityLevel,
    progression: rx.progression,
    weeks,
  });
}

export function buildDefinition(state: WizardState): Record<string, unknown> {
  const { step1, step2, step3, step4 } = state;
  const { name, description, programType, durationWeeks, frequencyDays } = step1;
  const preset = PROGRAM_PRESETS[programType];

  const programId = `${slugify(name)}_v1`;

  // Build sessions array
  const sessions = step3.sessions.map((session) => {
    const scheduledDay = step2.activeDays.find(
      (d) => d.dayIndex === session.dayIndex
    );
    const dayIndex = session.dayIndex + 1; // 1-based

    const blocks = session.blocks.map((block) => {
      const categoryTags = CATEGORY_TAGS[block.exerciseCategory];
      return {
        id: block.id,
        type: block.blockType,
        tags: [block.exerciseCategory],
        optional: false,
        exercise_selector: {
          count: 1,
          include_tags: categoryTags.include_tags,
        },
        prescription_ref: `rx_${block.id}`,
      };
    });

    return {
      day_index: dayIndex,
      tags: [scheduledDay?.sessionType ?? session.sessionType],
      optional: false,
      blocks,
    };
  });

  // Build prescriptions map
  const prescriptions: Record<string, unknown> = {};
  for (const session of step3.sessions) {
    for (const block of session.blocks) {
      const rx = step4.prescriptions.find((p) => p.blockId === block.id);
      if (!rx) continue;
      const outputMapping = buildOutputMapping(rx, durationWeeks);
      prescriptions[`rx_${block.id}`] = {
        mode: rx.trainingStyle,
        output_mapping: outputMapping,
      };
    }
  }

  return {
    program_id: programId,
    version: "1.0.0",
    name,
    description,
    parameter_spec: preset.parameter_spec,
    exercise_library_ref: {
      type: "external",
      path: "",
    },
    template: {
      weeks: { min: durationWeeks, max: durationWeeks },
      days_per_week: { min: frequencyDays, max: frequencyDays },
      sessions,
    },
    prescriptions,
    rules: preset.rules,
    validation: preset.validation,
  };
}

/**
 * Validate the built definition structure for obvious errors.
 * Returns a list of error strings (empty = valid).
 */
export function validateDefinitionStructure(def: Record<string, unknown>): string[] {
  const errors: string[] = [];

  const required = ["program_id", "version", "name", "parameter_spec", "template", "prescriptions", "rules", "validation"];
  for (const field of required) {
    if (!(field in def)) errors.push(`Missing required field: ${field}`);
  }

  const template = def.template as Record<string, unknown> | undefined;
  if (template) {
    const sessions = template.sessions as Array<Record<string, unknown>> | undefined;
    if (sessions) {
      for (const session of sessions) {
        const dayIndex = session.day_index as number;
        if (dayIndex < 1 || dayIndex > 7) {
          errors.push(`day_index ${dayIndex} out of range (1–7)`);
        }
        const blocks = session.blocks as Array<Record<string, unknown>> | undefined;
        if (blocks) {
          for (const block of blocks) {
            const ref = block.prescription_ref as string;
            const prescriptions = def.prescriptions as Record<string, unknown>;
            if (ref && prescriptions && !(ref in prescriptions)) {
              errors.push(`prescription_ref "${ref}" not found in prescriptions`);
            }
          }
        }
      }
    }
  }

  return errors;
}
