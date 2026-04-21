import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { useMatch, useNavigate, useParams } from "react-router-dom";
import { apiJson } from "../../api/client";
import { FormPageShell } from "../../components/FormPageShell";
import { InlineLoader } from "../../components/Loader";
import { objectViewHref } from "../../lib/objectLinks";

type ProvItem = { id: string; name: string; asn: number | null };

export function ProviderFormPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const isNew = useMatch({ path: "/circuits/providers/new", end: true }) !== null;
  const { providerId } = useParams<{ providerId: string }>();
  const id = isNew ? undefined : providerId;

  const [name, setName] = useState("");
  const [asn, setAsn] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const detailQ = useQuery({
    queryKey: ["provider", id],
    queryFn: () => apiJson<{ item: ProvItem }>(`/v1/providers/${id}`),
    enabled: Boolean(id),
  });

  useEffect(() => {
    const row = detailQ.data?.item;
    if (!row) return;
    setName(row.name);
    setAsn(row.asn != null ? String(row.asn) : "");
  }, [detailQ.data?.item]);

  const createMut = useMutation({
    mutationFn: (body: { name: string; asn: number | null }) =>
      apiJson<{ item: { id: string } }>("/v1/providers", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: async (data) => {
      await qc.invalidateQueries({ queryKey: ["providers"] });
      navigate(objectViewHref("Provider", data.item.id), { replace: true });
    },
  });

  const patchMut = useMutation({
    mutationFn: (body: { name: string; asn: number | null }) =>
      apiJson<{ item: { id: string } }>(`/v1/providers/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["providers"] });
      navigate(objectViewHref("Provider", id!), { replace: true });
    },
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    if (!name.trim()) {
      setErr("Name is required.");
      return;
    }
    const a = asn.trim();
    let asnNum: number | null = null;
    if (a) {
      const n = Number.parseInt(a, 10);
      if (!Number.isFinite(n)) {
        setErr("ASN must be a number.");
        return;
      }
      asnNum = n;
    }
    const body = { name: name.trim(), asn: asnNum };
    if (isNew) {
      createMut.mutate(body);
    } else {
      patchMut.mutate(body);
    }
  }

  const pending = createMut.isPending || patchMut.isPending;

  if (!isNew && id && detailQ.isLoading) {
    return (
      <FormPageShell title="Edit provider" subtitle="Carrier / ISP" backTo="/circuits/providers" backLabel="Back to providers">
        <InlineLoader label="Loading…" />
      </FormPageShell>
    );
  }

  if (!isNew && (detailQ.isError || !detailQ.data?.item)) {
    return (
      <FormPageShell title="Edit provider" subtitle="Carrier / ISP" backTo="/circuits/providers" backLabel="Back to providers">
        <div className="error-banner">{detailQ.isError ? String(detailQ.error) : "Not found"}</div>
      </FormPageShell>
    );
  }

  return (
    <FormPageShell
      title={isNew ? "New provider" : "Edit provider"}
      subtitle="Carrier / ISP"
      backTo="/circuits/providers"
      backLabel="Back to providers"
      footer={
        <>
          <button type="button" className="btn btn-ghost" onClick={() => navigate("/circuits/providers")}>
            Cancel
          </button>
          <button type="submit" form="provider-form" className="btn btn-primary" disabled={pending}>
            {pending ? "Saving…" : isNew ? "Create" : "Save"}
          </button>
        </>
      }
    >
      <form id="provider-form" className="form-stack" onSubmit={onSubmit}>
        {err ? <div className="error-banner">{err}</div> : null}
        {createMut.error ? <div className="error-banner">{String(createMut.error)}</div> : null}
        {patchMut.error ? <div className="error-banner">{String(patchMut.error)}</div> : null}
        <label>
          Name
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} required autoComplete="off" />
        </label>
        <label>
          ASN (optional)
          <input className="input" type="number" value={asn} onChange={(e) => setAsn(e.target.value)} placeholder="e.g. 65001" autoComplete="off" />
        </label>
      </form>
    </FormPageShell>
  );
}
