import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { useMatch, useNavigate, useParams } from "react-router-dom";
import { apiJson } from "../../api/client";
import { FormPageShell } from "../../components/FormPageShell";
import { InlineLoader } from "../../components/Loader";
import { objectViewHref } from "../../lib/objectLinks";

type ServiceItem = {
  id: string;
  name: string;
  serviceType: string;
  customerRef: string | null;
  metadata: Record<string, unknown> | null;
};

export function ServiceFormPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const isNew = useMatch({ path: "/platform/services/new", end: true }) !== null;
  const { serviceId } = useParams<{ serviceId: string }>();
  const id = isNew ? undefined : serviceId;

  const [name, setName] = useState("");
  const [serviceType, setServiceType] = useState("");
  const [customerRef, setCustomerRef] = useState("");
  const [metadataJson, setMetadataJson] = useState("{}");
  const [err, setErr] = useState<string | null>(null);

  const detailQ = useQuery({
    queryKey: ["service", id],
    queryFn: () => apiJson<{ item: ServiceItem }>(`/v1/services/${id}`),
    enabled: Boolean(id),
  });

  useEffect(() => {
    const row = detailQ.data?.item;
    if (!row) return;
    setName(row.name);
    setServiceType(row.serviceType);
    setCustomerRef(row.customerRef ?? "");
    setMetadataJson(JSON.stringify(row.metadata ?? {}, null, 2));
  }, [detailQ.data?.item]);

  const createMut = useMutation({
    mutationFn: (body: { name: string; serviceType: string; customerRef: string | null; metadata: Record<string, unknown> | null }) =>
      apiJson<{ item: { id: string } }>("/v1/services", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: async (data) => {
      await qc.invalidateQueries({ queryKey: ["services"] });
      navigate(objectViewHref("Service", data.item.id), { replace: true });
    },
  });

  const patchMut = useMutation({
    mutationFn: (body: { name: string; serviceType: string; customerRef: string | null; metadata: Record<string, unknown> | null }) =>
      apiJson<{ item: { id: string } }>(`/v1/services/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["services"] });
      navigate(objectViewHref("Service", id!), { replace: true });
    },
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    if (!name.trim()) {
      setErr("Name is required.");
      return;
    }
    if (!serviceType.trim()) {
      setErr("Service type is required.");
      return;
    }
    let metadata: Record<string, unknown> | null = null;
    const raw = metadataJson.trim();
    if (raw && raw !== "{}") {
      try {
        const j = JSON.parse(raw) as unknown;
        if (j === null || typeof j !== "object" || Array.isArray(j)) {
          setErr("Metadata must be a JSON object.");
          return;
        }
        metadata = j as Record<string, unknown>;
      } catch {
        setErr("Metadata must be valid JSON.");
        return;
      }
    }
    const body = {
      name: name.trim(),
      serviceType: serviceType.trim(),
      customerRef: customerRef.trim() || null,
      metadata,
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
      <FormPageShell title="Edit service" subtitle="Logical service instance" backTo="/platform/services" backLabel="Back to services">
        <InlineLoader label="Loading…" />
      </FormPageShell>
    );
  }

  if (!isNew && (detailQ.isError || !detailQ.data?.item)) {
    return (
      <FormPageShell title="Edit service" subtitle="Logical service instance" backTo="/platform/services" backLabel="Back to services">
        <div className="error-banner">{detailQ.isError ? String(detailQ.error) : "Not found"}</div>
      </FormPageShell>
    );
  }

  return (
    <FormPageShell
      title={isNew ? "New service" : "Edit service"}
      subtitle="Logical service instance"
      backTo="/platform/services"
      backLabel="Back to services"
      footer={
        <>
          <button type="button" className="btn btn-ghost" onClick={() => navigate("/platform/services")}>
            Cancel
          </button>
          <button type="submit" form="service-form" className="btn btn-primary" disabled={pending}>
            {pending ? "Saving…" : isNew ? "Create" : "Save"}
          </button>
        </>
      }
    >
      <form id="service-form" className="form-stack" onSubmit={onSubmit}>
        {err ? <div className="error-banner">{err}</div> : null}
        {createMut.error ? <div className="error-banner">{String(createMut.error)}</div> : null}
        {patchMut.error ? <div className="error-banner">{String(patchMut.error)}</div> : null}
        <label>
          Name
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} required autoComplete="off" />
        </label>
        <label>
          Service type
          <input className="input" value={serviceType} onChange={(e) => setServiceType(e.target.value)} placeholder="e.g. l3vpn, internet" required autoComplete="off" />
        </label>
        <label>
          Customer ref (optional)
          <input className="input" value={customerRef} onChange={(e) => setCustomerRef(e.target.value)} autoComplete="off" />
        </label>
        <label>
          Metadata (JSON object, optional)
          <textarea className="input mono" rows={4} value={metadataJson} onChange={(e) => setMetadataJson(e.target.value)} spellCheck={false} />
        </label>
      </form>
    </FormPageShell>
  );
}
