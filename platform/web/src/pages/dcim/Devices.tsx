import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { apiJson } from "../../api/client";
import { DataTable } from "../../components/DataTable";
import { ModelListPageHeader } from "../../components/ModelListPageHeader";
import { RowOverflowMenu } from "../../components/RowOverflowMenu";
import { objectEditHref, objectViewHref } from "../../lib/objectLinks";
import type { DeviceRow } from "./DeviceFormPage";
import { InlineLoader } from "../../components/Loader";

async function duplicateDevice(id: string): Promise<string> {
  const { item } = await apiJson<{ item: DeviceRow }>(`/v1/devices/${id}`);
  const res = await apiJson<{ item: { id: string } }>("/v1/devices", {
    method: "POST",
    body: JSON.stringify({
      name: `${item.name} (copy)`,
      deviceTypeId: item.deviceType.id,
      deviceRoleId: item.deviceRole.id,
      rackId: item.rack?.id ?? null,
      serialNumber: null,
      positionU: item.positionU ?? null,
      face: item.face ?? null,
      status: item.status,
      templateId: item.templateId ?? null,
      customAttributes: item.customAttributes ?? {},
    }),
  });
  return res.item.id;
}

export function DevicesPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["devices"],
    queryFn: () => apiJson<{ items: DeviceRow[] }>("/v1/devices"),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => apiJson(`/v1/devices/${id}`, { method: "DELETE" }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["devices"] }),
  });

  const dupMut = useMutation({
    mutationFn: duplicateDevice,
    onSuccess: (newId) => {
      void qc.invalidateQueries({ queryKey: ["devices"] });
      navigate(`/dcim/devices/${newId}/edit`);
    },
  });

  const err = q.error || deleteMut.error || dupMut.error ? String(q.error || deleteMut.error || dupMut.error) : null;

  function confirmArchive() {
    return window.confirm(
      "Archive this device? It will be removed from the active list. Interfaces must be removed first.",
    );
  }

  function confirmDelete(name: string) {
    return window.confirm(
      `Delete “${name}”? This removes it from inventory (same as archive). Interfaces must be removed first.`,
    );
  }

  return (
    <>
      <ModelListPageHeader
        title="Devices"
        subtitle="Network and facility assets — click a row for details, or Edit for the form"
        addNew={{ to: "/dcim/devices/new", label: "Add device" }}
        bulkResourceType="Device"
        onBulkSuccess={() => void qc.invalidateQueries({ queryKey: ["devices"] })}
      />
      <div className="main-body">
        {q.isLoading ? <InlineLoader /> : null}
        {err ? <div className="error-banner">{err}</div> : null}
        {q.data ? (
          <DataTable
            columns={[
              { key: "name", label: "Name" },
              { key: "role", label: "Role" },
              { key: "model", label: "Model" },
              { key: "status", label: "Status" },
              { key: "rack", label: "Rack" },
            ]}
            rows={q.data.items.map((i) => ({
              _id: i.id,
              name: i.name,
              role: i.deviceRole?.name ?? "—",
              model: `${i.deviceType?.manufacturer?.name ?? ""} ${i.deviceType?.model ?? ""}`.trim(),
              status: i.status,
              rack: i.rack?.name ?? "—",
            }))}
            onRowClick={(row) => navigate(objectViewHref("Device", String(row._id)))}
            actionsColumn={{
              label: "",
              render: (row) => {
                const id = String(row._id);
                const name = String(row.name);
                const edit = objectEditHref("Device", id);
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
