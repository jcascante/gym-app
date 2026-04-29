interface StepHeaderProps {
  title: string;
  subtitle: string;
}

export function StepHeader({ title, subtitle }: StepHeaderProps) {
  return (
    <div className="mb-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white">{title}</h2>
      <p className="mt-1 text-sm text-gray-500 dark:text-slate-400">{subtitle}</p>
    </div>
  );
}
