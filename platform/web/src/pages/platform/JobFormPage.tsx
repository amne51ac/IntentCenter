import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { useMatch, useNavigate, useParams } from "react-router-dom";
import { apiJson } from "../../api/client";
import { FormPageShell } from "../../components/FormPageShell";
import { InlineLoader } from "../../components/Loader";
import { objectViewHref } from "../../lib/objectLinks";

type JobItem = {
  id: string;
  key: string;
  name: string;
  description: string | null;
  requiresApproval: boolean;
  enabled: boolean;
};

export function JobFormPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const isNew = useMatch({ path: "/platform/jobs/new", end: true }) !== null;
  const { jobId } = useParams<{ jobId: string }>();
  const id = isNew ? undefined : jobId;

  const [key, setKey] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [requiresApproval, setRequiresApproval] = useState(false);
  const [enabled, setEnabled] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const detailQ = useQuery({
    queryKey: ["job-definition", id],
    queryFn: () => apiJson<{ item: JobItem }>(`/v1/jobs/${id}`),
    enabled: Boolean(id),
  });

  useEffect(() => {
    const row = detailQ.data?.item;
    if (!row) return;
    setKey(row.key);
    setName(row.name);
    setDescription(row.description ?? "");
    setRequiresApproval(row.requiresApproval);
    setEnabled(row.enabled);
  }, [detailQ.data?.item]);

  const createMut = useMutation({
    mutationFn: (body: { key: string; name: string; description: string | null; requiresApproval: boolean | null }) =>
      apiJson<{ item: { id: string } }>("/v1/jobs", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: async (data) => {
      await qc.invalidateQueries({ queryKey: ["jobs"] });
      navigate(objectViewHref("JobDefinition", data.item.id), { replace: true });
    },
  });

  const patchMut = useMutation({
    mutationFn: (body: {
      key?: string;
      name?: string;
      description?: string | null;
      requiresApproval?: boolean;
      enabled?: boolean;
    }) => apiJson<{ item: { id: string } }>(`/v1/jobs/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["jobs"] });
      navigate(objectViewHref("JobDefinition", id!), { replace: true });
    },
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    if (!key.trim()) {
      setErr("Key is required.");
      return;
    }
    if (!name.trim()) {
      setErr("Name is required.");
      return;
    }
    if (isNew) {
      createMut.mutate({
        key: key.trim(),
        name: name.trim(),
        description: description.trim() || null,
        requiresApproval,
      });
    } else {
      patchMut.mutate({
        key: key.trim(),
        name: name.trim(),
        description: description.trim() || null,
        requiresApproval,
        enabled,
      });
    }
  }

  const pending = createMut.isPending || patchMut.isPending;

  if (!isNew && id && detailQ.isLoading) {
    return (
      <FormPageShell title="Edit job definition" subtitle="Automation hook identifier" backTo="/platform/jobs" backLabel="Back to jobs">
        <InlineLoader label="Loading…" />
      </FormPageShell>
    );
  }

  if (!isNew && (detailQ.isError || !detailQ.data?.item)) {
    return (
      <FormPageShell title="Edit job definition" subtitle="Automation hook identifier" backTo="/platform/jobs" backLabel="Back to jobs">
        <div className="error-banner">{detailQ.isError ? String(detailQ.error) : "Not found"}</div>
      </FormPageShell>
    );
  }

  return (
    <FormPageShell
      title={isNew ? "New job definition" : "Edit job definition"}
      subtitle="Automation hook identifier"
      backTo="/platform/jobs"
      backLabel="Back to jobs"
      footer={
        <>
          <button type="button" className="btn btn-ghost" onClick={() => navigate("/platform/jobs")}>
            Cancel
          </button>
          <button type="submit" form="job-form" className="btn btn-primary" disabled={pending}>
            {pending ? "Saving…" : isNew ? "Create" : "Save"}
          </button>
        </>
      }
    >
      <form id="job-form" className="form-stack" onSubmit={onSubmit}>
        {err ? <div className="error-banner">{err}</div> : null}
        {createMut.error ? <div className="error-banner">{String(createMut.error)}</div> : null}
        {patchMut.error ? <div className="error-banner">{String(patchMut.error)}</div> : null}
        <label>
          Key
          <input className="input mono" value={key} onChange={(e) => setKey(e.target.value)} placeholder="e.g. sync_inventory" required autoComplete="off" />
        </label>
        <label>
          Display name
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} required autoComplete="off" />
        </label>
        <label>
          Description (optional)
          <textarea className="input" rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <input type="checkbox" checked={requiresApproval} onChange={(e) => setRequiresApproval(e.target.checked)} />
          <span>Requires approval before run</span>
        </label>
        {!isNew ? (
          <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
            <span>Enabled</span>
          </label>
        ) : null}
      </form>
    </FormPageShell>
  );
}
