import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { useMatch, useNavigate, useParams } from "react-router-dom";
import { apiJson } from "../../api/client";
import { FormPageShell } from "../../components/FormPageShell";
import { InlineLoader } from "../../components/Loader";
import { objectViewHref } from "../../lib/objectLinks";

type ProviderRow = { id: string; name: string };

type CircuitItem = {
  id: string;
  providerId: string;
  cid: string;
  bandwidthMbps: number | null;
  status: string;
  aSideNotes: string | null;
  zSideNotes: string | null;
  circuitDiversityGroupId: string | null;
};

const CIRCUIT_STATUSES = ["PLANNED", "ACTIVE", "DECOMMISSIONED"] as const;

export function CircuitFormPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const isNew = useMatch({ path: "/circuits/circuits/new", end: true }) !== null;
  const { circuitId } = useParams<{ circuitId: string }>();
  const id = isNew ? undefined : circuitId;

  const [providerId, setProviderId] = useState("");
  const [cid, setCid] = useState("");
  const [bandwidthMbps, setBandwidthMbps] = useState("");
  const [status, setStatus] = useState<string>("PLANNED");
  const [aSideNotes, setASideNotes] = useState("");
  const [zSideNotes, setZSideNotes] = useState("");
  const [diversityGroupId, setDiversityGroupId] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const providers = useQuery({
    queryKey: ["providers"],
    queryFn: () => apiJson<{ items: ProviderRow[] }>("/v1/providers"),
  });

  const diversityGroups = useQuery({
    queryKey: ["catalog", "CircuitDiversityGroup"],
    queryFn: () => apiJson<{ items: { id: string; name: string }[] }>("/v1/catalog/CircuitDiversityGroup/items"),
  });

  const detailQ = useQuery({
    queryKey: ["circuit", id],
    queryFn: () => apiJson<{ item: CircuitItem }>(`/v1/circuits/${id}`),
    enabled: Boolean(id),
  });

  useEffect(() => {
    const row = detailQ.data?.item;
    if (!row) return;
    setProviderId(row.providerId);
    setCid(row.cid);
    setBandwidthMbps(row.bandwidthMbps != null ? String(row.bandwidthMbps) : "");
    setStatus(row.status);
    setASideNotes(row.aSideNotes ?? "");
    setZSideNotes(row.zSideNotes ?? "");
    setDiversityGroupId(row.circuitDiversityGroupId ?? "");
  }, [detailQ.data?.item]);

  const createMut = useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      apiJson<{ item: { id: string } }>("/v1/circuits", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: async (data) => {
      await qc.invalidateQueries({ queryKey: ["circuits"] });
      navigate(objectViewHref("Circuit", data.item.id), { replace: true });
    },
  });

  const patchMut = useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      apiJson<{ item: { id: string } }>(`/v1/circuits/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["circuits"] });
      navigate(objectViewHref("Circuit", id!), { replace: true });
    },
  });

  function buildBody(): Record<string, unknown> {
    const bw = bandwidthMbps.trim();
    let bandwidth: number | null = null;
    if (bw) {
      const n = Number.parseInt(bw, 10);
      if (!Number.isFinite(n) || n <= 0) {
        throw new Error("Bandwidth must be a positive integer (Mbps).");
      }
      bandwidth = n;
    }
    const body: Record<string, unknown> = {
      providerId: providerId.trim(),
      cid: cid.trim(),
      bandwidthMbps: bandwidth,
      aSideNotes: aSideNotes.trim() || null,
      zSideNotes: zSideNotes.trim() || null,
      status,
    };
    if (diversityGroupId.trim()) {
      body.circuitDiversityGroupId = diversityGroupId.trim();
    } else {
      body.circuitDiversityGroupId = null;
    }
    return body;
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    if (!providerId.trim()) {
      setErr("Select a provider.");
      return;
    }
    if (!cid.trim()) {
      setErr("Circuit ID is required.");
      return;
    }
    try {
      const body = buildBody();
      if (isNew) {
        createMut.mutate(body);
      } else {
        patchMut.mutate(body);
      }
    } catch (er) {
      setErr(er instanceof Error ? er.message : String(er));
    }
  }

  const pending = createMut.isPending || patchMut.isPending;

  if (providers.isLoading) {
    return (
      <FormPageShell title={isNew ? "New circuit" : "Edit circuit"} subtitle="WAN / transport circuit" backTo="/circuits/circuits" backLabel="Back to circuits">
        <InlineLoader label="Loading providers…" />
      </FormPageShell>
    );
  }

  if (!isNew && id && detailQ.isLoading) {
    return (
      <FormPageShell title="Edit circuit" subtitle="WAN / transport circuit" backTo="/circuits/circuits" backLabel="Back to circuits">
        <InlineLoader label="Loading circuit…" />
      </FormPageShell>
    );
  }

  if (!isNew && (detailQ.isError || !detailQ.data?.item)) {
    return (
      <FormPageShell title="Edit circuit" subtitle="WAN / transport circuit" backTo="/circuits/circuits" backLabel="Back to circuits">
        <div className="error-banner">{detailQ.isError ? String(detailQ.error) : "Not found"}</div>
      </FormPageShell>
    );
  }

  return (
    <FormPageShell
      title={isNew ? "New circuit" : "Edit circuit"}
      subtitle="WAN / transport circuit"
      backTo="/circuits/circuits"
      backLabel="Back to circuits"
      footer={
        <>
          <button type="button" className="btn btn-ghost" onClick={() => navigate("/circuits/circuits")}>
            Cancel
          </button>
          <button type="submit" form="circuit-form" className="btn btn-primary" disabled={pending}>
            {pending ? "Saving…" : isNew ? "Create" : "Save"}
          </button>
        </>
      }
    >
      <form id="circuit-form" className="form-stack" onSubmit={onSubmit}>
        {err ? <div className="error-banner">{err}</div> : null}
        {createMut.error ? <div className="error-banner">{String(createMut.error)}</div> : null}
        {patchMut.error ? <div className="error-banner">{String(patchMut.error)}</div> : null}
        <label>
          Provider
          <select className="input" value={providerId} onChange={(e) => setProviderId(e.target.value)} required>
            <option value="">— Select —</option>
            {providers.data?.items.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Diversity group (optional)
          <select className="input" value={diversityGroupId} onChange={(e) => setDiversityGroupId(e.target.value)}>
            <option value="">— None —</option>
            {(diversityGroups.data?.items ?? []).map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </select>
        </label>
        {diversityGroups.isLoading ? <p className="muted">Loading diversity groups…</p> : null}
        <label>
          Circuit ID (carrier ref)
          <input className="input" value={cid} onChange={(e) => setCid(e.target.value)} required autoComplete="off" />
        </label>
        <label>
          Bandwidth (Mbps, optional)
          <input className="input" type="number" min={1} value={bandwidthMbps} onChange={(e) => setBandwidthMbps(e.target.value)} autoComplete="off" />
        </label>
        <label>
          Status
          <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
            {CIRCUIT_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label>
          A-side notes (optional)
          <textarea className="input" rows={2} value={aSideNotes} onChange={(e) => setASideNotes(e.target.value)} />
        </label>
        <label>
          Z-side notes (optional)
          <textarea className="input" rows={2} value={zSideNotes} onChange={(e) => setZSideNotes(e.target.value)} />
        </label>
      </form>
    </FormPageShell>
  );
}
