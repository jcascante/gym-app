import './PrescriptionCard.css';

type P = Record<string, unknown>;

function detectType(p: P): 'strength' | 'hypertrophy' | 'intervals' | 'steady' {
  if ('top_set' in p) return 'strength';
  if ('reps_range' in p) return 'hypertrophy';
  if ('work' in p && 'warmup_minutes' in p) return 'intervals';
  return 'steady';
}

function StrengthCard({ p }: { p: P }) {
  const top = p.top_set as { sets: number; reps: number; target_rpe: number; load_kg: number };
  const backoff = (p.backoff as Array<{ sets: number; reps: number; load_kg: number }>) ?? [];
  return (
    <div className="rx-card rx-strength">
      <div className="rx-top-set">
        <span className="rx-label">Top Set</span>
        <span className="rx-detail">
          {top.sets} × {top.reps} @ RPE {top.target_rpe} — <strong>{top.load_kg} kg</strong>
        </span>
      </div>
      {backoff.length > 0 && (
        <div className="rx-backoff">
          <span className="rx-label">Back-off</span>
          {backoff.map((s, i) => (
            <span key={i} className="rx-detail">
              {s.sets} × {s.reps} — {s.load_kg} kg
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function HypertrophyCard({ p }: { p: P }) {
  const rr = p.reps_range as [number, number];
  return (
    <div className="rx-card rx-hypertrophy">
      <span className="rx-detail">
        {p.sets as number} sets × {rr[0]}–{rr[1]} reps @ RIR {p.target_rir as number}
      </span>
      {!!p.load_note && <span className="rx-note">{p.load_note as string}</span>}
    </div>
  );
}

function IntervalsCard({ p }: { p: P }) {
  const work = p.work as { intervals: number; seconds_each: number; intensity: { target: string } };
  return (
    <div className="rx-card rx-intervals">
      <div className="rx-row"><span className="rx-label">Warm-up</span><span>{p.warmup_minutes as number} min</span></div>
      <div className="rx-row"><span className="rx-label">Work</span><span>{work.intervals} × {work.seconds_each}s — {work.intensity.target}</span></div>
      <div className="rx-row"><span className="rx-label">Rest</span><span>{p.rest_seconds as number}s between intervals</span></div>
      {!!p.cooldown_minutes && <div className="rx-row"><span className="rx-label">Cool-down</span><span>{p.cooldown_minutes as number} min</span></div>}
    </div>
  );
}

function SteadyCard({ p }: { p: P }) {
  const intensity = p.intensity as { target: string } | undefined;
  return (
    <div className="rx-card rx-steady">
      <div className="rx-row"><span className="rx-label">Duration</span><span>{p.duration_minutes as number} min</span></div>
      {intensity && <div className="rx-row"><span className="rx-label">Intensity</span><span>{intensity.target}</span></div>}
      {!!p.notes && <span className="rx-note">{p.notes as string}</span>}
    </div>
  );
}

export default function PrescriptionCard({ prescription }: { prescription: Record<string, unknown> }) {
  const type = detectType(prescription);
  if (type === 'strength') return <StrengthCard p={prescription} />;
  if (type === 'hypertrophy') return <HypertrophyCard p={prescription} />;
  if (type === 'intervals') return <IntervalsCard p={prescription} />;
  return <SteadyCard p={prescription} />;
}
