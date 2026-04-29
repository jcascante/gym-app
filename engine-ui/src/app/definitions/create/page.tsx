import { WizardShell } from "@/components/wizard/WizardShell";

export const metadata = { title: "Create Program — TrainGen" };

export default function CreateProgramPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Create Program
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-slate-400">
          Build a training program definition in 5 steps. No JSON required.
        </p>
      </div>
      <WizardShell />
    </div>
  );
}
