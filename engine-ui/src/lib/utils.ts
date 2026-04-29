export function formatLoad(kg: number, unit: "kg" | "lb" = "kg"): string {
  if (unit === "lb") {
    return `${(kg * 2.20462).toFixed(1)} lb`;
  }
  return `${kg} kg`;
}

export function formatHrRange(range: [number, number]): string {
  return `${range[0]}–${range[1]} bpm`;
}

export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const hrs = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hrs}h ${mins}min` : `${hrs}h`;
}
