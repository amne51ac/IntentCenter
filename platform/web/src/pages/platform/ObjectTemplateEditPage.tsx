import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { apiJson } from "../../api/client";
import { FormPageShell } from "../../components/FormPageShell";
import { InlineLoader } from "../../components/Loader";
import { objectViewHref } from "../../lib/objectLinks";

type TemplateItem = {
  id: string;
  resourceType: string;
  name: string;
  slug: string;
  description: string | null;
  isSystem: boolean;
  isDefault: boolean;
  definition: Record<string, unknown>;
};

export function ObjectTemplateEditPage() {
  const { templateId = "" } = useParams<{ templateId: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [definitionJson, setDefinitionJson] = useState("{}");
  const [isDefault, setIsDefault] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const detailQ = useQuery({
    queryKey: ["template", templateId],
    queryFn: () => apiJson<{ item: TemplateItem }>(`/v1/templates/${encodeURIComponent(templateId)}`),
    enabled: Boolean(templateId),
  });

  const item = detailQ.data?.item;

  useEffect(() => {
    if (!item) return;
    setName(item.name);
    setDescription(item.description ?? "");
    setDefinitionJson(JSON.stringify(item.definition ?? {}, null, 2));
    setIsDefault(item.isDefault);
  }, [item]);

  const patchMut = useMutation({
    mutationFn: (body: { name?: string; description?: string | null; definition?: Record<string, unknown>; isDefault?: boolean }) =>
      apiJson<{ item: TemplateItem }>(`/v1/templates/${encodeURIComponent(templateId)}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["templates"] });
      navigate(objectViewHref("ObjectTemplate", templateId), { replace: true });
    },
  });

  if (detailQ.isLoading) {
    return (
      <FormPageShell title="Edit template" subtitle="Object form definition" backTo="/platform/object-templates" backLabel="Back to templates">
        <InlineLoader label="Loading template…" />
      </FormPageShell>
    );
  }

  if (detailQ.error || !item) {
    return (
      <FormPageShell title="Edit template" subtitle="Object form definition" backTo="/platform/object-templates" backLabel="Back to templates">
        <div className="error-banner">{detailQ.error ? String(detailQ.error) : "Not found"}</div>
      </FormPageShell>
    );
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    let definition: Record<string, unknown> | undefined;
    try {
      definition = JSON.parse(definitionJson) as Record<string, unknown>;
      if (definition === null || typeof definition !== "object" || Array.isArray(definition)) {
        setErr("Definition must be a JSON object.");
        return;
      }
    } catch {
      setErr("Definition must be valid JSON.");
      return;
    }
    patchMut.mutate({
      name: name.trim(),
      description: description.trim() || null,
      definition,
      isDefault,
    });
  }

  return (
    <FormPageShell
      title="Edit template"
      subtitle={`${item.resourceType} · ${item.slug}`}
      backTo="/platform/object-templates"
      backLabel="Back to templates"
      footer={
        <>
          <button type="button" className="btn btn-ghost" onClick={() => navigate("/platform/object-templates")}>
            Cancel
          </button>
          <button type="submit" form="tmpl-edit-form" className="btn btn-primary" disabled={patchMut.isPending}>
            {patchMut.isPending ? "Saving…" : "Save"}
          </button>
        </>
      }
    >
      <form id="tmpl-edit-form" className="form-stack" onSubmit={onSubmit}>
        {err ? <div className="error-banner">{err}</div> : null}
        {patchMut.error ? <div className="error-banner">{String(patchMut.error)}</div> : null}
        <p className="muted mono" style={{ margin: 0 }}>
          {item.resourceType} / {item.slug}
          {item.isSystem ? " · system" : ""}
        </p>
        <label>
          Name
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} required autoComplete="off" />
        </label>
        <label>
          Description
          <textarea className="input" rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
        </label>
        <label>
          Definition (JSON)
          <textarea className="input mono" rows={12} value={definitionJson} onChange={(e) => setDefinitionJson(e.target.value)} spellCheck={false} />
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <input type="checkbox" checked={isDefault} onChange={(e) => setIsDefault(e.target.checked)} />
          <span>Default template for this resource type</span>
        </label>
      </form>
    </FormPageShell>
  );
}
