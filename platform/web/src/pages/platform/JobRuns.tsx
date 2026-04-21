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
  status: string;
  createdAt: string;
  jobDefinition: { name: string; key: string };
};

export function JobRunsPage() {
  const navigate = useNavigate();
  const q = useQuery({
    queryKey: ["job-runs"],
    queryFn: () => apiJson<{ items: Row[] }>("/v1/job-runs"),
  });

  return (
    <>
      <ModelListPageHeader title="Job runs" subtitle="Recent executions" addNew={{ to: "/platform/job-runs/new", label: "Add job run" }} />
      <div className="main-body">
        {q.isLoading ? <InlineLoader /> : null}
        {q.error ? <div className="error-banner">{String(q.error)}</div> : null}
        {q.data ? (
          <DataTable
            columns={[
              { key: "job", label: "Job" },
              { key: "status", label: "Status" },
              { key: "createdAt", label: "Started" },
            ]}
            rows={q.data.items.map((i) => ({
              _id: i.id,
              job: `${i.jobDefinition?.name ?? ""} (${i.jobDefinition?.key ?? ""})`,
              status: i.status,
              createdAt: new Date(i.createdAt).toLocaleString(),
            }))}
            onRowClick={(row) => navigate(objectHref("JobRun", String(row._id)))}
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
