import { apiFetch, apiJson } from "../api/client";

export async function importBulkCsv(resourceType: string, file: File, skipErrors = false): Promise<{ created: number; errors: unknown[] }> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await apiFetch(
    `/v1/bulk/${encodeURIComponent(resourceType)}/import/csv?skipErrors=${skipErrors ? "true" : "false"}`,
    { method: "POST", body: fd },
  );
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body?.detail === "string" ? body.detail : JSON.stringify(body?.detail ?? body);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<{ created: number; errors: unknown[] }>;
}

export async function importBulkJson(resourceType: string, file: File, skipErrors = false): Promise<{ created: number; errors: unknown[] }> {
  const text = await file.text();
  let rows: unknown;
  try {
    rows = JSON.parse(text) as unknown;
  } catch (e) {
    throw new Error(`Invalid JSON: ${String(e)}`);
  }
  if (!Array.isArray(rows)) {
    throw new Error("JSON import must be an array of objects.");
  }
  return apiJson<{ created: number; errors: unknown[] }>(`/v1/bulk/${encodeURIComponent(resourceType)}/import/json`, {
    method: "POST",
    body: JSON.stringify({ rows, skipErrors }),
  });
}
