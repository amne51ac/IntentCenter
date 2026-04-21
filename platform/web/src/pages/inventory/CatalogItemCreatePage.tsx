import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useMemo, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { apiJson } from "../../api/client";
import { FormPageShell } from "../../components/FormPageShell";
import { InlineLoader } from "../../components/Loader";
import { catalogBySlug } from "./inventoryCatalogConfig";

type BulkTemplate = {
  headers: string[];
  resourceType: string;
};

const SKIP_FIELDS = new Set([
  "id",
  "organizationId",
  "createdAt",
  "updatedAt",
  "deletedAt",
  "passwordHash",
]);

/** Heuristic: large JSON-ish columns use a textarea. */
function isJsonishColumn(key: string): boolean {
  const k = key.toLowerCase();
  return (
    k.includes("metadata") ||
    k.includes("definition") ||
    k.includes("preferences") ||
    k.includes("payload") ||
    k.includes("config") ||
    k.endsWith("json") ||
    k === "data"
  );
}

export function CatalogItemCreatePage() {
  const { catalogSlug = "" } = useParams<{ catalogSlug: string }>();
  const navigate = useNavigate();
  const cfg = catalogBySlug(catalogSlug);
  const qc = useQueryClient();
  const [values, setValues] = useState<Record<string, string>>({});
  const [err, setErr] = useState<string | null>(null);

  const tpl = useQuery({
    queryKey: ["bulk-template", cfg?.apiType],
    queryFn: () =>
      apiJson<BulkTemplate>(`/v1/bulk/${encodeURIComponent(cfg!.apiType)}/export?format=json&template=true`),
    enabled: Boolean(cfg && cfg.apiType !== "Tenant"),
  });

  const fieldKeys = useMemo(() => {
    if (!tpl.data?.headers) return [];
    return tpl.data.headers.filter((h) => !SKIP_FIELDS.has(h)).sort();
  }, [tpl.data?.headers]);

  const createMut = useMutation({
    mutationFn: async () => {
      if (!cfg) throw new Error("Missing catalog");
      const row: Record<string, unknown> = {};
      for (const key of fieldKeys) {
        const raw = values[key]?.trim() ?? "";
        if (!raw) continue;
        if (isJsonishColumn(key)) {
          try {
            row[key] = JSON.parse(raw) as unknown;
          } catch {
            throw new Error(`Invalid JSON for ${key}`);
          }
        } else {
          row[key] = raw;
        }
      }
      return apiJson<{ created: number; errors: unknown[] }>(`/v1/bulk/${encodeURIComponent(cfg.apiType)}/import/json`, {
        method: "POST",
        body: JSON.stringify({ rows: [row], skipErrors: false }),
      });
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["catalog", cfg?.apiType] });
    },
  });

  if (!cfg) {
    return <Navigate to="/" replace />;
  }

  if (cfg.apiType === "Tenant") {
    return <Navigate to={`/inventory/${catalogSlug}`} replace />;
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    createMut.mutate(undefined, {
      onError: (e: unknown) => setErr(String(e)),
      onSuccess: () => navigate(`/inventory/${catalogSlug}`, { replace: true }),
    });
  }

  function setField(key: string, v: string) {
    setValues((prev) => ({ ...prev, [key]: v }));
  }

  const loading = tpl.isLoading;
  const failed = tpl.isError;

  return (
    <FormPageShell
      title={`Add ${cfg.addNoun}`}
      subtitle={cfg.subtitle}
      backTo={`/inventory/${catalogSlug}`}
      backLabel="Back to list"
      footer={
        <>
          <Link to={`/inventory/${catalogSlug}`} className="btn btn-ghost">
            Cancel
          </Link>
          <button type="submit" form="catalog-create-form" className="btn btn-primary" disabled={createMut.isPending || loading || failed}>
            {createMut.isPending ? "Creating…" : "Create"}
          </button>
        </>
      }
    >
      <p className="muted" style={{ marginBottom: "1rem" }}>
        Fields match the bulk import template for <span className="mono">{cfg.apiType}</span>. Leave optional fields empty. For complex types, use the ⋯ menu on the list page to import JSON or CSV.
      </p>
      {loading ? <InlineLoader label="Loading field list…" /> : null}
      {failed ? <div className="error-banner">Could not load import template for this type.</div> : null}
      {tpl.data && fieldKeys.length === 0 ? <p className="muted">No writable columns exposed for this type. Use bulk import or the API.</p> : null}
      <form id="catalog-create-form" className="form-stack" onSubmit={onSubmit}>
        {err ? <div className="error-banner">{err}</div> : null}
        {createMut.error ? <div className="error-banner">{String(createMut.error)}</div> : null}
        {fieldKeys.map((key) => (
          <label key={key}>
            {key.replace(/([A-Z])/g, " $1").replace(/^./, (s) => s.toUpperCase())}
            {isJsonishColumn(key) ? (
              <textarea
                className="input mono"
                rows={4}
                placeholder="{}"
                value={values[key] ?? ""}
                onChange={(e) => setField(key, e.target.value)}
                spellCheck={false}
              />
            ) : (
              <input className="input" value={values[key] ?? ""} onChange={(e) => setField(key, e.target.value)} autoComplete="off" />
            )}
          </label>
        ))}
      </form>
    </FormPageShell>
  );
}
