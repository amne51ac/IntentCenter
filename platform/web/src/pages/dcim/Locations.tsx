import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { apiJson } from "../../api/client";
import { DataTable } from "../../components/DataTable";
import { ModelListPageHeader } from "../../components/ModelListPageHeader";
import { RowOverflowMenu } from "../../components/RowOverflowMenu";
import { objectEditHref, objectViewHref } from "../../lib/objectLinks";
import type { LocationRow } from "./LocationFormPage";
import { InlineLoader } from "../../components/Loader";

async function duplicateLocation(id: string): Promise<string> {
  const { item } = await apiJson<{ item: LocationRow }>(`/v1/locations/${id}`);
  const suffix = Date.now().toString(36);
  const res = await apiJson<{ item: { id: string } }>("/v1/locations", {
    method: "POST",
    body: JSON.stringify({
      name: `${item.name} (copy)`,
      slug: `${item.slug}-copy-${suffix}`,
      locationTypeId: item.locationType.id,
      parentId: item.parent?.id ?? null,
      description: item.description ?? null,
      templateId: item.templateId ?? null,
      customAttributes: item.customAttributes ?? {},
    }),
  });
  return res.item.id;
}

export function LocationsPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["locations"],
    queryFn: () => apiJson<{ items: LocationRow[] }>("/v1/locations"),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => apiJson(`/v1/locations/${id}`, { method: "DELETE" }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["locations"] }),
  });

  const dupMut = useMutation({
    mutationFn: duplicateLocation,
    onSuccess: (newId) => {
      void qc.invalidateQueries({ queryKey: ["locations"] });
      navigate(`/dcim/locations/${newId}/edit`);
    },
  });

  const err =
    q.error || deleteMut.error || dupMut.error ? String(q.error || deleteMut.error || dupMut.error) : null;

  function confirmArchive() {
    return window.confirm(
      "Archive this location? It will be removed from the active list. Child locations or racks must be moved first.",
    );
  }

  function confirmDelete(name: string) {
    return window.confirm(
      `Delete “${name}”? This removes it from inventory (same as archive). Child locations or racks must be moved first.`,
    );
  }

  return (
    <>
      <ModelListPageHeader
        title="Locations"
        subtitle="Physical / logical sites and hierarchy — click a row for details, or Edit for the form"
        addNew={{ to: "/dcim/locations/new", label: "Add location" }}
        bulkResourceType="Location"
        onBulkSuccess={() => void qc.invalidateQueries({ queryKey: ["locations"] })}
      />
      <div className="main-body">
        {q.isLoading ? <InlineLoader /> : null}
        {err ? <div className="error-banner">{err}</div> : null}
        {q.data ? (
          <DataTable
            columns={[
              { key: "name", label: "Name" },
              { key: "slug", label: "Slug" },
              { key: "type", label: "Type" },
              { key: "parent", label: "Parent" },
            ]}
            rows={q.data.items.map((i) => ({
              _id: i.id,
              name: i.name,
              slug: i.slug,
              type: i.locationType?.name ?? "—",
              parent: i.parent?.name ?? "—",
            }))}
            onRowClick={(row) => navigate(objectViewHref("Location", String(row._id)))}
            actionsColumn={{
              label: "",
              render: (row) => {
                const id = String(row._id);
                const name = String(row.name);
                const edit = objectEditHref("Location", id);
                return (
                  <>
                    {edit ? (
                      <Link to={edit} className="btn btn-ghost table-inline-link" onClick={(e) => e.stopPropagation()}>
                        Edit
                      </Link>
                    ) : null}
                    <RowOverflowMenu
                    items={[
                      {
                        id: "dup",
                        label: "Copy",
                        onSelect: () => {
                          void dupMut.mutateAsync(id).catch(() => undefined);
                        },
                      },
                      {
                        id: "archive",
                        label: "Archive",
                        onSelect: () => {
                          if (!confirmArchive()) return;
                          deleteMut.mutate(id);
                        },
                      },
                      {
                        id: "delete",
                        label: "Delete",
                        danger: true,
                        onSelect: () => {
                          if (!confirmDelete(name)) return;
                          deleteMut.mutate(id);
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
    </>
  );
}
