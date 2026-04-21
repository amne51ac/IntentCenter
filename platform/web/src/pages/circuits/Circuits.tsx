import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiJson } from "../../api/client";
import { DataTable } from "../../components/DataTable";
import { ModelListPageHeader } from "../../components/ModelListPageHeader";
import { RowOverflowMenu } from "../../components/RowOverflowMenu";
import { objectViewHref } from "../../lib/objectLinks";
import { notifyActionUnavailable } from "../../lib/rowActions";
import { InlineLoader } from "../../components/Loader";

type ProviderRef = { id: string; name: string };

type SegmentRow = {
  id: string;
  segmentIndex: number;
  label: string | null;
  status: string;
  bandwidthMbps: number | null;
  provider: ProviderRef;
};

type CircuitRow = {
  id: string;
  cid: string;
  status: string;
  bandwidthMbps: number | null;
  provider: ProviderRef;
  segments: SegmentRow[];
  circuitDiversityGroup?: { id: string; name: string; slug: string } | null;
};

export function CircuitsPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [addForCircuit, setAddForCircuit] = useState<string | null>(null);
  const [newLabel, setNewLabel] = useState("");
  const [newProviderId, setNewProviderId] = useState("");

  const circuits = useQuery({
    queryKey: ["circuits"],
    queryFn: () => apiJson<{ items: CircuitRow[] }>("/v1/circuits"),
  });

  const providers = useQuery({
    queryKey: ["providers"],
    queryFn: () => apiJson<{ items: { id: string; name: string }[] }>("/v1/providers"),
  });

  const addSegment = useMutation({
    mutationFn: async ({ circuitId, body }: { circuitId: string; body: Record<string, unknown> }) =>
      apiJson<{ item: SegmentRow }>(`/v1/circuits/${circuitId}/segments`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["circuits"] });
      setNewLabel("");
      setNewProviderId("");
      setAddForCircuit(null);
    },
  });

  const removeSegment = useMutation({
    mutationFn: async ({ circuitId, segmentId }: { circuitId: string; segmentId: string }) =>
      apiJson<{ ok: boolean }>(`/v1/circuits/${circuitId}/segments/${segmentId}`, { method: "DELETE" }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["circuits"] }),
  });

  return (
    <>
      <ModelListPageHeader
        title="Circuits"
        subtitle="WAN / transport — click a row for circuit details; use ··· → Manage segments to add legs here"
        addNew={{ to: "/circuits/circuits/new", label: "Add circuit" }}
      />
      <div className="main-body">
        {circuits.isLoading ? <InlineLoader /> : null}
        {circuits.error ? <div className="error-banner">{String(circuits.error)}</div> : null}
        {circuits.data ? (
          <>
            <DataTable
              columns={[
                { key: "cid", label: "Circuit ID" },
                { key: "provider", label: "Primary provider" },
                { key: "diversity", label: "Diversity group" },
                { key: "segments", label: "Segments" },
                { key: "status", label: "Status" },
                { key: "bw", label: "Mbps" },
              ]}
              rows={circuits.data.items.map((i) => ({
                cid: i.cid,
                provider: i.provider?.name ?? "—",
                diversity: i.circuitDiversityGroup?.name ?? "—",
                segments: String(i.segments?.length ?? 0),
                status: i.status,
                bw: i.bandwidthMbps ?? "—",
                _id: i.id,
              }))}
              onRowClick={(row) => {
                const id = typeof row._id === "string" ? row._id : null;
                if (!id) return;
                navigate(objectViewHref("Circuit", id));
              }}
              actionsColumn={{
                label: "",
                render: (row) => {
                  const id = String(row._id);
                  return (
                    <RowOverflowMenu
                      items={[
                        {
                          id: "segments",
                          label: "Manage segments",
                          onSelect: () => setExpandedId((e) => (e === id ? null : id)),
                        },
                        { id: "copy", label: "Copy", onSelect: () => notifyActionUnavailable("Copy") },
                        { id: "archive", label: "Archive", onSelect: () => notifyActionUnavailable("Archive") },
                        {
                          id: "delete",
                          label: "Delete",
                          danger: true,
                          onSelect: () => notifyActionUnavailable("Delete"),
                        },
                      ]}
                    />
                  );
                },
              }}
            />
            {circuits.data.items.map((c) =>
              expandedId === c.id ? (
                <div key={c.id} className="circuit-expand">
                  <h3 className="circuit-expand-title">
                    Legs for <span className="mono">{c.cid}</span>
                  </h3>
                  {c.segments.length === 0 ? (
                    <p className="muted">No segments yet — the primary row is the overall circuit; add legs for each hop or carrier handoff.</p>
                  ) : (
                    <table className="data segment-table">
                      <thead>
                        <tr>
                          <th>#</th>
                          <th>Label</th>
                          <th>Carrier</th>
                          <th>Status</th>
                          <th>Mbps</th>
                          <th />
                        </tr>
                      </thead>
                      <tbody>
                        {c.segments.map((s) => (
                          <tr key={s.id}>
                            <td className="mono">{s.segmentIndex}</td>
                            <td>{s.label ?? "—"}</td>
                            <td>{s.provider?.name ?? "—"}</td>
                            <td>{s.status}</td>
                            <td>{s.bandwidthMbps ?? "—"}</td>
                            <td>
                              <button
                                type="button"
                                className="btn btn-danger-text"
                                disabled={removeSegment.isPending}
                                onClick={() => removeSegment.mutate({ circuitId: c.id, segmentId: s.id })}
                              >
                                Remove
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                  {addForCircuit === c.id ? (
                    <div className="segment-add-form">
                      {providers.isLoading ? <InlineLoader label="Loading carriers…" /> : null}
                      <label>
                        Label <input value={newLabel} onChange={(e) => setNewLabel(e.target.value)} placeholder="e.g. Metro handoff" />
                      </label>
                      <label>
                        Carrier (optional — defaults to primary){" "}
                        <select value={newProviderId} onChange={(e) => setNewProviderId(e.target.value)} disabled={providers.isLoading}>
                          <option value="">— Same as circuit —</option>
                          {(providers.data?.items ?? []).map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.name}
                            </option>
                          ))}
                        </select>
                      </label>
                      <button
                        type="button"
                        className="btn btn-primary"
                        disabled={addSegment.isPending}
                        onClick={() => {
                          const body: Record<string, unknown> = {};
                          if (newLabel.trim()) body.label = newLabel.trim();
                          if (newProviderId) body.providerId = newProviderId;
                          addSegment.mutate({ circuitId: c.id, body });
                        }}
                      >
                        Add leg
                      </button>
                      <button type="button" className="btn" onClick={() => setAddForCircuit(null)}>
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button type="button" className="btn btn-primary" style={{ marginTop: "0.75rem" }} onClick={() => setAddForCircuit(c.id)}>
                      Add segment
                    </button>
                  )}
                </div>
              ) : null,
            )}
          </>
        ) : null}
      </div>
    </>
  );
}
