import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { apiJson } from "../../api/client";
import { DataTable } from "../../components/DataTable";
import { ModelListPageHeader } from "../../components/ModelListPageHeader";
import { RowOverflowMenu } from "../../components/RowOverflowMenu";
import { objectEditHref, objectViewHref } from "../../lib/objectLinks";
import type { RackRow } from "./RackFormPage";
import { InlineLoader } from "../../components/Loader";

async function duplicateRack(id: string): Promise<string> {
  const { item } = await apiJson<{ item: RackRow }>(`/v1/racks/${id}`);
  const res = await apiJson<{ item: { id: string } }>("/v1/racks", {
    method: "POST",
    body: JSON.stringify({
      name: `${item.name} (copy)`,
      locationId: item.location.id,
      uHeight: item.uHeight,
      templateId: item.templateId ?? null,
      customAttributes: item.customAttributes ?? {},
    }),
  });
  return res.item.id;
}

export function RacksPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["racks"],
    queryFn: () => apiJson<{ items: RackRow[] }>("/v1/racks"),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => apiJson(`/v1/racks/${id}`, { method: "DELETE" }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["racks"] }),
  });

  const dupMut = useMutation({
    mutationFn: duplicateRack,
    onSuccess: (newId) => {
      void qc.invalidateQueries({ queryKey: ["racks"] });
      navigate(`/dcim/racks/${newId}/edit`);
    },
  });

  const err = q.error || deleteMut.error || dupMut.error ? String(q.error || deleteMut.error || dupMut.error) : null;

  function confirmArchive() {
    return window.confirm(
      "Archive this rack? It will be removed from the active list. Devices must be moved first.",
    );
  }

  function confirmDelete(name: string) {
    return window.confirm(
      `Delete “${name}”? This removes it from inventory (same as archive). Devices must be moved first.`,
    );
  }

  return (
    <>
      <ModelListPageHeader
        title="Racks"
        subtitle="Cabinet inventory by location — click a row for details, or Edit for the form"
        addNew={{ to: "/dcim/racks/new", label: "Add rack" }}
        bulkResourceType="Rack"
        onBulkSuccess={() => void qc.invalidateQueries({ queryKey: ["racks"] })}
      />
      <div className="main-body">
        {q.isLoading ? <InlineLoader /> : null}
        {err ? <div className="error-banner">{err}</div> : null}
        {q.data ? (
          <DataTable
            columns={[
              { key: "name", label: "Name" },
              { key: "location", label: "Location" },
              { key: "uHeight", label: "U" },
            ]}
            rows={q.data.items.map((i) => ({
              _id: i.id,
              name: i.name,
              location: i.location?.name ?? "—",
              uHeight: i.uHeight,
            }))}
            onRowClick={(row) => navigate(objectViewHref("Rack", String(row._id)))}
            actionsColumn={{
              label: "",
              render: (row) => {
                const id = String(row._id);
                const name = String(row.name);
                const edit = objectEditHref("Rack", id);
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
