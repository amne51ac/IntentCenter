import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { apiJson } from "../../api/client";
import { DataTable } from "../../components/DataTable";
import { ModelListPageHeader } from "../../components/ModelListPageHeader";
import { InlineLoader } from "../../components/Loader";
import { RowOverflowMenu } from "../../components/RowOverflowMenu";
import { objectHref } from "../../lib/objectLinks";
import { notifyActionUnavailable } from "../../lib/rowActions";

type Row = {
  id: string;
  cidr: string;
  description: string | null;
  vrf: { id: string; name: string };
};

export function PrefixesPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["prefixes"],
    queryFn: () => apiJson<{ items: Row[] }>("/v1/prefixes"),
  });

  return (
    <>
      <ModelListPageHeader
        title="Prefixes"
        subtitle="IP aggregates by VRF — click a row to open"
        addNew={{ to: "/ipam/prefixes/new", label: "Add prefix" }}
        bulkResourceType="Prefix"
        onBulkSuccess={() => void qc.invalidateQueries({ queryKey: ["prefixes"] })}
      />
      <div className="main-body">
        {q.isLoading ? <InlineLoader /> : null}
        {q.error ? <div className="error-banner">{String(q.error)}</div> : null}
        {q.data ? (
          <DataTable
            columns={[
              { key: "cidr", label: "CIDR" },
              { key: "vrf", label: "VRF" },
              { key: "description", label: "Description" },
            ]}
            rows={q.data.items.map((i) => ({
              _id: i.id,
              cidr: i.cidr,
              vrf: i.vrf?.name ?? "—",
              description: i.description ?? "—",
            }))}
            onRowClick={(row) => navigate(objectHref("Prefix", String(row._id)))}
            actionsColumn={{
              label: "",
              render: () => {
                return (
                  <RowOverflowMenu
                    items={[
                      { id: "copy", label: "Copy", onSelect: () => notifyActionUnavailable("Copy") },
                      { id: "archive", label: "Archive", onSelect: () => notifyActionUnavailable("Archive") },
                      { id: "delete", label: "Delete", danger: true, onSelect: () => notifyActionUnavailable("Delete") },
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
