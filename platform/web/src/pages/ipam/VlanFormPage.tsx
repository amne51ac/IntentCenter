import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { useMatch, useNavigate, useParams } from "react-router-dom";
import { apiJson } from "../../api/client";
import { FormPageShell } from "../../components/FormPageShell";
import { InlineLoader } from "../../components/Loader";
import { objectViewHref } from "../../lib/objectLinks";

type VgRow = { id: string; name: string };

type VlanItem = {
  id: string;
  vid: number;
  name: string;
  vlanGroupId: string | null;
};

export function VlanFormPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const isNew = useMatch({ path: "/ipam/vlans/new", end: true }) !== null;
  const { vlanId } = useParams<{ vlanId: string }>();
  const id = isNew ? undefined : vlanId;

  const [vid, setVid] = useState("");
  const [name, setName] = useState("");
  const [vlanGroupId, setVlanGroupId] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const groups = useQuery({
    queryKey: ["catalog", "VlanGroup"],
    queryFn: () => apiJson<{ items: VgRow[] }>("/v1/catalog/VlanGroup/items"),
  });

  const detailQ = useQuery({
    queryKey: ["vlan", id],
    queryFn: () => apiJson<{ item: VlanItem }>(`/v1/vlans/${id}`),
    enabled: Boolean(id),
  });

  useEffect(() => {
    const row = detailQ.data?.item;
    if (!row) return;
    setVid(String(row.vid));
    setName(row.name);
    setVlanGroupId(row.vlanGroupId ?? "");
  }, [detailQ.data?.item]);

  const createMut = useMutation({
    mutationFn: (body: { vid: number; name: string; vlanGroupId: string | null }) =>
      apiJson<{ item: { id: string } }>("/v1/vlans", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: async (data) => {
      await qc.invalidateQueries({ queryKey: ["vlans"] });
      navigate(objectViewHref("Vlan", data.item.id), { replace: true });
    },
  });

  const patchMut = useMutation({
    mutationFn: (body: { vid: number; name: string; vlanGroupId: string | null }) =>
      apiJson<{ item: { id: string } }>(`/v1/vlans/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["vlans"] });
      navigate(objectViewHref("Vlan", id!), { replace: true });
    },
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    const v = Number.parseInt(vid, 10);
    if (!Number.isFinite(v) || v < 1 || v > 4094) {
      setErr("VLAN ID must be between 1 and 4094.");
      return;
    }
    if (!name.trim()) {
      setErr("Name is required.");
      return;
    }
    const gid = vlanGroupId.trim();
    const body = { vid: v, name: name.trim(), vlanGroupId: gid ? gid : null };
    if (isNew) {
      createMut.mutate(body);
    } else {
      patchMut.mutate(body);
    }
  }

  const pending = createMut.isPending || patchMut.isPending;

  if (groups.isLoading) {
    return (
      <FormPageShell title={isNew ? "New VLAN" : "Edit VLAN"} subtitle="Layer-2 segment" backTo="/ipam/vlans" backLabel="Back to VLANs">
        <InlineLoader label="Loading VLAN groups…" />
      </FormPageShell>
    );
  }

  if (!isNew && id && detailQ.isLoading) {
    return (
      <FormPageShell title="Edit VLAN" subtitle="Layer-2 segment" backTo="/ipam/vlans" backLabel="Back to VLANs">
        <InlineLoader label="Loading VLAN…" />
      </FormPageShell>
    );
  }

  if (!isNew && (detailQ.isError || !detailQ.data?.item)) {
    return (
      <FormPageShell title="Edit VLAN" subtitle="Layer-2 segment" backTo="/ipam/vlans" backLabel="Back to VLANs">
        <div className="error-banner">{detailQ.isError ? String(detailQ.error) : "Not found"}</div>
      </FormPageShell>
    );
  }

  return (
    <FormPageShell
      title={isNew ? "New VLAN" : "Edit VLAN"}
      subtitle="Layer-2 segment"
      backTo="/ipam/vlans"
      backLabel="Back to VLANs"
      footer={
        <>
          <button type="button" className="btn btn-ghost" onClick={() => navigate("/ipam/vlans")}>
            Cancel
          </button>
          <button type="submit" form="vlan-form" className="btn btn-primary" disabled={pending}>
            {pending ? "Saving…" : isNew ? "Create" : "Save"}
          </button>
        </>
      }
    >
      <form id="vlan-form" className="form-stack" onSubmit={onSubmit}>
        {err ? <div className="error-banner">{err}</div> : null}
        {createMut.error ? <div className="error-banner">{String(createMut.error)}</div> : null}
        {patchMut.error ? <div className="error-banner">{String(patchMut.error)}</div> : null}
        <label>
          VLAN ID (1–4094)
          <input className="input" type="number" min={1} max={4094} value={vid} onChange={(e) => setVid(e.target.value)} required />
        </label>
        <label>
          Name
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} required autoComplete="off" />
        </label>
        <label>
          VLAN group (optional)
          <select className="input" value={vlanGroupId} onChange={(e) => setVlanGroupId(e.target.value)}>
            <option value="">— None —</option>
            {groups.data?.items.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </select>
        </label>
      </form>
    </FormPageShell>
  );
}
