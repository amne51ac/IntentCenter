import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { useMatch, useNavigate, useParams } from "react-router-dom";
import { apiJson } from "../../api/client";
import { FormPageShell } from "../../components/FormPageShell";
import { InlineLoader } from "../../components/Loader";
import { objectViewHref } from "../../lib/objectLinks";

type PrefixRow = { id: string; cidr: string; vrf: { name: string } };

type IpItem = {
  id: string;
  prefixId: string;
  address: string;
  description: string | null;
  interfaceId: string | null;
};

export function IpAddressFormPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const isNew = useMatch({ path: "/ipam/ip-addresses/new", end: true }) !== null;
  const { ipAddressId } = useParams<{ ipAddressId: string }>();
  const id = isNew ? undefined : ipAddressId;

  const [prefixId, setPrefixId] = useState("");
  const [address, setAddress] = useState("");
  const [description, setDescription] = useState("");
  const [interfaceId, setInterfaceId] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const prefixes = useQuery({
    queryKey: ["prefixes"],
    queryFn: () => apiJson<{ items: PrefixRow[] }>("/v1/prefixes"),
  });

  const detailQ = useQuery({
    queryKey: ["ip-address", id],
    queryFn: () => apiJson<{ item: IpItem }>(`/v1/ip-addresses/${id}`),
    enabled: Boolean(id),
  });

  useEffect(() => {
    const row = detailQ.data?.item;
    if (!row) return;
    setPrefixId(row.prefixId);
    setAddress(row.address);
    setDescription(row.description ?? "");
    setInterfaceId(row.interfaceId ?? "");
  }, [detailQ.data?.item]);

  const createMut = useMutation({
    mutationFn: (body: {
      prefixId: string;
      address: string;
      description: string | null;
      interfaceId: string | null;
    }) => apiJson<{ item: { id: string } }>("/v1/ip-addresses", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: async (data) => {
      await qc.invalidateQueries({ queryKey: ["ip-addresses"] });
      navigate(objectViewHref("IpAddress", data.item.id), { replace: true });
    },
  });

  const patchMut = useMutation({
    mutationFn: (body: {
      prefixId: string;
      address: string;
      description: string | null;
      interfaceId: string | null;
    }) => apiJson<{ item: { id: string } }>(`/v1/ip-addresses/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["ip-addresses"] });
      navigate(objectViewHref("IpAddress", id!), { replace: true });
    },
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    if (!prefixId.trim()) {
      setErr("Select a prefix.");
      return;
    }
    if (!address.trim()) {
      setErr("Address is required.");
      return;
    }
    const iid = interfaceId.trim();
    const body = {
      prefixId: prefixId.trim(),
      address: address.trim(),
      description: description.trim() || null,
      interfaceId: iid ? iid : null,
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
      <FormPageShell title="Edit IP address" subtitle="Host address within a prefix" backTo="/ipam/ip-addresses" backLabel="Back to IP addresses">
        <InlineLoader label="Loading…" />
      </FormPageShell>
    );
  }

  if (!isNew && (detailQ.isError || !detailQ.data?.item)) {
    return (
      <FormPageShell title="Edit IP address" subtitle="Host address within a prefix" backTo="/ipam/ip-addresses" backLabel="Back to IP addresses">
        <div className="error-banner">{detailQ.isError ? String(detailQ.error) : "Not found"}</div>
      </FormPageShell>
    );
  }

  return (
    <FormPageShell
      title={isNew ? "New IP address" : "Edit IP address"}
      subtitle="Host address within a prefix"
      backTo="/ipam/ip-addresses"
      backLabel="Back to IP addresses"
      footer={
        <>
          <button type="button" className="btn btn-ghost" onClick={() => navigate("/ipam/ip-addresses")}>
            Cancel
          </button>
          <button type="submit" form="ip-form" className="btn btn-primary" disabled={pending || prefixes.isLoading}>
            {pending ? "Saving…" : isNew ? "Create" : "Save"}
          </button>
        </>
      }
    >
      <form id="ip-form" className="form-stack" onSubmit={onSubmit}>
        {err ? <div className="error-banner">{err}</div> : null}
        {createMut.error ? <div className="error-banner">{String(createMut.error)}</div> : null}
        {patchMut.error ? <div className="error-banner">{String(patchMut.error)}</div> : null}
        <label>
          Prefix
          <select className="input" value={prefixId} onChange={(e) => setPrefixId(e.target.value)} required disabled={prefixes.isLoading}>
            <option value="">— Select —</option>
            {prefixes.data?.items.map((p) => (
              <option key={p.id} value={p.id}>
                {p.cidr} ({p.vrf?.name ?? "VRF"})
              </option>
            ))}
          </select>
        </label>
        {prefixes.isLoading ? <InlineLoader label="Loading prefixes…" /> : null}
        <label>
          Address
          <input className="input" value={address} onChange={(e) => setAddress(e.target.value)} placeholder="e.g. 10.0.0.5" required autoComplete="off" />
        </label>
        <label>
          Description (optional)
          <input className="input" value={description} onChange={(e) => setDescription(e.target.value)} autoComplete="off" />
        </label>
        <label>
          Interface ID (optional)
          <input className="input mono" value={interfaceId} onChange={(e) => setInterfaceId(e.target.value)} placeholder="UUID" autoComplete="off" />
        </label>
      </form>
    </FormPageShell>
  );
}
