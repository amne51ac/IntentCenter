import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useEffect, useMemo, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { apiJson } from "../../api/client";
import { FormPageShell } from "../../components/FormPageShell";
import { InlineLoader } from "../../components/Loader";
import { objectViewHref } from "../../lib/objectLinks";
import { catalogBySlug } from "./inventoryCatalogConfig";

const SKIP_FIELDS = new Set([
  "id",
  "organizationId",
  "createdAt",
  "updatedAt",
  "deletedAt",
  "passwordHash",
]);

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

export function CatalogItemEditPage() {
  const { catalogSlug = "", itemId = "" } = useParams<{ catalogSlug: string; itemId: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const cfg = catalogBySlug(catalogSlug);
  const [values, setValues] = useState<Record<string, string>>({});
  const [err, setErr] = useState<string | null>(null);

  const itemQ = useQuery({
    queryKey: ["catalog-item", cfg?.apiType, itemId],
    queryFn: () =>
      apiJson<{ item: Record<string, unknown> }>(`/v1/catalog/${encodeURIComponent(cfg!.apiType)}/items/${encodeURIComponent(itemId)}`),
    enabled: Boolean(cfg && itemId && cfg.apiType !== "Tenant"),
  });

  const fieldKeys = useMemo(() => {
    const row = itemQ.data?.item;
    if (!row) return [];
    return Object.keys(row)
      .filter((k) => !SKIP_FIELDS.has(k))
      .sort();
  }, [itemQ.data?.item]);

  useEffect(() => {
    const row = itemQ.data?.item;
    if (!row) return;
    const next: Record<string, string> = {};
    for (const k of Object.keys(row)) {
      if (SKIP_FIELDS.has(k)) continue;
      const v = row[k];
      if (v === null || v === undefined) next[k] = "";
      else if (typeof v === "object") next[k] = JSON.stringify(v, null, 2);
      else next[k] = String(v);
    }
    setValues(next);
  }, [itemQ.data?.item]);

  const patchMut = useMutation({
    mutationFn: async () => {
      if (!cfg) throw new Error("Missing catalog");
      const body: Record<string, unknown> = {};
      for (const key of fieldKeys) {
        const raw = values[key]?.trim() ?? "";
        if (!raw) {
          body[key] = null;
          continue;
        }
        if (isJsonishColumn(key)) {
          try {
            body[key] = JSON.parse(raw) as unknown;
          } catch {
            throw new Error(`Invalid JSON for ${key}`);
          }
        } else {
          body[key] = raw;
        }
      }
      return apiJson<{ item: Record<string, unknown> }>(
        `/v1/catalog/${encodeURIComponent(cfg.apiType)}/items/${encodeURIComponent(itemId)}`,
        { method: "PATCH", body: JSON.stringify(body) },
      );
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["catalog", cfg?.apiType] });
      navigate(objectViewHref(cfg!.apiType, itemId), { replace: true });
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
    patchMut.mutate(undefined, {
      onError: (e: unknown) => setErr(String(e)),
    });
  }

  function setField(key: string, v: string) {
    setValues((prev) => ({ ...prev, [key]: v }));
  }

  if (itemQ.isLoading) {
    return (
      <>
        <FormPageShell title={`Edit ${cfg.addNoun}`} subtitle={cfg.subtitle} backTo={`/inventory/${catalogSlug}`} backLabel="Back to list">
          <InlineLoader label="Loading…" />
        </FormPageShell>
      </>
    );
  }

  if (itemQ.error) {
    return (
      <FormPageShell title={`Edit ${cfg.addNoun}`} subtitle={cfg.subtitle} backTo={`/inventory/${catalogSlug}`} backLabel="Back to list">
        <div className="error-banner">{String(itemQ.error)}</div>
      </FormPageShell>
    );
  }

  return (
    <FormPageShell
      title={`Edit ${cfg.addNoun}`}
      subtitle={cfg.subtitle}
      backTo={`/inventory/${catalogSlug}`}
      backLabel="Back to list"
      footer={
        <>
          <Link to={`/inventory/${catalogSlug}`} className="btn btn-ghost">
            Cancel
          </Link>
          <button type="submit" form="catalog-edit-form" className="btn btn-primary" disabled={patchMut.isPending}>
            {patchMut.isPending ? "Saving…" : "Save"}
          </button>
        </>
      }
    >
      <p className="muted" style={{ marginBottom: "1rem" }}>
        Updates are sent as <span className="mono">PATCH</span> to <span className="mono">{cfg.apiType}</span>. Empty fields are sent as null.
      </p>
      <form id="catalog-edit-form" className="form-stack" onSubmit={onSubmit}>
        {err ? <div className="error-banner">{err}</div> : null}
        {patchMut.error ? <div className="error-banner">{String(patchMut.error)}</div> : null}
        {fieldKeys.length === 0 ? <p className="muted">No editable columns returned for this row.</p> : null}
        {fieldKeys.map((key) => (
          <label key={key}>
            {key.replace(/([A-Z])/g, " $1").replace(/^./, (s) => s.toUpperCase())}
            {isJsonishColumn(key) ? (
              <textarea
                className="input mono"
                rows={4}
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
