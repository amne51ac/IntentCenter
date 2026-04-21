import { useMemo } from "react";

/** Edit string key/value pairs; values are always strings (JSON-parse on submit if needed). */
export function KeyValueEditor({
  value,
  onChange,
  label = "Custom attributes",
}: {
  value: Record<string, string>;
  onChange: (next: Record<string, string>) => void;
  label?: string;
}) {
  const rows = useMemo(() => Object.entries(value), [value]);

  function setPair(i: number, key: string, v: string) {
    const next: Record<string, string> = {};
    const list = [...rows];
    list[i] = [key, v];
    for (const [k, val] of list) {
      if (k.trim()) next[k.trim()] = val;
    }
    onChange(next);
  }

  function addRow() {
    onChange({ ...value, "": "" });
  }

  function removeAt(i: number) {
    const list = rows.filter((_, j) => j !== i);
    const next: Record<string, string> = {};
    for (const [k, v] of list) {
      if (k.trim()) next[k.trim()] = v;
    }
    onChange(next);
  }

  return (
    <div>
      <div style={{ marginBottom: "0.35rem", fontSize: "0.8rem", color: "var(--text-muted)" }}>{label}</div>
      <div className="kv-rows">
        {rows.length === 0 ? (
          <p className="muted" style={{ margin: 0, fontSize: "0.82rem" }}>
            No custom fields. Add rows for template-specific parameters.
          </p>
        ) : null}
        {rows.map(([k, v], i) => (
          <div key={i} className="kv-row">
            <input
              className="input"
              placeholder="Key"
              value={k}
              onChange={(e) => setPair(i, e.target.value, v)}
              aria-label={`Custom attribute key ${i + 1}`}
            />
            <input
              className="input"
              placeholder="Value"
              value={v}
              onChange={(e) => setPair(i, k, e.target.value)}
              aria-label={`Custom attribute value ${i + 1}`}
            />
            <button type="button" className="btn btn-ghost" onClick={() => removeAt(i)}>
              Remove
            </button>
          </div>
        ))}
      </div>
      <button type="button" className="btn btn-ghost" style={{ marginTop: "0.5rem" }} onClick={addRow}>
        Add field
      </button>
    </div>
  );
}

/** Convert string map to JSON-serializable object (attempt number/boolean parse for common cases). */
export function coerceCustomAttributes(raw: Record<string, string>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(raw)) {
    if (!k.trim()) continue;
    const t = v.trim();
    if (t === "true") {
      out[k] = true;
      continue;
    }
    if (t === "false") {
      out[k] = false;
      continue;
    }
    if (t !== "" && !Number.isNaN(Number(t)) && String(Number(t)) === t) {
      out[k] = Number(t);
      continue;
    }
    try {
      if ((t.startsWith("{") && t.endsWith("}")) || (t.startsWith("[") && t.endsWith("]"))) {
        out[k] = JSON.parse(t) as unknown;
        continue;
      }
    } catch {
      /* keep string */
    }
    out[k] = v;
  }
  return out;
}

export function stringMapFromUnknown(data: unknown): Record<string, string> {
  if (!data || typeof data !== "object") return {};
  const o: Record<string, string> = {};
  for (const [k, v] of Object.entries(data as Record<string, unknown>)) {
    if (typeof v === "string") o[k] = v;
    else if (v === null || v === undefined) o[k] = "";
    else o[k] = JSON.stringify(v);
  }
  return o;
}
