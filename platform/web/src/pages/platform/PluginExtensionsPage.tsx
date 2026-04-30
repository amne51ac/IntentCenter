import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch, apiJson } from "../../api/client";
import { BlockLoader, InlineLoader } from "../../components/Loader";
import { ModelListPageHeader } from "../../components/ModelListPageHeader";
import { PAGE_IDS } from "../../extensibility/pageIds";

type PluginRow = {
  id: string;
  packageName: string;
  version: string;
  enabled: boolean;
  contributions?: { summary?: { widgetCount?: number } };
};

type PlacementRow = {
  id: string;
  packageName?: string;
  pageId: string;
  slot: string;
  widgetKey: string;
  enabled: boolean;
  priority: number;
};

type ConnectorRow = { id: string; name: string; type: string; enabled: boolean; healthStatus?: string | null };

export function PluginExtensionsPage() {
  const qc = useQueryClient();
  const [deleting, setDeleting] = useState<string | null>(null);
  const [form, setForm] = useState<{
    pluginId: string;
    pageId: string;
    slot: string;
    widgetKey: string;
    priority: number;
  }>({
    pluginId: "",
    pageId: PAGE_IDS.inventoryObjectView,
    slot: "content.aside",
    widgetKey: "builtin.objectContext",
    priority: 0,
  });
  const [saving, setSaving] = useState(false);
  const [formErr, setFormErr] = useState<string | null>(null);

  const plugins = useQuery({
    queryKey: ["plugins"],
    queryFn: () => apiJson<{ items: PluginRow[] }>("/v1/plugins"),
  });

  const placements = useQuery({
    queryKey: ["admin", "plugin-placements"],
    queryFn: () => apiJson<{ items: PlacementRow[] }>("/v1/admin/plugin-placements?includeDisabled=true"),
  });

  const connectors = useQuery({
    queryKey: ["connectors"],
    queryFn: () => apiJson<{ items: ConnectorRow[] }>("/v1/connectors"),
  });

  async function onAdd(e: FormEvent) {
    e.preventDefault();
    if (!form.pluginId.trim()) {
      setFormErr("Select a plugin.");
      return;
    }
    setFormErr(null);
    setSaving(true);
    try {
      await apiJson("/v1/admin/plugin-placements", {
        method: "POST",
        body: JSON.stringify({
          pluginRegistrationId: form.pluginId,
          pageId: form.pageId,
          slot: form.slot,
          widgetKey: form.widgetKey,
          priority: form.priority,
          enabled: true,
        }),
      });
      await qc.invalidateQueries({ queryKey: ["admin", "plugin-placements"] });
    } catch (x) {
      setFormErr(x instanceof Error ? x.message : String(x));
    } finally {
      setSaving(false);
    }
  }

  async function onDeletePl(id: string) {
    if (!window.confirm("Remove this widget placement?")) return;
    setDeleting(id);
    try {
      await apiFetch(`/v1/admin/plugin-placements/${encodeURIComponent(id)}`, { method: "DELETE" });
      await qc.invalidateQueries({ queryKey: ["admin", "plugin-placements"] });
    } finally {
      setDeleting(null);
    }
  }

  if (plugins.isLoading) {
    return <BlockLoader label="Loading…" />;
  }
  if (plugins.error) {
    return <div className="error-banner">{String(plugins.error)}</div>;
  }

  return (
    <>
      <ModelListPageHeader
        title="Plugins & extensions"
        subtitle="Registered packages, UI slot placements, and connectors for this organization."
        showPin={false}
        showBulkTools={false}
        extraActions={
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", justifyContent: "flex-end" }}>
            <Link to="/platform/jobs" className="btn btn-ghost">
              Jobs
            </Link>
            <Link to="/platform/job-runs" className="btn btn-ghost">
              Job runs
            </Link>
          </div>
        }
      />
      <div className="main-body plugin-extensions-page">
        <div className="page-lede plugin-extensions-lede">
          <p>
            <strong>Connectors:</strong> run job <code className="mono">connector.sync</code> with{" "}
            <code className="mono">{"{ \"connectorId\": \"<uuid>\" }"}</code> in the run input. Types{" "}
            <code className="mono">webhook_outbound</code> and <code className="mono">http_get</code> perform outbound
            HTTP from the API process (use a worker in production for isolation).
          </p>
        </div>

        <section className="graph-section" aria-labelledby="ext-plugins-h">
          <h3 id="ext-plugins-h" className="graph-section-title">
            Registered plugins
          </h3>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Package</th>
                  <th>Version</th>
                  <th>Widgets (manifest)</th>
                </tr>
              </thead>
              <tbody>
                {(plugins.data?.items ?? []).map((p) => (
                  <tr key={p.id}>
                    <td className="mono">{p.packageName}</td>
                    <td>{p.version}</td>
                    <td>{p.contributions?.summary?.widgetCount ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="graph-section" aria-labelledby="ext-placements-h">
          <h3 id="ext-placements-h" className="graph-section-title">
            UI placements
          </h3>
          {placements.isLoading ? <InlineLoader label="Loading…" /> : null}
          {placements.error ? <div className="error-banner">{String(placements.error)}</div> : null}
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Page</th>
                  <th>Slot</th>
                  <th>Widget</th>
                  <th>Plugin</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {(placements.data?.items ?? []).map((r) => (
                  <tr key={r.id}>
                    <td className="mono" style={{ fontSize: "0.82em" }}>
                      {r.pageId}
                    </td>
                    <td className="mono" style={{ fontSize: "0.82em" }}>
                      {r.slot}
                    </td>
                    <td className="mono" style={{ fontSize: "0.82em" }}>
                      {r.widgetKey}
                    </td>
                    <td className="mono" style={{ fontSize: "0.82em" }}>
                      {r.packageName ?? "—"}
                    </td>
                    <td className="table-actions">
                      <button
                        type="button"
                        className="btn btn-ghost table-inline-link"
                        onClick={() => onDeletePl(r.id)}
                        disabled={deleting === r.id}
                      >
                        {deleting === r.id ? "…" : "Delete"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="graph-section" aria-labelledby="ext-add-h">
          <h3 id="ext-add-h" className="graph-section-title">
            Add placement
          </h3>
          <div className="plugin-extensions-form-panel">
            <form onSubmit={onAdd}>
              {formErr ? <div className="error-banner" style={{ marginBottom: "0.75rem" }}>{formErr}</div> : null}
              <div style={{ marginBottom: "0.85rem" }}>
                <label className="muted" htmlFor="pe-plugin">
                  Plugin
                </label>
                <select
                  id="pe-plugin"
                  className="input"
                  value={form.pluginId}
                  onChange={(e) => setForm((f) => ({ ...f, pluginId: e.target.value }))}
                  required
                  style={{ display: "block", width: "100%", maxWidth: "28rem", marginTop: "0.35rem" }}
                >
                  <option value="">—</option>
                  {(plugins.data?.items ?? []).map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.packageName} ({p.version})
                    </option>
                  ))}
                </select>
              </div>
              <div className="plugin-extensions-form-grid">
                <div>
                  <label className="muted" htmlFor="pe-page">
                    Page ID
                  </label>
                  <input
                    id="pe-page"
                    className="input"
                    value={form.pageId}
                    onChange={(e) => setForm((f) => ({ ...f, pageId: e.target.value }))}
                    style={{ display: "block", width: "100%", marginTop: "0.35rem" }}
                  />
                </div>
                <div>
                  <label className="muted" htmlFor="pe-slot">
                    Slot
                  </label>
                  <input
                    id="pe-slot"
                    className="input"
                    value={form.slot}
                    onChange={(e) => setForm((f) => ({ ...f, slot: e.target.value }))}
                    style={{ display: "block", width: "100%", marginTop: "0.35rem" }}
                  />
                </div>
                <div>
                  <label className="muted" htmlFor="pe-wkey">
                    Widget key
                  </label>
                  <input
                    id="pe-wkey"
                    className="input"
                    value={form.widgetKey}
                    onChange={(e) => setForm((f) => ({ ...f, widgetKey: e.target.value }))}
                    style={{ display: "block", width: "100%", marginTop: "0.35rem" }}
                  />
                </div>
                <div style={{ maxWidth: "7rem" }}>
                  <label className="muted" htmlFor="pe-pri">
                    Priority
                  </label>
                  <input
                    id="pe-pri"
                    type="number"
                    className="input"
                    value={form.priority}
                    onChange={(e) => setForm((f) => ({ ...f, priority: parseInt(e.target.value, 10) || 0 }))}
                    style={{ display: "block", width: "100%", marginTop: "0.35rem" }}
                  />
                </div>
              </div>
              <button className="btn btn-primary" type="submit" disabled={saving} style={{ marginTop: "0.9rem" }}>
                {saving ? "…" : "Add placement"}
              </button>
            </form>
          </div>
        </section>

        <section className="graph-section" aria-labelledby="ext-conn-h">
          <h3 id="ext-conn-h" className="graph-section-title">
            Connectors
          </h3>
          <p className="page-lede" style={{ marginTop: 0, marginBottom: "0.75rem" }}>
            List is read-only here; create and edit via the API (admin) or future forms.
          </p>
          {connectors.isLoading ? <InlineLoader label="Loading…" /> : null}
          {connectors.error ? <div className="error-banner">{String(connectors.error)}</div> : null}
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Health</th>
                </tr>
              </thead>
              <tbody>
                {(connectors.data?.items ?? []).map((c) => (
                  <tr key={c.id}>
                    <td className="mono" style={{ fontSize: "0.86em" }}>
                      {c.name}
                    </td>
                    <td>{c.type}</td>
                    <td>{c.healthStatus ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </>
  );
}
