import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiJson } from "../../api/client";
import { FormPageShell } from "../../components/FormPageShell";
import { InlineLoader } from "../../components/Loader";
import { objectViewHref } from "../../lib/objectLinks";

type JobRow = { id: string; key: string; name: string; enabled: boolean };

export function JobRunFormPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [jobKey, setJobKey] = useState("");
  const [inputJson, setInputJson] = useState("{}");
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const jobs = useQuery({
    queryKey: ["jobs"],
    queryFn: () => apiJson<{ items: JobRow[] }>("/v1/jobs"),
  });

  const runMut = useMutation({
    mutationFn: async ({ key, input, idempotencyKey: ik }: { key: string; input: Record<string, unknown> | null; idempotencyKey: string | null }) => {
      const body: Record<string, unknown> = {};
      if (input && Object.keys(input).length > 0) body.input = input;
      if (ik) body.idempotencyKey = ik;
      return apiJson<{ item: { id: string } }>(`/v1/jobs/${encodeURIComponent(key)}/run`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    onSuccess: async (data) => {
      await qc.invalidateQueries({ queryKey: ["job-runs"] });
      navigate(objectViewHref("JobRun", data.item.id), { replace: true });
    },
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    if (!jobKey.trim()) {
      setErr("Select a job.");
      return;
    }
    let parsed: Record<string, unknown> | null = null;
    const raw = inputJson.trim();
    if (raw && raw !== "{}") {
      try {
        const j = JSON.parse(raw) as unknown;
        if (j === null || typeof j !== "object" || Array.isArray(j)) {
          setErr("Input must be a JSON object.");
          return;
        }
        parsed = j as Record<string, unknown>;
      } catch {
        setErr("Input must be valid JSON.");
        return;
      }
    }
    runMut.mutate({
      key: jobKey.trim(),
      input: parsed,
      idempotencyKey: idempotencyKey.trim() || null,
    });
  }

  if (jobs.isLoading) {
    return (
      <FormPageShell title="Run job" subtitle="Queue an execution for a job definition" backTo="/platform/job-runs" backLabel="Back to job runs">
        <InlineLoader label="Loading job definitions…" />
      </FormPageShell>
    );
  }

  return (
    <FormPageShell
      title="Run job"
      subtitle="Queue an execution for a job definition"
      backTo="/platform/job-runs"
      backLabel="Back to job runs"
      footer={
        <>
          <button type="button" className="btn btn-ghost" onClick={() => navigate("/platform/job-runs")}>
            Cancel
          </button>
          <button type="submit" form="jobrun-new-form" className="btn btn-primary" disabled={runMut.isPending}>
            {runMut.isPending ? "Starting…" : "Run"}
          </button>
        </>
      }
    >
      <form id="jobrun-new-form" className="form-stack" onSubmit={onSubmit}>
        {err ? <div className="error-banner">{err}</div> : null}
        {runMut.error ? <div className="error-banner">{String(runMut.error)}</div> : null}
        <label>
          Job
          <select className="input" value={jobKey} onChange={(e) => setJobKey(e.target.value)} required>
            <option value="">— Select —</option>
            {jobs.data?.items.map((j) => (
              <option key={j.id} value={j.key} disabled={!j.enabled}>
                {j.name} ({j.key}){j.enabled ? "" : " — disabled"}
              </option>
            ))}
          </select>
        </label>
        {(jobs.data?.items?.length ?? 0) === 0 ? (
          <p className="muted">No job definitions yet. Create one under Platform → Jobs first.</p>
        ) : null}
        <label>
          Input (JSON object, optional)
          <textarea className="input mono" rows={6} value={inputJson} onChange={(e) => setInputJson(e.target.value)} spellCheck={false} />
        </label>
        <label>
          Idempotency key (optional)
          <input className="input mono" value={idempotencyKey} onChange={(e) => setIdempotencyKey(e.target.value)} autoComplete="off" />
        </label>
      </form>
    </FormPageShell>
  );
}
