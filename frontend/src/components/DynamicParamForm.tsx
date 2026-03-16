import type { ParameterField } from '../types/engine';
import './DynamicParamForm.css';

interface Props {
  fields: ParameterField[];
  values: Record<string, unknown>;
  onChange: (key: string, value: unknown) => void;
}

// Convert a dot-path key into a human-readable label when description is absent.
// e.g. "athlete.e1rm.squat" → "Squat 1RM (kg)"
//      "rules.main_method"  → "Main Method"
//      "athlete.level"      → "Level"
function formatLabel(key: string): string {
  const parts = key.split('.');
  const last = parts[parts.length - 1];
  const parent = parts[parts.length - 2];
  const readable = last.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  if (parent === 'e1rm') return `${readable} 1RM (kg)`;
  return readable;
}

// Resolve a dot-path like "athlete.level" against a flat key→value map
// that uses the same dot-path keys (e.g. { "athlete.level": "intermediate" })
function resolveValue(values: Record<string, unknown>, dotPath: string): unknown {
  // First try flat key lookup (our form uses dot-path keys directly)
  if (dotPath in values) return values[dotPath];
  // Fallback: nested object traversal
  return dotPath.split('.').reduce((acc: unknown, key) => {
    if (acc && typeof acc === 'object') return (acc as Record<string, unknown>)[key];
    return undefined;
  }, values as unknown);
}

function evalCondition(expr: string, values: Record<string, unknown>): boolean {
  return expr.split('&&').every(clause => {
    const m = clause.trim().match(/ctx\.([a-zA-Z0-9_.]+)\s*==\s*['"]?([^'")\s]+)['"]?/);
    if (!m) return true;
    const actual = resolveValue(values, m[1]);
    return String(actual ?? '') === m[2].trim();
  });
}

function applyDefault(field: ParameterField): unknown {
  const d = field.default_expr;
  if (d == null) {
    if (field.type === 'string_array' || field.type === 'number_array') return [];
    if (field.type === 'boolean') return false;
    if (field.type === 'number') return '';
    return '';
  }
  if (d === '[]') return [];
  if (d === 'true') return true;
  if (d === 'false') return false;
  const n = Number(d);
  if (!isNaN(n) && d !== '') return n;
  return d.replace(/^['"]|['"]$/g, '');
}

const EQUIPMENT_OPTIONS = [
  'barbell', 'rack', 'bench', 'dumbbells', 'cable', 'kettlebell',
  'pullup_bar', 'smith_machine', 'dip_station', 'machine', 'bands',
];

function StringArrayField({ field, value, onChange }: {
  field: ParameterField;
  value: string[];
  onChange: (v: string[]) => void;
}) {
  const isEquipment = field.key.includes('equipment');
  const options = isEquipment ? EQUIPMENT_OPTIONS : [];

  if (isEquipment) {
    return (
      <div className="dpf-checkbox-group">
        {options.map(opt => (
          <label key={opt} className="dpf-checkbox-label">
            <input
              type="checkbox"
              checked={value.includes(opt)}
              onChange={e => {
                if (e.target.checked) onChange([...value, opt]);
                else onChange(value.filter(v => v !== opt));
              }}
            />
            {opt}
          </label>
        ))}
      </div>
    );
  }

  return (
    <input
      className="dpf-input"
      type="text"
      value={value.join(', ')}
      placeholder="Comma-separated values"
      onChange={e => onChange(e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
    />
  );
}

export default function DynamicParamForm({ fields, values, onChange }: Props) {
  return (
    <div className="dpf-form">
      {fields.map(field => {
        if (field.visible_if && !evalCondition(field.visible_if, values)) return null;

        const isRequired = field.required ||
          (field.required_if ? evalCondition(field.required_if, values) : false);

        const rawVal = values[field.key] ?? applyDefault(field);

        return (
          <div key={field.key} className="dpf-field">
            <label className="dpf-label">
              {field.description ?? formatLabel(field.key)}
              {isRequired && <span className="dpf-required">*</span>}
            </label>

            {field.type === 'enum' && (
              <select
                className="dpf-select"
                value={String(rawVal ?? '')}
                onChange={e => onChange(field.key, e.target.value)}
              >
                <option value="">Select…</option>
                {(field.enum ?? []).map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            )}

            {field.type === 'number' && (
              <input
                className="dpf-input"
                type="number"
                min={field.min ?? undefined}
                max={field.max ?? undefined}
                value={rawVal as number | string}
                placeholder={`${field.min ?? ''}–${field.max ?? ''}`}
                onChange={e => onChange(field.key, e.target.value === '' ? '' : Number(e.target.value))}
              />
            )}

            {field.type === 'string' && (
              <input
                className="dpf-input"
                type="text"
                value={String(rawVal ?? '')}
                onChange={e => onChange(field.key, e.target.value)}
              />
            )}

            {field.type === 'boolean' && (
              <label className="dpf-toggle">
                <input
                  type="checkbox"
                  checked={Boolean(rawVal)}
                  onChange={e => onChange(field.key, e.target.checked)}
                />
                <span>{field.description ?? field.key}</span>
              </label>
            )}

            {(field.type === 'string_array') && (
              <StringArrayField
                field={field}
                value={(rawVal as string[]) ?? []}
                onChange={v => onChange(field.key, v)}
              />
            )}

            {field.type === 'number_array' && (
              <input
                className="dpf-input"
                type="text"
                value={Array.isArray(rawVal) ? (rawVal as number[]).join(', ') : ''}
                placeholder="Comma-separated numbers"
                onChange={e => onChange(field.key, e.target.value.split(',').map(s => Number(s.trim())).filter(n => !isNaN(n)))}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
