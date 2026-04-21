import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useState } from "react";
import { Link, useMatch, useNavigate, useParams } from "react-router-dom";
import { apiJson } from "../../api/client";
import { coerceCustomAttributes, KeyValueEditor, stringMapFromUnknown } from "../../components/KeyValueEditor";
import { FormPageShell } from "../../components/FormPageShell";
import { InlineLoader } from "../../components/Loader";

const STATUSES = ["PLANNED", "STAGED", "ACTIVE", "DECOMMISSIONED"] as const;

export type DeviceRow = {
  id: string;
  name: string;
  status: string;
  serialNumber?: string | null;
  positionU?: number | null;
  face?: string | null;
  rack: { id: string; name: string } | null;
  deviceType: { id: string; model: string; manufacturer: { name: string } };
  deviceRole: { id: string; name: string };
  templateId?: string | null;
  customAttributes?: Record<string, unknown>;
};

type TemplateOpt = { id: string; name: string; slug: string; isDefault?: boolean };
type DtOpt = { id: string; model: string; manufacturer: { name: string } };
type DrOpt = { id: string; name: string };
type RackOpt = { id: string; name: string };

export function DeviceFormPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const isNew = useMatch({ path: "/dcim/devices/new", end: true }) !== null;
  const { deviceId } = useParams<{ deviceId: string }>();
  const id = isNew ? undefined : deviceId;

  const dtQ = useQuery({
    queryKey: ["device-types"],
    queryFn: () => apiJson<{ items: DtOpt[] }>("/v1/device-types"),
  });
  const drQ = useQuery({
    queryKey: ["device-roles"],
    queryFn: () => apiJson<{ items: DrOpt[] }>("/v1/device-roles"),
  });
  const racksQ = useQuery({
    queryKey: ["racks"],
    queryFn: () => apiJson<{ items: RackOpt[] }>("/v1/racks"),
  });
  const templatesQ = useQuery({
    queryKey: ["templates", "Device"],
    queryFn: () => apiJson<{ items: TemplateOpt[] }>("/v1/templates?resourceType=Device"),
  });
  const detailQ = useQuery({
    queryKey: ["device", id],
    queryFn: () => apiJson<{ item: DeviceRow }>(`/v1/devices/${id}`),
    enabled: Boolean(id),
  });

  const createMut = useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      apiJson<{ item: DeviceRow }>("/v1/devices", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: async (data) => {
      await qc.invalidateQueries({ queryKey: ["devices"] });
      navigate(`/dcim/devices/${data.item.id}/edit`, { replace: true });
    },
  });

  const patchMut = useMutation({
    mutationFn: (args: { id: string; body: Record<string, unknown> }) =>
      apiJson(`/v1/devices/${args.id}`, { method: "PATCH", body: JSON.stringify(args.body) }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["devices"] });
      void qc.invalidateQueries({ queryKey: ["device", id] });
    },
  });

  const initial = isNew ? null : detailQ.data?.item ?? null;

  if (!isNew && detailQ.isLoading) {
    return (
      <FormPageShell title="Edit device" backTo="/dcim/devices" backLabel="Back to devices">
        <InlineLoader label="Loading device…" />
      </FormPageShell>
    );
  }
  if (!isNew && (detailQ.error || !initial)) {
    return (
      <FormPageShell title="Edit device" backTo="/dcim/devices" backLabel="Back to devices">
        <div className="error-banner">{detailQ.error ? String(detailQ.error) : "Not found"}</div>
      </FormPageShell>
    );
  }

  const refsLoading = dtQ.isLoading || drQ.isLoading || racksQ.isLoading || templatesQ.isLoading;
  if (refsLoading) {
    return (
      <FormPageShell
        title={isNew ? "New device" : "Edit device"}
        subtitle={isNew ? "Register hardware in a rack or unracked." : undefined}
        backTo="/dcim/devices"
        backLabel="Back to devices"
      >
        <InlineLoader label="Loading form options…" />
      </FormPageShell>
    );
  }

  return (
    <DeviceFormInner
      mode={isNew ? "create" : "edit"}
      initial={initial}
      deviceTypes={dtQ.data?.items ?? []}
      deviceRoles={drQ.data?.items ?? []}
      racks={racksQ.data?.items ?? []}
      templates={templatesQ.data?.items ?? []}
      submitting={createMut.isPending || patchMut.isPending}
      error={createMut.error || patchMut.error ? String(createMut.error || patchMut.error) : null}
      onCancel={() => navigate("/dcim/devices")}
      onSaveCreate={(body) => createMut.mutate(body)}
      onSaveEdit={id ? (body) => patchMut.mutate({ id, body }) : undefined}
      editResourceId={id}
    />
  );
}

