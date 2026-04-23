import { useQuery } from "@tanstack/react-query";
import { Suspense, type ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { apiJson } from "./api/client";
import { BlockLoader } from "./components/Loader";
import * as P from "./lazyPages";

function RequireAuth({ children }: { children: ReactNode }) {
  const session = useQuery({
    queryKey: ["me"],
    queryFn: () => apiJson<unknown>("/v1/me"),
    retry: false,
  });

  if (session.isLoading) {
    return (
      <div className="main">
        <BlockLoader label="Loading session…" />
      </div>
    );
  }

  if (session.isError) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function RouteFallback() {
  return (
    <div className="main">
      <BlockLoader label="Loading…" />
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/login" element={<P.LoginPage />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <P.AppShell />
            </RequireAuth>
          }
        >
          <Route index element={<P.Dashboard />} />
          <Route path="dcim/locations/new" element={<P.LocationFormPage />} />
          <Route path="dcim/locations/:locationId/edit" element={<P.LocationFormPage />} />
          <Route path="dcim/locations" element={<P.LocationsPage />} />
          <Route path="dcim/racks/new" element={<P.RackFormPage />} />
          <Route path="dcim/racks/:rackId/edit" element={<P.RackFormPage />} />
          <Route path="dcim/racks" element={<P.RacksPage />} />
          <Route path="dcim/devices/new" element={<P.DeviceFormPage />} />
          <Route path="dcim/devices/:deviceId/edit" element={<P.DeviceFormPage />} />
          <Route path="dcim/devices" element={<P.DevicesPage />} />
          <Route path="ipam/vrfs/new" element={<P.VrfFormPage />} />
          <Route path="ipam/vrfs/:vrfId/edit" element={<P.VrfFormPage />} />
          <Route path="ipam/vrfs" element={<P.VrfsPage />} />
          <Route path="ipam/prefixes/new" element={<P.PrefixFormPage />} />
          <Route path="ipam/prefixes/:prefixId/edit" element={<P.PrefixFormPage />} />
          <Route path="ipam/prefixes" element={<P.PrefixesPage />} />
          <Route path="ipam/ip-addresses/new" element={<P.IpAddressFormPage />} />
          <Route path="ipam/ip-addresses/:ipAddressId/edit" element={<P.IpAddressFormPage />} />
          <Route path="ipam/ip-addresses" element={<P.IpAddressesPage />} />
          <Route path="ipam/vlans/new" element={<P.VlanFormPage />} />
          <Route path="ipam/vlans/:vlanId/edit" element={<P.VlanFormPage />} />
          <Route path="ipam/vlans" element={<P.VlansPage />} />
          <Route path="circuits/providers/new" element={<P.ProviderFormPage />} />
          <Route path="circuits/providers/:providerId/edit" element={<P.ProviderFormPage />} />
          <Route path="circuits/providers" element={<P.ProvidersPage />} />
          <Route path="circuits/circuits/new" element={<P.CircuitFormPage />} />
          <Route path="circuits/circuits/:circuitId/edit" element={<P.CircuitFormPage />} />
          <Route path="circuits/circuits" element={<P.CircuitsPage />} />
          <Route path="platform/jobs/new" element={<P.JobFormPage />} />
          <Route path="platform/jobs/:jobId/edit" element={<P.JobFormPage />} />
          <Route path="platform/jobs" element={<P.JobsPage />} />
          <Route path="platform/job-runs/new" element={<P.JobRunFormPage />} />
          <Route path="platform/job-runs" element={<P.JobRunsPage />} />
          <Route path="platform/services/new" element={<P.ServiceFormPage />} />
          <Route path="platform/services/:serviceId/edit" element={<P.ServiceFormPage />} />
          <Route path="platform/services" element={<P.ServicesPage />} />
          <Route path="platform/audit" element={<P.AuditPage />} />
          <Route path="platform/object-templates/:templateId/edit" element={<P.ObjectTemplateEditPage />} />
          <Route path="platform/object-templates" element={<P.ObjectTemplatesPage />} />
          <Route path="inventory/:catalogSlug/new" element={<P.CatalogItemCreatePage />} />
          <Route path="inventory/:catalogSlug/:itemId/edit" element={<P.CatalogItemEditPage />} />
          <Route path="inventory/:catalogSlug" element={<P.CatalogListPage />} />
          <Route path="coming-soon/:slug" element={<P.ComingSoonPage />} />
          <Route path="o/:resourceType/:resourceId" element={<P.ObjectViewPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
