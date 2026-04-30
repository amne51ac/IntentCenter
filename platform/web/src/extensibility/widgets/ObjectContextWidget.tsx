import type { CSSProperties } from "react";

const row: CSSProperties = { display: "flex", justifyContent: "space-between", gap: "0.5rem", marginBottom: "0.35rem" };
const k: CSSProperties = { color: "var(--text-muted)", fontSize: "0.8rem" };
const v: CSSProperties = { fontSize: "0.88rem", textAlign: "right", wordBreak: "break-all" };

/** Built-in extension widget: shows macro-bound context (for demos and support / traceability). */
export function ObjectContextWidget(props: Record<string, string>) {
  return (
    <div className="ext-widget ext-widget--objectContext">
      <h4 className="ext-widget-title">{props.label || "Context"}</h4>
      <p className="muted" style={{ fontSize: "0.8rem", margin: "0 0 0.5rem" }}>
        Values come from the page context (macros v1). Use devtools to compare with{" "}
        <code>resource</code> in scope.
      </p>
      <div style={row}>
        <span style={k}>Type</span>
        <span className="mono" style={v}>
          {props.typeLine || "—"}
        </span>
      </div>
      <div style={row}>
        <span style={k}>Name</span>
        <span style={v}>{props.name || "—"}</span>
      </div>
      <div style={row}>
        <span style={k}>Id</span>
        <span className="mono" style={{ ...v, fontSize: "0.8rem" }}>
          {props.idLine || "—"}
        </span>
      </div>
    </div>
  );
}
