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
  vid: number;
  name: string;
  vlanGroup: { name: string } | null;
};

export function VlansPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["vlans"],
    queryFn: () => apiJson<{ items: Row[] }>("/v1/vlans"),
  });

  return (
    <>
      <ModelListPageHeader
        title="VLANs"
        subtitle="L2 segments — click a row to open"
        addNew={{ to: "/ipam/vlans/new", label: "Add VLAN" }}
        bulkResourceType="Vlan"
        onBulkSuccess={() => void qc.invalidateQueries({ queryKey: ["vlans"] })}
      />
      <div className="main-body">
        {q.isLoading ? <InlineLoader /> : null}
        {q.error ? <div className="error-banner">{String(q.error)}</div> : null}
        {q.data ? (
          <DataTable
            columns={[
              { key: "vid", label: "VID" },
              { key: "name", label: "Name" },
              { key: "group", label: "Group" },
            ]}
            rows={q.data.items.map((i) => ({
              _id: i.id,
              vid: i.vid,
              name: i.name,
              group: i.vlanGroup?.name ?? "—",
            }))}
            onRowClick={(row) => navigate(objectHref("Vlan", String(row._id)))}
            actionsColumn={{
              label: "",
              render: () => (
                <RowOverflowMenu
                  items={[
                    { id: "copy", label: "Copy", onSelect: () => notifyActionUnavailable("Copy") },
                    { id: "archive", label: "Archive", onSelect: () => notifyActionUnavailable("Archive") },
                    { id: "delete", label: "Delete", danger: true, onSelect: () => notifyActionUnavailable("Delete") },
                  ]}
                />
              ),
            }}
          />
        ) : null}
      </div>
    </>
  );
}
