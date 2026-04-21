import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { useMatch, useNavigate, useParams } from "react-router-dom";
import { apiJson } from "../../api/client";
import { FormPageShell } from "../../components/FormPageShell";
import { InlineLoader } from "../../components/Loader";
import { objectViewHref } from "../../lib/objectLinks";

export function VrfFormPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const isNew = useMatch({ path: "/ipam/vrfs/new", end: true }) !== null;
  const { vrfId } = useParams<{ vrfId: string }>();
  const id = isNew ? undefined : vrfId;

  const [name, setName] = useState("");
  const [rd, setRd] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const detailQ = useQuery({
    queryKey: ["vrf", id],
    queryFn: () => apiJson<{ item: { id: string; name: string; rd: string | null } }>(`/v1/vrfs/${id}`),
    enabled: Boolean(id),
  });

  useEffect(() => {
    const row = detailQ.data?.item;
    if (!row) return;
    setName(row.name);
    setRd(row.rd ?? "");
  }, [detailQ.data?.item]);

  const createMut = useMutation({
    mutationFn: (body: { name: string; rd: string | null }) =>
      apiJson<{ item: { id: string } }>("/v1/vrfs", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: async (data) => {
      await qc.invalidateQueries({ queryKey: ["vrfs"] });
      navigate(objectViewHref("Vrf", data.item.id), { replace: true });
    },
  });

  const patchMut = useMutation({
    mutationFn: (body: { name: string; rd: string | null }) =>
      apiJson<{ item: { id: string } }>(`/v1/vrfs/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["vrfs"] });
      await qc.invalidateQueries({ queryKey: ["vrf", id] });
      navigate(objectViewHref("Vrf", id!), { replace: true });
    },
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    if (!name.trim()) {
      setErr("Name is required.");
      return;
    }
    const body = { name: name.trim(), rd: rd.trim() || null };
    if (isNew) {
      createMut.mutate(body);
    } else {
      patchMut.mutate(body);
    }
  }

  const pending = createMut.isPending || patchMut.isPending;
  const loadErr = !isNew && detailQ.isError;

  if (!isNew && id && detailQ.isLoading) {
    return (
      <FormPageShell title="Edit VRF" subtitle="Routing / VPN context" backTo="/ipam/vrfs" backLabel="Back to VRFs">
        <InlineLoader label="Loading VRF…" />
      </FormPageShell>
    );
  }

  if (!isNew && (loadErr || !detailQ.data?.item)) {
    return (
      <FormPageShell title="Edit VRF" subtitle="Routing / VPN context" backTo="/ipam/vrfs" backLabel="Back to VRFs">
        <div className="error-banner">{loadErr ? String(detailQ.error) : "Not found"}</div>
      </FormPageShell>
    );
  }

  return (
    <FormPageShell
      title={isNew ? "New VRF" : "Edit VRF"}
      subtitle="Routing / VPN context"
      backTo="/ipam/vrfs"
      backLabel="Back to VRFs"
      footer={
        <>
          <button type="button" className="btn btn-ghost" onClick={() => navigate("/ipam/vrfs")}>
            Cancel
          </button>
          <button type="submit" form="vrf-form" className="btn btn-primary" disabled={pending}>
            {pending ? "Saving…" : isNew ? "Create" : "Save"}
          </button>
        </>
      }
    >
      <form id="vrf-form" className="form-stack" onSubmit={onSubmit}>
        {err ? <div className="error-banner">{err}</div> : null}
        {createMut.error ? <div className="error-banner">{String(createMut.error)}</div> : null}
        {patchMut.error ? <div className="error-banner">{String(patchMut.error)}</div> : null}
        <label>
          Name
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} autoComplete="off" required />
        </label>
        <label>
          Route distinguisher (optional)
          <input className="input" value={rd} onChange={(e) => setRd(e.target.value)} placeholder="e.g. 65000:1" autoComplete="off" />
        </label>
      </form>
    </FormPageShell>
  );
}
