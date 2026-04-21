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
  address: string;
  description: string | null;
  prefix: { cidr: string };
  interface: { name: string; device: { name: string } } | null;
};

export function IpAddressesPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["ip-addresses"],
    queryFn: () => apiJson<{ items: Row[] }>("/v1/ip-addresses"),
  });

  return (
    <>
      <ModelListPageHeader
        title="IP addresses"
        subtitle="Assignments (sample limit 500) — click a row to open"
        addNew={{ to: "/ipam/ip-addresses/new", label: "Add IP address" }}
        bulkResourceType="IpAddress"
        onBulkSuccess={() => void qc.invalidateQueries({ queryKey: ["ip-addresses"] })}
      />
      <div className="main-body">
        {q.isLoading ? <InlineLoader /> : null}
        {q.error ? <div className="error-banner">{String(q.error)}</div> : null}
        {q.data ? (
          <DataTable
            columns={[
              { key: "address", label: "Address" },
              { key: "prefix", label: "Prefix" },
              { key: "iface", label: "Interface / device" },
              { key: "description", label: "Description" },
            ]}
            rows={q.data.items.map((i) => ({
              _id: i.id,
              address: i.address,
              prefix: i.prefix?.cidr ?? "—",
              iface: i.interface ? `${i.interface.device.name} · ${i.interface.name}` : "—",
              description: i.description ?? "—",
            }))}
            onRowClick={(row) => navigate(objectHref("IpAddress", String(row._id)))}
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
