"use client";

import { useState } from "react";
import { Step1Basics } from "./steps/Step1Basics";
import { Step2Schedule } from "./steps/Step2Schedule";
import { Step3Sessions } from "./steps/Step3Sessions";
import { Step4Prescriptions } from "./steps/Step4Prescriptions";
import { Step5Review } from "./steps/Step5Review";
import type {
  WizardState,
  Step1Data,
  Step2Data,
  Step3Data,
  Step4Data,
  SessionDef,
  Block,
} from "@/lib/wizard/types";
import {
  DEFAULT_STEP1,
  DEFAULT_STEP2,
  DEFAULT_STEP3,
  DEFAULT_STEP4,
  defaultPrescription,
} from "@/lib/wizard/types";

const STEPS = [
  { label: "Basics" },
  { label: "Schedule" },
  { label: "Sessions" },
  { label: "Prescriptions" },
  { label: "Review" },
];

function canProceed(step: number, state: WizardState): boolean {
  if (step === 1) return state.step1.name.trim().length > 0;
  if (step === 2) {
    const { activeDays } = state.step2;
    return (
      activeDays.length === state.step1.frequencyDays &&
      activeDays.every((d) => !!d.sessionType)
    );
  }
  if (step === 3) {
    return state.step3.sessions.every((s) => s.blocks.length > 0);
  }
  return true;
}

/** Reconcile step4 prescriptions when blocks change */
function reconcilePrescriptions(
  sessions: SessionDef[],
  currentPrescriptions: Step4Data["prescriptions"]
): Step4Data["prescriptions"] {
  const allBlockIds = new Set(sessions.flatMap((s) => s.blocks.map((b) => b.id)));
  // Keep existing entries that still exist
  const retained = currentPrescriptions.filter((p) => allBlockIds.has(p.blockId));
  const retainedIds = new Set(retained.map((p) => p.blockId));
  // Add defaults for new blocks
  const newEntries = sessions.flatMap((s) =>
    s.blocks
      .filter((b) => !retainedIds.has(b.id))
      .map((b) => defaultPrescription(b.id, b.blockType))
  );
  return [...retained, ...newEntries];
}

/** Build step3 sessions from schedule, preserving existing blocks */
function reconcileSessions(
  activeDays: Step2Data["activeDays"],
  existing: SessionDef[]
): SessionDef[] {
  return activeDays.map((d) => {
    const found = existing.find((s) => s.dayIndex === d.dayIndex);
    return found
      ? { ...found, sessionType: d.sessionType }
      : { dayIndex: d.dayIndex, sessionType: d.sessionType, blocks: [] };
  });
}

export function WizardShell() {
  const [state, setState] = useState<WizardState>({
    currentStep: 1,
    step1: DEFAULT_STEP1,
    step2: DEFAULT_STEP2,
    step3: DEFAULT_STEP3,
    step4: DEFAULT_STEP4,
  });

  const { currentStep } = state;

  const updateStep1 = (step1: Step1Data) => setState((s) => ({ ...s, step1 }));

  const updateStep2 = (step2: Step2Data) => {
    setState((s) => {
      const sessions = reconcileSessions(step2.activeDays, s.step3.sessions);
      const prescriptions = reconcilePrescriptions(sessions, s.step4.prescriptions);
      return {
        ...s,
        step2,
        step3: { sessions },
        step4: { prescriptions },
      };
    });
  };

  const updateStep3 = (step3: Step3Data) => {
    setState((s) => {
      const prescriptions = reconcilePrescriptions(step3.sessions, s.step4.prescriptions);
      return { ...s, step3, step4: { prescriptions } };
    });
  };

  const updateStep4 = (step4: Step4Data) => setState((s) => ({ ...s, step4 }));

  const goTo = (step: number) =>
    setState((s) => ({ ...s, currentStep: step as WizardState["currentStep"] }));

  const next = () => {
    if (currentStep < 5) goTo(currentStep + 1);
  };

  const back = () => {
    if (currentStep > 1) goTo(currentStep - 1);
  };

  const canNext = canProceed(currentStep, state);

  return (
    <div className="mx-auto max-w-3xl">
      {/* Step indicator */}
      <div className="mb-8 flex items-center gap-0">
        {STEPS.map((step, i) => {
          const n = i + 1;
          const done = n < currentStep;
          const active = n === currentStep;
          return (
            <div key={n} className="flex flex-1 items-center">
              <button
                type="button"
                onClick={() => done && goTo(n)}
                disabled={!done}
                className="flex flex-col items-center gap-1"
              >
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold transition-all ${
                    done
                      ? "bg-indigo-600 text-white dark:bg-indigo-500"
                      : active
                      ? "bg-indigo-600 text-white ring-4 ring-indigo-500/30 dark:bg-indigo-500"
                      : "border-2 border-gray-300 bg-white text-gray-400 dark:border-slate-600 dark:bg-slate-900"
                  }`}
                >
                  {done ? (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <path d="M20 6L9 17l-5-5" />
                    </svg>
                  ) : (
                    n
                  )}
                </div>
                <span
                  className={`hidden text-xs font-medium sm:block ${
                    active ? "text-indigo-600 dark:text-indigo-400" : "text-gray-400 dark:text-slate-500"
                  }`}
                >
                  {step.label}
                </span>
              </button>
              {i < STEPS.length - 1 && (
                <div
                  className={`mx-1 h-0.5 flex-1 transition-colors ${
                    done ? "bg-indigo-600 dark:bg-indigo-500" : "bg-gray-200 dark:bg-slate-700"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Step content */}
      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        {currentStep === 1 && (
          <Step1Basics data={state.step1} onChange={updateStep1} />
        )}
        {currentStep === 2 && (
          <Step2Schedule
            data={state.step2}
            frequencyDays={state.step1.frequencyDays}
            onChange={updateStep2}
          />
        )}
        {currentStep === 3 && (
          <Step3Sessions
            data={state.step3}
            schedule={state.step2}
            onChange={updateStep3}
          />
        )}
        {currentStep === 4 && (
          <Step4Prescriptions
            data={state.step4}
            sessions={state.step3}
            onChange={updateStep4}
          />
        )}
        {currentStep === 5 && <Step5Review state={state} />}
      </div>

      {/* Navigation */}
      <div className="mt-4 flex items-center justify-between">
        <button
          type="button"
          onClick={back}
          disabled={currentStep === 1}
          className="rounded-xl border border-gray-300 px-5 py-2.5 text-sm font-semibold text-gray-600 transition-all hover:bg-gray-50 disabled:opacity-30 dark:border-slate-600 dark:text-slate-400 dark:hover:bg-slate-800"
        >
          Back
        </button>

        {currentStep < 5 && (
          <button
            type="button"
            onClick={next}
            disabled={!canNext}
            className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:bg-indigo-500 disabled:opacity-40 dark:bg-indigo-500"
          >
            Next
          </button>
        )}
      </div>
    </div>
  );
}
