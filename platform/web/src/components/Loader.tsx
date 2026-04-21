import type { ReactNode } from "react";

/**
 * Inline busy indicator — use for buttons, table cells, and compact UI.
 */
export function Spinner({ size = "md", className }: { size?: "sm" | "md"; className?: string }) {
  return (
    <span
      className={["spinner", size === "sm" ? "spinner--sm" : "spinner--md", className].filter(Boolean).join(" ")}
      role="status"
      aria-busy="true"
      aria-label="Loading"
    />
  );
}

/**
 * Spinner + optional label for list pages, forms, and panels.
 */
export function InlineLoader({ label = "Loading…", className }: { label?: ReactNode; className?: string }) {
  return (
    <div className={["inline-loader", className].filter(Boolean).join(" ")}>
      <Spinner size="sm" />
      {label != null && label !== "" ? <span className="inline-loader-label muted">{label}</span> : null}
    </div>
  );
}

/**
 * Centered loader for route gates, dashboard blocks, and full-width placeholders.
 */
export function BlockLoader({ label = "Loading…" }: { label?: ReactNode }) {
  return (
    <div className="block-loader">
      <InlineLoader label={label} />
    </div>
  );
}
