import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiJson } from "../../api/client";
import { DataTable } from "../../components/DataTable";
import { Modal } from "../../components/Modal";
import { ModelListPageHeader } from "../../components/ModelListPageHeader";
import { RowOverflowMenu } from "../../components/RowOverflowMenu";
import { objectViewHref } from "../../lib/objectLinks";
import { notifyActionUnavailable } from "../../lib/rowActions";
import { InlineLoader } from "../../components/Loader";

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

const emptyDef = { version: 1, fields: [] as unknown[] };

export function ObjectTemplatesPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const typesQ = useQuery({
    queryKey: ["template-resource-types"],
    queryFn: () => apiJson<{ items: string[] }>("/v1/templates/resource-types"),
  });
  const [filterType, setFilterType] = useState<string>("");
  const resourceType = filterType || undefined;

  const listQ = useQuery({
    queryKey: ["templates", resourceType],
    queryFn: () => {
      const q = resourceType ? `?resourceType=${encodeURIComponent(resourceType)}` : "";
      return apiJson<{ items: TemplateItem[] }>(`/v1/templates${q}`);
    },
  });

  const [modal, setModal] = useState<
    | { mode: "create" }
    | { mode: "edit"; item: TemplateItem }
    | { mode: "delete"; item: TemplateItem }
    | null
  >(null);

  const createMut = useMutation({
    mutationFn: (body: {
      resourceType: string;
      name: string;
      slug: string;
      description: string | null;
      definition: Record<string, unknown>;
      isDefault: boolean;
    }) => apiJson<{ item: TemplateItem }>("/v1/templates", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["templates"] });
      setModal(null);
    },
  });

  const patchMut = useMutation({
    mutationFn: (args: { id: string; body: Record<string, unknown> }) =>
      apiJson<{ item: TemplateItem }>(`/v1/templates/${args.id}`, {
        method: "PATCH",
        body: JSON.stringify(args.body),
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["templates"] });
      setModal(null);
    },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => apiJson(`/v1/templates/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["templates"] });
      setModal(null);
    },
  });

  const typeOptions = typesQ.data?.items ?? [];

  const err =
    createMut.error || patchMut.error || deleteMut.error || listQ.error || typesQ.error
      ? String(createMut.error || patchMut.error || deleteMut.error || listQ.error || typesQ.error)
      : null;

  return (
    <>
      <ModelListPageHeader
        title="Object templates"
        subtitle="Click a row to view template details; use Edit for the form designer."
        extraActions={
          <>
            <select
              className="input"
              style={{ maxWidth: "12rem" }}
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              aria-label="Filter by resource type"
              disabled={typesQ.isLoading}
            >
              <option value="">All types</option>
              {typeOptions.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <button type="button" className="btn btn-primary" onClick={() => setModal({ mode: "create" })}>
              New template
            </button>
          </>
        }
      />
      <div className="main-body">
        {listQ.isLoading || typesQ.isLoading ? <InlineLoader /> : null}
        {err ? <div className="error-banner">{err}</div> : null}
        {listQ.data ? (
          <DataTable
            columns={[
              { key: "resourceType", label: "Type" },
              { key: "name", label: "Name" },
              { key: "slug", label: "Slug" },
              { key: "flags", label: "Flags" },
            ]}
            rows={listQ.data.items.map((i) => ({
              _id: i.id,
              resourceType: i.resourceType,
              name: i.name,
              slug: i.slug,
              flags: [i.isSystem ? "system" : null, i.isDefault ? "default" : null].filter(Boolean).join(" · ") || "—",
            }))}
            onRowClick={(row) => navigate(objectViewHref("ObjectTemplate", String(row._id)))}
            actionsColumn={{
              label: "",
              render: (row) => {
                const item = listQ.data!.items.find((x) => x.id === row._id);
                if (!item) return null;
                return (
                  <>
                    <button
                      type="button"
                      className="btn btn-ghost table-inline-link"
                      onClick={(e) => {
                        e.stopPropagation();
                        setModal({ mode: "edit", item });
                      }}
                    >
                      Edit
                    </button>
                    <RowOverflowMenu
                    items={[
                      {
                        id: "copy",
                        label: "Copy",
                        onSelect: () => notifyActionUnavailable("Copy"),
                      },
                      {
                        id: "archive",
                        label: "Archive",
                        onSelect: () => notifyActionUnavailable("Archive"),
                      },
                      {
                        id: "delete",
                        label: "Delete",
                        danger: true,
                        onSelect: () => {
                          if (!item.isSystem) setModal({ mode: "delete", item });
                          else notifyActionUnavailable("Delete");
                        },
                      },
                    ]}
                  />
                  </>
                );
              },
            }}
          />
        ) : null}
      </div>

      {modal?.mode === "create" ? (
        <TemplateCreateModal
          resourceTypes={typeOptions}
          onClose={() => setModal(null)}
          onSubmit={(b) => createMut.mutate(b)}
          submitting={createMut.isPending}
        />
      ) : null}
      {modal?.mode === "edit" ? (
        <TemplateEditModal
          item={modal.item}
          onClose={() => setModal(null)}
          onSubmit={(id, body) => patchMut.mutate({ id, body })}
          submitting={patchMut.isPending}
        />
      ) : null}
      {modal?.mode === "delete" ? (
        <Modal
          title="Delete template"
          onClose={() => setModal(null)}
          footer={
            <>
              <button type="button" className="btn btn-ghost" onClick={() => setModal(null)}>
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => deleteMut.mutate(modal.item.id)}
                disabled={deleteMut.isPending}
              >
                Delete
              </button>
            </>
          }
        >
          <p style={{ margin: 0, fontSize: "0.9rem" }}>
            Delete <strong>{modal.item.name}</strong> ({modal.item.slug})? This cannot be undone.
          </p>
        </Modal>
      ) : null}
    </>
  );
}

function TemplateCreateModal({
  resourceTypes,
  onClose,
  onSubmit,
  submitting,
}: {
  resourceTypes: string[];
  onClose: () => void;
  onSubmit: (body: {
    resourceType: string;
    name: string;
    slug: string;
    description: string | null;
    definition: Record<string, unknown>;
    isDefault: boolean;
  }) => void;
  submitting: boolean;
}) {
  const [resourceType, setResourceType] = useState(resourceTypes[0] ?? "");
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [defJson, setDefJson] = useState(JSON.stringify(emptyDef, null, 2));
  const [isDefault, setIsDefault] = useState(false);
  const [localErr, setLocalErr] = useState<string | null>(null);

  const defObj = useMemo(() => {
    try {
      return JSON.parse(defJson) as Record<string, unknown>;
    } catch {
      return null;
    }
  }, [defJson]);

  function submit() {
    setLocalErr(null);
    if (!resourceType.trim()) {
      setLocalErr("Choose a resource type.");
      return;
    }
    if (!name.trim() || !slug.trim()) {
      setLocalErr("Name and slug are required.");
      return;
    }
    if (!defObj) {
      setLocalErr("Definition must be valid JSON.");
      return;
    }
    onSubmit({
      resourceType: resourceType.trim(),
      name: name.trim(),
      slug: slug.trim().toLowerCase(),
      description: description.trim() || null,
      definition: defObj,
      isDefault,
    });
  }

  return (
    <Modal
      title="New template"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn btn-ghost" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button type="button" className="btn btn-primary" onClick={submit} disabled={submitting}>
            Create
          </button>
        </>
      }
    >
      <div className="form-stack">
        {localErr ? <div className="error-banner">{localErr}</div> : null}
        <label>
          Resource type
          <select className="input" value={resourceType} onChange={(e) => setResourceType(e.target.value)}>
            {resourceTypes.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <label>
          Name
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label>
          Slug
          <input className="input" value={slug} onChange={(e) => setSlug(e.target.value)} placeholder="e.g. warehouse-a" />
        </label>
        <label>
          Description
          <input className="input" value={description} onChange={(e) => setDescription(e.target.value)} />
        </label>
        <label style={{ flexDirection: "row", alignItems: "center", gap: "0.5rem" }}>
          <input type="checkbox" checked={isDefault} onChange={(e) => setIsDefault(e.target.checked)} />
          Set as default for this resource type
        </label>
        <label>
          Definition (JSON)
          <textarea className="input" value={defJson} onChange={(e) => setDefJson(e.target.value)} spellCheck={false} />
        </label>
        <p className="muted" style={{ margin: 0, fontSize: "0.78rem" }}>
          Add custom fields under <code className="mono">fields</code> with{" "}
          <code className="mono">&#123; key, label, type, builtin: false &#125;</code> for extensions.
        </p>
      </div>
    </Modal>
  );
}

function TemplateEditModal({
  item,
  onClose,
  onSubmit,
  submitting,
}: {
  item: TemplateItem;
  onClose: () => void;
  onSubmit: (id: string, body: Record<string, unknown>) => void;
  submitting: boolean;
}) {
  const [name, setName] = useState(item.name);
  const [description, setDescription] = useState(item.description ?? "");
  const [defJson, setDefJson] = useState(JSON.stringify(item.definition ?? emptyDef, null, 2));
  const [isDefault, setIsDefault] = useState(item.isDefault);
  const [localErr, setLocalErr] = useState<string | null>(null);

  const defObj = useMemo(() => {
    try {
      return JSON.parse(defJson) as Record<string, unknown>;
    } catch {
      return null;
    }
  }, [defJson]);

  function submit() {
    setLocalErr(null);
    if (!name.trim()) {
      setLocalErr("Name is required.");
      return;
    }
    if (!defObj) {
      setLocalErr("Definition must be valid JSON.");
      return;
    }
    onSubmit(item.id, {
      name: name.trim(),
      description: description.trim() || null,
      definition: defObj,
      isDefault,
    });
  }

  return (
    <Modal
      title={item.isSystem ? `Edit system template (${item.slug})` : `Edit ${item.name}`}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn btn-ghost" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button type="button" className="btn btn-primary" onClick={submit} disabled={submitting}>
            Save
          </button>
        </>
      }
    >
      <div className="form-stack">
        {localErr ? <div className="error-banner">{localErr}</div> : null}
        <p className="muted" style={{ margin: 0, fontSize: "0.82rem" }}>
          {item.resourceType} · <span className="mono">{item.slug}</span>
          {item.isSystem ? (
            <>
              {" "}
              <span className="badge">system</span>
            </>
          ) : null}
        </p>
        <label>
          Name
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} disabled={item.isSystem} />
        </label>
        <label>
          Description
          <input className="input" value={description} onChange={(e) => setDescription(e.target.value)} />
        </label>
        <label style={{ flexDirection: "row", alignItems: "center", gap: "0.5rem" }}>
          <input type="checkbox" checked={isDefault} onChange={(e) => setIsDefault(e.target.checked)} />
          Default for {item.resourceType}
        </label>
        <label>
          Definition (JSON)
          <textarea className="input" value={defJson} onChange={(e) => setDefJson(e.target.value)} spellCheck={false} />
        </label>
      </div>
    </Modal>
  );
}
