import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { apiJson } from "../../api/client";
import { DataTable } from "../../components/DataTable";
import { ModelListPageHeader } from "../../components/ModelListPageHeader";
import { InlineLoader } from "../../components/Loader";
import { RowOverflowMenu } from "../../components/RowOverflowMenu";
import { objectHref } from "../../lib/objectLinks";
import { notifyActionUnavailable } from "../../lib/rowActions";

type Row = { id: string; name: string; rd: string | null };

export function VrfsPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["vrfs"],
    queryFn: () => apiJson<{ items: Row[] }>("/v1/vrfs"),
  });

  const dupMut = useMutation({
    mutationFn: async (row: Row) => {
      const res = await apiJson<{ item: { id: string } }>("/v1/vrfs", {
        method: "POST",
        body: JSON.stringify({
          name: `${row.name} (copy)`,
          rd: row.rd,
        }),
      });
      return res.item.id;
    },
    onSuccess: (newId) => {
      void qc.invalidateQueries({ queryKey: ["vrfs"] });
      navigate(objectHref("Vrf", newId));
    },
  });

  const err = q.error || dupMut.error ? String(q.error || dupMut.error) : null;

  return (
    <>
      <ModelListPageHeader
        title="VRFs"
        subtitle="Routing / VPN contexts — click a row to open"
        addNew={{ to: "/ipam/vrfs/new", label: "Add VRF" }}
        bulkResourceType="Vrf"
        onBulkSuccess={() => void qc.invalidateQueries({ queryKey: ["vrfs"] })}
      />
      <div className="main-body">
        {q.isLoading ? <InlineLoader /> : null}
        {err ? <div className="error-banner">{err}</div> : null}
        {q.data ? (
          <DataTable
            columns={[
              { key: "name", label: "Name" },
              { key: "rd", label: "RD" },
            ]}
            rows={q.data.items.map((i) => ({
              _id: i.id,
              name: i.name,
              rd: i.rd ?? "—",
            }))}
            onRowClick={(row) => navigate(objectHref("Vrf", String(row._id)))}
            actionsColumn={{
              label: "",
              render: (row) => {
                const id = String(row._id);
                const name = String(row.name);
                const full = q.data!.items.find((x) => x.id === id);
                return (
                  <RowOverflowMenu
                    items={[
                      {
                        id: "copy",
                        label: "Copy",
                        onSelect: () => {
                          if (!full) return;
                          void dupMut.mutateAsync(full).catch(() => undefined);
                        },
                      },
                      {
                        id: "archive",
                        label: "Archive",
                        onSelect: () => {
                          if (!window.confirm(`Archive VRF “${name}”?`)) return;
                          notifyActionUnavailable("Archive");
                        },
                      },
                      {
                        id: "delete",
                        label: "Delete",
                        danger: true,
                        onSelect: () => {
                          if (!window.confirm(`Delete VRF “${name}”?`)) return;
                          notifyActionUnavailable("Delete");
                        },
                      },
                    ]}
                  />
                );
              },
            }}
          />
        ) : null}
      </div>
    </>
  );
}
