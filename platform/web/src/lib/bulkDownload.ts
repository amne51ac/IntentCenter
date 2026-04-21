import { apiJson } from "../api/client";

export async function downloadBulkExport(
  resourceType: string,
  format: "csv" | "json",
  templateOnly: boolean,
): Promise<void> {
  const data = await apiJson<{
    csvText?: string;
    filename?: string;
    items?: unknown[];
  }>(`/v1/bulk/${encodeURIComponent(resourceType)}/export?format=${format}&template=${templateOnly ? "true" : "false"}`);
  if (format === "csv" && data.csvText != null) {
    const blob = new Blob([data.csvText], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = data.filename || `${resourceType.toLowerCase()}-export.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
    return;
  }
  const blob = new Blob([JSON.stringify(data.items ?? [], null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${resourceType.toLowerCase()}-export.json`;
  a.click();
  URL.revokeObjectURL(a.href);
}