function DeviceFormInner({
  mode,
  initial,
  deviceTypes,
  deviceRoles,
  racks,
  templates,
  submitting,
  error,
  onCancel,
  onSaveCreate,
  onSaveEdit,
  editResourceId,
}: {
  mode: "create" | "edit";
  initial: DeviceRow | null;
  deviceTypes: DtOpt[];
  deviceRoles: DrOpt[];
  racks: RackOpt[];
  templates: TemplateOpt[];
  submitting: boolean;
  error: string | null;
  onCancel: () => void;
  onSaveCreate: (body: Record<string, unknown>) => void;
  onSaveEdit: ((body: Record<string, unknown>) => void) | undefined;
  editResourceId?: string;
}) {
  const [name, setName] = useState(initial?.name ?? "");
  const [deviceTypeId, setDeviceTypeId] = useState(initial?.deviceType?.id ?? deviceTypes[0]?.id ?? "");
  const [deviceRoleId, setDeviceRoleId] = useState(initial?.deviceRole?.id ?? deviceRoles[0]?.id ?? "");
  const [rackId, setRackId] = useState(initial?.rack?.id ?? "");
  const [serialNumber, setSerialNumber] = useState(initial?.serialNumber ?? "");
  const [positionU, setPositionU] = useState(initial?.positionU != null ? String(initial.positionU) : "");
  const [face, setFace] = useState(initial?.face ?? "");
  const [status, setStatus] = useState(
    initial?.status && STATUSES.includes(initial.status as (typeof STATUSES)[number]) ? initial.status : "PLANNED",
  );
  const [templateId, setTemplateId] = useState(initial?.templateId ?? "");
  const [kv, setKv] = useState<Record<string, string>>(() =>
    initial?.customAttributes ? stringMapFromUnknown(initial.customAttributes) : {},
  );
  const [localErr, setLocalErr] = useState<string | null>(null);
  const defaultTpl = templates.find((t) => t.isDefault);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLocalErr(null);
    if (!name.trim() || !deviceTypeId || !deviceRoleId) {
      setLocalErr("Name, device type, and role are required.");
      return;
    }
    const body: Record<string, unknown> = {
      name: name.trim(),
      deviceTypeId,
      deviceRoleId,
      rackId: rackId || null,
      serialNumber: serialNumber.trim() || null,
      positionU: positionU.trim() ? Number(positionU) : null,
      face: face.trim() || null,
      status,
      templateId: templateId || null,
      customAttributes: coerceCustomAttributes(kv),
    };
    if (body.positionU !== null && Number.isNaN(body.positionU as number)) {
      setLocalErr("Position (U) must be a number.");
      return;
    }
    if (mode === "create") onSaveCreate(body);
    else onSaveEdit?.(body);
  }

  return (
    <FormPageShell
      title={mode === "create" ? "New device" : "Edit device"}
      subtitle={mode === "create" ? "Register hardware in a rack or unracked." : undefined}
      backTo="/dcim/devices"
      backLabel="Back to devices"
      footer={
        <>
          <button type="button" className="btn btn-ghost" onClick={onCancel} disabled={submitting}>
            Cancel
          </button>
          <button type="submit" form="device-form" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Saving…" : "Save"}
          </button>
        </>
      }
    >
      <form id="device-form" className="form-stack" onSubmit={handleSubmit}>
        {localErr ? <div className="error-banner">{localErr}</div> : null}
        {error ? <div className="error-banner">{error}</div> : null}
        {editResourceId ? (
          <p className="muted" style={{ margin: 0 }}>
            <Link to={`/o/Device/${editResourceId}`}>View relationships (graph)</Link>
          </p>
        ) : null}
        <label>
          Name
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} autoComplete="off" />
        </label>
        <label>
          Device type
          <select className="input" value={deviceTypeId} onChange={(e) => setDeviceTypeId(e.target.value)}>
            {deviceTypes.map((t) => (
              <option key={t.id} value={t.id}>
                {t.manufacturer.name} {t.model}
              </option>
            ))}
          </select>
        </label>
        <label>
          Role
          <select className="input" value={deviceRoleId} onChange={(e) => setDeviceRoleId(e.target.value)}>
            {deviceRoles.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Rack (optional)
          <select className="input" value={rackId} onChange={(e) => setRackId(e.target.value)}>
            <option value="">— None —</option>
            {racks.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Serial number
          <input className="input" value={serialNumber} onChange={(e) => setSerialNumber(e.target.value)} />
        </label>
        <label>
          Position (U)
          <input className="input" value={positionU} onChange={(e) => setPositionU(e.target.value)} inputMode="numeric" />
        </label>
        <label>
          Face
          <input className="input" value={face} onChange={(e) => setFace(e.target.value)} placeholder="front / rear" />
        </label>
        <label>
          Status
          <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
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
