import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { useMatch, useNavigate, useParams } from "react-router-dom";
import { apiJson } from "../../api/client";
import { FormPageShell } from "../../components/FormPageShell";
import { InlineLoader } from "../../components/Loader";
import { objectViewHref } from "../../lib/objectLinks";

type VrfRow = { id: string; name: string };

type PrefixItem = {
  id: string;
  vrfId: string;
  cidr: string;
  description: string | null;
  parentId: string | null;
};

export function PrefixFormPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const isNew = useMatch({ path: "/ipam/prefixes/new", end: true }) !== null;
  const { prefixId } = useParams<{ prefixId: string }>();
  const id = isNew ? undefined : prefixId;

  const [vrfId, setVrfId] = useState("");
  const [cidr, setCidr] = useState("");
  const [description, setDescription] = useState("");
  const [parentId, setParentId] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const vrfs = useQuery({
    queryKey: ["vrfs"],
    queryFn: () => apiJson<{ items: VrfRow[] }>("/v1/vrfs"),
  });

  const detailQ = useQuery({
    queryKey: ["prefix", id],
    queryFn: () => apiJson<{ item: PrefixItem }>(`/v1/prefixes/${id}`),
    enabled: Boolean(id),
  });

  useEffect(() => {
    const row = detailQ.data?.item;
    if (!row) return;
    setVrfId(row.vrfId);
    setCidr(row.cidr);
    setDescription(row.description ?? "");
    setParentId(row.parentId ?? "");
  }, [detailQ.data?.item]);

  const createMut = useMutation({
    mutationFn: (body: {
      vrfId: string;
      cidr: string;
      description: string | null;
      parentId: string | null;
    }) => apiJson<{ item: { id: string } }>("/v1/prefixes", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: async (data) => {
      await qc.invalidateQueries({ queryKey: ["prefixes"] });
      navigate(objectViewHref("Prefix", data.item.id), { replace: true });
    },
  });

  const patchMut = useMutation({
    mutationFn: (body: {
      vrfId: string;
      cidr: string;
      description: string | null;
      parentId: string | null;
    }) => apiJson<{ item: { id: string } }>(`/v1/prefixes/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["prefixes"] });
      navigate(objectViewHref("Prefix", id!), { replace: true });
    },
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    if (!vrfId.trim()) {
      setErr("Select a VRF.");
      return;
    }
    if (!cidr.trim()) {
      setErr("CIDR is required.");
      return;
    }
    const pid = parentId.trim();
    const body = {
      vrfId: vrfId.trim(),
      cidr: cidr.trim(),
      description: description.trim() || null,
      parentId: pid ? pid : null,
    };
    if (isNew) {
      createMut.mutate(body);
    } else {
      patchMut.mutate(body);
    }
  }

  const pending = createMut.isPending || patchMut.isPending;

  if (!isNew && id && detailQ.isLoading) {
    return (
      <FormPageShell title="Edit prefix" subtitle="IP aggregate within a VRF" backTo="/ipam/prefixes" backLabel="Back to prefixes">
        <InlineLoader label="Loading prefix…" />
      </FormPageShell>
    );
  }

  if (!isNew && (detailQ.isError || !detailQ.data?.item)) {
    return (
      <FormPageShell title="Edit prefix" subtitle="IP aggregate within a VRF" backTo="/ipam/prefixes" backLabel="Back to prefixes">
        <div className="error-banner">{detailQ.isError ? String(detailQ.error) : "Not found"}</div>
      </FormPageShell>
    );
  }

  return (
    <FormPageShell
      title={isNew ? "New prefix" : "Edit prefix"}
      subtitle="IP aggregate within a VRF"
      backTo="/ipam/prefixes"
      backLabel="Back to prefixes"
      footer={
        <>
          <button type="button" className="btn btn-ghost" onClick={() => navigate("/ipam/prefixes")}>
            Cancel
          </button>
          <button type="submit" form="prefix-form" className="btn btn-primary" disabled={pending || vrfs.isLoading}>
            {pending ? "Saving…" : isNew ? "Create" : "Save"}
          </button>
        </>
      }
    >
      <form id="prefix-form" className="form-stack" onSubmit={onSubmit}>
        {err ? <div className="error-banner">{err}</div> : null}
        {createMut.error ? <div className="error-banner">{String(createMut.error)}</div> : null}
        {patchMut.error ? <div className="error-banner">{String(patchMut.error)}</div> : null}
        <label>
          VRF
          <select className="input" value={vrfId} onChange={(e) => setVrfId(e.target.value)} required disabled={vrfs.isLoading}>
            <option value="">— Select —</option>
            {vrfs.data?.items.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name}
              </option>
            ))}
          </select>
        </label>
        {vrfs.isLoading ? <InlineLoader label="Loading VRFs…" /> : null}
        <label>
          CIDR
          <input className="input" value={cidr} onChange={(e) => setCidr(e.target.value)} placeholder="e.g. 10.0.0.0/16" required autoComplete="off" />
        </label>
        <label>
          Description (optional)
          <input className="input" value={description} onChange={(e) => setDescription(e.target.value)} autoComplete="off" />
        </label>
        <label>
          Parent prefix ID (optional)
          <input className="input mono" value={parentId} onChange={(e) => setParentId(e.target.value)} placeholder="UUID" autoComplete="off" />
        </label>
      </form>
    </FormPageShell>
  );
}
