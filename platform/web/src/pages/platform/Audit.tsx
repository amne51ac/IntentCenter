import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { apiJson } from "../../api/client";
import { DataTable } from "../../components/DataTable";
import { ModelListPageHeader } from "../../components/ModelListPageHeader";
import { InlineLoader } from "../../components/Loader";
import { RowOverflowMenu } from "../../components/RowOverflowMenu";
import { objectHref } from "../../lib/objectLinks";
import { notifyActionUnavailable } from "../../lib/rowActions";

type Row = {
  createdAt: string;
  actor: string;
  action: string;
  resourceType: string;
  resourceId: string;
};

export function AuditPage() {
  const navigate = useNavigate();
  const q = useQuery({
    queryKey: ["audit"],
    queryFn: () => apiJson<{ items: Row[] }>("/v1/audit-events?limit=100"),
  });

  return (
    <>
      <ModelListPageHeader title="Audit log" subtitle="Recent changes (newest first)" showBulkTools={false} />
      <div className="main-body">
        {q.isLoading ? <InlineLoader /> : null}
        {q.error ? <div className="error-banner">{String(q.error)}</div> : null}
        {q.data ? (
          <DataTable
            columns={[
              { key: "createdAt", label: "Time" },
              { key: "actor", label: "Actor" },
              { key: "action", label: "Action" },
              { key: "resourceType", label: "Resource" },
              { key: "resourceId", label: "ID" },
            ]}
            rows={q.data.items.map((i) => ({
              _id: `${i.resourceType}-${i.resourceId}-${i.createdAt}`,
              createdAt: new Date(i.createdAt).toLocaleString(),
              actor: i.actor,
              action: i.action,
              resourceType: i.resourceType,
              resourceId: i.resourceId,
            }))}
            onRowClick={(row) => {
              navigate(objectHref(String(row.resourceType), String(row.resourceId)));
            }}
            actionsColumn={{
              label: "",
              render: (row) => {
                const id = String(row.resourceId);
                const line = `${row.resourceType}\t${id}`;
                return (
                  <RowOverflowMenu
                    items={[
                      {
                        id: "copy",
                        label: "Copy",
                        onSelect: () => {
                          void navigator.clipboard.writeText(line).catch(() => notifyActionUnavailable("Copy"));
                        },
                      },
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
