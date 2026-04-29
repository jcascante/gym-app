interface Option<T extends string | number> {
  value: T;
  label: string;
  description?: string;
}

interface CardSelectProps<T extends string | number> {
  options: Option<T>[];
  value: T;
  onChange: (value: T) => void;
  columns?: 2 | 3 | 4;
}

export function CardSelect<T extends string | number>({
  options,
  value,
  onChange,
  columns = 3,
}: CardSelectProps<T>) {
  const gridCls = {
    2: "grid-cols-2",
    3: "grid-cols-3",
    4: "grid-cols-2 sm:grid-cols-4",
  }[columns];

  return (
    <div className={`grid gap-2 ${gridCls}`}>
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={`rounded-xl border px-3 py-2.5 text-left transition-all ${
              active
                ? "border-indigo-600 bg-indigo-50 ring-2 ring-indigo-500/30 dark:border-indigo-500 dark:bg-indigo-500/10"
                : "border-gray-200 bg-white hover:border-gray-300 dark:border-slate-700 dark:bg-slate-900 dark:hover:border-slate-600"
            }`}
          >
            <div
              className={`text-sm font-semibold ${
                active
                  ? "text-indigo-700 dark:text-indigo-400"
                  : "text-gray-900 dark:text-white"
              }`}
            >
              {opt.label}
            </div>
            {opt.description && (
              <div className="mt-0.5 text-xs text-gray-500 dark:text-slate-400">
                {opt.description}
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}

interface PillSelectProps<T extends string | number> {
  options: Option<T>[];
  value: T;
  onChange: (value: T) => void;
}

export function PillSelect<T extends string | number>({
  options,
  value,
  onChange,
}: PillSelectProps<T>) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={`rounded-full border px-4 py-1.5 text-sm font-medium transition-all ${
              active
                ? "border-indigo-600 bg-indigo-600 text-white dark:border-indigo-500 dark:bg-indigo-500"
                : "border-gray-300 text-gray-600 hover:border-gray-400 dark:border-slate-600 dark:text-slate-400"
            }`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
