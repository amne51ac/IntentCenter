import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useState } from "react";
import { useMatch, useNavigate, useParams } from "react-router-dom";
import { apiJson } from "../../api/client";
import { coerceCustomAttributes, KeyValueEditor, stringMapFromUnknown } from "../../components/KeyValueEditor";
import { FormPageShell } from "../../components/FormPageShell";
import { InlineLoader } from "../../components/Loader";

export type RackRow = {
  id: string;
  name: string;
  uHeight: number;
  location: { id: string; name: string };
  templateId?: string | null;
  customAttributes?: Record<string, unknown>;
};

type LocOpt = { id: string; name: string };
type TemplateOpt = { id: string; name: string; slug: string; isDefault?: boolean };

export function RackFormPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const isNew = useMatch({ path: "/dcim/racks/new", end: true }) !== null;
  const { rackId } = useParams<{ rackId: string }>();
  const id = isNew ? undefined : rackId;

  const locQ = useQuery({
    queryKey: ["locations"],
    queryFn: () => apiJson<{ items: LocOpt[] }>("/v1/locations"),
  });
  const templatesQ = useQuery({
    queryKey: ["templates", "Rack"],
    queryFn: () => apiJson<{ items: TemplateOpt[] }>("/v1/templates?resourceType=Rack"),
  });
  const detailQ = useQuery({
    queryKey: ["rack", id],
    queryFn: () => apiJson<{ item: RackRow }>(`/v1/racks/${id}`),
    enabled: Boolean(id),
  });

  const createMut = useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      apiJson<{ item: RackRow }>("/v1/racks", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: async (data) => {
      await qc.invalidateQueries({ queryKey: ["racks"] });
      navigate(`/dcim/racks/${data.item.id}/edit`, { replace: true });
    },
  });

  const patchMut = useMutation({
    mutationFn: (args: { id: string; body: Record<string, unknown> }) =>
      apiJson(`/v1/racks/${args.id}`, { method: "PATCH", body: JSON.stringify(args.body) }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["racks"] });
      void qc.invalidateQueries({ queryKey: ["rack", id] });
    },
  });

  const initial = isNew ? null : detailQ.data?.item ?? null;

  if (!isNew && detailQ.isLoading) {
    return (
      <FormPageShell title="Edit rack" backTo="/dcim/racks" backLabel="Back to racks">
        <InlineLoader label="Loading rack…" />
      </FormPageShell>
    );
  }
  if (!isNew && (detailQ.error || !initial)) {
    return (
      <FormPageShell title="Edit rack" backTo="/dcim/racks" backLabel="Back to racks">
        <div className="error-banner">{detailQ.error ? String(detailQ.error) : "Not found"}</div>
      </FormPageShell>
    );
  }

  const refsLoading = locQ.isLoading || templatesQ.isLoading;
  if (refsLoading) {
    return (
      <FormPageShell
        title={isNew ? "New rack" : "Edit rack"}
        subtitle={isNew ? "Add a cabinet at a location." : undefined}
        backTo="/dcim/racks"
        backLabel="Back to racks"
      >
        <InlineLoader label="Loading form options…" />
      </FormPageShell>
    );
  }

  return (
    <RackFormInner
      mode={isNew ? "create" : "edit"}
      initial={initial}
      locations={locQ.data?.items ?? []}
      templates={templatesQ.data?.items ?? []}
      submitting={createMut.isPending || patchMut.isPending}
      error={createMut.error || patchMut.error ? String(createMut.error || patchMut.error) : null}
      onCancel={() => navigate("/dcim/racks")}
      onSaveCreate={(body) => createMut.mutate(body)}
      onSaveEdit={id ? (body) => patchMut.mutate({ id, body }) : undefined}
    />
  );
}

function RackFormInner({
  mode,
  initial,
  locations,
  templates,
  submitting,
  error,
  onCancel,
  onSaveCreate,
  onSaveEdit,
}: {
  mode: "create" | "edit";
  initial: RackRow | null;
  locations: LocOpt[];
  templates: TemplateOpt[];
  submitting: boolean;
  error: string | null;
  onCancel: () => void;
  onSaveCreate: (body: Record<string, unknown>) => void;
  onSaveEdit: ((body: Record<string, unknown>) => void) | undefined;
}) {
  const [name, setName] = useState(initial?.name ?? "");
  const [locationId, setLocationId] = useState(initial?.location?.id ?? locations[0]?.id ?? "");
  const [uHeight, setUHeight] = useState(initial ? String(initial.uHeight) : "42");
  const [templateId, setTemplateId] = useState(initial?.templateId ?? "");
  const [kv, setKv] = useState<Record<string, string>>(() =>
    initial?.customAttributes ? stringMapFromUnknown(initial.customAttributes) : {},
  );
  const [localErr, setLocalErr] = useState<string | null>(null);
  const defaultTpl = templates.find((t) => t.isDefault);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLocalErr(null);
    if (!name.trim() || !locationId) {
      setLocalErr("Name and location are required.");
      return;
    }
    const u = uHeight.trim() ? Number(uHeight) : 42;
    if (Number.isNaN(u) || u < 1) {
      setLocalErr("U height must be a positive number.");
      return;
    }
    const body = {
      name: name.trim(),
      locationId,
      uHeight: u,
      templateId: templateId || null,
      customAttributes: coerceCustomAttributes(kv),
    };
    if (mode === "create") onSaveCreate(body);
    else onSaveEdit?.(body);
  }

  return (
    <FormPageShell
      title={mode === "create" ? "New rack" : "Edit rack"}
      subtitle={mode === "create" ? "Add a cabinet at a location." : undefined}
      backTo="/dcim/racks"
      backLabel="Back to racks"
      footer={
        <>
          <button type="button" className="btn btn-ghost" onClick={onCancel} disabled={submitting}>
            Cancel
          </button>
          <button type="submit" form="rack-form" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Saving…" : "Save"}
          </button>
        </>
      }
    >
      <form id="rack-form" className="form-stack" onSubmit={handleSubmit}>
        {localErr ? <div className="error-banner">{localErr}</div> : null}
        {error ? <div className="error-banner">{error}</div> : null}
        <label>
          Name
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} autoComplete="off" />
        </label>
        <label>
          Location
          <select className="input" value={locationId} onChange={(e) => setLocationId(e.target.value)}>
            {locations.map((l) => (
              <option key={l.id} value={l.id}>
                {l.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Height (U)
          <input className="input" value={uHeight} onChange={(e) => setUHeight(e.target.value)} inputMode="numeric" />
        </label>
        <label>
          Template (optional)
          <select className="input" value={templateId} onChange={(e) => setTemplateId(e.target.value)}>
            <option value="">— None {defaultTpl ? `(default: ${defaultTpl.name})` : ""} —</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name} ({t.slug}){t.isDefault ? " ★" : ""}
              </option>
            ))}
          </select>
        </label>
        <KeyValueEditor value={kv} onChange={setKv} />
      </form>
    </FormPageShell>
  );
}
