import type { ReactNode } from "react";

export function DataTable({
  columns,
  rows,
  emptyMessage = "No rows yet.",
  onRowClick,
  actionsColumn,
}: {
  columns: { key: string; label: string }[];
  rows: Record<string, unknown>[];
  emptyMessage?: string;
  onRowClick?: (row: Record<string, unknown>, rowIndex: number) => void;
  actionsColumn?: { label: string; render: (row: Record<string, unknown>, rowIndex: number) => ReactNode };
}) {
  if (rows.length === 0) {
    return <p className="empty">{emptyMessage}</p>;
  }
  return (
    <div className="table-wrap">
      <table className="data">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key}>{c.label}</th>
            ))}
            {actionsColumn ? (
              <th className="table-actions-header" scope="col">
                {actionsColumn.label ? actionsColumn.label : <span className="sr-only">Row actions</span>}
              </th>
            ) : null}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={String(row._id ?? row.id ?? i)}
              onClick={onRowClick ? () => onRowClick(row, i) : undefined}
              className={onRowClick ? "data-row-clickable" : undefined}
            >
              {columns.map((c) => (
                <td key={c.key} className={typeof row[c.key] === "string" && (row[c.key] as string).length > 40 ? "mono" : undefined}>
                  {formatCell(row[c.key])}
                </td>
              ))}
              {actionsColumn ? (
                <td className="table-actions" onClick={(e) => e.stopPropagation()}>
                  {actionsColumn.render(row, i)}
                </td>
              ) : null}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatCell(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}
