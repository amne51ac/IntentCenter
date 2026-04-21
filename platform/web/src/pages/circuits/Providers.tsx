import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { apiJson } from "../../api/client";
import { DataTable } from "../../components/DataTable";
import { ModelListPageHeader } from "../../components/ModelListPageHeader";
import { InlineLoader } from "../../components/Loader";
import { RowOverflowMenu } from "../../components/RowOverflowMenu";
import { objectHref } from "../../lib/objectLinks";
import { notifyActionUnavailable } from "../../lib/rowActions";

type Row = { id: string; name: string; asn: number | null };

export function ProvidersPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["providers"],
    queryFn: () => apiJson<{ items: Row[] }>("/v1/providers"),
  });

  return (
    <>
      <ModelListPageHeader
        title="Carriers & providers"
        subtitle="ASN and circuit vendors — click a row to open"
        addNew={{ to: "/circuits/providers/new", label: "Add provider" }}
        bulkResourceType="Provider"
        onBulkSuccess={() => void qc.invalidateQueries({ queryKey: ["providers"] })}
      />
      <div className="main-body">
        {q.isLoading ? <InlineLoader /> : null}
        {q.error ? <div className="error-banner">{String(q.error)}</div> : null}
        {q.data ? (
          <DataTable
            columns={[
              { key: "name", label: "Name" },
              { key: "asn", label: "ASN" },
            ]}
            rows={q.data.items.map((i) => ({
              _id: i.id,
              name: i.name,
              asn: i.asn ?? "—",
            }))}
            onRowClick={(row) => navigate(objectHref("Provider", String(row._id)))}
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
