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
  name: string;
  serviceType: string;
  status: string;
  customerRef: string | null;
};

export function ServicesPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["services"],
    queryFn: () => apiJson<{ items: Row[] }>("/v1/services"),
  });

  return (
    <>
      <ModelListPageHeader
        title="Service inventory"
        subtitle="AS1-style logical services over resources"
        addNew={{ to: "/platform/services/new", label: "Add service" }}
        bulkResourceType="ServiceInstance"
        onBulkSuccess={() => void qc.invalidateQueries({ queryKey: ["services"] })}
      />
      <div className="main-body">
        {q.isLoading ? <InlineLoader /> : null}
        {q.error ? <div className="error-banner">{String(q.error)}</div> : null}
        {q.data ? (
          <DataTable
            columns={[
              { key: "name", label: "Name" },
              { key: "serviceType", label: "Type" },
              { key: "status", label: "Status" },
              { key: "customerRef", label: "Customer ref" },
            ]}
            rows={q.data.items.map((i) => ({
              _id: i.id,
              name: i.name,
              serviceType: i.serviceType,
              status: i.status,
              customerRef: i.customerRef ?? "—",
            }))}
            onRowClick={(row) => navigate(objectHref("Service", String(row._id)))}
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
