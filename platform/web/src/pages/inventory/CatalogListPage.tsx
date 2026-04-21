import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { apiJson } from "../../api/client";
import { DataTable } from "../../components/DataTable";
import { ModelListPageHeader } from "../../components/ModelListPageHeader";
import { RowOverflowMenu } from "../../components/RowOverflowMenu";
import { objectEditHref, objectViewHref } from "../../lib/objectLinks";
import { notifyActionUnavailable } from "../../lib/rowActions";
import { catalogBySlug } from "./inventoryCatalogConfig";
import { InlineLoader } from "../../components/Loader";

const PREFERRED_KEYS = ["name", "slug", "title", "serviceType", "vpnType", "clusterType", "status", "id"];

function columnsForRow(sample: Record<string, unknown>): { key: string; label: string }[] {
  const keys = Object.keys(sample).filter((k) => !k.endsWith("_") || k === "metadata_");
  const ordered: string[] = [];
  for (const p of PREFERRED_KEYS) {
    if (keys.includes(p) && !ordered.includes(p)) ordered.push(p);
  }
  for (const k of keys.sort()) {
    if (ordered.includes(k)) continue;
    if (["definition", "metadata", "metadata_", "passwordHash", "preferences"].includes(k)) continue;
    ordered.push(k);
    if (ordered.length >= 8) break;
  }
  return ordered.map((k) => ({ key: k, label: k === "id" ? "ID" : k.replace(/([A-Z])/g, " $1").replace(/^./, (s) => s.toUpperCase()) }));
}

export function CatalogListPage() {
  const { catalogSlug = "" } = useParams<{ catalogSlug: string }>();
  const cfg = catalogBySlug(catalogSlug);
  const navigate = useNavigate();
  const qc = useQueryClient();

  const q = useQuery({
    queryKey: ["catalog", cfg?.apiType],
    queryFn: () => apiJson<{ items: Record<string, unknown>[] }>(`/v1/catalog/${cfg?.apiType}/items`),
    enabled: Boolean(cfg?.apiType),
  });

  if (!cfg) {
    return (
      <>
        <ModelListPageHeader title="Not found" subtitle="Unknown catalog page" showBulkTools={false} />
        <div className="main-body">
          <p className="error-banner">Unknown inventory catalog.</p>
        </div>
      </>
    );
  }

  const sample = q.data?.items?.[0];
  const cols = sample ? columnsForRow(sample) : [{ key: "id", label: "ID" }];

  return (
    <>
      <ModelListPageHeader
        title={cfg.title}
        subtitle={cfg.subtitle}
        pinLabel={cfg.title}
        bulkResourceType={cfg.apiType}
        onBulkSuccess={() => void qc.invalidateQueries({ queryKey: ["catalog", cfg.apiType] })}
        addNew={
          cfg.apiType === "Tenant"
            ? undefined
            : { to: `/inventory/${catalogSlug}/new`, label: `Add ${cfg.addNoun}` }
        }
      />
      <div className="main-body">
        {q.isLoading ? <InlineLoader label="Loading catalog…" /> : null}
        {q.error ? <div className="error-banner">{String(q.error)}</div> : null}
        {q.data?.items?.length === 0 ? <p className="muted">No rows yet.</p> : null}
        {q.data?.items && q.data.items.length > 0 ? (
          <DataTable
            columns={cols}
            rows={q.data.items.map((row) => {
              const out: Record<string, unknown> = { _id: String(row.id ?? "") };
              for (const c of cols) {
                const v = row[c.key];
                if (v !== null && typeof v === "object" && !Array.isArray(v)) {
                  out[c.key] = JSON.stringify(v);
                } else {
                  out[c.key] = v ?? "—";
                }
              }
              return out;
            })}
            onRowClick={(r) => {
              const id = String(r._id);
              if (cfg.apiType === "Tenant") return;
              navigate(objectViewHref(cfg.apiType, id));
            }}
            actionsColumn={{
              label: "",
              render: (r) => {
                const id = String(r._id);
                const edit = objectEditHref(cfg.apiType, id);
                return (
                  <>
                    {edit ? (
                      <Link to={edit} className="btn btn-ghost table-inline-link" onClick={(e) => e.stopPropagation()}>
                        Edit
                      </Link>
                    ) : null}
                    <RowOverflowMenu
                      items={[
                        { id: "copy", label: "Copy", onSelect: () => notifyActionUnavailable("Copy") },
                        { id: "archive", label: "Archive", onSelect: () => notifyActionUnavailable("Archive") },
                        { id: "delete", label: "Delete", danger: true, onSelect: () => notifyActionUnavailable("Delete") },
                      ]}
                    />
                  </>
                );
              },
            }}
          />
        ) : null}
      </div>
    </>
  );
}
