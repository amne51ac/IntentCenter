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
  id: string;
  key: string;
  name: string;
  enabled: boolean;
  requiresApproval: boolean;
};

export function JobsPage() {
  const navigate = useNavigate();
  const q = useQuery({
    queryKey: ["jobs"],
    queryFn: () => apiJson<{ items: Row[] }>("/v1/jobs"),
  });

  return (
    <>
      <ModelListPageHeader title="Job definitions" subtitle="Automation hooks (Phase 1 placeholders)" addNew={{ to: "/platform/jobs/new", label: "Add job" }} />
      <div className="main-body">
        {q.isLoading ? <InlineLoader /> : null}
        {q.error ? <div className="error-banner">{String(q.error)}</div> : null}
        {q.data ? (
          <DataTable
            columns={[
              { key: "key", label: "Key" },
              { key: "name", label: "Name" },
              { key: "enabled", label: "Enabled" },
              { key: "approval", label: "Approval" },
            ]}
            rows={q.data.items.map((i) => ({
              _id: i.id,
              key: i.key,
              name: i.name,
              enabled: i.enabled ? "yes" : "no",
              approval: i.requiresApproval ? "required" : "—",
            }))}
            onRowClick={(row) => navigate(objectHref("JobDefinition", String(row._id)))}
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
